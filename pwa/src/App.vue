<template>
  <template v-if="route.meta?.newLayout">
    <router-view />
  </template>
  <template v-else>
    <div class="flex flex-col h-dvh bg-gray-900 text-gray-100">
      <AppHeader />
      <router-view class="flex-1 overflow-hidden" />
      <AgentSidebar />
    </div>
  </template>
</template>

<script setup>
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import AgentSidebar from '@/components/AgentSidebar.vue'

const route = useRoute()
</script>
