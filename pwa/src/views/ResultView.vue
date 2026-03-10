<template>
  <div class="flex flex-col items-center justify-center gap-6 p-6 h-full">
    <!-- Summary card (only if header was present) -->
    <div
      v-if="summary"
      class="w-full max-w-xs rounded-lg bg-gray-800 border border-gray-700 p-4 text-sm"
    >
      <h2 class="font-semibold mb-2">Summary</h2>
      <div class="flex justify-between text-gray-400">
        <span>Rows</span>
        <span class="text-gray-100">{{ summary.rowCount }}</span>
      </div>
      <div class="flex justify-between text-gray-400 mt-1">
        <span>Flagged</span>
        <span class="text-yellow-400">{{ summary.flaggedCount }}</span>
      </div>
    </div>

    <!-- File size -->
    <p class="text-gray-500 text-xs">{{ fileSizeLabel }}</p>

    <!-- Download button -->
    <button
      class="w-full max-w-xs h-14 rounded-lg bg-blue-600 text-white font-medium text-lg active:bg-blue-700 transition-colors"
      @click="download"
    >
      Download
    </button>

    <!-- Save to Google Drive -->
    <button
      v-if="driveState === 'idle'"
      class="w-full max-w-xs h-14 rounded-lg bg-green-600 text-white font-medium text-lg active:bg-green-700 transition-colors"
      @click="startDriveSave"
    >
      Save to Google Drive
    </button>

    <!-- Authenticating / picking folder -->
    <div
      v-if="driveState === 'auth' || driveState === 'picking'"
      class="w-full max-w-xs text-center text-gray-400 text-sm"
    >
      {{ driveState === 'auth' ? 'Signing in...' : 'Picking folder...' }}
    </div>

    <!-- Folder selected — file name input + upload -->
    <div
      v-if="driveState === 'ready'"
      class="w-full max-w-xs flex flex-col gap-3"
    >
      <div class="text-sm text-gray-400">
        Folder: <span class="text-gray-200">{{ selectedFolder.name }}</span>
      </div>
      <input
        v-model="driveFileName"
        type="text"
        class="w-full h-10 rounded-lg bg-gray-800 border border-gray-600 px-3 text-sm text-gray-100 focus:border-green-500 focus:outline-none"
        placeholder="File name"
      />
      <button
        class="w-full h-12 rounded-lg bg-green-600 text-white font-medium active:bg-green-700 transition-colors"
        @click="doUpload"
      >
        Upload
      </button>
    </div>

    <!-- Uploading -->
    <button
      v-if="driveState === 'uploading'"
      class="w-full max-w-xs h-14 rounded-lg bg-green-800 text-green-200 font-medium text-lg cursor-not-allowed"
      disabled
    >
      Uploading...
    </button>

    <!-- Success -->
    <div
      v-if="driveState === 'done'"
      class="w-full max-w-xs flex flex-col items-center gap-2"
    >
      <span class="text-green-400 font-medium">Saved</span>
      <a
        v-if="driveLink"
        :href="driveLink"
        target="_blank"
        rel="noopener"
        class="text-blue-400 underline text-sm"
      >
        Open in Drive
      </a>
    </div>

    <!-- Error -->
    <div
      v-if="driveState === 'error'"
      class="w-full max-w-xs flex flex-col items-center gap-2"
    >
      <span class="text-red-400 text-sm">{{ driveError }}</span>
      <button
        class="text-gray-400 underline text-xs"
        @click="driveState = 'idle'"
      >
        Try again
      </button>
    </div>

    <!-- Scan another -->
    <button
      class="w-full max-w-xs h-14 rounded-lg border border-gray-600 text-gray-300 font-medium text-lg active:bg-gray-800 transition-colors"
      @click="scanAnother"
    >
      Scan
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useFormStore } from '@/composables/useFormStore.js'
import { useGoogleAuth } from '@/composables/useGoogleAuth.js'
import { useDriveSave } from '@/composables/useDriveSave.js'

const router = useRouter()
const { xlsxBytes, summary, reset } = useFormStore()
const { accessToken, requestAccessToken } = useGoogleAuth()
const { pickFolder, uploadFile } = useDriveSave()

const driveState = ref('idle') // idle | auth | picking | ready | uploading | done | error
const driveError = ref('')
const driveLink = ref('')
const selectedFolder = ref(null)
const driveFileName = ref('form_output.xlsx')

const fileSizeLabel = computed(() => {
  if (!xlsxBytes.value) return ''
  const kb = (xlsxBytes.value.byteLength / 1024).toFixed(1)
  return `${kb} KB`
})

function download() {
  if (!xlsxBytes.value) return
  const blob = new Blob([xlsxBytes.value], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'form_output.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

async function startDriveSave() {
  try {
    // Step 1: Auth
    let token = accessToken.value
    if (!token) {
      driveState.value = 'auth'
      token = await requestAccessToken()
    }

    // Step 2: Pick folder
    driveState.value = 'picking'
    selectedFolder.value = await pickFolder(token)

    // Step 3: Ready for file name + upload
    driveState.value = 'ready'
  } catch (e) {
    driveError.value = e.message || 'Something went wrong'
    driveState.value = 'error'
  }
}

async function doUpload() {
  if (!selectedFolder.value || !driveFileName.value.trim()) return
  try {
    driveState.value = 'uploading'
    const result = await uploadFile(
      accessToken.value,
      selectedFolder.value.id,
      driveFileName.value.trim(),
      xlsxBytes.value,
    )
    driveLink.value = result.webViewLink || ''
    driveState.value = 'done'
  } catch (e) {
    driveError.value = e.message || 'Upload failed'
    driveState.value = 'error'
  }
}

function scanAnother() {
  reset()
  router.push({ name: 'capture' })
}
</script>
