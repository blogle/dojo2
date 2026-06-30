import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/DatePicker.fixtures";
import DatePicker from "../../src/dojo/components/forms/DatePicker.vue";

describe("DatePicker", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=date-picker-root]").should("be.visible");
    });
  });

  it("emits update:modelValue when a date is entered", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(DatePicker, {
      props: {
        "onUpdate:modelValue": onUpdate,
      },
    });
    cy.get("[data-cy=date-picker-root] input").type("2026-01-15");
    cy.get("@onUpdate").should("have.been.called");
  });

  it("displays the calendar icon", () => {
    mount(DatePicker, {
      props: { label: "Pick a date" },
    });
    cy.get("[data-cy=date-picker-root]").should("contain.text", "📅");
  });
});
