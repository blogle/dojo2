import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/display/StateBadge.fixtures";
import StateBadge from "../../src/dojo/components/display/StateBadge.vue";

describe("StateBadge", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=state-badge-root]").should("be.visible");
    });
  });

  it("renders slot content", () => {
    mount(StateBadge, {
      props: { variant: "positive" },
      slots: { default: "Active" },
    });
    cy.get("[data-cy=state-badge-root]").should("contain.text", "Active");
  });

  it("applies the correct variant class", () => {
    mount(StateBadge, {
      props: { variant: "error" },
      slots: { default: "Error" },
    });
    cy.get("[data-cy=state-badge-root]").should(
      "have.class",
      "state-badge--error",
    );
  });

  it("applies the sm size class by default", () => {
    mount(StateBadge, { slots: { default: "Info" } });
    cy.get("[data-cy=state-badge-root]").should(
      "have.class",
      "state-badge--sm",
    );
  });

  it("applies the md size class when specified", () => {
    mount(StateBadge, { props: { size: "md" }, slots: { default: "Info" } });
    cy.get("[data-cy=state-badge-root]").should(
      "have.class",
      "state-badge--md",
    );
  });
});
