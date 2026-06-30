import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/CurrencyField.fixtures";
import CurrencyField from "../../src/dojo/components/forms/CurrencyField.vue";

describe("CurrencyField", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=text-field-root]").should("be.visible");
      cy.get("[data-cy=text-field-root] .field__prefix").should(
        "contain.text",
        "$",
      );
    });
  });

  it("displays the label", () => {
    mount(CurrencyField, { props: { label: "Amount" } });
    cy.get("[data-cy=text-field-root]").should("contain.text", "Amount");
  });

  it("displays helper text", () => {
    mount(CurrencyField, {
      props: { helper: "Enter a positive value" },
    });
    cy.get("[data-cy=text-field-root]").should(
      "contain.text",
      "Enter a positive value",
    );
  });

  it("disables the input when disabled prop is true", () => {
    mount(CurrencyField, { props: { disabled: true } });
    cy.get("[data-cy=text-field-root] input").should("be.disabled");
  });

  it("emits update:modelValue on input", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(CurrencyField, {
      props: { modelValue: "", "onUpdate:modelValue": onUpdate },
    });
    cy.get("[data-cy=text-field-root] input").type("100");
    cy.get("@onUpdate").should("have.been.called");
  });

  it("uses decimal inputmode", () => {
    mount(CurrencyField, {});
    cy.get("[data-cy=text-field-root] input").should(
      "have.attr",
      "inputmode",
      "decimal",
    );
  });
});
