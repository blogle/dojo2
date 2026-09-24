import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/ComboboxField.fixtures";
import ComboboxField from "../../src/dojo/components/forms/ComboboxField.vue";

describe("ComboboxField", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, { props: scenario.props });
      cy.get('[data-cy="combobox-field-trigger"]')
        .should("be.visible")
        .and("contain.text", "Groceries");
    });
  });

  it("shows a dropdown affordance while closed", () => {
    mount(ComboboxField, {
      props: {
        label: "Account",
        placeholder: "Select account...",
        options: [{ value: "checking", label: "Checking" }],
      },
    });
    cy.get('[data-cy="combobox-field-trigger"]')
      .should("contain.text", "Select account...")
      .find(".combobox-field__chevron")
      .should("be.visible");
    cy.get('[data-cy="combobox-field-search"]').should("not.exist");
  });

  it("filters immediately and selects an option with keyboard navigation", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(ComboboxField, {
      props: {
        label: "Category",
        modelValue: "",
        "onUpdate:modelValue": onUpdate,
        options: [
          { value: "groceries", label: "Groceries" },
          { value: "rent", label: "Rent" },
          { value: "disabled", label: "Disabled", disabled: true },
        ],
      },
    });

    cy.get('[data-cy="combobox-field-trigger"]').click();
    cy.get('[data-cy="combobox-field-search"]')
      .type("gro")
      .should("be.visible");
    cy.get('[role="option"]')
      .should("have.length", 1)
      .and("contain", "Groceries");
    cy.get("@onUpdate").should("not.have.been.called");
    cy.get('[data-cy="combobox-field-search"]').type("{downarrow}{enter}");
    cy.get("@onUpdate").should("have.been.calledWith", "groceries");
    cy.get('[data-cy="combobox-field-trigger"]')
      .should("contain.text", "Groceries")
      .and("have.focus");
  });

  it("never emits arbitrary values for constrained choices", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(ComboboxField, {
      props: {
        label: "Category",
        modelValue: "",
        placeholder: "Select category...",
        "onUpdate:modelValue": onUpdate,
        options: [{ value: "groceries", label: "Groceries" }],
      },
    });
    cy.get('[data-cy="combobox-field-trigger"]').click();
    cy.get('[data-cy="combobox-field-search"]').type("made up value");
    cy.get("@onUpdate").should("not.have.been.called");
    cy.get('[data-cy="combobox-field-search"]').type("{esc}");
    cy.get('[data-cy="combobox-field-trigger"]').should(
      "contain.text",
      "Select category...",
    );
  });

  it("keeps custom free-form text available when enabled", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(ComboboxField, {
      props: {
        label: "Memo",
        modelValue: "",
        allowCustom: true,
        "onUpdate:modelValue": onUpdate,
        options: [{ value: "prior memo", label: "Prior memo" }],
      },
    });
    cy.get('[data-cy="combobox-field-trigger"]').click();
    cy.get('[data-cy="combobox-field-search"]').type("Brand new memo");
    cy.get("@onUpdate").should("have.been.calledWith", "Brand new memo");
    cy.get('[data-cy="combobox-field-search"]').should(
      "have.value",
      "Brand new memo",
    );
  });

  it("exposes a disabled input when disabled", () => {
    mount(ComboboxField, {
      props: { label: "Account", disabled: true, options: [] },
    });
    cy.get('[data-cy="combobox-field-trigger"]').should("be.disabled");
  });
});
