<template>
  <div class="flex flex-col items-center justify-center gap-6 h-full p-6">
    <h2 class="text-xl font-semibold">Sign In</h2>

    <form class="flex flex-col gap-4 w-full max-w-xs" @submit.prevent="handleLogin">
      <input
        v-model="username"
        type="email"
        placeholder="Email"
        required
        class="px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        required
        class="px-4 py-3 rounded-lg bg-gray-800 border border-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
      />

      <button
        type="submit"
        :disabled="loading"
        class="px-6 py-3 rounded-lg bg-blue-600 text-white font-medium active:bg-blue-700 transition-colors disabled:opacity-50"
      >
        {{ loading ? 'Signing in...' : 'Sign In' }}
      </button>
    </form>

    <p v-if="authError" class="text-red-400 text-sm text-center max-w-xs">
      {{ authError }}
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

const router = useRouter()
const { login, authError } = useCognitoAuth()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  try {
    await login(username.value, password.value)
    router.push({ name: 'capture' })
  } catch {
    // authError is set by the composable
  } finally {
    loading.value = false
  }
}
</script>
