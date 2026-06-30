import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/tables/TableShell.fixtures";
import TableShell from "../../src/dojo/components/tables/TableShell.vue";

describe("TableShell", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=table-shell-root]").should("be.visible");
    });
  });

  it("renders column headers from columns prop", () => {
    mount(TableShell, {
      props: {
        columns: [
          { key: "name", label: "Name" },
          { key: "amount", label: "Amount" },
        ],
        rows: [],
      },
    });
    cy.get("[data-cy=table-shell-root] thead").should(
      "contain.text",
      "Name",
    );
    cy.get("[data-cy=table-shell-root] thead").should(
      "contain.text",
      "Amount",
    );
  });

  it("renders rows from rows prop", () => {
    mount(TableShell, {
      props: {
        columns: [{ key: "name", label: "Name" }],
        rows: [{ key: "a", name: "Groceries" }],
      },
    });
    cy.get("[data-cy=table-shell-root] tbody").should(
      "contain.text",
      "Groceries",
    );
  });

  it("shows empty text when rows is empty", () => {
    mount(TableShell, {
      props: {
        columns: [{ key: "name", label: "Name" }],
        rows: [],
        emptyText: "Nothing here",
      },
    });
    cy.get("[data-cy=table-shell-root]").should("contain.text", "Nothing here");
  });

  it("renders row slot for custom cell rendering", () => {
    mount(TableShell, {
      props: {
        columns: [{ key: "name", label: "Name" }],
        rows: [{ key: "a", name: "Test" }],
      },
      slots: {
        row: '<tr><td data-cy="custom-cell">Custom</td></tr>',
      },
    });
    cy.get("[data-cy=custom-cell]").should("contain.text", "Custom");
  });
});
