import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/tables/HierarchicalCategoryTable.fixtures";
import HierarchicalCategoryTable from "../../src/dojo/components/tables/HierarchicalCategoryTable.vue";

describe("HierarchicalCategoryTable", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=hierarchical-category-table-root]").should("be.visible");
    });
  });

  it("renders column headers", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        columns: [
          { key: "name", label: "Category" },
          { key: "available", label: "Available", align: "end" },
        ],
        rows: [],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "Category",
    );
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "Available",
    );
  });

  it("renders row labels", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        columns: [{ key: "name", label: "Category" }],
        rows: [
          { key: "a", label: "Housing", cells: {} },
          { key: "b", label: "Transportation", cells: {} },
        ],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "Housing",
    );
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "Transportation",
    );
  });

  it("renders cell values", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        columns: [
          { key: "name", label: "Category" },
          { key: "available", label: "Available", align: "end" },
        ],
        rows: [
          { key: "a", label: "Groceries", cells: { available: "$245.00" } },
        ],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "$245.00",
    );
  });

  it("emits toggle when expand button is clicked", () => {
    const onToggle = cy.spy().as("onToggle");
    mount(HierarchicalCategoryTable, {
      props: {
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            expanded: false,
            cells: {},
            children: [{ key: "c1", label: "Rent", cells: {} }],
          },
        ],
        onToggle,
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("button")
      .first()
      .click();
    cy.get("@onToggle").should("have.been.calledWith", "g1");
  });

  it("renders state badges when provided", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "a",
            label: "System category",
            cells: {},
            states: [{ label: "System", variant: "info" }],
          },
        ],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "System",
    );
  });
});
