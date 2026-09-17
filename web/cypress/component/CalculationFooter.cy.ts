import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/data/CalculationFooter.fixtures";

describe("CalculationFooter", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });

      cy.get("[data-cy=calculation-footer]")
        .should("be.visible")
        .and("have.css", "position", "sticky");
    });
  });

  it("keeps the scope label separate from the right-aligned value", () => {
    mount(fixtures.component, {
      props: fixtures.scenarios[0]?.props,
    });

    cy.get("[data-cy=calculation-footer-label]").should(
      "contain.text",
      "Available to budget",
    );
    cy.get("[data-cy=calculation-footer-value]")
      .should("contain.text", "$685.73")
      .should("have.css", "text-align", "right");
  });
});
