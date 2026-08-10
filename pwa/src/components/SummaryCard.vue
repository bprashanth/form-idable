<template>
  <div class="border border-outline-variant/25 bg-surface-container-lowest p-4">
    <p class="text-[9px] uppercase tracking-widest font-black text-on-surface-variant">{{ label }}</p>
    <p class="font-headline font-black text-3xl mt-2" :class="tone === 'red' ? 'text-error' : tone === 'orange' ? 'text-orange-600' : 'text-primary'">{{ value }}</p>
  </div>
</template>
<script setup>
defineProps({ label: String, value: [String, Number], tone: { type: String, default: '' } })
</script>
