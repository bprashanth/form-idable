import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'
import { useCognitoAuth } from './composables/useCognitoAuth.js'
import './main.css'

const { init } = useCognitoAuth()
init().then(() => {
  createApp(App).use(router).mount('#app')
})
