import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/InstitutionCombobox.fixtures";
import InstitutionCombobox from "../../src/dojo/components/forms/InstitutionCombobox.vue";

describe("InstitutionCombobox", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, { props: scenario.props });
      cy.get("[data-cy=institution-combobox-root]").should("be.visible");
    });
  });

  it("offers suggestions while accepting custom text", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(InstitutionCombobox, {
      props: {
        modelValue: "",
        options: ["Chase", "Fidelity"],
        "onUpdate:modelValue": onUpdate,
      },
    });

    cy.get("datalist option").should("have.length", 2);
    cy.get("input").type("Local Credit Union");
    cy.get("@onUpdate").should("have.been.called");
  });
});
