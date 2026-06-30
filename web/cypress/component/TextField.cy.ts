import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/TextField.fixtures";
import TextField from "../../src/dojo/components/forms/TextField.vue";

describe("TextField", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=text-field-root]").should("be.visible");
    });
  });

  it("displays the label", () => {
    mount(TextField, { props: { label: "Email" } });
    cy.get("[data-cy=text-field-root]").should("contain.text", "Email");
  });

  it("displays helper text", () => {
    mount(TextField, { props: { helper: "Required field" } });
    cy.get("[data-cy=text-field-root]").should("contain.text", "Required field");
  });

  it("displays error text", () => {
    mount(TextField, { props: { error: "Invalid input" } });
    cy.get("[data-cy=text-field-root]").should("contain.text", "Invalid input");
  });

  it("disables the input when disabled prop is true", () => {
    mount(TextField, { props: { disabled: true } });
    cy.get("[data-cy=text-field-root] input").should("be.disabled");
  });

  it("emits update:modelValue on input", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(TextField, {
      props: { modelValue: "", "onUpdate:modelValue": onUpdate },
    });
    cy.get("[data-cy=text-field-root] input").type("hello");
    cy.get("@onUpdate").should("have.been.called");
  });

  it("renders the prefix slot", () => {
    mount(TextField, {
      slots: { prefix: "$" },
    });
    cy.get("[data-cy=text-field-root] .field__prefix").should(
      "contain.text",
      "$",
    );
  });

  it("prioritizes error over helper", () => {
    mount(TextField, {
      props: { error: "Error shown", helper: "Helper hidden" },
    });
    cy.get("[data-cy=text-field-root]").should(
      "contain.text",
      "Error shown",
    );
    cy.get("[data-cy=text-field-root]").should(
      "not.contain.text",
      "Helper hidden",
    );
  });
});
