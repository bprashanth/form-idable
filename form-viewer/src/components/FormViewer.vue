<template>
  <div ref="container" class="relative mx-auto select-none" style="max-width: 900px">
    <img :src="imageUrl" alt="Form" class="w-full h-auto block" />

    <!-- Render overlay boxes -->
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
</template>

<script setup>
import { ref } from 'vue'
import BoxOverlay from '@/components/BoxOverlay.vue'

defineProps({
  formData: Object,
  imageUrl: String,
})

const emit = defineEmits(['select-row'])
const selectedGroupId = ref(null)

function selectRow(row) {
  selectedGroupId.value = row.system.group_id
  emit('select-row', row)
}
</script>
