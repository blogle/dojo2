import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/RadioGroup.fixtures";
import RadioGroup from "../../src/dojo/components/forms/RadioGroup.vue";

describe("RadioGroup", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=radio-group-root]").should("be.visible");
    });
  });

  it("emits update:modelValue when an option is clicked", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(RadioGroup, {
      props: {
        modelValue: "a",
        options: [
          { value: "a", label: "A" },
          { value: "b", label: "B" },
        ],
        "onUpdate:modelValue": onUpdate,
      },
    });
    cy.contains("B").click();
    cy.get("@onUpdate").should("have.been.calledWith", "b");
  });

  it("disables buttons when disabled prop is true", () => {
    mount(RadioGroup, {
      props: {
        modelValue: "a",
        options: [
          { value: "a", label: "A" },
          { value: "b", label: "B" },
        ],
        disabled: true,
      },
    });
    cy.get("[data-cy=radio-group-root] button").should("be.disabled");
  });
});
