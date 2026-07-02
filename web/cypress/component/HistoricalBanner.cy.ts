import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/feedback/HistoricalBanner.fixtures";
import HistoricalBanner from "../../src/dojo/components/feedback/HistoricalBanner.vue";

describe("HistoricalBanner", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=historical-banner-root]").should("be.visible");
    });
  });

  it("renders the label", () => {
    mount(HistoricalBanner, {});
    cy.get("[data-cy=historical-banner-root]").should(
      "contain.text",
      "Viewing historical data",
    );
  });

  it("renders the description when provided", () => {
    mount(HistoricalBanner, {
      props: { description: "As of May 15, 2025" },
    });
    cy.get("[data-cy=historical-banner-root]").should(
      "contain.text",
      "As of May 15, 2025",
    );
  });

  it("renders the exit button with custom label", () => {
    mount(HistoricalBanner, {
      props: { exitLabel: "Go to today" },
    });
    cy.get("[data-cy=historical-banner-root]").should(
      "contain.text",
      "Go to today",
    );
  });

  it("emits exit when the exit button is clicked", () => {
    const onExit = cy.spy().as("onExit");
    mount(HistoricalBanner, { props: { onExit } });
    cy.get("[data-cy=historical-banner-root]")
      .contains("Return to current")
      .click();
    cy.get("@onExit").should("have.been.called");
  });
});
