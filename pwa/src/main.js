import { createApp } from 'vue'
import { registerSW } from 'virtual:pwa-register'
import App from './App.vue'
import router from './router.js'
import { useCognitoAuth } from './composables/useCognitoAuth.js'
import './main.css'

registerSW({ immediate: true })

const { init } = useCognitoAuth()
init().then(() => {
  createApp(App).use(router).mount('#app')
})
