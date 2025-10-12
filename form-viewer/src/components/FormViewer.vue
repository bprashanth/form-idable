<template>
  <!-- Full-size viewer pane -->
  <div ref="containerRef" class="relative w-full h-full select-none bg-gray-800 overflow-hidden">
    <!-- The image+overlay box that exactly matches the displayed image rectangle -->
    <div
      class="absolute"
      :style="{
        left: box.left + 'px',
        top: box.top + 'px',
        width: box.width + 'px',
        height: box.height + 'px',
      }"
    >
      <!-- Background image sized to the computed box -->
      <img :src="imageUrl" alt="Form" ref="imgRef" class="block w-full h-full" @load="onImgLoad" />

      <!-- Overlays are children of the same sized box → percentage math stays correct -->
      <template v-for="(row, rIndex) in formData.rows" :key="rIndex">
        <template v-for="(cell, cellId) in row.system.cells" :key="cellId">
          <BoxOverlay
            :bbox="cell.bbox"
            :confidence="cell.confidence"
            :text="cell.text"
            :selected="selectedGroupId === row.system.group_id"
            @click="selectRow(row)"
          />
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import BoxOverlay from '@/components/BoxOverlay.vue'

const props = defineProps({
  formData: { type: Object, required: true },
  imageUrl: { type: String, required: true },
  zoom: { type: Number, default: 1 },
})

const emit = defineEmits(['select-row'])

const containerRef = ref(null)
const imgRef = ref(null)

const natural = reactive({ w: 0, h: 0 })
const container = reactive({ w: 0, h: 0 })
let ro // ResizeObserver

function onImgLoad() {
  if (imgRef.value) {
    // Natural size of the image
    natural.w = imgRef.value.naturalWidth || 0
    natural.h = imgRef.value.naturalHeight || 0
    measureContainer()
  }
}

function measureContainer() {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  container.w = rect.width
  container.h = rect.height
}

onMounted(() => {
  measureContainer()
  ro = new ResizeObserver(measureContainer)
  ro.observe(containerRef.value)
})

onBeforeUnmount(() => {
  ro?.disconnect()
})

const box = computed(() => {
  // When sizes are unknown, return zero box
  if (!natural.w || !natural.h || !container.w || !container.h) {
    return { left: 0, top: 0, width: 0, height: 0 }
  }
  // "Contain" fit within container, then apply zoom around center
  const scale = Math.min(container.w / natural.w, container.h / natural.h) * (props.zoom || 1)
  const width = natural.w * scale
  const height = natural.h * scale
  const left = (container.w - width) / 2
  const top = (container.h - height) / 2
  return { left, top, width, height }
})

const selectedGroupId = ref(null)
function selectRow(row) {
  selectedGroupId.value = row.system.group_id
  emit('select-row', row)
}
</script>
