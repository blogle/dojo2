import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/feedback/ReorderModeBanner.fixtures";
import ReorderModeBanner from "../../src/dojo/components/feedback/ReorderModeBanner.vue";

describe("ReorderModeBanner", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=reorder-mode-banner-root]").should("be.visible");
    });
  });

  it("shows pending count when greater than 0", () => {
    mount(ReorderModeBanner, {
      props: { pendingCount: 3 },
    });
    cy.get("[data-cy=reorder-mode-banner-root]").should(
      "contain.text",
      "3 changes pending",
    );
  });

  it("emits cancel when cancel button is clicked", () => {
    const onCancel = cy.spy().as("onCancel");
    mount(ReorderModeBanner, {
      props: { onCancel: onCancel },
    });
    cy.get(
      "[data-cy=reorder-mode-banner-root] .reorder-banner__cancel",
    ).click();
    cy.get("@onCancel").should("have.been.calledOnce");
  });

  it("emits save when save button is clicked", () => {
    const onSave = cy.spy().as("onSave");
    mount(ReorderModeBanner, {
      props: { onSave: onSave },
    });
    cy.get("[data-cy=reorder-mode-banner-root] .reorder-banner__save").click();
    cy.get("@onSave").should("have.been.calledOnce");
  });
});
