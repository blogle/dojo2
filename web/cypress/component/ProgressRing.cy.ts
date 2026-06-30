import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/display/ProgressRing.fixtures";
import ProgressRing from "../../src/dojo/components/display/ProgressRing.vue";

describe("ProgressRing", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=progress-ring-root]").should("be.visible");
    });
  });

  it("renders SVG with correct structure", () => {
    mount(ProgressRing, {
      props: { value: 65 },
    });
    cy.get("[data-cy=progress-ring-root] svg").should("exist");
    cy.get("[data-cy=progress-ring-root] circle").should("have.length", 2);
  });

  it("applies the correct size", () => {
    mount(ProgressRing, {
      props: { value: 50, size: 120 },
    });
    cy.get("[data-cy=progress-ring-root] svg")
      .should("have.attr", "width", "120")
      .and("have.attr", "height", "120");
  });

  it("applies the correct stroke width", () => {
    mount(ProgressRing, {
      props: { value: 50, strokeWidth: 8 },
    });
    cy.get("[data-cy=progress-ring-root] circle").should(
      "have.attr",
      "stroke-width",
      "8",
    );
  });
});
