<template>
  <div class="flex flex-col h-screen bg-gray-900 text-gray-100">
    <ToolBar
      class="border-b border-gray-700"
      @json-loaded="onJsonLoaded"
      @image-loaded="onImageLoaded"
      @save-json="saveJson"
      @zoom-in="zoomIn"
      @zoom-out="zoomOut"
    />

    <div class="flex flex-1 overflow-hidden">
      <div class="flex-1 relative overflow-auto bg-gray-800">
        <FormViewer
          v-if="formData && imageUrl"
          :formData="formData"
          :imageUrl="imageUrl"
          :zoom="zoom"
          @select-row="onSelectRow"
        />
        <div v-else class="h-full flex items-center justify-center text-gray-500">
          <p>Select an image and JSON to begin.</p>
        </div>
      </div>

      <div class="w-80 border-l border-gray-700 bg-gray-850">
        <SidePanel :selectedRow="selectedRow" @update-row="updateRow" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ToolBar from '@/components/ToolBar.vue'
import FormViewer from '@/components/FormViewer.vue'
import SidePanel from '@/components/SidePanel.vue'

const formData = ref(null)
const imageUrl = ref(null)
const selectedRow = ref(null)
const zoom = ref(1)

function onJsonLoaded(json) {
  formData.value = json
}
function onImageLoaded(url) {
  imageUrl.value = url
}
function onSelectRow(row) {
  selectedRow.value = row
}
function updateRow(updatedRow) {
  if (!formData.value || !selectedRow.value) return
  const idx = formData.value.rows.findIndex(
    (r) => r.system.group_id === selectedRow.value.system.group_id,
  )
  if (idx !== -1) {
    formData.value.rows[idx] = updatedRow
    selectedRow.value = updatedRow
  }
}
function saveJson() {
  if (!formData.value) return
  const blob = new Blob([JSON.stringify(formData.value, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'updated_output.json'
  a.click()
  URL.revokeObjectURL(url)
}
function zoomIn() {
  zoom.value = Math.min(zoom.value + 0.1, 2)
}
function zoomOut() {
  zoom.value = Math.max(zoom.value - 0.1, 0.5)
}
</script>
