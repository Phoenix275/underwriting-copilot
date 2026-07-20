import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteSingleFile } from 'vite-plugin-singlefile'

// One HTML file out. The same artifact is served three ways — GitHub Pages,
// a Streamlit components.html iframe, and a local file:// open — so nothing
// may depend on a base URL or a runtime fetch. Fonts, data and assets are all
// inlined; assetsInlineLimit is raised past the largest inlined asset.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  base: './',
  build: {
    assetsInlineLimit: 100 * 1024 * 1024,
    cssCodeSplit: false,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 4000,
  },
})
