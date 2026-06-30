import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/actions/Button.fixtures";

describe("Button", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=button-root]").should("be.visible");
    });
  });

  it("renders slot content", () => {
    mount(fixtures.component, {
      props: { variant: "primary" },
      slots: { default: "Save" },
    });
    cy.get("[data-cy=button-root]").should("contain.text", "Save");
  });

  it("disables the button when disabled prop is true", () => {
    mount(fixtures.component, {
      props: { disabled: true },
      slots: { default: "Save" },
    });
    cy.get("[data-cy=button-root]").should("be.disabled");
  });

  it("disables the button when loading", () => {
    mount(fixtures.component, {
      props: { loading: true },
      slots: { default: "Save" },
    });
    cy.get("[data-cy=button-root]").should("be.disabled");
  });
});
