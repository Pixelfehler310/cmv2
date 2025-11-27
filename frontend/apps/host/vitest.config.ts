import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@rpg/types': path.resolve(__dirname, '../../packages/types'),
      '@rpg/ui': path.resolve(__dirname, '../../packages/ui'),
      '@': path.resolve(__dirname, './src'),
    },
  },
});



