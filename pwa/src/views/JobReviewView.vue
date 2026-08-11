<template>
  <div class="flex h-screen w-full overflow-hidden bg-surface font-body text-on-surface">

    <!-- Sidebar -->
    <aside class="hidden md:flex flex-col h-full py-6 px-4 bg-surface-container-low w-64 shrink-0 border-r border-outline-variant/20">
      <div class="mb-8 px-2 flex items-center gap-3">
        <div class="w-8 h-8 bg-primary flex items-center justify-center rounded-sm shrink-0">
          <span class="material-symbols-outlined text-on-primary text-sm">dynamic_form</span>
        </div>
        <div>
          <h1 class="font-headline font-black text-lg text-primary leading-none tracking-tighter">FORMIDABLE</h1>
          <p class="text-[10px] uppercase tracking-widest text-on-surface-variant mt-0.5">Form Processing Engine</p>
        </div>
      </div>
      <nav class="flex-1 space-y-1">
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer"
           @click="router.push('/dashboard')">
          <span class="material-symbols-outlined">dashboard</span>
          <span>Dashboard</span>
        </a>
        <a class="flex items-center gap-3 px-3 py-2 text-primary font-bold bg-surface-container-highest rounded-sm cursor-pointer">
          <span class="material-symbols-outlined">find_in_page</span>
          <span>Review</span>
        </a>
        <a class="flex items-center gap-3 px-3 py-2 transition-colors"
           data-testid="analytics-nav"
           :class="reviewManifest
             ? 'text-on-surface-variant hover:bg-surface-container-high cursor-pointer'
             : 'text-outline/45 cursor-not-allowed'"
           :title="reviewManifest ? 'Open read-only distributions' : 'Analytics is available for High effort jobs'"
           @click="reviewManifest && router.push({ name: 'job-analytics', params: { jobId } })">
          <span class="material-symbols-outlined">analytics</span>
          <span>Analytics</span>
        </a>
      </nav>
      <div class="pt-4 border-t border-outline-variant/20 space-y-1">
        <a class="flex items-center gap-3 px-3 py-2 text-on-surface-variant hover:bg-surface-container-high transition-colors cursor-pointer">
          <span class="material-symbols-outlined">help</span>
          <span>Help Center</span>
        </a>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden">

      <!-- Header -->
      <header class="flex justify-between items-center px-6 py-3 border-b border-outline-variant/20 bg-surface-container-lowest shrink-0 z-40"
              style="box-shadow: 0 8px 32px rgba(11,28,48,0.06)">
        <div class="flex items-center gap-3">
          <button class="p-2 -ml-2 text-on-surface-variant hover:bg-surface-container-low rounded-sm"
                  @click="router.push('/dashboard')">
            <span class="material-symbols-outlined">arrow_back</span>
          </button>
          <div>
            <h2 class="font-headline font-black text-lg text-primary leading-tight">{{ jobName }}</h2>
            <p class="text-[10px] text-on-surface-variant">{{ route.params.jobId }}</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div v-if="correctionCount > 0"
               class="flex items-center gap-2 px-3 py-1.5 bg-tertiary-fixed-dim/30 text-on-background text-xs font-bold rounded-sm">
            <span class="material-symbols-outlined text-sm">edit_note</span>
            {{ correctionCount }} correction{{ correctionCount !== 1 ? 's' : '' }}
          </div>
          <div class="flex items-center gap-2 bg-surface-container-low px-3 py-1.5 rounded-sm">
            <button :disabled="currentPage <= 1"
                    class="disabled:opacity-30 text-on-surface-variant hover:text-primary transition-colors"
                    @click="goPage(currentPage - 1)">
              <span class="material-symbols-outlined text-lg">chevron_left</span>
            </button>
            <span class="text-sm font-bold min-w-[4rem] text-center text-primary">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button :disabled="currentPage >= totalPages"
                    class="disabled:opacity-30 text-on-surface-variant hover:text-primary transition-colors"
                    @click="goPage(currentPage + 1)">
              <span class="material-symbols-outlined text-lg">chevron_right</span>
            </button>
          </div>
          <button
            class="bg-secondary text-on-secondary px-5 py-2 text-xs font-black tracking-widest hover:opacity-90 active:scale-95 transition-all"
            @click="submitReview"
          >SUBMIT REVIEW</button>
        </div>
      </header>

      <!-- Zoom toolbar -->
      <div class="flex items-center gap-1 px-4 py-2 border-b border-outline-variant/10 bg-surface-container-lowest shrink-0">
        <button
          class="p-1.5 rounded-sm text-on-surface-variant hover:bg-surface-container transition-colors disabled:opacity-30"
          :disabled="imgZoom <= 1"
          title="Zoom out"
          @click="stepZoom(-1)"
        >
          <span class="material-symbols-outlined text-lg">zoom_out</span>
        </button>
        <span class="text-xs font-mono font-bold text-on-surface-variant min-w-[3.5rem] text-center select-none">
          {{ Math.round(imgZoom * 100) }}%
        </span>
        <button
          class="p-1.5 rounded-sm text-on-surface-variant hover:bg-surface-container transition-colors disabled:opacity-30"
          :disabled="imgZoom >= MAX_ZOOM"
          title="Zoom in"
          @click="stepZoom(1)"
        >
          <span class="material-symbols-outlined text-lg">zoom_in</span>
        </button>
        <div class="w-px h-4 bg-outline-variant/40 mx-1" />
        <button
          class="p-1.5 rounded-sm text-on-surface-variant hover:bg-surface-container transition-colors disabled:opacity-30"
          :disabled="imgZoom === 1"
          title="Reset"
          @click="resetZoom"
        >
          <span class="material-symbols-outlined text-lg">fit_screen</span>
        </button>
        <template v-if="reviewManifest">
          <div class="w-px h-4 bg-outline-variant/40 mx-1" />
          <button
            class="p-1.5 rounded-sm text-on-surface-variant hover:bg-surface-container transition-colors"
            title="Rotate page left"
            data-testid="rotate-page-left"
            @click="rotatePage(-90)"
          >
            <span class="material-symbols-outlined text-lg">rotate_left</span>
          </button>
          <button
            class="p-1.5 rounded-sm text-on-surface-variant hover:bg-surface-container transition-colors"
            title="Rotate page right"
            data-testid="rotate-page-right"
            @click="rotatePage(90)"
          >
            <span class="material-symbols-outlined text-lg">rotate_right</span>
          </button>
        </template>
        <span class="ml-3 text-[10px] text-on-surface-variant">
          {{ imgZoom > 1 ? 'Drag to pan · Hover crop to sync table · Click to inspect' : 'Hover crop to sync table · Click to inspect · Scroll or +/− to zoom' }}
        </span>
      </div>

      <!-- Optional v2 review queues. Transcription uncertainty and ecology
           plausibility stay separate so a domain hint is never mistaken for
           a literal correction. -->
      <div
        v-if="reviewManifest"
        class="flex items-center gap-2 px-4 py-2 border-b border-outline-variant/15 bg-surface-container-low shrink-0"
        data-testid="review-summary"
      >
        <span class="text-[10px] uppercase tracking-widest font-black text-on-surface-variant mr-1">Review focus</span>
        <button
          v-for="choice in reviewChoices"
          :key="choice.id"
          class="px-3 py-1.5 text-[10px] font-black uppercase tracking-wide border transition-colors"
          :class="reviewMode === choice.id
            ? 'bg-primary text-on-primary border-primary'
            : 'bg-surface text-on-surface-variant border-outline-variant/40 hover:border-primary/50'"
          :data-testid="`review-mode-${choice.id}`"
          @click="reviewMode = choice.id"
        >
          {{ choice.label }} <span class="font-mono">{{ choice.count }}</span>
        </button>
        <span class="ml-auto text-[10px] text-on-surface-variant">
          Values shown are literal; alternatives and ecology flags are never auto-applied.
        </span>
      </div>

      <!-- Split content area: image (left) + Excel table (right) -->
      <div class="flex-1 flex min-h-0 overflow-hidden">

        <!-- Left: page image viewport with bbox overlays -->
        <div
          ref="viewport"
          class="flex-1 min-w-0 overflow-hidden relative select-none"
          data-testid="review-content"
          @wheel.prevent="onWheel"
        >
          <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-on-surface-variant text-sm">
            Loading form…
          </div>

          <div v-else-if="loadError" class="absolute inset-0 flex items-center justify-center p-8">
            <div class="max-w-md w-full border border-error/30 bg-error-container p-6 flex flex-col gap-3">
              <div class="flex items-center gap-2 text-error font-black text-sm uppercase tracking-widest">
                <span class="material-symbols-outlined text-base">error</span>
                Failed to load form data
              </div>
              <p class="text-sm text-on-error-container">{{ loadError }}</p>
              <p class="text-[10px] font-mono text-error/70 break-all">job: {{ jobId }}</p>
              <button
                class="self-start mt-1 px-4 py-2 text-xs font-black bg-error text-on-error hover:opacity-90 transition-opacity"
                @click="retryLoad"
              >
                Retry
              </button>
            </div>
          </div>

          <!-- Panning layer — fills viewport, centres content -->
          <div
            v-else
            class="absolute inset-0 flex items-center justify-center"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
          >
            <!-- Scaled + panned image group -->
            <div
              class="relative inline-block"
              data-testid="page-image-wrapper"
              :style="canvasStyle"
            >
              <img
                ref="pageImg"
                :src="currentPageBlobUrl"
                class="block max-w-none"
                :style="imgSizeStyle"
                :data-testid="`page-img-${currentPage}`"
                @load="onImageLoad"
                @click="onImgClick"
                draggable="false"
              />

              <!-- Crop bbox overlays — 4px inset so borders stay inside image bounds -->
              <div
                v-for="crop in currentCrops"
                :key="crop.file"
                class="absolute border-2 transition-colors"
                :class="hasCropCorrections(crop)
                  ? 'border-tertiary-fixed-dim bg-tertiary-fixed-dim/20 hover:bg-tertiary-fixed-dim/30'
                  : 'border-secondary bg-secondary/10 hover:bg-secondary/20'"
                :style="cropStyle(crop)"
                :title="crop.note"
                :data-testid="`crop-${crop.file}`"
                @mouseenter="hoveredCrop = crop"
                @mouseleave="hoveredCrop = null"
                @click.stop="onCropClick(crop)"
              >
                <span v-if="hasCropCorrections(crop)"
                      class="absolute -top-1.5 -right-1.5 w-3 h-3 bg-tertiary-fixed-dim rounded-full border border-white" />
              </div>

              <!-- Cell-level attention overlays sit above broad production
                   crops and open the same correction modal at the exact bbox. -->
              <button
                v-for="item in currentAttention"
                :key="item.cell_id"
                class="absolute border-2 border-error bg-error/15 hover:bg-error/30 z-10"
                :style="attentionStyle(item)"
                :title="`${item.reason}: ${item.presented_value ?? 'blank'}`"
                :data-testid="`attention-${item.cell_id}`"
                @click.stop="onAttentionClick(item)"
              >
                <span class="sr-only">Review {{ item.cell_id }}</span>
              </button>

              <button
                v-for="item in currentEcologyWithBoxes"
                :key="`ecology-${item.finding_id}`"
                class="absolute border-2 border-orange-500 bg-orange-400/15 hover:bg-orange-400/30 z-[9]"
                :style="attentionStyle(item)"
                :title="`${item.message}: ${item.observed ?? 'blank'}`"
                :data-testid="`ecology-overlay-${item.finding_id}`"
                @click.stop="goToFinding(item)"
              >
                <span class="sr-only">Ecology review {{ item.finding_id }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Right: full Excel table panel -->
        <div class="w-[44%] shrink-0 flex flex-col border-l border-outline-variant/20 bg-surface overflow-hidden">
          <div class="px-4 py-2 border-b border-outline-variant/10 shrink-0 flex items-center gap-2 bg-surface-container-lowest">
            <span class="material-symbols-outlined text-sm text-on-surface-variant">{{ reviewMode === 'all' ? 'table_chart' : 'fact_check' }}</span>
            <span class="text-[10px] uppercase tracking-widest font-black text-on-surface-variant">
              {{ reviewMode === 'all' ? 'Excel Output' : reviewMode === 'attention' ? 'Transcription attention' : 'Ecology anomalies' }}
            </span>
            <span class="ml-auto text-[10px] text-outline/60">{{ panelCountLabel }}</span>
          </div>
          <div v-if="reviewMode === 'all'" ref="xlsxPanel" class="flex-1 overflow-auto min-h-0" data-testid="xlsx-panel">
            <div v-if="loading || !xlsxRows.length" class="p-4 text-xs text-on-surface-variant">
              {{ loading ? 'Loading…' : 'No data.' }}
            </div>
            <table v-else class="text-[11px] border-collapse">
              <tbody>
                <tr
                  v-for="row in xlsxRows"
                  :key="row.rowNum"
                  :data-rownum="row.rowNum"
                  :class="[
                    'border-b border-outline-variant/10 transition-colors',
                    isRowHighlighted(row.rowNum)
                      ? 'bg-secondary/15 ring-1 ring-inset ring-secondary/30'
                      : 'hover:bg-primary/5',
                  ]"
                >
                  <td class="py-1 px-2 font-mono text-[10px] text-outline font-bold text-center align-top sticky left-0 bg-surface border-r border-outline-variant/10 w-8 shrink-0">
                    {{ row.rowNum }}
                  </td>
                  <td
                    v-for="(cell, ci) in row.cells"
                    :key="ci"
                    :data-testid="`xlsx-cell-${currentPage}-${row.rowNum}-${ci}`"
                    class="py-1 px-2 border-r border-outline-variant/10 align-top whitespace-nowrap"
                    :style="cellBgStyle(row.rowNum, ci, cell)"
                  >
                    <span
                      :class="isCellCorrected(row.rowNum, ci)
                        ? 'font-semibold underline decoration-tertiary-fixed-dim decoration-2 underline-offset-2'
                        : ''"
                    >{{ getCellValue(row.rowNum, ci, cell) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else-if="reviewMode === 'attention'" class="flex-1 overflow-auto min-h-0 p-3 space-y-2" data-testid="attention-queue">
            <button
              v-for="item in currentAttention"
              :key="item.cell_id"
              class="w-full text-left border border-error/25 bg-error-container/20 hover:bg-error-container/35 p-3 transition-colors"
              @click="onAttentionClick(item)"
            >
              <div class="flex items-start justify-between gap-3">
                <span class="font-mono text-xs font-black text-error">{{ item.presented_value ?? '∅' }}</span>
                <span class="text-[9px] uppercase tracking-widest font-black text-error">{{ item.priority }}</span>
              </div>
              <p class="text-xs text-on-surface mt-1">{{ item.reason }}</p>
              <p v-if="otherAlternatives(item).length" class="text-[10px] text-on-surface-variant mt-1">
                Other reader: {{ otherAlternatives(item).join(' · ') }}
              </p>
              <p class="text-[9px] font-mono text-outline mt-2 break-all">{{ item.cell_id }}</p>
            </button>
            <p v-if="!currentAttention.length" class="p-4 text-xs text-on-surface-variant">No transcription items on this page.</p>
          </div>
          <div v-else class="flex-1 overflow-auto min-h-0 p-3 space-y-2" data-testid="ecology-queue">
            <button
              v-for="item in currentEcology"
              :key="item.finding_id"
              class="w-full text-left border border-tertiary-fixed-dim/50 bg-tertiary-fixed/20 hover:bg-tertiary-fixed/35 p-3 transition-colors"
              @click="goToFinding(item)"
            >
              <div class="flex items-start justify-between gap-3">
                <span class="text-xs font-black text-on-surface">{{ item.label || item.code }}</span>
                <span class="text-[9px] uppercase tracking-widest font-black text-on-surface-variant">{{ item.severity }}</span>
              </div>
              <p class="text-xs text-on-surface mt-1">{{ item.message }}</p>
              <p class="text-[10px] text-on-surface-variant mt-1">
                Observed {{ item.observed ?? '—' }}<span v-if="item.median != null"> · median {{ item.median }}</span><span v-if="item.mad != null"> · MAD {{ item.mad }}</span>
              </p>
              <p class="text-[9px] text-outline mt-2">Flag only—no value was changed.</p>
            </button>
            <p v-if="!currentEcology.length" class="p-4 text-xs text-on-surface-variant">No ecology findings on this page.</p>
          </div>
        </div>

      </div>
    </main>

    <!-- Modal -->
    <Teleport to="body">
      <div
        v-if="modal"
        class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40 backdrop-blur-sm"
        data-testid="review-modal"
        @click.self="closeModal"
      >
        <div class="relative flex gap-0 max-w-5xl w-full mx-4 max-h-[88vh] overflow-hidden shadow-2xl"
             style="background: rgba(255,255,255,0.98)">

          <button class="absolute top-4 right-4 z-10 p-1 text-on-surface-variant hover:text-primary"
                  @click="closeModal">
            <span class="material-symbols-outlined">close</span>
          </button>

          <!-- Left: image with zoom/pan -->
          <div class="w-[45%] shrink-0 flex flex-col bg-surface-container-lowest border-r border-outline-variant/20 overflow-hidden">
            <div class="px-5 py-3 border-b border-outline-variant/20 flex items-center gap-3 shrink-0">
              <span class="text-[10px] uppercase tracking-widest font-black text-on-surface-variant">
                {{ modal.type === 'crop' ? 'Crop Extract' : 'Page Zoom' }}
              </span>
              <span v-if="modal.note" class="text-[10px] text-on-surface-variant italic truncate">{{ modal.note }}</span>
            </div>
            <!-- Zoomable viewport -->
            <div
              class="flex-1 overflow-hidden relative min-h-0"
              @wheel.prevent="onModalWheel"
              @mousedown="onModalMouseDown"
              @mousemove="onModalMouseMove"
            >
              <div class="absolute inset-0 flex items-center justify-center p-4">
                <div :style="modalCanvasStyle">
                  <img
                    v-if="modal.type === 'crop'"
                    :src="modalCropBlobUrl"
                    class="block max-w-none"
                    style="max-width: 100%; max-height: 100%;"
                    data-testid="modal-crop-img"
                  />
                  <canvas
                    v-else
                    ref="zoomCanvas"
                    class="block"
                    data-testid="modal-zoom-canvas"
                  />
                </div>
              </div>
              <!-- Floating zoom HUD -->
              <div class="absolute bottom-3 right-3 flex items-center gap-0.5 bg-white/90 border border-outline-variant/30 shadow-sm px-1 py-0.5">
                <button
                  class="p-1 text-on-surface-variant hover:text-primary disabled:opacity-30 transition-colors"
                  :disabled="modalZoom <= 0.2"
                  @click.stop="stepModalZoom(-1)"
                >
                  <span class="material-symbols-outlined text-base leading-none">remove</span>
                </button>
                <span class="text-[10px] font-mono font-bold text-on-surface-variant min-w-[2.8rem] text-center select-none">
                  {{ Math.round(modalZoom * 100) }}%
                </span>
                <button
                  class="p-1 text-on-surface-variant hover:text-primary disabled:opacity-30 transition-colors"
                  :disabled="modalZoom >= 10"
                  @click.stop="stepModalZoom(1)"
                >
                  <span class="material-symbols-outlined text-base leading-none">add</span>
                </button>
                <div class="w-px h-3 bg-outline-variant/40 mx-0.5" />
                <button
                  class="p-1 text-on-surface-variant hover:text-primary transition-colors"
                  @click.stop="resetModalZoom"
                >
                  <span class="material-symbols-outlined text-base leading-none">fit_screen</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Right: correction panel -->
          <div class="flex-1 min-w-0 flex flex-col">
            <div class="px-5 py-3 border-b border-outline-variant/20 flex items-center justify-between shrink-0">
              <div>
                <span class="text-[10px] uppercase tracking-widest font-black text-on-surface-variant">
                  {{ modal.type === 'crop' ? `Rows ${modal.rowRange}` : 'Estimated rows' }}
                </span>
                <p class="text-[10px] text-on-surface-variant mt-0.5">Click any cell to correct it</p>
              </div>
              <span class="text-[10px] text-on-surface-variant">{{ modal.rows?.length ?? 0 }} row(s)</span>
            </div>
            <div class="flex-1 overflow-auto min-h-0">
              <div v-if="modal.rows?.length" class="overflow-x-auto min-w-0">
                <table class="text-[11px] border-collapse">
                  <tbody>
                    <tr v-for="row in modal.rows" :key="row.rowNum" class="border-b border-outline-variant/10">
                      <td class="py-1 px-2 font-mono text-outline font-bold w-8 text-center align-top sticky left-0 bg-surface border-r border-outline-variant/10">{{ row.rowNum }}</td>
                      <td
                        v-for="(cell, ci) in row.cells"
                        :key="ci"
                        class="py-0.5 px-1 border-r border-outline-variant/10 align-top"
                        :style="cellBgStyle(row.rowNum, ci, cell)"
                      >
                        <input
                          :value="getCellValue(row.rowNum, ci, cell)"
                          class="min-w-[7rem] bg-transparent border-0 focus:ring-0 text-[11px] py-0.5 px-1 focus:outline-none focus:ring-1 focus:ring-secondary/40 transition-colors"
                          :class="isCellCorrected(row.rowNum, ci) ? 'font-semibold underline decoration-tertiary-fixed-dim decoration-2 underline-offset-2' : ''"
                          @change="onCellEdit(row.rowNum, ci, $event.target.value, cell.value)"
                          @focus="$event.target.select()"
                        />
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p v-else class="text-on-surface-variant text-xs p-4">No rows available.</p>
            </div>
            <div class="px-5 py-3 border-t border-outline-variant/20 flex justify-between items-center shrink-0">
              <button v-if="modalHasCorrections"
                      class="text-xs text-error font-bold hover:opacity-70 transition-opacity"
                      @click="revertModalCorrections">
                Revert changes
              </button>
              <span v-else class="text-[10px] text-on-surface-variant">No corrections yet</span>
              <button class="bg-primary text-on-primary px-4 py-2 text-xs font-black tracking-widest active:scale-95 transition-all"
                      @click="closeModal">Done</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useJobStore } from '@/composables/useJobStore.js'

const route  = useRoute()
const router = useRouter()
const { fetchJobDetail, fetchAuthedUrl, pageUrl, cropUrl, estimateRows, rowsForRange, submitReview: submitReviewApi } = useJobStore()

const jobId = route.params.jobId

// ── Excel panel + hover/pan sync ─────────────────────────────────────────────
const xlsxPanel   = ref(null)
const hoveredCrop = ref(null)

const hoveredRange = computed(() => {
  if (!hoveredCrop.value?.rows) return null
  const crops = currentCrops.value
  const idx   = crops.findIndex(c => c.file === hoveredCrop.value.file)
  const parts = String(hoveredCrop.value.rows).split(':').map(Number)
  const end   = parts[1] ?? parts[0]
  // Extend start back to fill the gap after the previous crop ends.
  // The codex agent sometimes leaves column-header rows (e.g. rows 6-9) between
  // crop ranges; visually they're inside this crop's bbox so we highlight them too.
  let start = parts[0]
  if (idx > 0) {
    const prev     = crops[idx - 1]
    const prevParts = String(prev.rows).split(':').map(Number)
    start = (prevParts[1] ?? prevParts[0]) + 1
  }
  return { start, end, scrollTo: parts[0] }
})

function isRowHighlighted(rowNum) {
  const r = hoveredRange.value
  return r !== null && rowNum >= r.start && rowNum <= r.end
}

watch(hoveredCrop, (crop) => {
  if (!crop?.rows || !xlsxPanel.value) return
  const range = hoveredRange.value
  if (!range) return
  const el = xlsxPanel.value.querySelector(`tr[data-rownum="${range.scrollTo}"]`)
  if (el) {
    const panelH = xlsxPanel.value.clientHeight
    xlsxPanel.value.scrollTop = Math.max(0, el.offsetTop - panelH / 4)
  }
}, { flush: 'post' })

// Piecewise-linear mapping: image Y fraction → xlsxRows index
// Uses crop bboxes as calibration anchors so the mapping follows form structure,
// not just a naive linear proportion. Side-by-side crops at the same Y get
// deduplicated (keep the min row index = the earlier/left table).
function _imageYToExcelRow(fracY) {
  const rows  = xlsxRows.value
  const crops = currentCrops.value.filter(c => c.bbox && c.rows)
  if (!rows.length || !crops.length) return 0
  const anchors = []
  for (const crop of crops) {
    const [, y0, , y1] = crop.bbox
    const rowNum = parseInt(String(crop.rows).split(':')[0])
    const idx    = rows.findIndex(r => r.rowNum === rowNum)
    if (idx >= 0) anchors.push({ imgY: (y0 + y1) / 2, idx })
  }
  anchors.sort((a, b) => a.imgY - b.imgY || a.idx - b.idx)
  // Deduplicate same imgY, keep min idx
  const pts = []
  for (const a of anchors) {
    if (!pts.length || a.imgY !== pts[pts.length - 1].imgY) pts.push(a)
  }
  if (!pts.length) return 0
  if (fracY <= pts[0].imgY) return pts[0].idx
  if (fracY >= pts[pts.length - 1].imgY) return pts[pts.length - 1].idx
  for (let i = 1; i < pts.length; i++) {
    if (fracY <= pts[i].imgY) {
      const t = (fracY - pts[i - 1].imgY) / (pts[i].imgY - pts[i - 1].imgY)
      return Math.round(pts[i - 1].idx + t * (pts[i].idx - pts[i - 1].idx))
    }
  }
  return pts[pts.length - 1].idx
}

function syncExcelScroll() {
  if (!xlsxPanel.value || !imgNatH.value || !imgNatW.value) return

  // Y axis — crop-anchor interpolation
  const fracY  = Math.max(0, Math.min(1, 0.5 - panY.value / imgNatH.value))
  const rowIdx = _imageYToExcelRow(fracY)
  const rowEls = xlsxPanel.value.querySelectorAll('tr')
  if (rowEls[rowIdx]) {
    const panelH = xlsxPanel.value.clientHeight
    xlsxPanel.value.scrollTop = Math.max(0, rowEls[rowIdx].offsetTop - panelH / 3)
  }

  // X axis — proportional within whichever data crop the viewport center falls in.
  // Only tall crops (>20% page height) are data crops; short ones are header/notes rows
  // whose metadata columns don't match the data column layout.
  const fracX     = Math.max(0, Math.min(1, 0.5 - panX.value / imgNatW.value))
  const dataCrop  = currentCrops.value.find(c => {
    if (!c.bbox) return false
    const [x0, y0, x1, y1] = c.bbox
    return (y1 - y0) > 0.20 && fracX >= x0 && fracX <= x1
  })
  if (dataCrop) {
    const [x0, , x1] = dataCrop.bbox
    const fracXInCrop = (fracX - x0) / (x1 - x0)
    const maxScrollX  = xlsxPanel.value.scrollWidth - xlsxPanel.value.clientWidth
    if (maxScrollX > 0) xlsxPanel.value.scrollLeft = fracXInCrop * maxScrollX
  }
}

function scrollSharedWorkbookToPage() {
  if (xlsxPages.value.length !== 1 || totalPages.value <= 1 || !xlsxPanel.value) return
  const candidates = currentCrops.value
    .map(crop => {
      const [start, end = start] = String(crop.rows ?? '').split(':').map(Number)
      return { start, span: end - start }
    })
    .filter(item => Number.isFinite(item.start))
    .sort((a, b) => b.span - a.span || a.start - b.start)
  const target = candidates[0]
  if (!target) return
  const row = xlsxPanel.value.querySelector(`tr[data-rownum="${target.start}"]`)
  if (row) xlsxPanel.value.scrollTop = Math.max(0, row.offsetTop - 16)
}

// ── Data ─────────────────────────────────────────────────────────────────────
const loading     = ref(true)
const loadError   = ref(null)
const manifest    = ref(null)
const xlsxPages   = ref([])
const xlsxSheetNames = ref([])
const reviewManifest = ref(null)
const reviewMode  = ref('all')
const currentPage = ref(1)
const corrections = ref({})
const modal       = ref(null)
const zoomCanvas  = ref(null)

// New exact-layout outputs contain one workbook sheet per paper page. Legacy
// production workbooks may still be one flat sheet, so retain page one as the
// explicit fallback instead of silently showing it as if it matched every page.
const currentSheetIndex = computed(() => {
  const exact = xlsxSheetNames.value.indexOf(`page${currentPage.value}`)
  if (exact >= 0) return exact
  return xlsxPages.value.length === 1 ? 0 : Math.min(
    currentPage.value - 1, Math.max(0, xlsxPages.value.length - 1))
})
const currentSheetName = computed(() =>
  xlsxSheetNames.value[currentSheetIndex.value] ?? null
)
const xlsxRows = computed(() =>
  xlsxPages.value[currentSheetIndex.value] ?? xlsxPages.value[0] ?? []
)

// ── Image / zoom refs ────────────────────────────────────────────────────────
const pageImg    = ref(null)
const viewport   = ref(null)
const imgNatW    = ref(0)
const imgNatH    = ref(0)
const imgZoom    = ref(1)
const panX       = ref(0)
const panY       = ref(0)
const pageRotation = ref(0)

// Sync Excel scroll (both axes) on pan; skip the default (0,0) position on initial load.
watch([panX, panY], ([x, y]) => {
  if (x === 0 && y === 0) return
  syncExcelScroll()
})

const MAX_ZOOM   = 8
const STEP       = 1.5

// Page-image drag state
let dragActive  = false
let dragMoved   = false
let dragOriginX = 0
let dragOriginY = 0
let panOriginX  = 0
let panOriginY  = 0

// ── Modal image zoom/pan ─────────────────────────────────────────────────────
const modalZoom = ref(1)
const modalPanX = ref(0)
const modalPanY = ref(0)

// Modal drag state
let mDragActive  = false
let mDragMoved   = false
let mDragOriginX = 0
let mDragOriginY = 0
let mPanOriginX  = 0
let mPanOriginY  = 0

// ── Derived ──────────────────────────────────────────────────────────────────
const totalPages = computed(() => manifest.value?.pages?.length ?? 0)
const jobName    = computed(() =>
  loadError.value ? 'Review' :
  manifest.value?.pages?.length ? `Review: Page ${currentPage.value}` : 'Loading…'
)
const currentPageUrl     = computed(() => pageUrl(jobId, `page_${currentPage.value}.png`))
const currentPageBlobUrl = ref(null)
const modalCropBlobUrl   = ref(null)

watch(currentPageUrl, async (url) => {
  currentPageBlobUrl.value = null
  currentPageBlobUrl.value = await fetchAuthedUrl(url)
}, { immediate: true })

watch(() => modal.value?.cropUrl, async (url) => {
  modalCropBlobUrl.value = null
  if (!url) return
  modalCropBlobUrl.value = await fetchAuthedUrl(url)
})
const currentCrops   = computed(() => {
  const pages = manifest.value?.pages ?? []
  return pages[currentPage.value - 1]?.crops ?? []
})
const allAttention = computed(() => reviewManifest.value?.views?.transcription_attention ?? [])
const allEcology = computed(() => reviewManifest.value?.views?.ecology_anomalies ?? [])
const currentAttention = computed(() =>
  allAttention.value.filter(item => Number(item.page) === currentPage.value)
)
const currentEcology = computed(() =>
  allEcology.value.filter(item => Number(item.location?.page ?? item.page) === currentPage.value)
)
const currentEcologyWithBoxes = computed(() =>
  currentEcology.value.filter(item => Array.isArray(item.bbox) && item.bbox.length === 4)
)
const reviewChoices = computed(() => [
  { id: 'all', label: 'All cells', count: reviewManifest.value?.summary?.target_cells_including_blanks ?? xlsxRows.value.length },
  { id: 'attention', label: 'Transcription', count: allAttention.value.length },
  { id: 'ecology', label: 'Ecology', count: allEcology.value.length },
])
const panelCountLabel = computed(() => {
  if (reviewMode.value === 'attention') return `${currentAttention.value.length} item${currentAttention.value.length === 1 ? '' : 's'}`
  if (reviewMode.value === 'ecology') return `${currentEcology.value.length} item${currentEcology.value.length === 1 ? '' : 's'}`
  return `${xlsxRows.value.length} rows`
})
const reviewCellsByCoordinate = computed(() => {
  const result = new Map()
  const attentionIds = new Set(allAttention.value.map(item => item.cell_id))
  for (const cell of reviewManifest.value?.cells ?? []) {
    if (attentionIds.has(cell.id) && cell.xlsx_row != null && cell.xlsx_column != null) {
      result.set(`${cell.xlsx_sheet}:${cell.xlsx_row}:${cell.xlsx_column}`, cell)
    }
  }
  return result
})
const reviewCellsById = computed(() =>
  new Map((reviewManifest.value?.cells ?? []).map(cell => [cell.id, cell]))
)
const ecologyCellsByCoordinate = computed(() => {
  const result = new Map()
  for (const item of allEcology.value) {
    if (item.xlsx_row != null && item.xlsx_column != null) {
      const unambiguousLegacySheet = xlsxSheetNames.value.length === 1
        ? xlsxSheetNames.value[0]
        : null
      const pageNumber = item.location?.page ?? item.page
      const pageSheet = xlsxSheetNames.value.includes(`page${pageNumber}`)
        ? `page${pageNumber}`
        : null
      const sheet = item.xlsx_sheet ?? pageSheet ?? unambiguousLegacySheet
      if (sheet) result.set(`${sheet}:${item.xlsx_row}:${item.xlsx_column}`, item)
    }
  }
  return result
})
const correctionCount = computed(() => Object.keys(corrections.value).length)
const modalHasCorrections = computed(() =>
  modal.value?.rows?.some(row => row.cells.some((_c, ci) => isCellCorrected(row.rowNum, ci))) ?? false
)

// Image fills viewport naturally; zoom scales from centre
const imgSizeStyle = computed(() => ({
  width:  imgNatW.value ? `${imgNatW.value}px` : 'auto',
  height: imgNatH.value ? `${imgNatH.value}px` : 'auto',
  maxWidth: 'none',
}))

const canvasStyle = computed(() => {
  const z = imgZoom.value
  const cur = dragActive
    ? (dragMoved ? 'grabbing' : 'grab')
    : (z > 1 ? 'grab' : 'default')
  return {
    transform:  `scale(${z}) translate(${panX.value}px, ${panY.value}px) rotate(${pageRotation.value}deg)`,
    transformOrigin: 'center center',
    cursor: cur,
    willChange: 'transform',
  }
})

const modalCanvasStyle = computed(() => {
  const z = mDragActive
    ? (mDragMoved ? 'grabbing' : 'grab')
    : (modalZoom.value > 1 ? 'grab' : 'default')
  return {
    transform: `scale(${modalZoom.value}) translate(${modalPanX.value}px, ${modalPanY.value}px)`,
    transformOrigin: 'center center',
    cursor: z,
    willChange: 'transform',
    display: 'inline-block',
  }
})

// ── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    const detail = await fetchJobDetail(jobId)
    manifest.value = detail.manifest
    xlsxPages.value = detail.xlsxPages?.length ? detail.xlsxPages : [detail.xlsxRows]
    xlsxSheetNames.value = detail.xlsxSheetNames?.length
      ? detail.xlsxSheetNames
      : xlsxPages.value.map((_page, index) => `page${index + 1}`)
    reviewManifest.value = detail.reviewManifest
  } catch (e) {
    console.error('Failed to load job detail', e)
    loadError.value = e.message ?? String(e)
  } finally {
    loading.value = false
  }
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})

