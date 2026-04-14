<template>
  <div class="flex flex-col h-dvh bg-gray-900 text-gray-100">
    <AppHeader />
    <router-view class="flex-1 overflow-hidden" />
    <AgentSidebar />
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
import AgentSidebar from '@/components/AgentSidebar.vue'
</script>
