import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  base: '/',                 // OK para prod servido por Flask
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      // envía cualquier llamada a /api desde Vite (5173) al backend Flask (5000)
      '/api': 'http://localhost:5000',
    },
  },
});