async function retryLoad() {
  loadError.value = null
  loading.value   = true
  try {
    const detail = await fetchJobDetail(jobId)
    manifest.value = detail.manifest
    xlsxPages.value = detail.xlsxPages?.length ? detail.xlsxPages : [detail.xlsxRows]
    xlsxSheetNames.value = detail.xlsxSheetNames?.length
      ? detail.xlsxSheetNames
      : xlsxPages.value.map((_page, index) => `page${index + 1}`)
    reviewManifest.value = detail.reviewManifest
  } catch (e) {
    loadError.value = e.message ?? String(e)
  } finally {
    loading.value = false
  }
}

function onKey(e) {
  if (e.key === 'Escape') closeModal()
  if (modal.value) return
  if (e.key === '+' || e.key === '=') stepZoom(1)
  if (e.key === '-') stepZoom(-1)
  if (e.key === '0') resetZoom()
}

// ── Image load ───────────────────────────────────────────────────────────────
function onImageLoad(e) {
  imgNatW.value = e.target.naturalWidth
  imgNatH.value = e.target.naturalHeight
  // Fit image to viewport on first load / page change
  nextTick(fitToViewport)
}

function fitToViewport() {
  if (!viewport.value || !imgNatW.value) return
  const vw = viewport.value.clientWidth  - 48
  const vh = viewport.value.clientHeight - 48
  const sideways = Math.abs(pageRotation.value) % 180 === 90
  const displayW = sideways ? imgNatH.value : imgNatW.value
  const displayH = sideways ? imgNatW.value : imgNatH.value
  const scale = Math.min(1, vw / displayW, vh / displayH)
  imgZoom.value = Math.max(0.1, scale)
  panX.value = 0
  panY.value = 0
}

