import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/feedback/PersistentWarningBanner.fixtures";
import PersistentWarningBanner from "../../src/dojo/components/feedback/PersistentWarningBanner.vue";

describe("PersistentWarningBanner", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=persistent-warning-banner-root]").should("be.visible");
    });
  });

  it("renders the title", () => {
    mount(PersistentWarningBanner, {
      props: { title: "Warning title" },
    });
    cy.get("[data-cy=persistent-warning-banner-root]").should(
      "contain.text",
      "Warning title",
    );
  });

  it("renders the description", () => {
    mount(PersistentWarningBanner, {
      props: { description: "Something happened" },
    });
    cy.get("[data-cy=persistent-warning-banner-root]").should(
      "contain.text",
      "Something happened",
    );
  });

  it("renders primary action button", () => {
    mount(PersistentWarningBanner, {
      props: { primaryAction: "Resolve" },
    });
    cy.get("[data-cy=persistent-warning-banner-root]").should(
      "contain.text",
      "Resolve",
    );
  });

  it("emits primary when primary button is clicked", () => {
    const onPrimary = cy.spy().as("onPrimary");
    mount(PersistentWarningBanner, {
      props: { primaryAction: "Resolve", onPrimary },
    });
    cy.get("[data-cy=persistent-warning-banner-root]")
      .contains("Resolve")
      .click();
    cy.get("@onPrimary").should("have.been.called");
  });

  it("emits secondary when secondary button is clicked", () => {
    const onSecondary = cy.spy().as("onSecondary");
    mount(PersistentWarningBanner, {
      props: { secondaryAction: "Details", onSecondary },
    });
    cy.get("[data-cy=persistent-warning-banner-root]")
      .contains("Details")
      .click();
    cy.get("@onSecondary").should("have.been.called");
  });

  it("emits dismiss when dismiss button is clicked", () => {
    const onDismiss = cy.spy().as("onDismiss");
    mount(PersistentWarningBanner, {
      props: { dismissible: true, onDismiss },
    });
    cy.get("[data-cy=persistent-warning-banner-root]")
      .find("[aria-label='Dismiss banner']")
      .click();
    cy.get("@onDismiss").should("have.been.called");
  });

  it("applies the correct severity class", () => {
    mount(PersistentWarningBanner, {
      props: { severity: "error", title: "Error" },
    });
    cy.get("[data-cy=persistent-warning-banner-root]").should(
      "have.class",
      "persistent-warning-banner--error",
    );
  });
});
