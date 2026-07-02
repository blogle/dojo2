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

  it("hides children when group is collapsed", () => {
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
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "not.contain.text",
      "Rent",
    );
  });

  it("shows children when group is expanded", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            expanded: true,
            cells: {},
            children: [{ key: "c1", label: "Rent", cells: {} }],
          },
        ],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]").should(
      "contain.text",
      "Rent",
    );
  });

  it("renders chevron SVG that rotates when collapsed", () => {
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
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find(".hierarchical-category-table__chevron")
      .should("have.class", "hierarchical-category-table__chevron--collapsed");
  });

  it("shows drag handles when reorderable", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [{ key: "a", label: "Housing", cells: {} }],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find(".hierarchical-category-table__drag-handle")
      .should("exist");
  });

  it("makes rows draggable when reorderable", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          { key: "a", label: "Housing", cells: {} },
          { key: "b", label: "Transportation", cells: {} },
        ],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[draggable='true']")
      .should("have.length", 2);
  });

  it("does not show drag handles when not reorderable", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: false,
        columns: [{ key: "name", label: "Category" }],
        rows: [{ key: "a", label: "Housing", cells: {} }],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find(".hierarchical-category-table__drag-handle")
      .should("not.exist");
  });

  it("emits reorder when a row is dropped on another", () => {
    const onReorder = cy.spy().as("onReorder");
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          { key: "a", label: "Housing", cells: {} },
          { key: "b", label: "Transportation", cells: {} },
        ],
        onReorder,
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[draggable='true']")
      .first()
      .then(($row) => {
        const dataTransfer = new DataTransfer();

        cy.get("[data-cy=hierarchical-category-table-root]")
          .find("tr[draggable='true']")
          .last()
          .then(($target) => {
            const targetEvent = new DragEvent("dragover", {
              bubbles: true,
              cancelable: true,
              dataTransfer,
              clientY: $target[0].getBoundingClientRect().bottom - 1,
            });
            $target[0].dispatchEvent(targetEvent);

            const dropEvent = new DragEvent("drop", {
              bubbles: true,
              cancelable: true,
              dataTransfer,
            });
            $target[0].dispatchEvent(dropEvent);
          });

        const dragStartEvent = new DragEvent("dragstart", {
          bubbles: true,
          cancelable: true,
          dataTransfer,
        });
        $row[0].dispatchEvent(dragStartEvent);
      });

    cy.get("@onReorder").should("have.been.called");
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

  it("renders row icons when provided", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        columns: [{ key: "name", label: "Category" }],
        rows: [{ key: "a", label: "Housing", icon: "home", cells: {} }],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("[data-cy=icon-glyph-root]")
      .should("exist");
  });

  it("applies cell variant colors", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        columns: [
          { key: "name", label: "Category" },
          { key: "available", label: "Available" },
        ],
        rows: [
          {
            key: "a",
            label: "Dining Out",
            cells: { available: "-$48.00" },
            cellVariants: { available: "error" },
          },
        ],
      },
    });
    cy.get("[data-cy=hierarchical-category-table-root]")
      .find(".hierarchical-category-table__cell--error")
      .should("contain.text", "-$48.00");
  });
});