function rotatePage(delta) {
  pageRotation.value = (pageRotation.value + delta + 360) % 360
  nextTick(fitToViewport)
}

// ── Zoom controls ────────────────────────────────────────────────────────────
function stepZoom(dir) {
  const next = dir > 0
    ? Math.min(MAX_ZOOM, imgZoom.value * STEP)
    : Math.max(0.1,      imgZoom.value / STEP)
  imgZoom.value = next
  if (next <= 1) { panX.value = 0; panY.value = 0 }
}

function resetZoom() {
  fitToViewport()
}

function onWheel(e) {
  const delta = e.deltaY < 0 ? STEP : 1 / STEP
  const next  = Math.min(MAX_ZOOM, Math.max(0.1, imgZoom.value * delta))
  imgZoom.value = next
  if (next <= 0.15) { panX.value = 0; panY.value = 0 }
}

// ── Pan / drag ───────────────────────────────────────────────────────────────
function onMouseDown(e) {
  if (e.button !== 0) return
  e.preventDefault()
  hoveredCrop.value = null  // switch from hover-sync to pan-sync for the duration of the drag
  dragActive  = true
  dragMoved   = false
  dragOriginX = e.clientX
  dragOriginY = e.clientY
  panOriginX  = panX.value
  panOriginY  = panY.value
  const up = () => { dragActive = false; window.removeEventListener('mouseup', up) }
  window.addEventListener('mouseup', up)
}

