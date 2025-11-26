import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@rpg/types': path.resolve(__dirname, '../../packages/types'),
      '@rpg/ui': path.resolve(__dirname, '../../packages/ui'),
    },
  },
  server: {
    port: 5176,
    host: true,
  },
});

