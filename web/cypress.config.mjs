import vue from "@vitejs/plugin-vue";
import { defineConfig } from "cypress";

export default defineConfig({
  video: false,
  component: {
    devServer: {
      framework: "vue",
      bundler: "vite",
      viteConfig: {
        plugins: [vue()],
        server: {
          port: 0,
        },
      },
    },
    specPattern: "cypress/component/**/*.cy.ts",
    supportFile: "cypress/support/component.ts",
  },
});
