import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  define: {
    global: 'globalThis',
  },
  envPrefix: ['VITE_', 'VUE_APP_'],
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true,
    proxy: {
      '/api': {
        target: process.env.API_TARGET || 'http://localhost:8070',
        changeOrigin: true,
      },
    },
  },
})
