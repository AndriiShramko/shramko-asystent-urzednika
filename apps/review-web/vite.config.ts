import { defineConfig } from 'vitest/config'

// The service serves the built files under /ui/, so every asset address is relative (base './').
// Nothing is loaded from the network at run time: no fonts, no scripts, no analytics.
export default defineConfig({
  base: './',
  build: { outDir: 'dist', sourcemap: false, assetsInlineLimit: 0 },
  test: { environment: 'happy-dom', include: ['tests/**/*.test.ts'] }
})
