<template>
  <div class="flex flex-col items-center gap-6 p-6 h-full overflow-y-auto">
    <!-- Picker -->
    <label
      v-if="pages.length === 0"
      class="flex items-center justify-center w-full max-w-xs h-14 rounded-lg bg-blue-600 text-white font-medium text-lg active:bg-blue-700 cursor-pointer transition-colors"
      :class="{ 'opacity-60 pointer-events-none': loading }"
    >
      {{ loading ? 'Splitting PDF…' : 'Choose PDF' }}
      <input type="file" accept="application/pdf" class="sr-only" @change="onFile" />
    </label>

    <p v-if="error" class="text-red-400 text-sm text-center max-w-xs">{{ error }}</p>

    <!-- Thumbnail grid -->
    <template v-if="pages.length > 0">
      <div class="w-full flex items-center justify-between max-w-2xl">
        <p class="text-sm text-gray-400">{{ sourceFilename }} — {{ pages.length }} pages</p>
        <label class="text-xs text-blue-400 hover:text-blue-300 cursor-pointer underline">
          Choose another
          <input type="file" accept="application/pdf" class="sr-only" @change="onFile" />
        </label>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 w-full max-w-2xl">
        <button
          v-for="(p, i) in pages"
          :key="p.page"
          class="relative rounded-lg overflow-hidden border border-gray-700 bg-gray-800 aspect-[3/4] flex items-center justify-center disabled:cursor-default"
          :disabled="p.status !== 'done'"
          @click="goToReview(i)"
        >
          <img :src="thumbUrls[i]" class="w-full h-full object-cover" :alt="`Page ${p.page}`" />

          <span class="absolute top-1 left-1 text-xs bg-black/60 text-gray-200 rounded px-1.5 py-0.5">
            {{ p.page }}
          </span>

          <span
            class="absolute bottom-1 right-1 text-xs rounded px-1.5 py-0.5 font-medium"
            :class="badgeClass(p.status)"
          >{{ badgeLabel(p.status) }}</span>
        </button>
      </div>

      <p v-if="processError" class="text-red-400 text-sm text-center max-w-xs">{{ processError }}</p>

      <div class="flex flex-col gap-3 w-full max-w-xs">
        <button
          class="w-full h-12 rounded-lg bg-blue-600 text-white font-medium active:bg-blue-700 transition-colors disabled:opacity-40"
          :disabled="processing || allDone"
          @click="onProcessAll"
        >{{ processing ? `Processing page ${processingIndex + 1} of ${pages.length}…` : 'Process all' }}</button>

        <button
          class="w-full h-12 rounded-lg bg-green-700 text-white font-medium active:bg-green-800 transition-colors disabled:opacity-40"
          :disabled="!anyDone"
          @click="goToReview(firstDoneIndex)"
        >Start review</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { usePdfStore } from '@/composables/usePdfStore.js'

const router = useRouter()
const { pages, sourceFilename, reset, loadFromUpload, processPage } = usePdfStore()

const loading = ref(false)
const error = ref('')
const processing = ref(false)
const processError = ref('')
const processingIndex = ref(-1)

const allDone = computed(() => pages.value.length > 0 && pages.value.every((p) => p.status === 'done'))
const anyDone = computed(() => pages.value.some((p) => p.status === 'done'))
const firstDoneIndex = computed(() => pages.value.findIndex((p) => p.status === 'done'))

// ── Thumbnails ────────────────────────────────────────────────────────────────

const thumbUrls = ref([])

function rebuildThumbs() {
  thumbUrls.value.forEach((u) => URL.revokeObjectURL(u))
  thumbUrls.value = pages.value.map((p) => URL.createObjectURL(p.imageBlob))
}

watch(() => pages.value.length, rebuildThumbs)

onBeforeUnmount(() => {
  thumbUrls.value.forEach((u) => URL.revokeObjectURL(u))
})

function badgeClass(status) {
  switch (status) {
    case 'done': return 'bg-green-900 text-green-300'
    case 'processing': return 'bg-blue-900 text-blue-300'
    case 'error': return 'bg-red-900 text-red-300'
    default: return 'bg-gray-700 text-gray-400'
  }
}

function badgeLabel(status) {
  switch (status) {
    case 'done': return 'done'
    case 'processing': return '…'
    case 'error': return 'error'
    default: return 'pending'
  }
}

// ── File select ───────────────────────────────────────────────────────────────

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return

  loading.value = true
  error.value = ''
  processError.value = ''
  reset()

  try {
    const fd = new FormData()
    fd.append('file', file, file.name)
    const res = await fetch('/agent/pdf/pages', { method: 'POST', body: fd })
    if (!res.ok) {
      const text = await res.text().catch(() => res.statusText)
      throw new Error(text || `Server error ${res.status}`)
    }
    const data = await res.json()
    loadFromUpload(data, file.name)
  } catch (err) {
    error.value = err.message || 'Failed to split PDF'
  } finally {
    loading.value = false
  }
}

// ── Process all ──────────────────────────────────────────────────────────────

async function onProcessAll() {
  processing.value = true
  processError.value = ''
  try {
    for (let i = 0; i < pages.value.length; i++) {
      if (pages.value[i].status === 'done') continue
      processingIndex.value = i
      await processPage(i)
      if (pages.value[i].status === 'error') {
        processError.value = `Page ${pages.value[i].page}: ${pages.value[i].error}`
      }
    }
  } finally {
    processing.value = false
    processingIndex.value = -1
  }
}

function goToReview(index) {
  if (index < 0) return
  router.push({ name: 'pdf-review', params: { pageIndex: index } })
}
</script>
