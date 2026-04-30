import { defineConfig } from "vite";

export default defineConfig({
  build: {
    lib: {
      entry: "src/evenkeel-boat-card.ts",
      formats: ["es"],
      fileName: () => "evenkeel-boat-card.js",
    },
    rollupOptions: {
      // Lit is bundled, not externalized — HA cards are single-file drops.
      external: [],
    },
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: true,
    target: "es2022",
    minify: "esbuild",
  },
  test: {
    environment: "happy-dom",
    globals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      exclude: ["dist/**", "vite.config.ts", "**/*.test.ts"],
    },
  },
});
