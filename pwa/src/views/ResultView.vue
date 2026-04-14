<template>
  <!-- ── Split view: species review ───────────────────────────────────────── -->
  <div v-if="speciesProposals.length > 0" class="flex h-full overflow-hidden">

    <!-- Left: proposals list -->
    <div class="w-80 shrink-0 flex flex-col gap-3 overflow-y-auto p-4 border-r border-gray-700">
      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Review corrections</p>

      <div
        v-for="p in speciesProposals"
        :key="p.original"
        class="rounded-lg bg-gray-800 border border-gray-700 p-3 flex flex-col gap-2 text-xs"
      >
        <div class="flex items-baseline gap-1 flex-wrap">
          <span class="text-gray-600 w-6 shrink-0">#{{ p.first_serial }}</span>
          <span class="font-mono text-gray-300">{{ p.original }}</span>
          <span class="text-gray-600 mx-1">→</span>
          <span v-if="p.matched_display && p.corrected" class="text-green-400">
            {{ p.matched_display }} <span class="text-gray-500">({{ p.corrected }})</span>
          </span>
          <span v-else class="text-gray-500 italic">no match</span>
          <span class="text-gray-600 ml-auto">{{ p.score }}%</span>
        </div>
        <div v-if="p.match_field" class="text-gray-600">via {{ p.match_field }}</div>

        <div v-if="p.editing" class="flex gap-1">
          <input
            v-model="p.editValue"
            class="flex-1 h-8 bg-gray-700 border border-gray-600 rounded px-2 text-gray-100 focus:outline-none focus:border-blue-500"
            @keyup.enter="doneEdit(p)"
          />
          <button
            class="px-3 h-8 rounded bg-gray-600 text-gray-200 hover:bg-gray-500 text-xs"
            @click="doneEdit(p)"
          >done</button>
        </div>
        <button
          v-else
          class="self-start text-gray-500 hover:text-gray-300 underline"
          @click="toggleEdit(p)"
        >edit</button>
      </div>

      <button
        class="w-full h-10 rounded-lg bg-green-700 text-white text-sm font-medium active:bg-green-800 transition-colors disabled:opacity-40 mt-auto shrink-0"
        :disabled="applyingSpecies"
        @click="applySpecies"
      >{{ applyingSpecies ? 'Applying…' : 'Apply to Excel' }}</button>

      <p v-if="agentError" class="text-red-400 text-xs shrink-0">{{ agentError }}</p>
    </div>

    <!-- Right: form image -->
    <div class="flex-1 overflow-auto p-4 bg-gray-950 flex items-start justify-center">
      <img
        v-if="croppedImageUrl"
        :src="croppedImageUrl"
        class="max-w-full rounded shadow-lg"
        alt="Original form"
      />
    </div>
  </div>

  <!-- ── Normal single-column view ─────────────────────────────────────── -->
  <div v-else class="flex flex-col items-center gap-4 p-4 h-full overflow-y-auto">

    <!-- Summary card -->
    <div
      v-if="summary"
      class="w-full max-w-xs rounded-lg bg-gray-800 border border-gray-700 p-4 text-sm"
    >
      <h2 class="font-semibold mb-2">Summary</h2>
      <div class="flex justify-between text-gray-400">
        <span>Rows</span><span class="text-gray-100">{{ summary.rowCount }}</span>
      </div>
      <div class="flex justify-between text-gray-400 mt-1">
        <span>Flagged</span><span class="text-yellow-400">{{ summary.flaggedCount }}</span>
      </div>
    </div>

    <p class="text-gray-500 text-xs">{{ fileSizeLabel }}</p>

    <!-- Download -->
    <button
      class="w-full max-w-xs h-14 rounded-lg bg-blue-600 text-white font-medium text-lg active:bg-blue-700 transition-colors"
      @click="download"
    >Download</button>

    <!-- ── Agent Pipeline ── -->
    <div class="w-full max-w-xs flex flex-col gap-3">
      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Data Checks</p>

      <!-- Stage 0: Infer types -->
      <button
        class="w-full h-12 rounded-lg border border-gray-600 text-gray-300 font-medium active:bg-gray-800 transition-colors disabled:opacity-40"
        :disabled="inferringTypes"
        @click="inferTypes"
      >{{ inferringTypes ? 'Analysing…' : 'Infer Column Types' }}</button>

      <!-- Type map review -->
      <div v-if="typeMap && !typeMapConfirmed" class="rounded-lg bg-gray-800 border border-gray-700 p-3 text-sm flex flex-col gap-2">
        <p class="text-gray-400 text-xs font-medium">Detected types — confirm to proceed</p>

        <div v-if="Object.keys(typeMap).length === 0" class="text-yellow-400 text-xs">
          No columns matched. Edit the cheatsheet to add keywords, then re-run.
        </div>

        <div v-for="(info, col) in typeMap" :key="col" class="flex items-center gap-2">
          <span class="text-gray-200 truncate flex-1">{{ col }}</span>
          <span class="text-xs px-2 py-0.5 rounded-full"
            :class="info.type === 'species' ? 'bg-green-900 text-green-300' : 'bg-blue-900 text-blue-300'"
          >{{ info.type }}</span>
          <span class="text-xs text-gray-500">"{{ info.matched_keyword }}"</span>
        </div>

        <div v-if="unmatchedHeaders.length" class="text-xs text-gray-600 mt-1">
          No type: {{ unmatchedHeaders.join(', ') }}
        </div>

        <div class="flex gap-2 mt-1">
          <button
            class="flex-1 h-9 rounded-lg bg-blue-600 text-white text-sm font-medium active:bg-blue-700 transition-colors disabled:opacity-40"
            :disabled="Object.keys(typeMap).length === 0"
            @click="typeMapConfirmed = true"
          >Confirm</button>
          <button
            class="h-9 px-3 rounded-lg border border-gray-600 text-gray-400 text-sm active:bg-gray-800 transition-colors"
            @click="openSidebar('cheatsheet')"
          >Edit Cheatsheet</button>
        </div>
      </div>

      <!-- Confirmed badge + reset -->
      <div v-if="typeMapConfirmed" class="flex items-center justify-between text-xs text-gray-500">
        <span>Types confirmed</span>
        <button class="underline hover:text-gray-300" @click="resetTypeMap">Re-infer</button>
      </div>

      <!-- Stage 1: Serial (runs before species so numbers match the image) -->
      <button
        v-if="typeMapConfirmed && hasSerial"
        class="w-full h-12 rounded-lg border border-blue-700 text-blue-300 font-medium active:bg-gray-800 transition-colors disabled:opacity-40"
        :disabled="checkingSerial"
        @click="checkSerial"
      >{{ checkingSerial ? 'Fixing serial numbers…' : 'Check Serial Numbers' }}</button>
      <p v-if="serialCount !== null" class="text-xs text-blue-400">
        Corrected serial numbers 1–{{ serialCount }}
      </p>

      <!-- Stage 2: Species -->
      <button
        v-if="typeMapConfirmed && hasSpecies"
        class="w-full h-12 rounded-lg border border-green-700 text-green-300 font-medium active:bg-gray-800 transition-colors disabled:opacity-40"
        :disabled="checkingSpecies"
        @click="checkSpecies"
      >{{ checkingSpecies ? 'Checking species…' : 'Check Species Names' }}</button>

      <p v-if="agentError" class="text-red-400 text-xs">{{ agentError }}</p>
    </div>

    <!-- Save to Google Drive -->
    <button
      v-if="driveState === 'idle'"
      class="w-full max-w-xs h-14 rounded-lg bg-green-600 text-white font-medium text-lg active:bg-green-700 transition-colors"
      @click="startDriveSave"
    >Save to Google Drive</button>

    <div v-if="driveState === 'auth' || driveState === 'picking'" class="text-gray-400 text-sm">
      {{ driveState === 'auth' ? 'Signing in…' : 'Picking folder…' }}
    </div>

    <div v-if="driveState === 'ready'" class="w-full max-w-xs flex flex-col gap-3">
      <div class="text-sm text-gray-400">Folder: <span class="text-gray-200">{{ selectedFolder.name }}</span></div>
      <input
        v-model="driveFileName"
        type="text"
        class="w-full h-10 rounded-lg bg-gray-800 border border-gray-600 px-3 text-sm text-gray-100 focus:border-green-500 focus:outline-none"
        placeholder="File name"
      />
      <button
        class="w-full h-12 rounded-lg bg-green-600 text-white font-medium active:bg-green-700 transition-colors"
        @click="doUpload"
      >Upload</button>
    </div>

    <button
      v-if="driveState === 'uploading'"
      class="w-full max-w-xs h-14 rounded-lg bg-green-800 text-green-200 font-medium text-lg cursor-not-allowed"
      disabled
    >Uploading…</button>

    <div v-if="driveState === 'done'" class="flex flex-col items-center gap-2">
      <span class="text-green-400 font-medium">Saved</span>
      <a v-if="driveLink" :href="driveLink" target="_blank" rel="noopener" class="text-blue-400 underline text-sm">
        Open in Drive
      </a>
    </div>

    <div v-if="driveState === 'error'" class="flex flex-col items-center gap-2">
      <span class="text-red-400 text-sm">{{ driveError }}</span>
      <button class="text-gray-400 underline text-xs" @click="driveState = 'idle'">Try again</button>
    </div>

    <button
      class="w-full max-w-xs h-14 rounded-lg border border-gray-600 text-gray-300 font-medium text-lg active:bg-gray-800 transition-colors"
      @click="scanAnother"
    >Scan</button>

  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFormStore } from '@/composables/useFormStore.js'
