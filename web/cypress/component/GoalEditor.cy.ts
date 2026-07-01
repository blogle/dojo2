import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/budget/GoalEditor.fixtures";
import GoalEditor from "../../src/dojo/components/budget/GoalEditor.vue";

describe("GoalEditor", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=goal-editor-root]").should("be.visible");
    });
  });

  it("emits goalType when radio is selected", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(GoalEditor, {
      props: {
        goalType: null,
        goalAmountMinor: null,
        goalFrequency: null,
        goalDueDate: null,
        monthlyFundingMinor: 0,
        "onUpdate:goalType": onUpdate,
      },
    });
    cy.contains("Recurring goal").click();
    cy.get("@onUpdate").should("have.been.calledWith", "RECURRING");
  });

  it("shows recurring fields when recurring goal is selected", () => {
    mount(GoalEditor, {
      props: {
        goalType: "RECURRING",
        goalAmountMinor: 15000,
        goalFrequency: "MONTHLY",
        goalDueDate: "2026-07-01",
        monthlyFundingMinor: 15000,
      },
    });
    cy.contains("Amount per occurrence").should("be.visible");
    cy.contains("Frequency").should("be.visible");
    cy.contains("Next due date").should("be.visible");
    cy.contains("Monthly funding").should("be.visible");
  });

  it("shows one-time fields when one-time goal is selected", () => {
    mount(GoalEditor, {
      props: {
        goalType: "ONE_TIME",
        goalAmountMinor: 50000,
        goalFrequency: null,
        goalDueDate: "2026-12-01",
        monthlyFundingMinor: 10000,
      },
    });
    cy.contains("Goal amount").should("be.visible");
    cy.contains("Goal date").should("be.visible");
  });

  it("shows discretionary field when discretionary goal is selected", () => {
    mount(GoalEditor, {
      props: {
        goalType: "DISCRETIONARY",
        goalAmountMinor: 20000,
        goalFrequency: null,
        goalDueDate: null,
        monthlyFundingMinor: 20000,
      },
    });
    cy.contains("Monthly goal").should("be.visible");
  });
});
