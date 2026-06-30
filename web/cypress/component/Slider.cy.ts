import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/forms/Slider.fixtures";
import Slider from "../../src/dojo/components/forms/Slider.vue";

describe("Slider", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=slider-root]").should("be.visible");
    });
  });

  it("emits update:modelValue when the slider is moved", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(Slider, {
      props: {
        modelValue: 50,
        min: 0,
        max: 100,
        "onUpdate:modelValue": onUpdate,
      },
    });
    cy.get("[data-cy=slider-root] input[type=range]")
      .invoke("val", 75)
      .trigger("input");
    cy.get("@onUpdate").should("have.been.calledWith", 75);
  });

  it("displays min and max labels", () => {
    mount(Slider, {
      props: {
        modelValue: 50,
        minLabel: "Min",
        maxLabel: "Max",
      },
    });
    cy.get("[data-cy=slider-root]").should("contain.text", "Min");
    cy.get("[data-cy=slider-root]").should("contain.text", "Max");
  });
});
