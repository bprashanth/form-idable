<template>
  <div class="flex items-center justify-between px-4 py-2 bg-white shadow-sm">
    <div class="text-sm font-semibold">📄 FormViewer</div>
    <div class="flex space-x-2">
      <label class="text-sm bg-gray-200 px-2 py-1 rounded cursor-pointer hover:bg-gray-300">
        Load JSON
        <input type="file" accept=".json" class="hidden" @change="handleJson" />
      </label>

      <label class="text-sm bg-gray-200 px-2 py-1 rounded cursor-pointer hover:bg-gray-300">
        Load Image
        <input type="file" accept="image/*" class="hidden" @change="handleImage" />
      </label>

      <button
        class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
        @click="saveJson"
        :disabled="!jsonObject"
      >
        Save JSON
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['json-loaded', 'image-loaded'])

const jsonObject = ref(null)

function handleJson(e) {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result)
      jsonObject.value = data
      emit('json-loaded', data)
    } catch (err) {
      alert('Invalid JSON file' + err)
    }
  }
  reader.readAsText(file)
}

function handleImage(e) {
  const file = e.target.files[0]
  if (!file) return
  const url = URL.createObjectURL(file)
  emit('image-loaded', url)
}

function saveJson() {
  if (!jsonObject.value) return
  const blob = new Blob([JSON.stringify(jsonObject.value, null, 2)], {
    type: 'application/json',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'updated_output.json'
  a.click()
  URL.revokeObjectURL(url)
}
</script>
