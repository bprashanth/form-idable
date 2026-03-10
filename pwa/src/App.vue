<template>
  <div class="flex flex-col h-dvh bg-gray-900 text-gray-100">
    <AppHeader />
    <router-view class="flex-1 overflow-hidden" />
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
</script>
