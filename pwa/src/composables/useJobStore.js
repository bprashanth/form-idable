import { ref } from 'vue'
import * as XLSX from 'xlsx'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

// Module-level singletons — shared across all callers
const jobs        = ref([])
const jobsLoading = ref(false)
const cache       = {}

// Non-reactive: File objects keyed by job_id for same-session upload retry
const _pendingFiles = {}

// VITE_API_BASE_URL is set in .env.production for direct API calls (no proxy).
// In dev the Vite proxy handles /api/* and /vision/*, so no prefix is needed.
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function _authHeaders() {
  const { idToken } = useCognitoAuth()
  const token = idToken.value
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function useJobStore() {
  async function fetchJobs() {
    jobsLoading.value = true
    try {
      const res = await fetch(`${API_BASE}/api/jobs`, { headers: _authHeaders() })
      jobs.value = res.ok ? await res.json() : []
    } finally {
      jobsLoading.value = false
    }
  }

  async function fetchJobDetail(jobId) {
    if (cache[jobId]) return cache[jobId]

    const [mRes, xRes, reviewRes] = await Promise.all([
      fetch(`${API_BASE}/api/jobs/${jobId}/manifest`, { headers: _authHeaders() }),
      fetch(`${API_BASE}/api/jobs/${jobId}/xlsx`,     { headers: _authHeaders() }),
      // Optional v2 artifact. A 404 keeps the production v1 review path fully
      // functional while local/new workers can expose focused review queues.
      fetch(`${API_BASE}/api/jobs/${jobId}/review-manifest`, { headers: _authHeaders() }),
    ])

    if (!mRes.ok) throw new Error(`manifest fetch failed: ${mRes.status}`)
    if (!xRes.ok) throw new Error(`xlsx fetch failed: ${xRes.status}`)

    const manifest = await mRes.json()
    const { url: xlsxPresigned } = await xRes.json()
    const xlsxFetch = await fetch(xlsxPresigned)
    if (!xlsxFetch.ok) throw new Error(`xlsx S3 fetch failed: ${xlsxFetch.status}`)
    const xlsxBuf  = await xlsxFetch.arrayBuffer()
    const wb       = XLSX.read(xlsxBuf, { type: 'array', cellStyles: true })
    let reviewManifest = null
    if (reviewRes.ok) {
      try {
        const candidate = await reviewRes.json()
        if (candidate?.version === 'formidable-review-v1') reviewManifest = candidate
      } catch {
        // The review manifest is additive. A malformed optional artifact must
        // not make the form or its original xlsx impossible to review.
      }
    }
    const xlsxSheets = wb.SheetNames.map(name => ({
      name,
      rows: _parseSheet(wb.Sheets[name]),
    }))
    _ensureReviewCoordinates(xlsxSheets, reviewManifest)
    const xlsxPages = xlsxSheets.map(sheet => sheet.rows)
    const xlsxSheetNames = xlsxSheets.map(sheet => sheet.name)
    const xlsxRows = xlsxPages[0] ?? []

    cache[jobId] = { manifest, xlsxRows, xlsxPages, xlsxSheetNames, reviewManifest }
    return cache[jobId]
  }

  async function initUpload(filename, name, email = '', effort = 'low') {
    const body = { filename, name, effort }
    if (email) body.notification_email = email
    const res = await fetch(`${API_BASE}/vision/extract`, {
      method:  'POST',
      headers: { ..._authHeaders(), 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => res.status)
      throw new Error(`Upload init failed (${res.status}): ${text}`)
    }
    return res.json()  // { job_id, upload_url, status }
  }

  async function s3Put(upload_url, file) {
    const res = await fetch(upload_url, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/octet-stream' },
      body:    file,
    })
    if (!res.ok) throw new Error(`S3 upload failed (${res.status})`)
  }

  async function startJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/start`, {
      method:  'POST',
      headers: _authHeaders(),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => res.status)
      throw new Error(`Job start failed (${res.status}): ${text}`)
    }
    return res.json()  // { status: 'queued' } or { needs_upload: true, upload_url }
  }

  function savePendingFile(jobId, file) {
    _pendingFiles[jobId] = file
  }

  function getPendingFile(jobId) {
    return _pendingFiles[jobId] ?? null
  }

  async function fetchProgress(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/progress`, {
      headers: _authHeaders(),
    })
    if (!res.ok) return null
    return res.json()
  }

  async function fetchAnalytics(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/analytics`, {
      headers: _authHeaders(),
    })
    if (res.status === 404) return null
    if (!res.ok) throw new Error(`analytics fetch failed (${res.status})`)
    const value = await res.json()
    return value?.version === 'formidable-analytics-v1' ? value : null
  }

  async function deleteJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
      method:  'DELETE',
      headers: _authHeaders(),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => res.status)
      throw new Error(`Delete failed (${res.status}): ${text}`)
    }
    // Remove from cache
    delete cache[jobId]
  }

  // Rerun creates a NEW job from the source job's input (the original is left
  // untouched). Returns { job_id, status } for the new job.
  async function rerunJob(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/rerun`, {
      method:  'POST',
      headers: _authHeaders(),
    })
    if (!res.ok) {
      const text = await res.text().catch(() => res.status)
      throw new Error(`Rerun failed (${res.status}): ${text}`)
    }
    return res.json()  // { job_id, status: 'queued' }
  }

  function pollJob(jobId, interval = 5000) {
    const tick = async () => {
      const res = await fetch(`${API_BASE}/api/jobs/${jobId}/status`, {
        headers: _authHeaders(),
      })
      if (!res.ok) return
      const data = await res.json()
      const idx  = jobs.value.findIndex(j => j.job_id === jobId)
      if (idx === -1) return
      jobs.value[idx] = { ...jobs.value[idx], ...data }
      if (data.status !== 'complete' && data.status !== 'failed') {
        setTimeout(tick, interval)
      }
    }
    setTimeout(tick, interval)
  }

  function _parseSheet(ws) {
    if (!ws || !ws['!ref']) return []
    const range = XLSX.utils.decode_range(ws['!ref'])
    const rows  = []
    for (let r = range.s.r; r <= range.e.r; r++) {
      const cells = []
      for (let c = range.s.c; c <= range.e.c; c++) {
        const addr  = XLSX.utils.encode_cell({ r, c })
        const cell  = ws[addr]
        const value = cell ? (cell.v ?? '') : ''
        cells.push({ value, color: _cellColor(cell) })
      }
      rows.push({ rowNum: r + 1, cells })
    }
    return rows
  }

  function _ensureReviewCoordinates(sheets, reviewManifest) {
    if (!reviewManifest) return
    const byName = new Map(sheets.map(sheet => [sheet.name, sheet]))
    for (const target of reviewManifest.cells ?? []) {
      const sheet = byName.get(target.xlsx_sheet)
      const rowNumber = Number(target.xlsx_row)
      const columnNumber = Number(target.xlsx_column)
      if (!sheet || !Number.isInteger(rowNumber) || rowNumber < 1
          || !Number.isInteger(columnNumber) || columnNumber < 1) continue
      const existingColumns = Math.max(
        columnNumber,
        ...sheet.rows.map(row => row.cells.length),
        0,
      )
      while (sheet.rows.length < rowNumber) {
        sheet.rows.push({
          rowNum: sheet.rows.length + 1,
          cells: Array.from({ length: existingColumns }, () => ({ value: '', color: null })),
        })
      }
      for (const row of sheet.rows) {
        while (row.cells.length < existingColumns) row.cells.push({ value: '', color: null })
      }
    }
  }

  function _cellColor(cell) {
    const rgb = cell?.s?.fgColor?.rgb
    if (!rgb) return null
    const hex = rgb.length === 8 ? rgb.slice(2) : rgb
    if (['FFFFFF', '000000'].includes(hex.toUpperCase())) return null
    return `#${hex}`
  }

  async function fetchAuthedUrl(url) {
    try {
      const res = await fetch(url, { headers: _authHeaders() })
      if (!res.ok) return null
      const { url: presigned } = await res.json()
      return presigned ?? null
    } catch {
      return null
    }
  }

  async function getXlsxUrl(jobId) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/xlsx`, { headers: _authHeaders() })
    if (!res.ok) throw new Error(`xlsx url fetch failed (${res.status})`)
    return res.json()  // { url, filename }
  }

  async function submitReview(jobId, corrections) {
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/submit`, {
      method: 'POST',
      headers: { ..._authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrections }),
    })
    if (!res.ok) throw new Error(`review submit failed (${res.status})`)
    delete cache[jobId]
    return res.json()
  }

  function pageUrl(jobId, filename) {
    return `${API_BASE}/api/jobs/${jobId}/pages/${filename}`
  }

  function cropUrl(jobId, filename) {
    return `${API_BASE}/api/jobs/${jobId}/crops/${filename}`
  }

  function xlsxUrl(jobId) {
    return `${API_BASE}/api/jobs/${jobId}/xlsx`
  }

  function estimateRows(fracY, xlsxRows, window = 4) {
    const total = xlsxRows.length
    const mid   = Math.round(fracY * total)
    const start = Math.max(0, mid - window)
    const end   = Math.min(total - 1, mid + window)
    return xlsxRows.slice(start, end + 1)
  }

  function parseRowRange(rowsStr) {
    if (!rowsStr) return null
    const parts = String(rowsStr).split(':').map(Number)
    return { start: parts[0], end: parts[1] ?? parts[0] }
  }

  function rowsForRange(rangeStr, xlsxRows) {
    const r = parseRowRange(rangeStr)
    if (!r) return []
    // +2 buffer: codex manifest row ranges sometimes undercount by 1-2
    return xlsxRows.filter(row => row.rowNum >= r.start && row.rowNum <= r.end + 2)
  }

  return {
    jobs,
    jobsLoading,
    fetchJobs,
    fetchJobDetail,
    initUpload,
    s3Put,
    startJob,
    savePendingFile,
    getPendingFile,
    deleteJob,
    rerunJob,
    fetchProgress,
    fetchAnalytics,
    pollJob,
    fetchAuthedUrl,
    getXlsxUrl,
    submitReview,
    pageUrl,
    cropUrl,
    xlsxUrl,
    estimateRows,
    rowsForRange,
  }
}
