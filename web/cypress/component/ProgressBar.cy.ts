import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/display/ProgressBar.fixtures";
import ProgressBar from "../../src/dojo/components/display/ProgressBar.vue";

describe("ProgressBar", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=progress-bar-root]").should("be.visible");
    });
  });

  it("applies the correct variant class", () => {
    mount(ProgressBar, {
      props: { value: 50, variant: "positive" },
    });
    cy.get("[data-cy=progress-bar-root] .progress-bar__fill").should(
      "have.class",
      "progress-bar__fill--positive",
    );
  });

  it("clamps value to 0-100", () => {
    mount(ProgressBar, {
      props: { value: 150, showValue: true },
    });
    cy.get("[data-cy=progress-bar-root]").should("contain.text", "100%");
  });

  it("shows value when showValue is true", () => {
    mount(ProgressBar, {
      props: { value: 42, showValue: true },
    });
    cy.get("[data-cy=progress-bar-root]").should("contain.text", "42%");
  });
});
