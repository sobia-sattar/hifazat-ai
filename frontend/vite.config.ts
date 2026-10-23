import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "VITE_");
  // In dev, proxy /api to local backend. In prod build, VITE_API_URL is baked in via api.ts.
  const apiTarget = env.VITE_API_URL || env.VITE_API_TARGET || "http://127.0.0.1:8011";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
