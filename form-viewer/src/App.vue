<template>
  <div class="flex flex-col h-screen">
    <Toolbar
      class="border-b border-gray-300"
      @json-loaded="onJsonLoaded"
      @image-loaded="onImageLoaded"
    />

    <div class="flex flex-1 overflow-hidden">
      <!-- Form Viewer -->
      <div class="flex-1 relative overflow-auto bg-gray-100">
        <FormViewer
          v-if="formData && imageUrl"
          :formData="formData"
          :imageUrl="imageUrl"
          @select-row="onSelectRow"
        />
        <div v-else class="h-full flex items-center justify-center text-gray-500">
          <p>Select an image and JSON to begin.</p>
        </div>
      </div>

      <!-- Side Panel -->
      <div class="w-80 border-l border-gray-300 bg-gray-50">
        <SidePanel :selectedRow="selectedRow" @update-row="onUpdateRow" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Toolbar from '@/components/ToolBar.vue'
import FormViewer from '@/components/FormViewer.vue'
import SidePanel from '@/components/SidePanel.vue'

const formData = ref(null)
const imageUrl = ref(null)
const selectedRow = ref(null)

function onJsonLoaded(json) {
  formData.value = json
}
function onImageLoaded(url) {
  imageUrl.value = url
}
function onSelectRow(row) {
  selectedRow.value = row
}
function onUpdateRow(updatedRow) {
  selectedRow.value = updatedRow
}
</script>