function onMouseMove(e) {
  if (!dragActive) return
  const dx = e.clientX - dragOriginX
  const dy = e.clientY - dragOriginY
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragMoved = true
  // translate is in element space (pre-scale), so divide by zoom
  panX.value = panOriginX + dx / imgZoom.value
  panY.value = panOriginY + dy / imgZoom.value
}

// ── Click routing ────────────────────────────────────────────────────────────
// Called by the img element click — only fires when not dragging
function onImgClick(e) {
  if (dragMoved) { dragMoved = false; return }
  resetModalZoom()
  const rect  = pageImg.value.getBoundingClientRect()
  const visualX = (e.clientX - rect.left) / rect.width
  const visualY = (e.clientY - rect.top)  / rect.height
  const rotation = pageRotation.value
  const [fracX, fracY] = rotation === 90 ? [visualY, 1 - visualX]
    : rotation === 180 ? [1 - visualX, 1 - visualY]
      : rotation === 270 ? [1 - visualY, visualX]
        : [visualX, visualY]
  const rows  = estimateRows(fracY, xlsxRows.value, 4)
  modal.value = { type: 'free', fracX, fracY, note: null, rows }
  nextTick(() => drawZoom(fracX, fracY))
}

function onCropClick(crop) {
  if (dragMoved) { dragMoved = false; return }
  resetModalZoom()
  const rows = rowsForRange(crop.rows, xlsxRows.value)
  modal.value = {
    type:     'crop',
    cropUrl:  cropUrl(jobId, crop.file),
    rowRange: crop.rows,
    note:     crop.note,
    rows,
  }
}