import { useGoogleAuth } from '@/composables/useGoogleAuth.js'
import { useDriveSave } from '@/composables/useDriveSave.js'
import { useSidebar } from '@/composables/useSidebar.js'

const router = useRouter()
const { xlsxBytes, croppedImage, summary, reset } = useFormStore()
const { accessToken, requestAccessToken } = useGoogleAuth()
const { pickFolder, uploadFile } = useDriveSave()
const { open: openSidebar } = useSidebar()

// ── Helpers ──────────────────────────────────────────────────────────────────

function xlsxBlob() {
  return new Blob([xlsxBytes.value], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
}

// Agent calls always use relative paths so the Vite proxy routes them to
// localhost:8071 regardless of VUE_APP_API_BASE_URL.
async function agentPost(path, formData) {
  const res = await fetch(path, { method: 'POST', body: formData })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text)
  }
  return res
}

// ── Image ─────────────────────────────────────────────────────────────────────

const croppedImageUrl = computed(() =>
  croppedImage.value ? URL.createObjectURL(croppedImage.value) : null
)

// ── Download ──────────────────────────────────────────────────────────────────

const fileSizeLabel = computed(() => {
  if (!xlsxBytes.value) return ''
  return `${(xlsxBytes.value.byteLength / 1024).toFixed(1)} KB`
})

