import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/navigation/Tabs.fixtures";
import Tabs from "../../src/dojo/components/navigation/Tabs.vue";

describe("Tabs", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=tabs-root]").should("be.visible");
    });
  });

  it("emits update:modelValue when a tab is clicked", () => {
    const onUpdate = cy.spy().as("onUpdate");
    mount(Tabs, {
      props: {
        items: [
          { key: "a", label: "Tab A" },
          { key: "b", label: "Tab B" },
        ],
        modelValue: "a",
        "onUpdate:modelValue": onUpdate,
      },
    });
    cy.contains("Tab B").click();
    cy.get("@onUpdate").should("have.been.calledWith", "b");
  });

  it("marks the active tab as selected", () => {
    mount(Tabs, {
      props: {
        items: [
          { key: "a", label: "Tab A" },
          { key: "b", label: "Tab B" },
        ],
        modelValue: "a",
      },
    });
    cy.contains("Tab A").should("have.attr", "aria-selected", "true");
    cy.contains("Tab B").should("have.attr", "aria-selected", "false");
  });

  it("renders all tab items", () => {
    mount(Tabs, {
      props: {
        items: [
          { key: "a", label: "Alpha" },
          { key: "b", label: "Beta" },
          { key: "c", label: "Gamma" },
        ],
      },
    });
    cy.get("[data-cy=tabs-root] [role='tab']").should("have.length", 3);
  });

  it("applies active class to the selected tab", () => {
    mount(Tabs, {
      props: {
        items: [
          { key: "a", label: "Tab A" },
          { key: "b", label: "Tab B" },
        ],
        modelValue: "a",
      },
    });
    cy.contains("Tab A").should("have.class", "tabs__item--active");
    cy.contains("Tab B").should("not.have.class", "tabs__item--active");
  });
});
