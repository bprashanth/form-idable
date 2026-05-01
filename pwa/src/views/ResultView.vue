<template>
  <!-- ── Split view: species review ───────────────────────────────────────── -->
  <div v-if="speciesProposals.length > 0" class="flex h-full overflow-hidden">

    <!-- Left: proposals list -->
    <div class="w-80 shrink-0 flex flex-col gap-3 overflow-y-auto p-4 border-r border-gray-700">
      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Review corrections</p>

      <div
        v-for="p in speciesProposals"
        :key="p.original"
        class="rounded-lg bg-gray-800 p-3 flex flex-col gap-2 text-xs cursor-pointer transition-colors"
        :class="[
          p.reviewed ? 'border border-green-800' : 'border border-gray-700',
          activeProposal === p ? 'ring-1 ring-blue-600' : '',
        ]"
        @click="activeProposal = p"
      >
        <!-- Match summary line -->
        <div class="flex items-baseline gap-1 flex-wrap">
          <span class="text-gray-600 w-6 shrink-0">#{{ p.system_serials[0] }}</span>
          <span class="font-mono text-gray-300">{{ p.original }}</span>
          <span class="text-gray-600 mx-1">→</span>
          <span v-if="p.matched_display && p.corrected" class="text-green-400">
            {{ p.matched_display }} <span class="text-gray-500">({{ p.corrected }})</span>
          </span>
          <span v-else class="text-gray-500 italic">no match</span>
          <span class="text-gray-600 ml-auto">{{ p.score }}%</span>
        </div>
        <div v-if="p.match_field" class="text-gray-600">via {{ p.match_field }}</div>

        <!-- Looking up spinner -->
        <div v-if="p.looking_up" class="flex items-center gap-2 text-gray-500">
          <div class="w-3 h-3 border-2 border-gray-500 border-t-blue-400 rounded-full animate-spin shrink-0"></div>
          <span>Looking up…</span>
        </div>

        <!-- "Update all / Just this row" confirmation -->
        <div v-else-if="p.pending_confirm" class="flex flex-col gap-1.5">
          <span class="text-gray-400">
            Found in <span class="text-gray-200">{{ p.system_serials.length }}</span> rows — apply new match to all?
          </span>
          <div class="flex gap-1.5">
            <button
              class="flex-1 h-7 rounded bg-blue-700 text-white hover:bg-blue-600 transition-colors"
              @click.stop="applyToAll(p)"
            >Update all</button>
            <button
              class="flex-1 h-7 rounded bg-gray-700 text-gray-200 hover:bg-gray-600 transition-colors"
              @click.stop="applyToOne(p)"
            >Just this row</button>
          </div>
        </div>

        <!-- Edit input -->
        <div v-else-if="p.editing" class="flex gap-1" @click.stop>
          <input
            v-model="p.editValue"
            class="flex-1 h-8 bg-gray-700 border border-gray-600 rounded px-2 text-gray-100 focus:outline-none focus:border-blue-500"
            @keyup.enter="doneEdit(p)"
          />
          <button
            class="px-3 h-8 rounded bg-gray-600 text-gray-200 hover:bg-gray-500 text-xs"
            @click.stop="doneEdit(p)"
          >done</button>
        </div>

        <!-- Edit trigger -->
        <button
          v-else
          class="self-start text-gray-500 hover:text-gray-300 underline"
          @click.stop="toggleEdit(p)"
        >edit</button>
      </div>

      <button
        class="w-full h-10 rounded-lg bg-green-700 text-white text-sm font-medium active:bg-green-800 transition-colors disabled:opacity-40 mt-auto shrink-0"
        :disabled="applyingSpecies || speciesProposals.some(p => p.pending_confirm)"
        @click="applySpecies"
      >{{ applyingSpecies ? 'Saving…' : 'Save changes' }}</button>

      <p v-if="speciesProposals.some(p => p.pending_confirm)" class="text-yellow-500 text-xs shrink-0">
        Resolve all pending confirmations before saving.
      </p>
      <p v-if="agentError" class="text-red-400 text-xs shrink-0">{{ agentError }}</p>
    </div>

    <!-- Right: form image with bbox overlay -->
    <div class="flex-1 overflow-auto p-4 bg-gray-950 flex items-start justify-center">
      <FormImageOverlay
        :image-blob="croppedImage"
        :primary-entries="primaryEntries"
        :secondary-entries="secondaryEntries"
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

      <!-- Stage 1: Serial -->
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

    <!-- Download -->
    <button
      class="w-full max-w-xs h-14 rounded-lg bg-blue-600 text-white font-medium text-lg active:bg-blue-700 transition-colors"
      @click="download"
    >Download</button>

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
import { useSidebar } from '@/composables/useSidebar.js'
import FormImageOverlay from '@/components/FormImageOverlay.vue'

