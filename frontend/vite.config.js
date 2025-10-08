import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // Proxy API requests to Docker backend services
    // This allows local Vite dev server to reach services running in Docker
    proxy: {
      '/user-service-api': {
        target: 'http://localhost:8004',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/user-service-api/, ''),
      },
      '/question-service-api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/question-service-api/, ''),
      },
      '/matching-service-api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/matching-service-api/, ''),
      },
      '/history-service-api': {
        target: 'http://localhost:8003',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/history-service-api/, ''),
      },
      '/collaboration-service-api': {
        target: 'http://localhost:8005',
        changeOrigin: true,
        // Rewrite to remove the /collaboration-service-api prefix
        rewrite: (path) => path.replace(/^\/collaboration-service-api/, ''),
        ws: true, // Enable WebSocket proxying for Socket.IO
      },
      '/chat-service-api': {
        target: 'http://localhost:8006',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/chat-service-api/, ''),
        ws: true, // Enable WebSocket proxying for Socket.IO
      },
    },
  },
})
