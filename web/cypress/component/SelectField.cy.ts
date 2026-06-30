import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/SelectField.fixtures";
import SelectField from "../../src/dojo/components/forms/SelectField.vue";

describe("SelectField", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=select-field-root]").should("be.visible");
    });
  });

  it("displays the label", () => {
    mount(SelectField, {
      props: {
        label: "Category",
        options: [{ value: "a", label: "Option A" }],
      },
    });
    cy.get("[data-cy=select-field-root]").should("contain.text", "Category");
  });

  it("displays helper text", () => {
    mount(SelectField, {
      props: {
        helper: "Choose one",
        options: [{ value: "a", label: "Option A" }],
      },
    });
    cy.get("[data-cy=select-field-root]").should(
      "contain.text",
      "Choose one",
    );
  });

  it("displays error text", () => {
    mount(SelectField, {
      props: {
        error: "Required",
        options: [{ value: "a", label: "Option A" }],
      },
    });
    cy.get("[data-cy=select-field-root]").should("contain.text", "Required");
  });

  it("disables the select when disabled prop is true", () => {
    mount(SelectField, {
      props: {
        disabled: true,
        options: [{ value: "a", label: "Option A" }],
      },
    });
    cy.get("[data-cy=select-field-root] select").should("be.disabled");
  });

  it("emits update:modelValue on change", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(SelectField, {
      props: {
        modelValue: "a",
        "onUpdate:modelValue": onUpdate,
        options: [
          { value: "a", label: "Option A" },
          { value: "b", label: "Option B" },
        ],
      },
    });
    cy.get("[data-cy=select-field-root] select").select("b");
    cy.get("@onUpdate").should("have.been.calledWith", "b");
  });

  it("renders all options", () => {
    mount(SelectField, {
      props: {
        options: [
          { value: "a", label: "Alpha" },
          { value: "b", label: "Beta" },
          { value: "c", label: "Gamma" },
        ],
      },
    });
    cy.get("[data-cy=select-field-root] option").should("have.length", 3);
    cy.get("[data-cy=select-field-root]").should("contain.text", "Alpha");
    cy.get("[data-cy=select-field-root]").should("contain.text", "Beta");
    cy.get("[data-cy=select-field-root]").should("contain.text", "Gamma");
  });
});
