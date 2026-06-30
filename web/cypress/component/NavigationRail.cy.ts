import { mount } from "cypress/vue";
import { defineComponent, h, ref } from "vue";

import fixtures from "../../src/dojo/components/navigation/NavigationRail.fixtures";

describe("NavigationRail", () => {
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
    const Harness = defineComponent({
      setup() {
        const expanded = ref(false);
        const collapsed = fixtures.scenarios.find((scenario) => scenario.name === "collapsed");
        const expandedScenario = fixtures.scenarios.find((scenario) => scenario.name === "expanded");

        return {
          expanded,
          items: expandedScenario?.props?.items ?? collapsed?.props?.items ?? [],
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
              items: this.items,
              expanded: this.expanded,
              collapsible: true,
              fullHeight: true,
              onToggle: () => {
                this.expanded = !this.expanded;
              },
            }),
          ],
        );
      },
    });

    mount(Harness);

    cy.get("[data-cy=navigation-rail-root]").then(($rail) => {
      const collapsedRect = $rail[0].getBoundingClientRect();

      cy.get("[data-cy=navigation-rail-toggle]").click();

      cy.get("[data-cy=navigation-rail-root]").then(($expandedRail) => {
        const expandedRect = $expandedRail[0].getBoundingClientRect();
        expect(expandedRect.width).to.be.greaterThan(collapsedRect.width);

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
        items: [
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
});
