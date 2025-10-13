<template>
  <div ref="containerRef" class="relative w-full h-full select-none bg-gray-800 overflow-hidden">
    <div
      class="absolute"
      :style="{
        left: box.left + 'px',
        top: box.top + 'px',
        width: box.width + 'px',
        height: box.height + 'px',
      }"
    >
      <img :src="imageUrl" alt="Form" ref="imgRef" class="block w-full h-full" @load="onImgLoad" />

      <!-- Universal Fields -->
      <template v-for="(uf, key) in formData.universal_fields" :key="'uf-' + key">
        <BoxOverlay
          :bbox="uf.system?.bbox || { Left: 0, Top: 0, Width: 0, Height: 0 }"
          :confidence="100"
          :text="key"
          :selected="selectedMode === 'universal'"
          :disabled="!uf.system?.valid"
          colorClass="border-cyan-400"
          @click="selectUniversal()"
        />
      </template>

      <!-- Header overlay (single box) -->
      <BoxOverlay
        v-if="formData.header_map?.system?.bbox"
        :bbox="formData.header_map.system.bbox"
        :confidence="84"
        text="Headers"
        :selected="selectedMode === 'header'"
        colorClass="border-indigo-400"
        @click="selectHeaderMode"
      />

      <!-- Rows -->
      <template v-for="(row, rIndex) in formData.rows" :key="rIndex">
        <template v-for="(cell, cellId) in row.system.cells" :key="cellId">
          <BoxOverlay
            :bbox="cell.bbox"
            :confidence="cell.confidence"
            :text="cell.text"
            :selected="selectedMode === 'row' && selectedGroupId === row.system.group_id"
            @click="selectRow(row)"
          />
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import BoxOverlay from '@/components/BoxOverlay.vue'

const props = defineProps({
  formData: Object,
  imageUrl: String,
  zoom: Number,
})

const emit = defineEmits(['select-row', 'select-header', 'select-universal'])

const containerRef = ref(null)
const imgRef = ref(null)
const natural = reactive({ w: 0, h: 0 })
const container = reactive({ w: 0, h: 0 })

function onImgLoad() {
  natural.w = imgRef.value.naturalWidth
  natural.h = imgRef.value.naturalHeight
  measureContainer()
}

function measureContainer() {
  const rect = containerRef.value.getBoundingClientRect()
  container.w = rect.width
  container.h = rect.height
}

onMounted(() => {
  const ro = new ResizeObserver(measureContainer)
  ro.observe(containerRef.value)
})

const box = computed(() => {
  const scale = Math.min(container.w / natural.w, container.h / natural.h) * (props.zoom || 1)
  const width = natural.w * scale
  const height = natural.h * scale
  const left = (container.w - width) / 2
  const top = (container.h - height) / 2
  return { left, top, width, height }
})

const selectedMode = ref(null)
const selectedGroupId = ref(null)

function selectRow(row) {
  selectedMode.value = 'row'
  selectedGroupId.value = row.system.group_id
  emit('select-row', row)
}
// script additions
function selectHeaderMode() {
  selectedMode.value = 'header'
  emit('select-header')
}

function selectUniversal() {
  selectedMode.value = 'universal'
  emit('select-universal')
}
</script>
