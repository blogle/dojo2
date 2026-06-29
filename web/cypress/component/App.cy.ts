import { mount } from "cypress/vue";

import App from "../../src/dojo/App.vue";

describe("App", () => {
  it("renders the frontend reset placeholder", () => {
    mount(App);

    cy.contains("UI rebuild pending");
    cy.contains("SPEC.md");
  });
});
