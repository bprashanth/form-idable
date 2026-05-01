<template>
  <div class="flex flex-col items-center justify-center gap-4 h-full p-6">
    <!-- Spinner -->
    <div
      class="w-12 h-12 border-4 border-gray-600 border-t-blue-500 rounded-full animate-spin"
    ></div>

    <p class="text-gray-400 text-sm">Processing your form...</p>

    <p v-if="error" class="text-red-400 text-sm text-center max-w-xs mt-4">{{ error }}</p>
    <button
      v-if="error"
      class="mt-2 px-6 py-2 rounded-lg border border-gray-600 text-gray-300 active:bg-gray-800 transition-colors"
      @click="retry"
    >
      Retry
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFormStore } from '@/composables/useFormStore.js'
import { apiFetch } from '@/composables/useApi.js'

const router = useRouter()
const { croppedImage, xlsxBytes, summary, rowBboxes } = useFormStore()
const error = ref(null)

async function upload() {
  error.value = null

  const formData = new FormData()
  formData.append('image', croppedImage.value, 'capture.jpg')

  try {
    const res = await apiFetch('/api/upload', {
      method: 'POST',
      body: formData,
    })

    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `Server error ${res.status}`)
    }

    const payload = await res.json()
    xlsxBytes.value = Uint8Array.from(atob(payload.xlsx), c => c.charCodeAt(0)).buffer
    summary.value = payload.summary ?? null
    rowBboxes.value = new Map(
      (payload.rows ?? []).map(r => [r.system_serial, r.bbox])
    )

    router.push({ name: 'result' })
  } catch (e) {
    error.value = e.message || 'Upload failed'
  }
}

function retry() {
  upload()
}

onMounted(() => {
  if (croppedImage.value) upload()
})
</script>
