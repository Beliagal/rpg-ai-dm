import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

// Forzamos un tipado amplio y seguro compatible con el ecosistema de Vitest 3/Vite 8
const vitePlugins = [react()] as unknown[];

export default defineConfig({
  plugins: vitePlugins as never[],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});