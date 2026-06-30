import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/display/Tooltip.fixtures";
import Tooltip from "../../src/dojo/components/display/Tooltip.vue";

describe("Tooltip", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=tooltip-root]").should("be.visible");
    });
  });

  it("contains the tooltip text", () => {
    mount(Tooltip, {
      props: { text: "Helpful tip", position: "top" },
      slots: { default: '<button type="button">Trigger</button>' },
    });
    cy.get("[data-cy=tooltip-root] .tooltip__content").should(
      "contain.text",
      "Helpful tip",
    );
  });

  it("applies the correct position class", () => {
    mount(Tooltip, {
      props: { text: "Helpful tip", position: "bottom" },
      slots: { default: '<button type="button">Trigger</button>' },
    });
    cy.get("[data-cy=tooltip-root] .tooltip__content").should(
      "have.class",
      "tooltip__content--bottom",
    );
  });
});
