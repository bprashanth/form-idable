import { createRouter, createWebHistory } from 'vue-router'
import { useFormStore } from '@/composables/useFormStore.js'
import { usePdfStore } from '@/composables/usePdfStore.js'
import { useCognitoAuth } from '@/composables/useCognitoAuth.js'

import CaptureView from '@/views/CaptureView.vue'
import CropView from '@/views/CropView.vue'
import ProcessingView from '@/views/ProcessingView.vue'
import ResultView from '@/views/ResultView.vue'
import LoginView from '@/views/LoginView.vue'
import PDFUploadView from '@/views/PDFUploadView.vue'
import PDFReviewView from '@/views/PDFReviewView.vue'

const routes = [
  { path: '/login', name: 'login', component: LoginView },
  { path: '/', name: 'capture', component: CaptureView },
  { path: '/crop', name: 'crop', component: CropView },
  { path: '/processing', name: 'processing', component: ProcessingView },
  { path: '/result', name: 'result', component: ResultView },
  { path: '/pdf', name: 'pdf-upload', component: PDFUploadView },
  { path: '/pdf/review/:pageIndex', name: 'pdf-review', component: PDFReviewView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  // Auth guard — skip for login page
  if (to.name !== 'login') {
    const { isAuthenticated, refreshSession } = useCognitoAuth()
    if (!isAuthenticated.value) {
      await refreshSession()
      if (!isAuthenticated.value) {
        return { name: 'login' }
      }
    }
  }

  // Form flow guards
  const { capturedImage, croppedImage, xlsxBytes } = useFormStore()

  if (to.name === 'crop' && !capturedImage.value) {
    return { name: 'capture' }
  }
  if (to.name === 'processing' && !croppedImage.value) {
    return { name: 'capture' }
  }
  if (to.name === 'result' && !xlsxBytes.value) {
    return { name: 'capture' }
  }

  // PDF flow guards
  if (to.name === 'pdf-review') {
    const { pages } = usePdfStore()
    const index = parseInt(to.params.pageIndex, 10)
    if (!pages.value.length || Number.isNaN(index) || !pages.value[index]) {
      return { name: 'pdf-upload' }
    }
  }
})

export default router
