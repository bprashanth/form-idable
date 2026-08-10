import { createRouter, createWebHistory } from 'vue-router'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import JobReviewView from '@/views/JobReviewView.vue'
import JobAnalyticsView from '@/views/JobAnalyticsView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView, meta: { newLayout: true } },
  { path: '/dashboard', name: 'dashboard', component: DashboardView, meta: { newLayout: true } },
  { path: '/review/:jobId', name: 'job-review', component: JobReviewView, meta: { newLayout: true } },
  { path: '/analytics/:jobId', name: 'job-analytics', component: JobAnalyticsView, meta: { newLayout: true } },
  { path: '/', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  // Browser tests run against the local mock API and have no Cognito session.
  // Both conditions are required so a production build cannot enable this.
  const e2eBypass = import.meta.env.DEV && import.meta.env.VITE_E2E_BYPASS_AUTH === 'true'
  if (e2eBypass) return
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
