import { mount } from "cypress/vue";
import { createRouter, createMemoryHistory } from "vue-router";

import App from "../../src/dojo/App.vue";

describe("App", () => {
  it("renders without error", () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/dev/test",
          component: {
            template: '<div data-cy="app-test-route">test route</div>',
          },
        },
      ],
    });

    router.push("/dev/test");
    router.isReady().then(() => {
      mount(App, {
        global: {
          plugins: [router],
        },
      });

      cy.get("[data-cy=app-test-route]").should("contain.text", "test route");
    });
  });
});
