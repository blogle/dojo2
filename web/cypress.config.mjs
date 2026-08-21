import { fileURLToPath, URL } from "node:url";
import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "cypress";

export default defineConfig({
  video: false,
  retries: 0,
  viewportWidth: 1280,
  viewportHeight: 900,
  env: {
    apiBaseUrl: process.env.VITE_API_BASE_URL ?? "http://localhost:8000",
    e2eToken: process.env.DOJO_E2E_TOKEN ?? "",
  },
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL ?? "http://localhost:5173",
    specPattern: "cypress/e2e/**/*.cy.ts",
    supportFile: "cypress/support/e2e.ts",
    setupNodeEvents(on, config) {
      const tests = [];
      const outputDir = process.env.E2E_OUTPUT_DIR;

      on("task", {
        recordE2eTest(metrics) {
          tests.push(metrics);
          return null;
        },
      });

      on("after:spec", (spec, results) => {
        if (!outputDir) return;
        mkdirSync(outputDir, { recursive: true });
        const specTests = tests.filter((test) => test.spec === spec.relative);
        writeFileSync(
          path.join(
            outputDir,
            `${path.basename(spec.relative, ".cy.ts")}.json`,
          ),
          JSON.stringify(
            {
              spec: spec.relative,
              durationMs: results?.stats?.wallClockDuration ?? null,
              tests: specTests,
            },
            null,
            2,
          ),
        );
      });

      on("after:run", (results) => {
        if (!outputDir) return;
        mkdirSync(outputDir, { recursive: true });
        writeFileSync(
          path.join(outputDir, "run.json"),
          JSON.stringify(
            {
              status: results.status,
              totalDurationMs: results.totalDuration,
              totalTests: results.totalTests,
              totalPassed: results.totalPassed,
              totalFailed: results.totalFailed,
              tests,
            },
            null,
            2,
          ),
        );
      });

      return config;
    },
  },
  component: {
    devServer: {
      framework: "vue",
      bundler: "vite",
      viteConfig: {
        plugins: [vue()],
        resolve: {
          alias: {
            "@": fileURLToPath(new URL("./src", import.meta.url)),
          },
        },
        server: {
          port: 0,
        },
      },
    },
    specPattern: "cypress/component/**/*.cy.ts",
    supportFile: "cypress/support/component.ts",
  },
});
