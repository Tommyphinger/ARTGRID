import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path'; // For path resolution

export default defineConfig({
  plugins: [react()],
  base: '/', // Use root-relative paths (adjust to '/your-subpath/' if deployed under a subdir)
  build: {
    outDir: 'dist',
    sourcemap: true, // Enable source maps for better error debugging
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'), // Maps @/ to the src directory
    },
  },
});