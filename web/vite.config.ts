import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api/cloud': { target: 'http://localhost:8000', changeOrigin: true },
      '/api/assistant': { target: 'http://localhost:8003', changeOrigin: true },
      '/api/opportunity': { target: 'http://localhost:8002', changeOrigin: true },
      '/api/sales-assistant': { target: 'http://localhost:8004', changeOrigin: true },
      '/api/sales-coach': { target: 'http://localhost:8001', changeOrigin: true },
      '/api/intel': { target: 'http://localhost:8006', changeOrigin: true },
    },
  },
  build: {
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react-dom') || id.includes('node_modules/react-router-dom') || id.includes('node_modules/react')) return 'vendor-react'
          if (id.includes('node_modules/recharts')) return 'vendor-recharts'
          if (id.includes('node_modules/@tanstack/react-table')) return 'vendor-table'
        },
      },
    },
  },
  test: { globals: true, environment: 'jsdom' },
})
