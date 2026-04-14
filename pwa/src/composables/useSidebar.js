import { ref } from 'vue'

const sidebarOpen = ref(false)
const sidebarTab  = ref('cheatsheet')

export function useSidebar() {
  function open(tab = 'cheatsheet') {
    sidebarTab.value = tab
    sidebarOpen.value = true
  }
  function close() {
    sidebarOpen.value = false
  }
  return { sidebarOpen, sidebarTab, open, close }
}
