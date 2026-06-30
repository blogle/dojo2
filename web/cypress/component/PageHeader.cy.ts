import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/data/PageHeader.fixtures";
import PageHeader from "../../src/dojo/components/data/PageHeader.vue";

describe("PageHeader", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=page-header-root]").should("be.visible");
    });
  });

  it("renders the title", () => {
    mount(PageHeader, { props: { title: "Budget" } });
    cy.get("[data-cy=page-header-root]").should("contain.text", "Budget");
  });

  it("renders the subtitle when provided", () => {
    mount(PageHeader, {
      props: { title: "Budget", subtitle: "Monthly overview" },
    });
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Monthly overview",
    );
  });

  it("renders the metadata when provided", () => {
    mount(PageHeader, {
      props: { title: "Budget", metadata: "May 2025" },
    });
    cy.get("[data-cy=page-header-root]").should("contain.text", "May 2025");
  });

  it("renders the actions slot", () => {
    mount(PageHeader, {
      props: { title: "Budget" },
      slots: {
        actions: '<button data-cy="test-action">Add</button>',
      },
    });
    cy.get("[data-cy=test-action]").should("be.visible");
  });

  it("renders the tabs slot", () => {
    mount(PageHeader, {
      props: { title: "Budget" },
      slots: {
        tabs: '<div data-cy="test-tabs">Tabs here</div>',
      },
    });
    cy.get("[data-cy=test-tabs]").should("be.visible");
  });
});