function download() {
  const url = URL.createObjectURL(xlsxBlob())
  const a = document.createElement('a')
  a.href = url
  a.download = 'form_output.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

// ── Agent state ───────────────────────────────────────────────────────────────

const typeMap      = ref(null)   // {col: {type, confidence, matched_keyword}}
const allHeaders   = ref([])
const typeMapConfirmed = ref(false)
const speciesProposals = ref([]) // [{original, corrected, status, editing, editValue}]
const agentError   = ref('')

const inferringTypes  = ref(false)
const checkingSpecies = ref(false)
const applyingSpecies = ref(false)
const checkingSerial  = ref(false)
const serialCount     = ref(null)   // number of rows renumbered, set after check-serial

const hasSpecies = computed(() =>
  typeMap.value && Object.values(typeMap.value).some(v => v.type === 'species')
)
const hasSerial = computed(() =>
  typeMap.value && Object.values(typeMap.value).some(v => v.type === 'serial')
)
const unmatchedHeaders = computed(() => {
  if (!typeMap.value || !allHeaders.value.length) return []
  return allHeaders.value.filter(h => h && !typeMap.value[h])
})
const confirmedCorrections = computed(() =>
  speciesProposals.value
    .filter(p => p.corrected || (p.editing && p.editValue) || p.editValue)
    .map(p => ({
      original: p.original,
      corrected: p.editValue || p.corrected,
    }))
)

function resetTypeMap() {
  typeMap.value = null
  typeMapConfirmed.value = false
  speciesProposals.value = []
  serialCount.value = null
  agentError.value = ''
}

// Stage 0
async function inferTypes() {
  inferringTypes.value = true
  agentError.value = ''
  resetTypeMap()
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    const data = await (await agentPost('/agent/infer-types', fd)).json()
    typeMap.value = data.type_map
    allHeaders.value = data.all_headers || []
  } catch (e) {
    agentError.value = `Infer types failed: ${e.message}`
  } finally {
    inferringTypes.value = false
  }
}

