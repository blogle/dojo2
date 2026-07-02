import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/data/MetricStrip.fixtures";
import MetricStrip from "../../src/dojo/components/data/MetricStrip.vue";

describe("MetricStrip", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=metric-strip-root]").should("be.visible");
    });
  });

  it("renders metric labels", () => {
    mount(MetricStrip, {
      props: {
        items: [
          { key: "a", label: "Revenue", value: "$100" },
          { key: "b", label: "Expenses", value: "$50" },
        ],
      },
    });
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Revenue");
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Expenses");
  });

  it("renders metric values", () => {
    mount(MetricStrip, {
      props: {
        items: [{ key: "a", label: "Revenue", value: "$10,000" }],
      },
    });
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "$10,000");
  });

  it("renders delta with positive class", () => {
    mount(MetricStrip, {
      props: {
        items: [{ key: "a", label: "Revenue", value: "$100", delta: 5 }],
      },
    });
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "+5");
  });

  it("renders delta with negative class", () => {
    mount(MetricStrip, {
      props: {
        items: [{ key: "a", label: "Revenue", value: "$100", delta: -3 }],
      },
    });
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "-3");
  });

  it("renders status badge when provided", () => {
    mount(MetricStrip, {
      props: {
        items: [
          {
            key: "a",
            label: "Revenue",
            value: "$100",
            status: { label: "On track", variant: "positive" },
          },
        ],
      },
    });
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "On track");
  });

  it("shows skeleton when loading", () => {
    mount(MetricStrip, {
      props: {
        items: [{ key: "a", label: "Revenue", loading: true }],
      },
    });
    cy.get("[data-cy=metric-strip-root]")
      .find(".metric-strip__skeleton")
      .should("exist");
  });

  it("emits select when a clickable item is activated", () => {
    const onSelect = cy.spy().as("onSelect");
    mount(MetricStrip, {
      props: {
        items: [
          { key: "revenue", label: "Revenue", value: "$100", clickable: true },
        ],
        onSelect,
      },
    });
    cy.get("[data-cy=metric-strip-root]")
      .find(".metric-strip__item--clickable")
      .click();
    cy.get("@onSelect").should("have.been.calledWith", "revenue");
  });
});
