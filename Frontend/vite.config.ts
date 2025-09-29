import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',      // allows the bundle to work from any path
  build: {
    outDir: 'dist'
  }
})