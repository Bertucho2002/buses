import { defineConfig } from "vite";

// base: la app se sirve desde https://<usuario>.github.io/buses/
export default defineConfig({
  base: process.env.GITHUB_PAGES === "true" ? "/buses/" : "/",
  build: { outDir: "dist" },
});
