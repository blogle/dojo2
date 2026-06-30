import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/overlays/LargeDetailModal.fixtures";
import LargeDetailModal from "../../src/dojo/components/overlays/LargeDetailModal.vue";

describe("LargeDetailModal", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=large-detail-modal-root]").should("be.visible");
    });
  });

  it("renders the title", () => {
    mount(LargeDetailModal, {
      props: { visible: true, contained: true, title: "Category detail" },
    });
    cy.get("[data-cy=large-detail-modal-root]").should(
      "contain.text",
      "Category detail",
    );
  });

  it("renders the subtitle when provided", () => {
    mount(LargeDetailModal, {
      props: {
        visible: true,
        contained: true,
        title: "Groceries",
        subtitle: "Available: $245.00",
      },
    });
    cy.get("[data-cy=large-detail-modal-root]").should(
      "contain.text",
      "Available: $245.00",
    );
  });

  it("renders the close button", () => {
    mount(LargeDetailModal, {
      props: { visible: true, contained: true },
    });
    cy.get("[data-cy=large-detail-modal-root]")
      .contains("Close")
      .should("be.visible");
  });

  it("emits close when the close button is clicked", () => {
    const onClose = cy.spy().as("onClose");
    mount(LargeDetailModal, {
      props: { visible: true, contained: true, onClose },
    });
    cy.get("[data-cy=large-detail-modal-root]").contains("Close").click();
    cy.get("@onClose").should("have.been.called");
  });

  it("renders body slot content", () => {
    mount(LargeDetailModal, {
      props: { visible: true, contained: true },
      slots: { default: '<div data-cy="test-body">Body content</div>' },
    });
    cy.get("[data-cy=test-body]").should("be.visible");
  });

  it("renders the tabs slot", () => {
    mount(LargeDetailModal, {
      props: { visible: true, contained: true },
      slots: { tabs: '<div data-cy="test-tabs">Tab bar</div>' },
    });
    cy.get("[data-cy=test-tabs]").should("be.visible");
  });

  it("renders the footer slot", () => {
    mount(LargeDetailModal, {
      props: { visible: true, contained: true },
      slots: { footer: '<div data-cy="test-footer">Footer</div>' },
    });
    cy.get("[data-cy=test-footer]").should("be.visible");
  });
});
