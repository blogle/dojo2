import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/data/StackedEntityCard.fixtures";
import StackedEntityCard from "../../src/dojo/components/data/StackedEntityCard.vue";

describe("StackedEntityCard", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=stacked-entity-card-root]").should("be.visible");
    });
  });

  it("renders name and value", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Test Account",
        primaryValue: "$1,000.00",
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").should(
      "contain.text",
      "Test Account",
    );
    cy.get("[data-cy=stacked-entity-card-root]").should(
      "contain.text",
      "$1,000.00",
    );
  });

  it("emits select event when clickable", () => {
    const onSelect = cy.stub().as("onSelect");
    mount(StackedEntityCard, {
      props: {
        name: "Clickable Account",
        primaryValue: "$500.00",
        clickable: true,
        onSelect,
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").click();
    cy.get("@onSelect").should("have.been.calledOnce");
  });

  it("does not emit select event when not clickable", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Non-clickable Account",
        primaryValue: "$500.00",
        clickable: false,
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").click({ force: true });
  });

  it("applies clickable class when clickable", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Clickable",
        primaryValue: "$100.00",
        clickable: true,
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").should(
      "have.class",
      "stacked-entity-card--clickable",
    );
  });

  it("shows source of truth badge", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Account",
        primaryValue: "$100.00",
        sourceOfTruth: "ledger",
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").should(
      "contain.text",
      "ledger",
    );
  });

  it("shows status badge", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Account",
        primaryValue: "$100.00",
        status: {
          label: "Reconciled",
          variant: "positive",
        },
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").should(
      "contain.text",
      "Reconciled",
    );
  });

  it("shows positive delta", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Account",
        primaryValue: "$100.00",
        delta: 50,
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").should("contain.text", "+50");
  });

  it("shows negative delta", () => {
    mount(StackedEntityCard, {
      props: {
        name: "Account",
        primaryValue: "$100.00",
        delta: -25,
      },
    });
    cy.get("[data-cy=stacked-entity-card-root]").should("contain.text", "-25");
  });
});