// ── Canvas zoom-in for free click ────────────────────────────────────────────
function drawZoom(fracX, fracY) {
  if (!zoomCanvas.value || !pageImg.value) return
  const src = pageImg.value
  const W = src.naturalWidth; const H = src.naturalHeight
  const winW = W * 0.30;      const winH = H * 0.30
  const sx = Math.max(0, fracX * W - winW / 2)
  const sy = Math.max(0, fracY * H - winH / 2)
  const sw = Math.min(winW, W - sx); const sh = Math.min(winH, H - sy)
  const outW = 480; const outH = Math.round(outW * (sh / sw))
  const c = zoomCanvas.value
  c.width = outW; c.height = outH
  const ctx = c.getContext('2d')
  ctx.drawImage(src, sx, sy, sw, sh, 0, 0, outW, outH)
  const cx = outW / 2; const cy = outH / 2
  ctx.strokeStyle = 'rgba(0,109,53,0.8)'; ctx.lineWidth = 1.5
  ctx.beginPath(); ctx.moveTo(cx - 14, cy); ctx.lineTo(cx + 14, cy); ctx.stroke()
  ctx.beginPath(); ctx.moveTo(cx, cy - 14); ctx.lineTo(cx, cy + 14); ctx.stroke()
}

// ── Bbox styles ──────────────────────────────────────────────────────────────
function cropStyle(crop) {
  const [x0, y0, x1, y1] = crop.bbox
  // 2px inset so the border-2 never bleeds outside the image bounds
  return {
    left:   `calc(${x0 * 100}% + 2px)`,
    top:    `calc(${y0 * 100}% + 2px)`,
    width:  `calc(${(x1 - x0) * 100}% - 4px)`,
    height: `calc(${(y1 - y0) * 100}% - 4px)`,
  }
}

