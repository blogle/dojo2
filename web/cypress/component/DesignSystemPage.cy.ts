import { mount } from "cypress/vue";

import DesignSystemPage from "../../src/dojo/pages/DesignSystemPage.vue";

describe("DesignSystemPage", () => {
  it("shifts the catalog content right when the navigation rail expands", () => {
    cy.viewport(1280, 900);
    mount(DesignSystemPage);

    cy.get("[data-cy=design-system-page-container]").then(($container) => {
      const collapsedLeft = $container[0].getBoundingClientRect().left;

      cy.get("[data-cy=design-system-page-nav-shell]")
        .find("[data-cy=navigation-rail-toggle]")
        .click();

      cy.get("[data-cy=design-system-page-container]").should(
        ($expandedContainer) => {
          const expandedLeft =
            $expandedContainer[0].getBoundingClientRect().left;

          expect(expandedLeft).to.be.greaterThan(collapsedLeft);
        },
      );
    });
  });

  it("keeps the page rail collapsed on compact viewports", () => {
    cy.viewport(390, 844);
    mount(DesignSystemPage);

    cy.get("[data-cy=design-system-page-nav-shell]")
      .find("[data-cy=navigation-rail-toggle]")
      .should("not.exist");
    cy.get("[data-cy=design-system-page-nav-shell]").should(($shell) => {
      expect($shell[0].getBoundingClientRect().width).to.equal(56);
    });
  });
});
