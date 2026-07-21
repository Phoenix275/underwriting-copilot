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
  // Escape every non-ASCII character (×, —, ≥, curly quotes …) to a \u sequence
  // in the JS output. The bundle then decodes identically under any charset, so
  // text renders correctly even where the <meta charset> is ignored — notably
  // inside Streamlit's srcdoc iframe, which was showing mojibake (× -> Ã—).
  esbuild: { charset: 'ascii' },
  build: {
    assetsInlineLimit: 100 * 1024 * 1024,
    cssCodeSplit: false,
    reportCompressedSize: false,
    chunkSizeWarningLimit: 4000,
    // apply the same ASCII-only rule to the minified output
    minify: 'esbuild',
  },
})