function attentionStyle(item) {
  if (!Array.isArray(item.bbox) || item.bbox.length !== 4) return { display: 'none' }
  const [x0, y0, x1, y1] = item.bbox
  return {
    left: `${x0 * 100}%`,
    top: `${y0 * 100}%`,
    width: `${Math.max(0.006, x1 - x0) * 100}%`,
    height: `${Math.max(0.006, y1 - y0) * 100}%`,
  }
}

function otherAlternatives(item) {
  const primary = String(item.presented_value ?? '').trim().toLocaleLowerCase()
  return (item.alternatives ?? []).filter(value =>
    String(value ?? '').trim().toLocaleLowerCase() !== primary
  )
}

function onAttentionClick(item) {
  if (!item.bbox) return
  resetModalZoom()
  const cell = reviewCellsById.value.get(item.cell_id)
  const [, y0, , y1] = item.bbox
  const rows = cell?.xlsx_row != null
    ? xlsxRows.value.filter(row => row.rowNum === cell.xlsx_row)
    : estimateRows((y0 + y1) / 2, xlsxRows.value, 2)
  const [x0, , x1] = item.bbox
  modal.value = {
    type: 'attention',
    note: `${item.reason}; literal ${item.presented_value ?? 'blank'}`,
    rows,
  }
  nextTick(() => drawZoom((x0 + x1) / 2, (y0 + y1) / 2))
}

