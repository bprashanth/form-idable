import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // Load all .env/.env.local variables ('' prefix = no filter).
  // These are build-time proxy targets, not exposed to client code.
  const env = loadEnv(mode, process.cwd(), '')

  return {
    define: {
      global: 'globalThis',
    },
    envPrefix: ['VITE_', 'VUE_APP_'],
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: true,
      proxy: {
        '/api': {
          target: env.API_TARGET || 'http://localhost:8070',
          changeOrigin: true,
        },
        '/agent': {
          target: env.AGENT_TARGET || 'http://localhost:8071',
          changeOrigin: true,
        },
      },
    },
  }
})
