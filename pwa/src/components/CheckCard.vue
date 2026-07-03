<template>
  <div class="rounded-lg bg-gray-800 border border-gray-700 p-3 flex flex-col gap-2 text-sm">
    <div class="flex items-center gap-2">
      <span class="text-gray-200 truncate flex-1">{{ column }}</span>
      <span class="text-xs px-2 py-0.5 rounded-full"
        :class="typeInfo.type === 'species' ? 'bg-green-900 text-green-300' : 'bg-blue-900 text-blue-300'"
      >{{ typeInfo.type }}</span>
    </div>

    <!-- Serial: auto-apply, no review needed -->
    <template v-if="typeInfo.type === 'serial'">
      <button
        v-if="serialCount === null"
        class="w-full h-10 rounded-lg border border-blue-700 text-blue-300 font-medium active:bg-gray-700 transition-colors disabled:opacity-40"
        :disabled="checkingSerial"
        @click="checkSerial"
      >{{ checkingSerial ? 'Renumbering…' : 'Run check' }}</button>
      <p v-else class="text-xs text-blue-400">Renumbered 1–{{ serialCount }} ✓</p>
    </template>

    <!-- Species: review proposals -->
    <template v-else-if="typeInfo.type === 'species'">
      <button
        v-if="!speciesChecked"
        class="w-full h-10 rounded-lg border border-green-700 text-green-300 font-medium active:bg-gray-700 transition-colors disabled:opacity-40"
        :disabled="checkingSpecies"
        @click="checkSpecies"
      >{{ checkingSpecies ? 'Checking species…' : 'Run check' }}</button>

      <template v-else>
        <p v-if="speciesProposals.length === 0" class="text-xs text-green-400">No corrections needed ✓</p>

        <div v-else class="flex flex-col gap-2">
          <p class="text-xs text-gray-500">{{ speciesProposals.length }} proposals</p>

          <div
            v-for="p in speciesProposals"
            :key="p.original"
            class="rounded-lg bg-gray-900 p-2 flex flex-col gap-1.5 text-xs cursor-pointer transition-colors"
            :class="[
              p.reviewed ? 'border border-green-800' : 'border border-gray-700',
              activeProposal === p ? 'ring-1 ring-blue-600' : '',
            ]"
            @click="activeProposal = p"
          >
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

            <div v-if="p.looking_up" class="flex items-center gap-2 text-gray-500">
              <div class="w-3 h-3 border-2 border-gray-500 border-t-blue-400 rounded-full animate-spin shrink-0"></div>
              <span>Looking up…</span>
            </div>

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

            <button
              v-else
              class="self-start text-gray-500 hover:text-gray-300 underline"
              @click.stop="toggleEdit(p)"
            >edit</button>
          </div>

          <button
            class="w-full h-9 rounded-lg bg-green-700 text-white text-sm font-medium active:bg-green-800 transition-colors disabled:opacity-40"
            :disabled="applyingSpecies || saved || speciesProposals.some(p => p.pending_confirm)"
            @click="applySpecies"
          >{{ saved ? 'Saved ✓' : applyingSpecies ? 'Saving…' : 'Save corrections' }}</button>

          <p v-if="speciesProposals.some(p => p.pending_confirm)" class="text-yellow-500 text-xs">
            Resolve all pending confirmations before saving.
          </p>
        </div>
      </template>
    </template>

    <!-- Unsupported type -->
    <p v-else class="text-xs text-gray-500">No automated check for type "{{ typeInfo.type }}"</p>

    <p v-if="agentError" class="text-red-400 text-xs">{{ agentError }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  column:    { type: String, required: true },
  typeInfo:  { type: Object, required: true }, // {type, matched_keyword, ...}
  typeMap:   { type: Object, required: true }, // full type_map for the page
  xlsxBytes: { type: ArrayBuffer, required: true },
  rowBboxes: { type: Object, default: null },  // Map<system_serial, bbox>
})

const emit = defineEmits(['xlsx-updated', 'highlight'])

function xlsxBlob() {
  return new Blob([props.xlsxBytes], {
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

const agentError = ref('')

// ── Serial ────────────────────────────────────────────────────────────────────

const checkingSerial = ref(false)
const serialCount = ref(null)

async function checkSerial() {
  checkingSerial.value = true
  agentError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(props.typeMap))
    const res = await agentPost('/agent/check-serial', fd)
    serialCount.value = parseInt(res.headers.get('x-row-count') || '0', 10)
    emit('xlsx-updated', await res.arrayBuffer())
  } catch (e) {
    agentError.value = `Serial check failed: ${e.message}`
  } finally {
    checkingSerial.value = false
  }
}

// ── Species ───────────────────────────────────────────────────────────────────

const checkingSpecies = ref(false)
const speciesChecked  = ref(false)
const speciesProposals = ref([])
const activeProposal   = ref(null)
const applyingSpecies  = ref(false)
const saved            = ref(false)

async function checkSpecies() {
  checkingSpecies.value = true
  agentError.value = ''
  speciesProposals.value = []
  activeProposal.value = null
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(props.typeMap))
    const data = await (await agentPost('/agent/check-species', fd)).json()
    speciesProposals.value = data.proposals.map((p) => ({
      ...p,
      editing:         false,
      editValue:       p.matched_display || '',
      looking_up:      false,
      pending_confirm: false,
      reviewed:        false,
    }))
    activeProposal.value = speciesProposals.value[0] ?? null
    speciesChecked.value = true
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
    p.corrected       = match.corrected
    p.matched_display = match.matched_display
    p.match_field     = match.match_field
    p.score           = match.score
    p.editValue       = match.matched_display || p.editValue

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

function applyToAll(p) {
  p.pending_confirm = false
  p.reviewed = true
}

function applyToOne(p) {
  p.system_serials = [p.system_serials[0]]
  p.pending_confirm = false
  p.reviewed = true
}

const confirmedCorrections = computed(() =>
  speciesProposals.value
    .filter((p) => !p.pending_confirm && (p.corrected || p.editValue))
    .map((p) => ({
      original: p.original,
      corrected: p.editValue || p.corrected,
      system_serials: p.system_serials,
    }))
)

async function applySpecies() {
  applyingSpecies.value = true
  agentError.value = ''
  try {
    const fd = new FormData()
    fd.append('file', xlsxBlob(), 'form.xlsx')
    fd.append('type_map', JSON.stringify(props.typeMap))
    fd.append('corrections', JSON.stringify(confirmedCorrections.value))
    const buf = await (await agentPost('/agent/apply-species', fd)).arrayBuffer()
    emit('xlsx-updated', buf)
    saved.value = true
  } catch (e) {
    agentError.value = `Save failed: ${e.message}`
  } finally {
    applyingSpecies.value = false
  }
}

// ── Bbox highlighting ────────────────────────────────────────────────────────

watch(activeProposal, (p) => {
  if (!p || !props.rowBboxes) {
    emit('highlight', { primary: [], secondary: [] })
    return
  }
  const serials = p.system_serials ?? []
  const primary = []
  const secondary = []
  serials.forEach((s, i) => {
    const bbox = props.rowBboxes.get(s)
    if (!bbox) return
    if (i === 0) primary.push({ serial: s, bbox })
    else secondary.push({ serial: s, bbox })
  })
  emit('highlight', { primary, secondary })
})
</script>
