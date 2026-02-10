import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  // Load Vite env variables from .env files (build-time).
  const env = loadEnv(mode, process.cwd(), 'VITE_')

  return {
    // For path-based deployments (e.g. https://tangyunxuan.com/id-dss/),
    // set in .env.production: VITE_PUBLIC_BASE_PATH=/id-dss/
    base: env.VITE_PUBLIC_BASE_PATH || '/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})

