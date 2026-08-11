<template>
  <div class="flex min-h-screen bg-surface font-body text-on-surface">
    <aside class="hidden md:flex flex-col min-h-screen py-6 px-4 bg-surface-container-low w-64 shrink-0 border-r border-outline-variant/20 print:hidden">
      <div class="mb-8 px-2 flex items-center gap-3">
        <img src="/logo.png" class="w-8 h-8 shrink-0 border-[3px] border-black rounded-sm" alt="Formidable" />
        <div>
          <h1 class="font-headline font-black text-lg text-primary leading-none tracking-tighter">FORMIDABLE</h1>
          <p class="text-[10px] uppercase tracking-widest text-on-surface-variant mt-0.5">Form Processing Engine</p>
        </div>
      </div>
      <nav class="flex-1 space-y-1">
        <button class="w-full flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high" @click="router.push('/dashboard')">
          <span class="material-symbols-outlined">dashboard</span><span>Dashboard</span>
        </button>
        <button class="w-full flex items-center gap-3 px-3 py-2 text-primary font-bold bg-surface-container-highest rounded-sm">
          <span class="material-symbols-outlined">architecture</span><span>Form Builder</span>
        </button>
      </nav>
      <div class="pt-4 border-t border-outline-variant/20 text-[10px] leading-relaxed text-on-surface-variant">
        QR identity + OMR fiducials follow the paperroast geometry scheme.
      </div>
    </aside>

    <main class="flex-1 min-w-0">
      <header class="flex justify-between items-center px-7 py-4 border-b border-outline-variant/20 bg-surface-container-lowest sticky top-0 z-20 print:hidden">
        <div>
          <p class="text-[10px] uppercase tracking-[0.22em] font-black text-error">Prototype · Form Builder</p>
          <h2 class="font-headline font-black text-2xl text-primary">{{ selectedJob ? 'Printable clone' : 'Choose a form to clone' }}</h2>
        </div>
        <div class="flex gap-2">
          <button v-if="selectedJob" class="px-4 py-2 border border-outline-variant/40 text-xs font-black" @click="router.push('/builder')">All forms</button>
          <button v-if="selectedJob" data-testid="print-form-button" class="px-4 py-2 bg-primary text-on-primary text-xs font-black" @click="printPrototype">Print prototype</button>
        </div>
      </header>

      <section v-if="loading" class="p-10 text-sm text-on-surface-variant">Building empty form…</section>
      <section v-else-if="error" class="p-10 text-error">{{ error }}</section>

      <section v-else-if="!selectedJob" class="p-7 print:hidden">
        <div class="max-w-5xl">
          <p class="text-sm text-on-surface-variant max-w-2xl mb-7">
            Clone any processed form into a clean, reusable collection sheet. Handwritten values are removed; printed structure is inferred from the workbook.
          </p>
          <div class="grid md:grid-cols-2 xl:grid-cols-3 gap-4" data-testid="builder-gallery">
            <button
              v-for="job in completeJobs"
              :key="job.job_id"
              class="text-left border border-outline-variant/30 bg-white p-5 hover:border-primary hover:shadow-lg transition-all"
              :data-testid="`clone-form-${job.job_id}`"
              @click="openClone(job.job_id)"
            >
              <div class="flex justify-between gap-4">
                <span class="w-10 h-12 border border-outline-variant/30 flex items-center justify-center bg-surface-container-low">
                  <span class="material-symbols-outlined text-primary">description</span>
                </span>
                <span class="material-symbols-outlined text-outline">arrow_forward</span>
              </div>
              <h3 class="font-headline font-black text-primary mt-4 line-clamp-2">{{ job.name }}</h3>
              <p class="text-[10px] text-on-surface-variant mt-2">{{ job.pages || '—' }} pages · {{ job.effort === 'high' ? 'High evidence available' : 'Low source' }}</p>
              <p class="text-[10px] uppercase tracking-widest font-black text-error mt-4">Create QR + OMR clone</p>
            </button>
          </div>
        </div>
      </section>

      <section v-else class="p-6 lg:p-9 bg-surface-container-low min-h-[calc(100vh-81px)] print:p-0 print:bg-white">
        <div class="max-w-6xl mx-auto grid xl:grid-cols-[minmax(0,1fr)_250px] gap-7 print:block">
          <article
            class="paper-sheet bg-white shadow-2xl mx-auto relative overflow-hidden"
            :class="template.orientation === 'landscape' ? 'paper-landscape' : 'paper-portrait'"
            data-testid="builder-preview"
          >
            <div class="px-10 pt-7 pb-5 border-b-2 border-black flex items-start justify-between gap-5">
              <div class="min-w-0">
                <p class="text-[8px] tracking-[0.24em] uppercase font-black">Formidable field sheet</p>
                <h1 class="font-headline font-black text-lg leading-tight mt-1">{{ template.title }}</h1>
                <p class="text-[8px] mt-1 text-black/60">Clean collection copy · values intentionally blank</p>
              </div>
              <div class="shrink-0 text-center">
                <img :src="qrDataUrl" class="w-16 h-16 image-render-pixel" alt="Form identity QR code" data-testid="builder-qr" />
                <p class="font-mono text-[8px] font-black tracking-wider mt-1">{{ formId }}</p>
              </div>
            </div>

            <div v-if="template.headerFields.length" class="grid grid-cols-2 gap-x-8 gap-y-4 px-10 py-5">
              <div v-for="field in template.headerFields" :key="field" class="flex items-end gap-2 text-[9px]">
                <span class="font-bold whitespace-nowrap">{{ field }}:</span><span class="h-4 border-b border-black flex-1"></span>
              </div>
            </div>

            <div class="px-10 pb-9 pt-3">
              <div class="relative omr-grid">
                <table class="w-full border-collapse table-fixed text-[8px]">
                  <thead>
                    <tr>
                      <th v-for="column in template.columns" :key="column.label" class="border border-black px-1.5 py-2 font-black leading-tight break-words">{{ column.label }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in template.rows" :key="row" class="h-7">
                      <td v-for="(column, index) in template.columns" :key="index" class="border border-black px-1 text-center">
                        <span v-if="index === 0 && template.serialFirst" class="text-[7px] text-black/65">{{ row }}</span>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div class="absolute -left-5 top-0 bottom-0 flex flex-col justify-between py-[1px]" aria-hidden="true" data-testid="omr-left-marks">
                  <span v-for="mark in template.rows + 2" :key="`l${mark}`" class="block w-2 bg-black" :class="mark === 1 ? 'h-3' : 'h-1.5'"></span>
                </div>
                <div class="absolute -right-5 top-0 bottom-0 flex flex-col justify-between py-[1px]" aria-hidden="true" data-testid="omr-right-marks">
                  <span v-for="mark in template.rows + 2" :key="`r${mark}`" class="block w-2 bg-black" :class="mark === 1 ? 'h-3' : 'h-1.5'"></span>
                </div>
                <div class="absolute -bottom-4 left-0 right-0 flex justify-between" aria-hidden="true" data-testid="omr-column-marks">
                  <span v-for="column in template.columns.length + 1" :key="`c${column}`" class="block w-1.5 h-2 bg-black"></span>
                </div>
              </div>
              <p class="text-[7px] text-black/55 mt-7">Write inside the boxes. A dot = 0. A tick = yes. Leave blank when there is nothing to record.</p>
            </div>
          </article>

          <aside class="space-y-4 print:hidden">
            <div class="bg-white border border-outline-variant/30 p-5">
              <p class="text-[9px] uppercase tracking-widest font-black text-error">Geometry added</p>
              <ul class="mt-3 space-y-3 text-xs text-on-surface-variant">
                <li><strong class="text-on-surface">QR form ID</strong><br />Template lookup without visual fingerprinting.</li>
                <li><strong class="text-on-surface">Row fiducials</strong><br />Paired marks follow page curl and camera perspective.</li>
                <li><strong class="text-on-surface">Column ticks</strong><br />Printed grid coordinates stay deterministic.</li>
              </ul>
            </div>
            <div class="bg-primary text-on-primary p-5">
              <p class="text-[9px] uppercase tracking-widest font-black opacity-70">Source</p>
              <p class="font-bold text-sm mt-2 break-words">{{ selectedJob.name }}</p>
              <p class="text-[10px] opacity-70 mt-2">{{ template.columns.length }} inferred columns · {{ template.rows }} reusable rows</p>
            </div>
            <p class="text-[10px] leading-relaxed text-on-surface-variant">
              Meeting prototype: structure is inferred from the extracted workbook. A production builder will let the user confirm labels, row count, legends and page breaks before saving a versioned descriptor.
            </p>
          </aside>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import { useJobStore } from '@/composables/useJobStore.js'

const route = useRoute()
const router = useRouter()
const { jobs, fetchJobs, fetchJobDetail } = useJobStore()
const selectedJob = ref(null)
const template = ref({ title: '', columns: [], headerFields: [], rows: 12, serialFirst: false, orientation: 'portrait' })
const qrDataUrl = ref('')
const loading = ref(false)
const error = ref('')
const completeJobs = computed(() => jobs.value.filter(job => job.status === 'complete'))
const formId = computed(() => `FM-${String(route.params.jobId || '').replaceAll('-', '').slice(0, 8).toUpperCase()}`)

function cellValue(cell) {
  return String(cell?.value ?? '').trim()
}

function deriveTemplate(job, detail) {
  const pages = detail.xlsxPages ?? []
  const sheetIndex = pages.reduce((best, page, index) =>
    page.length > (pages[best]?.length ?? 0) ? index : best, 0)
  const rows = pages[sheetIndex] ?? []
  const sheetName = detail.xlsxSheetNames?.[sheetIndex]
  const manifestCells = detail.reviewManifest?.cells ?? []
  const tableCells = manifestCells.filter(cell =>
    cell.xlsx_sheet === sheetName && cell.context
      && !String(cell.id).includes(':field:') && !String(cell.id).includes(':text:'))
  const contextsByColumn = new Map()
  for (const cell of tableCells) {
    if (!Number.isInteger(cell.xlsx_column)) continue
    const counts = contextsByColumn.get(cell.xlsx_column) ?? new Map()
    counts.set(cell.context, (counts.get(cell.context) ?? 0) + 1)
    contextsByColumn.set(cell.xlsx_column, counts)
  }
  const canonicalLabels = [...contextsByColumn.entries()]
    .sort(([left], [right]) => left - right)
    .map(([, counts]) => [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0])
  const candidates = rows.slice(0, 30).map((row, index) => {
    const values = row.cells.map(cellValue)
    const filled = values.filter(Boolean)
    const text = filled.filter(value => /[A-Za-z]/.test(value)).length
    const numeric = filled.filter(value => /^[-+]?\d+(?:\.\d+)?$/.test(value)).length
    const unique = new Set(filled.map(value => value.toLocaleLowerCase())).size
    return { index, values, filled: filled.length, text, numeric, unique,
      score: text * 2 + filled.length + unique * 5 - numeric * 4 }
  }).filter(item => item.filled >= 2)
  const header = candidates.sort((a, b) =>
    b.score - a.score || a.index - b.index)[0]
  const rawLabels = header?.values ?? ['No.', 'Observation', 'Value', 'Notes']
  let last = Math.max(1, rawLabels.reduce((result, value, index) => value ? index : result, 0))
  last = Math.min(last, 11)
  let columns = rawLabels.slice(0, last + 1).map((label, index) => ({
    label: label || `Field ${index + 1}`,
  }))
  if (canonicalLabels.length >= 2) {
    columns = canonicalLabels.slice(0, 12).map(label => ({ label }))
  }
  const canonicalHeaderFields = manifestCells
    .filter(cell => String(cell.id).includes(':field:') && cell.context)
    .map(cell => cell.context)
  const prior = rows.slice(0, header?.index ?? 0)
    .map(row => cellValue(row.cells[0]).replace(/:$/, ''))
    .filter(value => value && /[A-Za-z]/.test(value) && value.length < 35)
  const headerFields = [...new Set(canonicalHeaderFields.length
    ? canonicalHeaderFields
    : prior)].slice(0, 4)
  const sourceRows = Math.max(0, rows.length - (header?.index ?? 0) - 1)
  const rowCount = Math.max(10, Math.min(18, sourceRows || 12))
  const first = columns[0]?.label.toLocaleLowerCase() ?? ''
  return {
    title: String(job.name || 'Ecology field form').replace(/\.(pdf|png|jpe?g)$/i, ''),
    columns,
    headerFields: headerFields.length ? headerFields : ['Site / plot', 'Date', 'Observer'],
    rows: rowCount,
    serialFirst: /^(s\.?\s*no\.?|no\.?|serial|row)$/.test(first),
    orientation: columns.length > 7 ? 'landscape' : 'portrait',
  }
}

async function load() {
  error.value = ''
  if (!jobs.value.length) await fetchJobs()
  const jobId = route.params.jobId
  if (!jobId) {
    selectedJob.value = null
    return
  }
  loading.value = true
  try {
    const job = jobs.value.find(item => item.job_id === jobId)
    if (!job || job.status !== 'complete') throw new Error('Only completed forms can be cloned.')
    const detail = await fetchJobDetail(jobId)
    selectedJob.value = job
    template.value = deriveTemplate(job, detail)
    qrDataUrl.value = await QRCode.toDataURL(formId.value, {
      errorCorrectionLevel: 'M', margin: 1, width: 160,
      color: { dark: '#000000', light: '#ffffff' },
    })
  } catch (reason) {
    error.value = reason.message ?? String(reason)
  } finally {
    loading.value = false
  }
}

function openClone(jobId) {
  router.push({ name: 'form-builder-clone', params: { jobId } })
}

function printPrototype() {
  window.print()
}

onMounted(load)
watch(() => route.params.jobId, load)
</script>

<style scoped>
.paper-sheet { color: #111; }
.paper-portrait { width: min(100%, 720px); aspect-ratio: 210 / 297; }
.paper-landscape { width: min(100%, 980px); aspect-ratio: 297 / 210; }
.image-render-pixel { image-rendering: pixelated; }
@media print {
  .paper-sheet { width: 100% !important; min-height: 100vh; box-shadow: none !important; }
}
</style>
