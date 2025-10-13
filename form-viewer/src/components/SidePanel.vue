<template>
  <div class="p-4 text-sm h-full overflow-y-auto bg-gray-900 text-gray-100">
    <!-- Row editing -->
    <template v-if="mode === 'row' && selectedRow">
      <h2 class="font-semibold mb-2">Row Fields</h2>
      <div v-for="[key, val] in filteredRowEntries" :key="`row-${key}`" class="mb-2">
        <label class="block text-gray-400">{{ key }}</label>
        <input
          :value="val"
          @input="emit('update-row', { ...selectedRow, [key]: $event.target.value })"
          class="w-full border border-gray-600 bg-gray-800 rounded px-1 py-0.5 text-xs text-gray-100"
        />
      </div>
    </template>

    <!-- Header editing -->
    <template v-else-if="mode === 'header' && headers">
      <h2 class="font-semibold mb-2">Header Fields</h2>

      <div
        v-for="[key, hdr] in localHeaderEntries"
        :key="`hdr-${key}`"
        class="mb-3 p-2 rounded border border-gray-700 bg-gray-800"
      >
        <div class="mb-1">
          <label class="block text-gray-400 text-xs">Indicator (key)</label>
          <input
            v-model="hdr._editKey"
            class="w-full border border-indigo-500 bg-gray-900 rounded px-1 py-0.5 text-xs text-gray-100"
          />
        </div>
        <div class="mb-1">
          <label class="block text-gray-400 text-xs">Field Name</label>
          <input
            v-model="hdr.field_name"
            class="w-full border border-indigo-400 bg-gray-900 rounded px-1 py-0.5 text-xs text-gray-100"
          />
        </div>
        <div>
          <label class="block text-gray-400 text-xs">Description</label>
          <textarea
            rows="2"
            v-model="hdr.description"
            class="w-full border border-indigo-400 bg-gray-900 rounded px-1 py-0.5 text-xs text-gray-100"
          ></textarea>
        </div>
      </div>

      <button
        class="mt-4 w-full py-1 text-sm bg-indigo-600 hover:bg-indigo-700 rounded text-white"
        @click="saveHeaderChanges"
      >
        Save
      </button>
    </template>

    <!-- Universal editing (unchanged) -->
    <template v-else-if="mode === 'universal' && universals">
      <h2 class="font-semibold mb-2">Universal Fields</h2>
      <div v-for="(uf, key) in universals" :key="key" class="mb-2 flex items-center gap-2">
        <input type="checkbox" v-model="uf.system.valid" class="accent-cyan-500" title="Valid?" />
        <div class="flex-1">
          <label class="block text-gray-400">{{ key }}</label>
          <input
            :value="uf.value"
            @input="updateUniversal(key, $event.target.value)"
            class="w-full border border-cyan-500 bg-gray-800 rounded px-1 py-0.5 text-xs text-gray-100"
          />
        </div>
      </div>
    </template>

    <div v-else class="text-gray-500">Click a box to edit.</div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  mode: String,
  selectedRow: Object,
  headers: Object,
  universals: Object,
})

const localHeaders = ref({})

// sync local editable copy whenever headers prop changes
watch(
  () => props.headers,
  (newVal) => {
    if (!newVal) {
      localHeaders.value = {}
      return
    }
    const copy = {}
    for (const [key, hdr] of Object.entries(newVal)) {
      if (key === 'system') continue
      copy[key] = {
        ...hdr,
        _editKey: key, // store editable key separately
      }
    }
    localHeaders.value = copy
  },
  { immediate: true, deep: true },
)

const localHeaderEntries = computed(() => Object.entries(localHeaders.value))

function saveHeaderChanges() {
  // Loop through local edits and emit final updates
  for (const [originalKey, hdr] of Object.entries(localHeaders.value)) {
    const newKey = hdr._editKey
    // emit indicator rename only if changed
    if (newKey !== originalKey) {
      emit('update-header', { key: originalKey, field: 'indicator', value: newKey })
    }
    emit('update-header', { key: newKey, field: 'field_name', value: hdr.field_name })
    emit('update-header', { key: newKey, field: 'description', value: hdr.description })
  }
}

// Filtered computed properties that exclude 'system' key
const filteredRowEntries = computed(() => {
  if (!props.selectedRow) return []
  return Object.entries(props.selectedRow).filter(([key]) => key !== 'system')
})

const emit = defineEmits(['update-row', 'update-header', 'update-universal'])

function updateUniversal(key, value) {
  emit('update-universal', { key, newVal: value })
}
</script>
