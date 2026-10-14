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
    cy.get("[data-cy=table-shell-root] thead").should("contain.text", "Name");
    cy.get("[data-cy=table-shell-root] thead").should("contain.text", "Amount");
  });

  it("shares column sizing and alignment between headers and body cells", () => {
    mount(TableShell, {
      props: {
        columns: [
          { key: "symbol", label: "Symbol", width: "30%" },
          { key: "quantity", label: "Qty", align: "end" },
          { key: "basis", label: "Cost basis", align: "end" },
          { key: "value", label: "Value", align: "end" },
          { key: "gain", label: "Gain", align: "end" },
        ],
        rows: [
          {
            key: "cash",
            symbol: "CASH",
            quantity: "25",
            basis: "$1,100.00",
            value: "$1,250.00",
            gain: "$150.00",
          },
        ],
      },
    });

    cy.get(".table-shell__table col")
      .eq(0)
      .then(($col) => {
        expect($col[0].getAttribute("style")).to.contain("30%");
      });
    cy.get(".table-shell__head").each(($header, index) => {
      cy.get(".table-shell__cell")
        .eq(index)
        .then(($cell) => {
          const headerRect = $header[0].getBoundingClientRect();
          const cellRect = $cell[0].getBoundingClientRect();
          expect(Math.abs(headerRect.left - cellRect.left)).to.be.lessThan(1);
          expect(Math.abs(headerRect.right - cellRect.right)).to.be.lessThan(1);
        });
    });
    cy.get(".table-shell__head")
      .eq(0)
      .then(($header) => {
        expect(["left", "start"]).to.include(
          getComputedStyle($header[0]).textAlign,
        );
      });
    cy.get(".table-shell__cell")
      .eq(0)
      .then(($cell) => {
        expect(["left", "start"]).to.include(
          getComputedStyle($cell[0]).textAlign,
        );
      });
    cy.get(".table-shell__head").each(($header, index) => {
      if (index === 0) return;
      cy.wrap($header).should("have.css", "text-align", "right");
      cy.get(".table-shell__cell")
        .eq(index)
        .should("have.css", "text-align", "right");
    });
  });

  it("allows wide content to scroll inside a narrow container", () => {
    mount(TableShell, {
      props: {
        columns: [
          { key: "date", label: "Date", width: "180px" },
          { key: "description", label: "Description", width: "180px" },
        ],
        rows: [
          {
            key: "long",
            date: "Oct 14",
            description:
              "A deliberately long table value that must remain readable without overlapping other columns",
          },
        ],
      },
    });

    cy.get(".table-shell").invoke("css", "width", "180px");
    cy.get(".table-shell").should(($container) => {
      expect($container[0].scrollWidth).to.be.greaterThan(
        $container[0].clientWidth,
      );
    });
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

  it("renders cell slot for custom cell rendering", () => {
    mount(TableShell, {
      props: {
        columns: [{ key: "name", label: "Name" }],
        rows: [{ key: "a", name: "Test" }],
      },
      slots: {
        cell: '<span data-cy="custom-cell">Custom</span>',
      },
    });
    cy.get("[data-cy=custom-cell]").should("contain.text", "Custom");
  });
});
