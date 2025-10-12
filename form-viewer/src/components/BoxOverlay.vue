<template>
  <div
    class="absolute border rounded pointer-events-auto"
    :class="[confidenceClass, selected && 'outline outline-2 outline-blue-400']"
    :style="{
      left: `${bbox.Left * 100}%`,
      top: `${bbox.Top * 100}%`,
      width: `${bbox.Width * 100}%`,
      height: `${bbox.Height * 100}%`,
    }"
    @click.stop="emit('click')"
    :title="`Confidence: ${confidence.toFixed(1)}%`"
  ></div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  bbox: Object,
  confidence: Number,
  text: String,
  selected: Boolean,
})

const emit = defineEmits(['click'])

const confidenceClass = computed(() => {
  if (props.confidence < 70) return 'border-red-400 shadow-[0_0_3px_rgba(255,0,0,0.3)]'
  if (props.confidence < 85) return 'border-orange-400 shadow-[0_0_3px_rgba(255,165,0,0.3)]'
  return 'border-green-400 shadow-[0_0_3px_rgba(0,255,0,0.3)]'
})
</script>

<style scoped>
div {
  background: transparent;
  backdrop-filter: blur(0.5px);
}
</style>
