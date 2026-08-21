import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    // Ensure assets are referenced with absolute paths — required for Render
    // static site serving from the root of the dist folder.
    outDir: 'dist',
    assetsDir: 'assets',
    // Generate sourcemaps in production so errors are traceable on Render logs.
    sourcemap: false,
  },
})
