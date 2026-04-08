import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';
import path from 'path';

export default defineConfig({
  plugins: [react(), visualizer({ open: false, filename: 'dist/bundle-stats.html' })],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('/i18n/locales/ar.json')) return 'locale-ar';
          if (id.includes('/i18n/locales/en.json')) return 'locale-en';
          if (id.includes('node_modules/react-dom/')) return 'vendor';
          if (id.includes('node_modules/react/')) return 'vendor';
          if (id.includes('node_modules/react-router')) return 'vendor';
          if (id.includes('node_modules/@tanstack/react-query')) return 'query';
          if (id.includes('node_modules/i18next') || id.includes('node_modules/react-i18next'))
            return 'i18n';
          if (id.includes('node_modules/d3-')) return 'd3-libs';
          if (id.includes('node_modules/recharts/') && id.includes('/cartesian'))
            return 'charts-cartesian';
          if (id.includes('node_modules/recharts/') && id.includes('/polar')) return 'charts-polar';
          if (id.includes('node_modules/recharts')) return 'charts-core';
          if (id.includes('node_modules/zod')) return 'schemas';
        },
      },
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
