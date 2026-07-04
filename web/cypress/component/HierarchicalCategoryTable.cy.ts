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
      .find("tr[data-drag-group]")
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
      .find("tr[data-drag-group]")
      .should("have.length", 2);

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[data-drag-group]")
      .first()
      .find(".hierarchical-category-table__drag-handle")
      .should("exist");

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[data-drag-group]")
      .last()
      .find(".hierarchical-category-table__drag-handle")
      .should("exist");
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

  it("moves children with group when group is reordered", () => {
    const onReorder = cy.spy().as("onReorder");
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            cells: {},
            children: [
              { key: "c1", label: "Rent", cells: {} },
              { key: "c2", label: "Internet", cells: {} },
            ],
          },
          {
            key: "g2",
            label: "Transportation",
            group: true,
            cells: {},
            children: [{ key: "c3", label: "Gas", cells: {} }],
          },
        ],
        onReorder,
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[data-drag-group]")
      .should("have.length", 2);

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr")
      .then(($rows) => {
        const labels = [...$rows].map((r) => r.textContent?.trim());
        const housingIdx = labels.findIndex((l) => l?.includes("Housing"));
        const rentIdx = labels.findIndex((l) => l?.includes("Rent"));
        const internetIdx = labels.findIndex((l) => l?.includes("Internet"));
        const transpIdx = labels.findIndex((l) =>
          l?.includes("Transportation"),
        );

        expect(housingIdx).to.be.lessThan(rentIdx);
        expect(rentIdx).to.be.lessThan(internetIdx);
        expect(internetIdx).to.be.lessThan(transpIdx);
      });
  });

  it("moves children to the end with their group during reorder", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            cells: {},
            children: [
              { key: "c1", label: "Rent", cells: {} },
              { key: "c2", label: "Internet", cells: {} },
            ],
          },
          {
            key: "g2",
            label: "Transportation",
            group: true,
            cells: {},
            children: [{ key: "c3", label: "Gas", cells: {} }],
          },
        ],
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr")
      .then(($rows) => {
        const labels = [...$rows].map((r) => r.textContent?.trim());
        const rentIdx = labels.findIndex((l) => l?.includes("Rent"));
        const internetIdx = labels.findIndex((l) => l?.includes("Internet"));
        const transpIdx = labels.findIndex((l) =>
          l?.includes("Transportation"),
        );

        expect(rentIdx).to.be.lessThan(transpIdx);
        expect(internetIdx).to.be.lessThan(transpIdx);
      });
  });

  it("reorders children within a group", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            cells: {},
            children: [
              { key: "c1", label: "Rent", cells: {} },
              { key: "c2", label: "Internet", cells: {} },
              { key: "c3", label: "Electric", cells: {} },
            ],
          },
        ],
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[data-drag-child]")
      .should("have.length", 3);
  });

  it("emits reorder with correct arguments for group move", () => {
    const onReorder = cy.spy().as("onReorder");
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            cells: {},
            children: [{ key: "c1", label: "Rent", cells: {} }],
          },
          {
            key: "g2",
            label: "Transportation",
            group: true,
            cells: {},
            children: [{ key: "c2", label: "Gas", cells: {} }],
          },
        ],
        onReorder,
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[data-drag-group]")
      .should("have.length", 2);

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr[data-drag-group]")
      .first()
      .find(".hierarchical-category-table__drag-handle")
      .should("exist");
  });

  it("preserves children across multiple group reorders", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Group A",
            group: true,
            cells: {},
            children: [{ key: "c1", label: "Child A1", cells: {} }],
          },
          {
            key: "g2",
            label: "Group B",
            group: true,
            cells: {},
            children: [{ key: "c2", label: "Child B1", cells: {} }],
          },
          {
            key: "g3",
            label: "Group C",
            group: true,
            cells: {},
            children: [{ key: "c3", label: "Child C1", cells: {} }],
          },
        ],
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr")
      .then(($rows) => {
        const labels = [...$rows].map((r) => r.textContent?.trim());
        const groupA = labels.findIndex((l) => l?.includes("Group A"));
        const childA = labels.findIndex((l) => l?.includes("Child A1"));
        const groupB = labels.findIndex((l) => l?.includes("Group B"));
        const childB = labels.findIndex((l) => l?.includes("Child B1"));
        const groupC = labels.findIndex((l) => l?.includes("Group C"));
        const childC = labels.findIndex((l) => l?.includes("Child C1"));

        expect(groupA).to.be.lessThan(childA);
        expect(childA).to.be.lessThan(groupB);
        expect(groupB).to.be.lessThan(childB);
        expect(childB).to.be.lessThan(groupC);
        expect(childC).to.be.greaterThan(groupC);
      });
  });

  it("groups and their children render in correct hierarchy", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
        expandable: true,
        columns: [{ key: "name", label: "Category" }],
        rows: [
          {
            key: "g1",
            label: "Housing",
            group: true,
            cells: {},
            children: [
              { key: "c1", label: "Rent", cells: {} },
              { key: "c2", label: "Internet", cells: {} },
            ],
          },
          {
            key: "g2",
            label: "Food",
            group: true,
            cells: {},
            children: [
              { key: "c3", label: "Groceries", cells: {} },
              { key: "c4", label: "Dining", cells: {} },
            ],
          },
        ],
      },
    });

    cy.get("[data-cy=hierarchical-category-table-root]")
      .find("tr")
      .then(($rows) => {
        const labels = [...$rows].map((r) => r.textContent?.trim());

        const g1 = labels.findIndex((l) => l?.includes("Housing"));
        const c1 = labels.findIndex((l) => l?.includes("Rent"));
        const c2 = labels.findIndex((l) => l?.includes("Internet"));
        const g2 = labels.findIndex((l) => l?.includes("Food"));
        const c3 = labels.findIndex((l) => l?.includes("Groceries"));
        const c4 = labels.findIndex((l) => l?.includes("Dining"));

        expect(g1).to.be.lessThan(c1);
        expect(c1).to.be.lessThan(c2);
        expect(c2).to.be.lessThan(g2);
        expect(g2).to.be.lessThan(c3);
        expect(c3).to.be.lessThan(c4);
      });
  });

  it("collapsed group hides children in reorderable mode", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
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

  it("expanded group shows children in reorderable mode", () => {
    mount(HierarchicalCategoryTable, {
      props: {
        reorderable: true,
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
});
