import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/data/PeriodSelector.fixtures";
import PeriodSelector from "../../src/dojo/components/data/PeriodSelector.vue";

describe("PeriodSelector", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=period-selector-root]").should("be.visible");
    });
  });

  it("emits update:modelValue when a preset is clicked", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(PeriodSelector, {
      props: {
        modelValue: "1m",
        "onUpdate:modelValue": onUpdate,
      },
    });
    cy.get("[data-cy=period-selector-root]").contains("3M").click();
    cy.get("@onUpdate").should("have.been.calledWith", "3m");
  });

  it("highlights the active preset", () => {
    mount(PeriodSelector, {
      props: { modelValue: "3m" },
    });
    cy.get("[data-cy=period-selector-root]")
      .contains("3M")
      .should("have.class", "period-selector__preset--active");
    cy.get("[data-cy=period-selector-root]")
      .contains("1M")
      .should("not.have.class", "period-selector__preset--active");
  });

  it("renders all preset buttons", () => {
    mount(PeriodSelector, {});
    cy.get("[data-cy=period-selector-root] .period-selector__preset").should(
      "have.length",
      6,
    );
  });

  it("shows comparison checkbox when comparison prop is true", () => {
    mount(PeriodSelector, {
      props: { comparison: true },
    });
    cy.get("[data-cy=period-selector-root]").should(
      "contain.text",
      "Compare",
    );
  });

  it("emits update:comparison when checkbox is toggled", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(PeriodSelector, {
      props: { comparison: true, "onUpdate:comparison": onUpdate },
    });
    cy.get("[data-cy=period-selector-root] input[type='checkbox']").click({
      force: true,
    });
    cy.get("@onUpdate").should("have.been.called");
  });
});
