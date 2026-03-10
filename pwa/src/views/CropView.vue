<template>
  <div class="flex flex-col h-full">
    <!-- Cropper area -->
    <div class="flex-1 min-h-0 overflow-hidden bg-black">
      <img ref="imgEl" :src="imageUrl" class="max-w-full block" />
    </div>

    <!-- Action bar -->
    <div class="p-4 flex justify-center">
      <button
        class="w-full max-w-xs h-14 rounded-lg bg-green-600 text-white font-medium text-lg active:bg-green-700 transition-colors"
        @click="cropAndSend"
      >
        Crop &amp; Send
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import { useFormStore } from '@/composables/useFormStore.js'

const MAX_DIM = 2048

const router = useRouter()
const { capturedImage, croppedImage } = useFormStore()

const imgEl = ref(null)
const imageUrl = ref(null)
let cropper = null

onMounted(() => {
  if (!capturedImage.value) return
  imageUrl.value = URL.createObjectURL(capturedImage.value)

  // Wait for image to load before initializing cropper
  const img = imgEl.value
  img.addEventListener('load', () => {
    cropper = new Cropper(img, {
      viewMode: 1,
      autoCropArea: 1,
      responsive: true,
    })
  }, { once: true })
})

onBeforeUnmount(() => {
  cropper?.destroy()
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
})

function cropAndSend() {
  if (!cropper) return

  const canvas = cropper.getCroppedCanvas({
    maxWidth: MAX_DIM,
    maxHeight: MAX_DIM,
  })

  canvas.toBlob(
    (blob) => {
      croppedImage.value = blob
      router.push({ name: 'processing' })
    },
    'image/jpeg',
    0.85,
  )
}
</script>
