<template>
  <header class="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-900">
    <h1 class="text-lg font-semibold tracking-tight">scribe</h1>
    <div class="flex items-center gap-3">
      <button
        class="text-gray-500 hover:text-gray-200 transition-colors"
        title="Settings"
        @click="openSidebar('cheatsheet')"
      >⚙</button>
      <button
        v-if="route.name !== 'capture' && route.name !== 'login'"
        class="text-sm text-gray-400 hover:text-gray-200 transition-colors"
        @click="startOver"
      >
        Start Over
      </button>
      <button
        v-if="isAuthenticated"
        class="text-sm text-gray-500 hover:text-gray-200 transition-colors"
        @click="handleLogout"
      >
        Logout
      </button>
    </div>
  </header>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useFormStore } from '@/composables/useFormStore.js'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'
import { useSidebar } from '@/composables/useSidebar.js'

const route = useRoute()
const router = useRouter()
const { reset } = useFormStore()
const { logout, isAuthenticated } = useCognitoAuth()
const { open: openSidebar } = useSidebar()

function startOver() {
  reset()
  router.push({ name: 'capture' })
}

function handleLogout() {
  reset()
  logout()
  router.push({ name: 'login' })
}
</script>
