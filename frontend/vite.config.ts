import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  // For path-based deployments (e.g. https://tangyunxuan.com/id-dss/),
  // build with: VITE_PUBLIC_BASE_PATH=/id-dss/ npm run build
  base: process.env.VITE_PUBLIC_BASE_PATH || '/',
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
})

