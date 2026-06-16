import { ref } from 'vue'
import * as XLSX from 'xlsx'
import { apiFetch } from '@/composables/useApi.js'

// Each entry: {
//   page,            // 1-indexed page number
//   imageBlob,       // Blob (JPEG) of the rendered page
//   width, height,   // pixel dimensions of the rendered page
//   status,          // 'pending' | 'processing' | 'done' | 'error'
//   error,           // string | null
//   xlsxBytes,       // ArrayBuffer | null
//   rowBboxes,       // Map<system_serial, {left,top,width,height}> | null
//   summary,         // {rowCount, flaggedCount} | null
//   typeMap,         // object | null
//   allHeaders,      // string[] | null
// }
const pages = ref([])
const sourceFilename = ref('')

function base64ToBlob(base64, mime = 'image/jpeg') {
  const byteChars = atob(base64)
  const byteNumbers = new Array(byteChars.length)
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i)
  }
  return new Blob([new Uint8Array(byteNumbers)], { type: mime })
}

export function usePdfStore() {
  function reset() {
    pages.value = []
    sourceFilename.value = ''
  }

  // data = {page_count, pages: [{page, image, width, height}]} from /agent/pdf/pages
  function loadFromUpload(data, filename) {
    sourceFilename.value = filename || ''
    pages.value = (data.pages || []).map((p) => ({
      page: p.page,
      imageBlob: base64ToBlob(p.image),
      width: p.width,
      height: p.height,
      status: 'pending',
      error: null,
      xlsxBytes: null,
      rowBboxes: null,
      summary: null,
      typeMap: null,
      allHeaders: null,
    }))
  }

  // Runs a single page through /api/upload (good-shepherd) then /agent/infer-types.
  async function processPage(index) {
    const entry = pages.value[index]
    if (!entry) return

    entry.status = 'processing'
    entry.error = null

    try {
      const formData = new FormData()
      formData.append('image', entry.imageBlob, `page-${entry.page}.jpg`)

      const uploadRes = await apiFetch('/api/upload', {
        method: 'POST',
        body: formData,
      })
      if (!uploadRes.ok) {
        const text = await uploadRes.text().catch(() => uploadRes.statusText)
        throw new Error(text || `Server error ${uploadRes.status}`)
      }
      const payload = await uploadRes.json()
      const xlsxBytes = Uint8Array.from(atob(payload.xlsx), (c) => c.charCodeAt(0)).buffer
      entry.xlsxBytes = xlsxBytes
      entry.summary = payload.summary ?? null
      entry.rowBboxes = new Map((payload.rows ?? []).map((r) => [r.system_serial, r.bbox]))

      const fd = new FormData()
      fd.append('file', new Blob([xlsxBytes], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      }), 'form.xlsx')
      const typesRes = await fetch('/agent/infer-types', { method: 'POST', body: fd })
      if (!typesRes.ok) {
        const text = await typesRes.text().catch(() => typesRes.statusText)
        throw new Error(text || `Agent error ${typesRes.status}`)
      }
      const typesData = await typesRes.json()
      entry.typeMap = typesData.type_map
      entry.allHeaders = typesData.all_headers || []

      entry.status = 'done'
    } catch (e) {
      entry.status = 'error'
      entry.error = e.message || 'Processing failed'
    }
  }

  async function processAll() {
    for (let i = 0; i < pages.value.length; i++) {
      if (pages.value[i].status !== 'done') {
        await processPage(i)
      }
    }
  }

  // Merges each page's xlsx into one workbook (one sheet per page) and downloads it.
  function downloadMerged() {
    const wb = XLSX.utils.book_new()

    pages.value.forEach((p) => {
      if (!p.xlsxBytes) return
      const pageWb = XLSX.read(new Uint8Array(p.xlsxBytes), { type: 'array' })
      const sheet = pageWb.Sheets[pageWb.SheetNames[0]]
      XLSX.utils.book_append_sheet(wb, sheet, `Page ${p.page}`)
    })

    const out = XLSX.write(wb, { type: 'array', bookType: 'xlsx' })
    const blob = new Blob([out], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const base = sourceFilename.value.replace(/\.pdf$/i, '') || 'form'
    a.download = `${base}_merged.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  }

  return {
    pages,
    sourceFilename,
    reset,
    loadFromUpload,
    processPage,
    processAll,
    downloadMerged,
  }
}
