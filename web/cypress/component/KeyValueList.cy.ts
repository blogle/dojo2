import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/display/KeyValueList.fixtures";
import KeyValueList from "../../src/dojo/components/display/KeyValueList.vue";

describe("KeyValueList", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=key-value-list-root]").should("be.visible");
    });
  });

  it("renders all items", () => {
    mount(KeyValueList, {
      props: {
        items: [
          { label: "Name", value: "Test" },
          { label: "Amount", value: "$100" },
        ],
      },
    });
    cy.get("[data-cy=key-value-list-root] .key-value-list__row").should(
      "have.length",
      2,
    );
  });

  it("applies variant class to value", () => {
    mount(KeyValueList, {
      props: {
        items: [{ label: "Status", value: "Good", variant: "positive" }],
      },
    });
    cy.get("[data-cy=key-value-list-root] .key-value-list__value").should(
      "have.class",
      "key-value-list__value--positive",
    );
  });
});