function goToFinding(item) {
  const page = Number(item.location?.page ?? item.page)
  if (page >= 1 && page <= totalPages.value && page !== currentPage.value) goPage(page)
  reviewMode.value = 'ecology'
}

// ── Corrections ──────────────────────────────────────────────────────────────
function cellKey(r, c)   { return `${currentPage.value}:${r}:${c}` }
function isCellCorrected(r, c) { return cellKey(r, c) in corrections.value }

function getCellValue(rowNum, ci, cell) {
  return corrections.value[cellKey(rowNum, ci)]?.corrected ?? cell.value
}

function cellBgStyle(rowNum, ci, cell) {
  if (isCellCorrected(rowNum, ci)) return { backgroundColor: 'rgba(255,183,125,0.25)' }
  if (reviewCellsByCoordinate.value.has(`${currentSheetName.value}:${rowNum}:${ci + 1}`)) {
    return { backgroundColor: 'rgba(186,26,26,0.14)', boxShadow: 'inset 0 0 0 1px rgba(186,26,26,0.35)' }
  }
  if (ecologyCellsByCoordinate.value.has(`${currentSheetName.value}:${rowNum}:${ci + 1}`)) {
    return { backgroundColor: 'rgba(251,146,60,0.18)', boxShadow: 'inset 0 0 0 1px rgba(234,88,12,0.35)' }
  }
  if (cell.color) {
    const r = parseInt(cell.color.slice(1, 3), 16)
    const g = parseInt(cell.color.slice(3, 5), 16)
    const b = parseInt(cell.color.slice(5, 7), 16)
    return { backgroundColor: `rgba(${r},${g},${b},0.35)` }
  }
  return {}
}

