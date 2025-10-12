<template>
  <div
    v-if="shouldShow"
    class="absolute text-[0.55rem] text-gray-200"
    :class="[borderClass, selected && 'outline outline-2 outline-blue-400']"
    :style="{
      left: `${bbox.Left * 100}%`,
      top: `${bbox.Top * 100}%`,
      width: `${bbox.Width * 100}%`,
      height: `${bbox.Height * 100}%`,
    }"
    @click.stop="emit('click')"
  >
    <div class="absolute top-0 right-0 pr-[2px] pt-[1px] text-[0.55rem] opacity-80">
      {{ text }}
    </div>
  </div>
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

const shouldShow = computed(() => props.text && props.confidence < 85)

const borderClass = computed(() => {
  if (props.confidence < 70) return 'border border-red-500'
  if (props.confidence < 85) return 'border border-orange-400'
  return 'border-none'
})
</script>

<style scoped>
div {
  background: transparent;
  backdrop-filter: blur(0.5px);
}
</style>
