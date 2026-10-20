import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig} from 'vite';

export default defineConfig(() => {
  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      // Same-origin API proxy for `npm run dev` (mirrors the production nginx).
      proxy: {
        '/api/auth': { target: 'https://localhost:4288', secure: false, changeOrigin: true, rewrite: (p: string) => p.replace(/^\/api\/auth/, '') },
        '/api/core': { target: 'https://localhost:4289', secure: false, changeOrigin: true, rewrite: (p: string) => p.replace(/^\/api\/core/, '') },
      },
      // HMR is disabled in AI Studio via DISABLE_HMR env var.
      // Do not modifyâfile watching is disabled to prevent flickering during agent edits.
      hmr: process.env.DISABLE_HMR !== 'true',
      // Disable file watching when DISABLE_HMR is true to save CPU during agent edits.
      watch: process.env.DISABLE_HMR === 'true' ? null : {},
    },
  };
});
