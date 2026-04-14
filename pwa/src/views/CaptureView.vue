<template>
  <div class="flex flex-col items-center justify-center gap-6 p-6 h-full">
    <!-- Camera capture -->
    <label
      class="flex items-center justify-center w-full max-w-xs h-14 rounded-lg bg-blue-600 text-white font-medium text-lg active:bg-blue-700 cursor-pointer transition-colors"
    >
      Take Photo
      <input
        type="file"
        accept="image/*"
        capture="environment"
        class="sr-only"
        @change="onFile"
      />
    </label>

    <!-- Gallery fallback -->
    <label
      class="flex items-center justify-center w-full max-w-xs h-14 rounded-lg border border-gray-600 text-gray-300 font-medium text-lg active:bg-gray-800 cursor-pointer transition-colors"
    >
      Choose from Gallery
      <input type="file" accept="image/*" class="sr-only" @change="onFile" />
    </label>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useFormStore } from '@/composables/useFormStore.js'

const router = useRouter()
const { capturedImage } = useFormStore()

function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  capturedImage.value = file
  router.push({ name: 'crop' })
}
</script>
