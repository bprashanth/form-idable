<template>
  <div v-if="page" class="flex h-full overflow-hidden">
    <!-- Left: page image with bbox overlay -->
    <div class="flex-1 overflow-auto p-4 bg-gray-950 flex items-start justify-center">
      <FormImageOverlay
        :image-blob="page.imageBlob"
        :primary-entries="highlight.primary"
        :secondary-entries="highlight.secondary"
      />
    </div>

    <!-- Right: check cards -->
    <div class="w-80 shrink-0 flex flex-col gap-3 overflow-y-auto p-4 border-l border-gray-700">
      <div class="flex items-center justify-between">
        <button
          class="text-xs text-gray-500 hover:text-gray-300 underline"
          @click="router.push({ name: 'pdf-upload' })"
        >← Pages</button>
        <p class="text-xs text-gray-500">Page {{ page.page }} of {{ pages.length }}</p>
      </div>

      <p v-if="summary" class="text-xs text-gray-500">
        {{ summary.rowCount }} rows · {{ summary.flaggedCount }} flagged
      </p>

      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Data checks</p>

      <div v-if="typeEntries.length === 0" class="text-xs text-gray-500">
        No recognised columns on this page.
      </div>

      <CheckCard
        v-for="[col, info] in typeEntries"
        :key="col"
        :column="col"
        :type-info="info"
        :type-map="page.typeMap"
        :xlsx-bytes="page.xlsxBytes"
        :row-bboxes="page.rowBboxes"
        @xlsx-updated="(buf) => onXlsxUpdated(buf)"
        @highlight="(h) => (highlight = h)"
      />

      <!-- Page nav -->
      <div class="flex gap-2 mt-auto pt-2 shrink-0">
        <button
          class="flex-1 h-10 rounded-lg border border-gray-600 text-gray-300 active:bg-gray-800 transition-colors disabled:opacity-40"
          :disabled="pageIndex === 0"
          @click="goTo(pageIndex - 1)"
        >Prev</button>
        <button
          class="flex-1 h-10 rounded-lg border border-gray-600 text-gray-300 active:bg-gray-800 transition-colors disabled:opacity-40"
          :disabled="pageIndex === pages.length - 1"
          @click="goTo(pageIndex + 1)"
        >Next</button>
      </div>

      <button
        class="w-full h-12 rounded-lg bg-blue-600 text-white font-medium active:bg-blue-700 transition-colors disabled:opacity-40 shrink-0"
        :disabled="!allDone"
        @click="download"
      >Download merged Excel</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePdfStore } from '@/composables/usePdfStore.js'
import FormImageOverlay from '@/components/FormImageOverlay.vue'
import CheckCard from '@/components/CheckCard.vue'

const route = useRoute()
const router = useRouter()
const { pages, downloadMerged } = usePdfStore()

const pageIndex = computed(() => parseInt(route.params.pageIndex, 10))
const page = computed(() => pages.value[pageIndex.value] ?? null)
const summary = computed(() => page.value?.summary ?? null)

const typeEntries = computed(() => Object.entries(page.value?.typeMap ?? {}))

const allDone = computed(() => pages.value.length > 0 && pages.value.every((p) => p.status === 'done'))

const highlight = ref({ primary: [], secondary: [] })

// Reset highlight when navigating between pages
watch(pageIndex, () => {
  highlight.value = { primary: [], secondary: [] }
})

function onXlsxUpdated(buf) {
  if (page.value) page.value.xlsxBytes = buf
}

function goTo(index) {
  router.push({ name: 'pdf-review', params: { pageIndex: index } })
}

function download() {
  downloadMerged()
}
</script>
