import { createRouter, createWebHistory } from 'vue-router'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import JobReviewView from '@/views/JobReviewView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { newLayout: true } },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { newLayout: true } },
  { path: '/review/:jobId', name: 'job-review', component: JobReviewView, meta: { newLayout: true } },
  { path: '/', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.name !== 'login') {
    const { isAuthenticated, refreshSession } = useCognitoAuth()
    if (!isAuthenticated.value) {
      await refreshSession()
      if (!isAuthenticated.value) {
        return { name: 'login' }
      }
    }
  }
})

export default router
