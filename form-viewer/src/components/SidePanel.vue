<template>
  <div class="p-4 text-sm h-full overflow-y-auto">
    <h2 class="font-semibold mb-2">Selected Row</h2>
    <div v-if="selectedRow">
      <div v-for="(val, key) in selectedRow" :key="key" class="mb-1">
        <div v-if="key !== 'system'">
          <label class="block text-gray-700">{{ key }}</label>
          <input
            :value="selectedRow[key]"
            @input="updateField(key, $event.target.value)"
            class="w-full border border-gray-300 rounded px-1 py-0.5 text-xs"
          />
        </div>
      </div>
    </div>
    <div v-else class="text-gray-400">Click a row to edit.</div>
  </div>
</template>

<script setup>
const props = defineProps({ selectedRow: Object })
const emit = defineEmits(['update-row'])

function updateField(key, value) {
  emit('update-row', { ...props.selectedRow, [key]: value })
}
</script>
