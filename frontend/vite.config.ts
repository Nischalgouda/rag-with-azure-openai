import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // In development the browser talks to /api/*, and Vite forwards it to the FastAPI backend.
    // Same-origin requests mean no CORS configuration is needed locally.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    // Never inline assets as data: URIs. The production Content-Security-Policy forbids them, and tiny
    // font subsets would otherwise be inlined and blocked (a console error in production).
    assetsInlineLimit: 0,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});
