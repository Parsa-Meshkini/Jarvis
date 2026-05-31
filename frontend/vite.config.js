import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/command': 'http://localhost:8000',
      '/tasks':   'http://localhost:8000',
      '/memory':  'http://localhost:8000',
      '/voice':   'http://localhost:8000',
      '/health':  'http://localhost:8000',
    }
  }
})
