import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/BinaryToggle.fixtures";
import BinaryToggle from "../../src/dojo/components/forms/BinaryToggle.vue";

describe("BinaryToggle", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, { props: scenario.props });
      cy.get("[data-cy^=binary-toggle-]").should("be.visible");
    });
  });

  it("cycles between status values from one current-state button", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(BinaryToggle, {
      props: {
        label: "Status",
        dataName: "status",
        kind: "status",
        modelValue: "PENDING",
        "onUpdate:modelValue": onUpdate,
        options: [
          { value: "PENDING", label: "Pending" },
          { value: "CLEARED", label: "Cleared" },
        ],
      },
    });

    cy.get("[data-cy=binary-toggle-status]")
      .should("contain.text", "Pending")
      .and("not.contain.text", "Cleared")
      .click();
    cy.get("@onUpdate").should("have.been.calledWith", "CLEARED");
  });

  it("cycles between direction values using the keyboard", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(BinaryToggle, {
      props: {
        label: "Direction",
        dataName: "direction",
        kind: "direction",
        modelValue: "outflow",
        "onUpdate:modelValue": onUpdate,
        options: [
          { value: "outflow", label: "Outflow", icon: "↓" },
          { value: "inflow", label: "Inflow", icon: "↑" },
        ],
      },
    });

    cy.get("[data-cy=binary-toggle-direction]")
      .should("contain.text", "Outflow")
      .and("not.contain.text", "Inflow")
      .focus()
      .type("{enter}");
    cy.get("@onUpdate").should("have.been.calledWith", "inflow");
  });
});
