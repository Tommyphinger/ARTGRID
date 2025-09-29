import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path'; // Add this import for path resolution

export default defineConfig({
  plugins: [react()],
  base: './',      // Allows the bundle to work from any path
  build: {
    outDir: 'dist'
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'), // Maps @/ to the src directory
    },
  },
});