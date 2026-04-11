import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import tailwindcss from "@tailwindcss/vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    host: true,
    hmr: {
      clientPort: process.env.VITE_HMR_PORT ? parseInt(process.env.VITE_HMR_PORT) : 3000,
    },
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8020",
        changeOrigin: true,
        rewrite: (path) => {
          // Keep /api for modern routers that already include it server-side.
          const preserveApiPrefix = ["/api/compendium", "/api/characters", "/api/dev"];
          if (preserveApiPrefix.some((prefix) => path.startsWith(prefix))) {
            return path;
          }
          return path.replace(/^\/api/, "");
        },
      },
      "/ws": {
        target: process.env.VITE_BACKEND_URL?.replace("http", "ws") || "ws://localhost:8020",
        ws: true,
        rewrite: (path) => path.replace(/^\/ws/, ""),
      },
    },
  },
});