function hasCropCorrections(crop) {
  return rowsForRange(crop.rows, xlsxRows.value)
    .some(row => row.cells.some((_c, ci) => isCellCorrected(row.rowNum, ci)))
}

function onCellEdit(rowNum, ci, newVal, origVal) {
  const k = cellKey(rowNum, ci)
  if (newVal === String(origVal)) {
    const c = { ...corrections.value }; delete c[k]; corrections.value = c
  } else {
    corrections.value = { ...corrections.value, [k]: { original: origVal, corrected: newVal } }
  }
}

function revertModalCorrections() {
  if (!modal.value?.rows) return
  const c = { ...corrections.value }
  for (const row of modal.value.rows)
    for (let ci = 0; ci < row.cells.length; ci++) delete c[cellKey(row.rowNum, ci)]
  corrections.value = c
}

// ── Modal zoom/pan ────────────────────────────────────────────────────────────
function stepModalZoom(dir) {
  const next = dir > 0
    ? Math.min(10, modalZoom.value * STEP)
    : Math.max(0.2, modalZoom.value / STEP)
  modalZoom.value = next
  if (next <= 1) { modalPanX.value = 0; modalPanY.value = 0 }
}

function resetModalZoom() {
  modalZoom.value = 1; modalPanX.value = 0; modalPanY.value = 0
}

function onModalWheel(e) {
  const delta = e.deltaY < 0 ? STEP : 1 / STEP
  const next  = Math.min(10, Math.max(0.2, modalZoom.value * delta))
  modalZoom.value = next
  if (next <= 0.25) { modalPanX.value = 0; modalPanY.value = 0 }
}

function onModalMouseDown(e) {
  if (e.button !== 0) return
  e.preventDefault()
  mDragActive = true; mDragMoved = false
  mDragOriginX = e.clientX; mDragOriginY = e.clientY
  mPanOriginX  = modalPanX.value; mPanOriginY = modalPanY.value
  const up = () => { mDragActive = false; window.removeEventListener('mouseup', up) }
  window.addEventListener('mouseup', up)
}

function onModalMouseMove(e) {
  if (!mDragActive) return
  const dx = e.clientX - mDragOriginX
  const dy = e.clientY - mDragOriginY
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) mDragMoved = true
  modalPanX.value = mPanOriginX + dx / modalZoom.value
  modalPanY.value = mPanOriginY + dy / modalZoom.value
}

// ── Page nav / modal ─────────────────────────────────────────────────────────
function closeModal() { modal.value = null; resetModalZoom() }

function goPage(n) {
  if (n < 1 || n > totalPages.value) return
  currentPage.value = n
  imgZoom.value = 1; panX.value = 0; panY.value = 0
  pageRotation.value = 0
  closeModal()
  nextTick(scrollSharedWorkbookToPage)
}

async function submitReview() {
  const count = correctionCount.value
  const values = Object.fromEntries(Object.entries(corrections.value)
    .map(([key, change]) => [key, String(change.corrected ?? '')]))
  try {
    await submitReviewApi(jobId, values)
    alert(count > 0 ? `Review submitted with ${count} correction(s).` : 'Review marked complete.')
  } catch (error) {
    alert(`Review could not be submitted: ${error.message}`)
  }
}
</script>