const router = useRouter()
const { xlsxBytes, croppedImage, summary, rowBboxes, reset } = useFormStore()
const { open: openSidebar } = useSidebar()

// ── Helpers ──────────────────────────────────────────────────────────────────

function xlsxBlob() {
  return new Blob([xlsxBytes.value], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
}

async function agentPost(path, formData) {
  const res = await fetch(path, { method: 'POST', body: formData })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text)
  }
  return res
}

async function lookupSpecies(query) {
  const res = await fetch('/agent/lookup-species', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(text)
  }
  return res.json()
}

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

const typeMap           = ref(null)
const allHeaders        = ref([])
const typeMapConfirmed  = ref(false)
const speciesProposals  = ref([])
const activeProposal    = ref(null)
const agentError        = ref('')

const inferringTypes  = ref(false)
const checkingSpecies = ref(false)
const applyingSpecies = ref(false)
const checkingSerial  = ref(false)
const serialCount     = ref(null)

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

// Primary: the first system_serial ("this row") — shown in red
const primaryEntries = computed(() => {
  if (!activeProposal.value || !rowBboxes.value) return []
  const first = activeProposal.value.system_serials?.[0]
  if (first == null) return []
  const bbox = rowBboxes.value.get(first)
  return bbox ? [{ serial: first, bbox }] : []
})

// Secondary: all other system_serials for this proposal — shown in amber
const secondaryEntries = computed(() => {
  if (!activeProposal.value || !rowBboxes.value) return []
  return (activeProposal.value.system_serials ?? [])
    .slice(1)
    .map(s => ({ serial: s, bbox: rowBboxes.value.get(s) }))
    .filter(e => e.bbox)
})

// Corrections to send: only proposals with a corrected value and no pending confirm
const confirmedCorrections = computed(() =>
  speciesProposals.value
    .filter(p => !p.pending_confirm && (p.corrected || p.editValue))
    .map(p => ({
      original: p.original,
      corrected: p.editValue || p.corrected,
      system_serials: p.system_serials,
    }))
)

function resetTypeMap() {
  typeMap.value = null
  typeMapConfirmed.value = false
  speciesProposals.value = []
  activeProposal.value = null
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

// Stage 1a — serial
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

// Stage 1b — get species proposals
async function checkSpecies() {
  checkingSpecies.value = true
  agentError.value = ''
  speciesProposals.value = []
  activeProposal.value = null
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(typeMap.value))
    const data = await (await agentPost('/agent/check-species', fd)).json()
    speciesProposals.value = data.proposals.map(p => ({
      ...p,
      editing:         false,
      editValue:       p.matched_display || '',  // show the "via" word, not the scientific name
      looking_up:      false,
      pending_confirm: false,
      reviewed:        false,
    }))
    activeProposal.value = speciesProposals.value[0] ?? null
  } catch (e) {
    agentError.value = `Species check failed: ${e.message}`
  } finally {
    checkingSpecies.value = false
  }
}

function toggleEdit(p) {
  p.editing = true
}

async function doneEdit(p) {
  const changed = p.editValue.trim() !== (p.matched_display || '')
  p.editing = false

  if (!changed) {
    p.reviewed = true
    return
  }

  p.looking_up = true
  agentError.value = ''
  try {
    const match = await lookupSpecies(p.editValue.trim())
    p.corrected      = match.corrected
    p.matched_display = match.matched_display
    p.match_field    = match.match_field
    p.score          = match.score
    // Reset edit box to the new matched display so next edit starts from there
    p.editValue      = match.matched_display || p.editValue

    if (p.system_serials.length > 1) {
      p.pending_confirm = true
    } else {
      p.reviewed = true
    }
  } catch (e) {
    agentError.value = `Lookup failed: ${e.message}`
    p.reviewed = true
  } finally {
    p.looking_up = false
  }
}

// Apply new match to all rows this proposal covers
function applyToAll(p) {
  p.pending_confirm = false
  p.reviewed = true
}

// Apply new match to the first (highlighted) row only
function applyToOne(p) {
  p.system_serials = [p.system_serials[0]]
  p.pending_confirm = false
  p.reviewed = true
}

// Stage 2 — write corrections back to xlsx
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
    activeProposal.value = null
  } catch (e) {
    agentError.value = `Save failed: ${e.message}`
  } finally {
    applyingSpecies.value = false
  }
}

function scanAnother() {
  reset()
  router.push({ name: 'capture' })
}
</script>
