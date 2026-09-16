import { mount } from "cypress/vue";
import { h } from "vue";

import fixtures from "../../src/dojo/components/navigation/NavigationRail.fixtures";

describe("NavigationRail", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
  });

  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });

      cy.get("[data-cy=navigation-rail-root]").should("be.visible");
    });
  });

  it("widens when expanded and keeps the current item inside bounds", () => {
    const Harness = {
      setup() {
        const collapsed = fixtures.scenarios.find(
          (scenario) => scenario.name === "collapsed",
        );
        const expandedScenario = fixtures.scenarios.find(
          (scenario) => scenario.name === "expanded",
        );

        return {
          items:
            expandedScenario?.props?.primaryItems ??
            collapsed?.props?.primaryItems ??
            [],
        };
      },
      render() {
        return h(
          "div",
          {
            style:
              "height: 480px; width: 260px; padding: 12px; background: var(--color-background);",
          },
          [
            h(fixtures.component, {
              primaryItems: this.items,
              collapsible: true,
            }),
          ],
        );
      },
    };

    mount(Harness);

    cy.get("[data-cy=navigation-rail-root]").then(($rail) => {
      const collapsedRect = $rail[0].getBoundingClientRect();

      cy.get("[data-cy=navigation-rail-toggle]").click();

      cy.get("[data-cy=navigation-rail-root]").should(($expandedRail) => {
        const expandedRect = $expandedRail[0].getBoundingClientRect();
        expect(expandedRect.width).to.be.greaterThan(collapsedRect.width);
      });

      cy.get("[data-cy=navigation-rail-root]").should(($expandedRail) => {
        const expandedRect = $expandedRail[0].getBoundingClientRect();
        expect(expandedRect.width).to.be.greaterThan(160);
      });

      cy.wait(200);
      cy.get("[data-cy=navigation-rail-root]").then(($expandedRail) => {
        const expandedRect = $expandedRail[0].getBoundingClientRect();
        cy.get("[data-cy=navigation-rail-item-transactions]").then(($item) => {
          const itemRect = $item[0].getBoundingClientRect();

          expect(itemRect.left).to.be.at.least(expandedRect.left);
          expect(itemRect.right).to.be.at.most(expandedRect.right);
        });
      });
    });
  });

  it("uses visible labels when expanded", () => {
    mount(fixtures.component, {
      props: {
        expanded: true,
        primaryItems: [
          {
            kind: "anchor",
            key: "foundations",
            label: "1. Foundations",
            visibleLabel: "Foundations",
            icon: "foundations",
            href: "#foundations",
            current: true,
          },
        ],
      },
    });

    cy.get("[data-cy=navigation-rail-item-foundations]").should(
      "contain.text",
      "Foundations",
    );
    cy.get("[data-cy=navigation-rail-item-foundations]").should(
      "not.contain.text",
      "1. Foundations",
    );
  });

  it("keeps a full-height rail pinned while the page scrolls", () => {
    const scenario = fixtures.scenarios.find(({ name }) => name === "expanded");

    const Harness = {
      setup() {
        return {
          primaryItems: scenario?.props?.primaryItems ?? [],
        };
      },
      render() {
        return h(
          "div",
          {
            style:
              "display: flex; min-height: 1600px; background: var(--color-background);",
          },
          [
            h(fixtures.component, {
              primaryItems: this.primaryItems,
            }),
            h("main", { style: "flex: 1;" }, "Scrollable content"),
          ],
        );
      },
    };

    mount(Harness);

    cy.scrollTo(0, 600);

    cy.get("[data-cy=navigation-rail-root]").should(($rail) => {
      expect($rail[0].getBoundingClientRect().top).to.equal(0);
    });
  });

  it("keeps demo items inert while rendering the same anchor markup", () => {
    mount(fixtures.component, {
      props: {
        expanded: true,
        primaryItems: [
          {
            kind: "anchor",
            key: "budget",
            label: "Budget",
            icon: "budget",
            href: "#budget",
            current: true,
            interactive: false,
          },
        ],
      },
    });

    cy.window().then((window) => {
      window.history.replaceState(
        {},
        "",
        window.location.pathname + window.location.search,
      );
    });

    cy.get("[data-cy=navigation-rail-item-budget]")
      .should("have.prop", "tagName", "A")
      .and("have.attr", "aria-disabled", "true")
      .click();

    cy.location("hash").should("eq", "");
  });

  it("renders lower utilities and persists uncontrolled expansion", () => {
    mount(fixtures.component, {
      props: {
        primaryItems: [],
        secondaryItems: [
          {
            kind: "action",
            key: "account",
            label: "Account",
            icon: "account",
            interactive: false,
          },
        ],
      },
    });

    cy.get("[data-cy=navigation-rail-item-account]")
      .should("have.attr", "aria-label", "Account")
      .should("be.visible");
    cy.get("[data-cy=navigation-rail-toggle]").click();
    cy.get("[data-cy=navigation-rail-root]").should(
      "have.class",
      "navigation-rail--expanded",
    );
    cy.get("[data-cy=navigation-rail-toggle]")
      .should("have.attr", "aria-label", "Collapse navigation rail")
      .should("not.contain.text", "Collapse")
      .find("svg")
      .should("be.visible");

    mount(fixtures.component, {
      props: { primaryItems: [] },
    });
    cy.get("[data-cy=navigation-rail-root]").should(
      "have.class",
      "navigation-rail--expanded",
    );
  });
});
