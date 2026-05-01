<template>
  <!-- max-w-full: image shows at natural size, scales down if wider than panel, never zooms -->
  <div class="relative inline-block max-w-full">
    <img
      v-if="imageUrl"
      :src="imageUrl"
      class="block max-w-full rounded shadow-lg"
      alt="Original form"
    />
    <!-- Primary: the "this row" highlight — red -->
    <div
      v-for="(b, i) in primaryMerged"
      :key="'p' + i"
      class="absolute pointer-events-none"
      :style="boxStyle(b, 'rgba(239,68,68,0.9)', 'rgba(239,68,68,0.13)')"
    />
    <!-- Secondary: other rows where this value appears — amber -->
    <div
      v-for="(b, i) in secondaryMerged"
      :key="'s' + i"
      class="absolute pointer-events-none"
      :style="boxStyle(b, 'rgba(251,146,60,0.8)', 'rgba(251,146,60,0.10)')"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  imageBlob:        { type: Object, default: null },
  // [{serial: number, bbox: {left,top,width,height}}]
  primaryEntries:   { type: Array,  default: () => [] }, // "this row" — red
  secondaryEntries: { type: Array,  default: () => [] }, // other matching rows — amber
})

// ── Object URL lifecycle ──────────────────────────────────────────────────────

const imageUrl = ref(null)

watch(
  () => props.imageBlob,
  (blob) => {
    if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
    imageUrl.value = blob ? URL.createObjectURL(blob) : null
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
})

// ── Helpers ───────────────────────────────────────────────────────────────────

const BUFFER = 0.008  // fractional padding on each side of a final merged box

function boxStyle(b, borderColor, bgColor) {
  return {
    left:       b.left   * 100 + '%',
    top:        b.top    * 100 + '%',
    width:      b.width  * 100 + '%',
    height:     b.height * 100 + '%',
    border:     `2px solid ${borderColor}`,
    background: bgColor,
    borderRadius: '2px',
  }
}

/**
 * Given [{serial, bbox}] entries, group into runs of consecutive serials,
 * compute the union bbox for each run, then add a buffer around each union.
 *
 * Only consecutive serials are merged — non-adjacent rows stay separate so a
 * species appearing at rows 1 and 8 shows two distinct highlights, not one
 * large rectangle that covers unrelated rows in between.
 */
function processEntries(entries) {
  if (!entries.length) return []

  const sorted = [...entries].sort((a, b) => a.serial - b.serial)

  // Group into consecutive runs
  const runs = [[sorted[0]]]
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i].serial === sorted[i - 1].serial + 1) {
      runs[runs.length - 1].push(sorted[i])
    } else {
      runs.push([sorted[i]])
    }
  }

  // Union bbox per run, then buffer
  return runs.map(run => {
    const bboxes = run.map(e => e.bbox)
    const left   = Math.min(...bboxes.map(b => b.left))
    const top    = Math.min(...bboxes.map(b => b.top))
    const right  = Math.max(...bboxes.map(b => b.left + b.width))
    const bottom = Math.max(...bboxes.map(b => b.top  + b.height))
    return {
      left:   Math.max(0, left   - BUFFER),
      top:    Math.max(0, top    - BUFFER),
      width:  Math.min(1, right  + BUFFER) - Math.max(0, left - BUFFER),
      height: Math.min(1, bottom + BUFFER) - Math.max(0, top  - BUFFER),
    }
  })
}

const primaryMerged   = computed(() => processEntries(props.primaryEntries))
const secondaryMerged = computed(() => processEntries(props.secondaryEntries))
</script>
