<template>
  <div
    class="min-h-screen flex flex-col font-body"
    style="background-color:#eef2f7; background-image: linear-gradient(rgba(100,120,160,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(100,120,160,0.12) 1px, transparent 1px); background-size: 80px 80px;"
  >
    <!-- Top bar -->
    <header class="flex items-center px-6 py-4">
      <div class="flex items-center gap-3">
        <img :src="'/logo.png'" class="w-8 h-8 shrink-0 border-[3px] border-black rounded-sm" alt="Formidable" />
        <span class="font-headline font-black text-lg leading-none tracking-tighter text-[#111]">Formidable</span>
      </div>
    </header>

    <!-- Card -->
    <div class="flex-1 flex items-center justify-center px-4">
      <div class="bg-white w-full max-w-md px-12 py-12">
        <h2 class="font-headline font-black text-3xl text-[#111] mb-8">Formidable</h2>

        <!-- ── Step 1: Sign in ── -->
        <form v-if="!needsNewPassword" class="flex flex-col gap-6" autocomplete="off" @submit.prevent="handleLogin">
          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] uppercase tracking-widest font-bold text-[#666]">Email</label>
            <input
              v-model="username"
              type="email"
              autocomplete="off"
              placeholder="identity@ecology.data"
              required
              class="border-0 border-b border-[#ccc] pb-2 bg-transparent text-sm text-[#111] placeholder:text-[#bbb] focus:outline-none focus:border-[#111] transition-colors"
            />
          </div>

          <div class="flex flex-col gap-1.5">
            <div class="flex justify-between items-center">
              <label class="text-[10px] uppercase tracking-widest font-bold text-[#666]">Password</label>
              <span class="text-[10px] uppercase tracking-widest text-[#999] select-none">Forgot password?</span>
            </div>
            <div class="relative">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="off"
                required
                class="w-full border-0 border-b border-[#ccc] pb-2 pr-8 bg-transparent text-sm text-[#111] focus:outline-none focus:border-[#111] transition-colors"
              />
              <button
                type="button"
                class="absolute right-0 bottom-1.5 text-[#999] hover:text-[#111] transition-colors"
                @click="showPassword = !showPassword"
              >
                <span class="material-symbols-outlined text-base leading-none">
                  {{ showPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <p v-if="authError" class="text-red-600 text-xs -mt-2">{{ authError }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="mt-2 w-full py-3.5 bg-[#111] text-white font-black text-xs tracking-widest uppercase disabled:opacity-50 transition-opacity"
          >
            {{ loading ? 'Signing in…' : 'Sign In' }}
          </button>
        </form>

        <!-- ── Step 2: Set new password (first login) ── -->
        <form v-else class="flex flex-col gap-6" autocomplete="off" @submit.prevent="handleNewPassword">
          <p class="text-sm text-[#444] -mt-2 mb-2">
            This is your first login. Please set a new password to continue.
          </p>

          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] uppercase tracking-widest font-bold text-[#666]">New password</label>
            <div class="relative">
              <input
                v-model="newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                autocomplete="off"
                required
                class="w-full border-0 border-b border-[#ccc] pb-2 pr-8 bg-transparent text-sm text-[#111] focus:outline-none focus:border-[#111] transition-colors"
              />
              <button
                type="button"
                class="absolute right-0 bottom-1.5 text-[#999] hover:text-[#111] transition-colors"
                @click="showNewPassword = !showNewPassword"
              >
                <span class="material-symbols-outlined text-base leading-none">
                  {{ showNewPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="text-[10px] uppercase tracking-widest font-bold text-[#666]">Confirm new password</label>
            <div class="relative">
              <input
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                autocomplete="off"
                required
                class="w-full border-0 border-b border-[#ccc] pb-2 pr-8 bg-transparent text-sm text-[#111] focus:outline-none focus:border-[#111] transition-colors"
              />
              <button
                type="button"
                class="absolute right-0 bottom-1.5 text-[#999] hover:text-[#111] transition-colors"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <span class="material-symbols-outlined text-base leading-none">
                  {{ showConfirmPassword ? 'visibility_off' : 'visibility' }}
                </span>
              </button>
            </div>
          </div>

          <p v-if="authError" class="text-red-600 text-xs -mt-2">{{ authError }}</p>

          <button
            type="submit"
            :disabled="loading"
            class="mt-2 w-full py-3.5 bg-[#111] text-white font-black text-xs tracking-widest uppercase disabled:opacity-50 transition-opacity"
          >
            {{ loading ? 'Saving…' : 'Set Password' }}
          </button>
        </form>

        <p v-if="!needsNewPassword" class="mt-8 text-center text-xs text-[#888]">
          Don't have an account?
          <span class="font-bold text-[#111] ml-1 select-none">Sign Up</span>
        </p>
      </div>
    </div>

    <!-- Footer -->
    <footer class="flex items-center gap-8 px-6 py-4">
      <span class="text-[10px] uppercase tracking-widest text-[#888] select-none">Privacy Policy</span>
      <span class="text-[10px] uppercase tracking-widest text-[#888] select-none">Terms of Service</span>
      <span class="text-[10px] uppercase tracking-widest text-[#888] select-none">Support</span>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

const router = useRouter()
const { login, authError } = useCognitoAuth()

const username           = ref('')
const password           = ref('')
const newPassword        = ref('')
const confirmPassword    = ref('')
const loading            = ref(false)
const needsNewPassword   = ref(false)
const showPassword       = ref(false)
const showNewPassword    = ref(false)
const showConfirmPassword = ref(false)

let _pendingUser = null

async function handleLogin() {
  loading.value = true
  authError.value = null
  try {
    await login(username.value, password.value, {
      onNewPasswordRequired(cognitoUser) {
        _pendingUser = cognitoUser
        needsNewPassword.value = true
      },
    })
    router.push({ name: 'dashboard' })
  } catch (e) {
    if (e.message !== 'newPasswordRequired') {
      // authError already set by composable
    }
  } finally {
    loading.value = false
  }
}

async function handleNewPassword() {
  if (newPassword.value !== confirmPassword.value) {
    authError.value = 'Passwords do not match.'
    return
  }
  loading.value = true
  authError.value = null
  try {
    await completeNewPassword(_pendingUser, newPassword.value)
    router.push({ name: 'dashboard' })
  } catch (err) {
    authError.value = err.message || 'Failed to set password.'
  } finally {
    loading.value = false
  }
}

function completeNewPassword(cognitoUser, pwd) {
  return new Promise((resolve, reject) => {
    cognitoUser.completeNewPasswordChallenge(pwd, {}, {
      onSuccess(session) {
        const { idToken } = useCognitoAuth()
        idToken.value = session.getIdToken().getJwtToken()
        resolve()
      },
      onFailure(err) {
        reject(err)
      },
    })
  })
}
</script>