// Stage 1 — get proposals
async function checkSpecies() {
  checkingSpecies.value = true
  agentError.value = ''
  speciesProposals.value = []
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(typeMap.value))
    const data = await (await agentPost('/agent/check-species', fd)).json()
    speciesProposals.value = data.proposals.map(p => ({
      ...p,
      editing: false,
      editValue: p.corrected || '',
    }))
  } catch (e) {
    agentError.value = `Species check failed: ${e.message}`
  } finally {
    checkingSpecies.value = false
  }
}

function toggleEdit(p) {
  p.editing = true
}

function doneEdit(p) {
  p.editing = false
}

// Stage 1 — apply confirmed corrections
async function applySpecies() {
  applyingSpecies.value = true
  agentError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(typeMap.value))
    fd.append('corrections', JSON.stringify(confirmedCorrections.value))
    const buf = await (await agentPost('/agent/apply-species', fd)).arrayBuffer()
    xlsxBytes.value = buf
    speciesProposals.value = []
  } catch (e) {
    agentError.value = `Apply failed: ${e.message}`
  } finally {
    applyingSpecies.value = false
  }
}

// Stage 1 — serial (auto-applies, records count)
async function checkSerial() {
  checkingSerial.value = true
  agentError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(typeMap.value))
    const res = await agentPost('/agent/check-serial', fd)
    serialCount.value = parseInt(res.headers.get('x-row-count') || '0', 10)
    xlsxBytes.value = await res.arrayBuffer()
  } catch (e) {
    agentError.value = `Serial check failed: ${e.message}`
  } finally {
    checkingSerial.value = false
  }
}

// ── Google Drive ──────────────────────────────────────────────────

const driveState    = ref('idle')
const driveError    = ref('')
const driveLink     = ref('')
const selectedFolder = ref(null)
const driveFileName = ref('form_output.xlsx')

async function startDriveSave() {
  try {
    let token = accessToken.value
    if (!token) {
      driveState.value = 'auth'
      token = await requestAccessToken()
    }
    driveState.value = 'picking'
    selectedFolder.value = await pickFolder(token)
    driveState.value = 'ready'
  } catch (e) {
    driveError.value = e.message || 'Something went wrong'
    driveState.value = 'error'
  }
}

async function doUpload() {
  if (!selectedFolder.value || !driveFileName.value.trim()) return
  try {
    driveState.value = 'uploading'
    const result = await uploadFile(
      accessToken.value,
      selectedFolder.value.id,
      driveFileName.value.trim(),
      xlsxBytes.value,
    )
    driveLink.value = result.webViewLink || ''
    driveState.value = 'done'
  } catch (e) {
    driveError.value = e.message || 'Upload failed'
    driveState.value = 'error'
  }
}

function scanAnother() {
  reset()
  router.push({ name: 'capture' })
}
</script>
