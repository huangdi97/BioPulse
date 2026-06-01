import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api/cloud': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api/assistant': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/api/opportunity': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/sales-assistant': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      '/api/sales-coach': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
