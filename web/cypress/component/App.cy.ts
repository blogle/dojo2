import { mount } from "cypress/vue";
import { createRouter, createMemoryHistory } from "vue-router";

import App from "../../src/dojo/App.vue";

describe("App", () => {
  it("renders without error", () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/",
          component: { template: "<div>test route</div>" },
        },
      ],
    });

    router.isReady().then(() => {
      mount(App, {
        global: {
          plugins: [router],
        },
      });

      cy.get("body").should("exist");
    });
  });
});
