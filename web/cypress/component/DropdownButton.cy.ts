import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/actions/DropdownButton.fixtures";

describe("DropdownButton", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=dropdown-button-root]").should("be.visible");
    });
  });

  it("opens the menu when the toggle is clicked", () => {
    mount(fixtures.component, {
      props: { items: [{ key: "a", label: "Item A" }] },
    });
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .click();
    cy.get("[data-cy=dropdown-button-root]")
      .contains("Item A")
      .should("be.visible");
  });

  it("sets aria-expanded on the toggle", () => {
    mount(fixtures.component, {
      props: { items: [{ key: "a", label: "Item A" }] },
    });
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .should("have.attr", "aria-expanded", "false");
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .click();
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .should("have.attr", "aria-expanded", "true");
  });

  it("emits select when a menu item is clicked", () => {
    const onSelect = cy.spy().as("onSelect");
    mount(fixtures.component, {
      props: {
        items: [{ key: "a", label: "Item A" }],
        onSelect,
      },
    });
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .click();
    cy.get("[data-cy=dropdown-button-root]")
      .contains("Item A")
      .click({ force: true });
    cy.get("@onSelect").should("have.been.calledWith", "a");
  });

  it("closes the menu after selection", () => {
    mount(fixtures.component, {
      props: {
        items: [{ key: "a", label: "Item A" }],
        onSelect: () => {},
      },
    });
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .click();
    cy.get("[data-cy=dropdown-button-root]")
      .contains("Item A")
      .click({ force: true });
    cy.get("[data-cy=dropdown-button-root]")
      .find('[role="menu"]')
      .should("not.exist");
  });

  it("does not emit select for disabled items", () => {
    const onSelect = cy.spy().as("onSelect");
    mount(fixtures.component, {
      props: {
        items: [{ key: "a", label: "Item A", disabled: true }],
        onSelect,
      },
    });
    cy.get("[data-cy=dropdown-button-root]")
      .find('[aria-label="Add options"]')
      .click();
    cy.get("[data-cy=dropdown-button-root]")
      .find('[role="menuitem"]')
      .should("have.attr", "data-disabled");
  });

  it("disables both buttons when disabled prop is true", () => {
    mount(fixtures.component, {
      props: {
        items: [{ key: "a", label: "Item A" }],
        disabled: true,
      },
    });
    cy.get("[data-cy=dropdown-button-root]")
      .find(".dropdown-button__primary")
      .should("be.disabled");
    cy.get("[data-cy=dropdown-button-root]")
      .find(".dropdown-button__toggle")
      .should("be.disabled");
  });
});
