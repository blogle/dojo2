import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/feedback/PreviewBox.fixtures";
import PreviewBox from "../../src/dojo/components/feedback/PreviewBox.vue";

describe("PreviewBox", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=preview-box-root]").should("be.visible");
    });
  });

  it("renders title when provided", () => {
    mount(PreviewBox, {
      props: { title: "Balance change" },
      slots: { default: "Content" },
    });
    cy.get("[data-cy=preview-box-root]").should(
      "contain.text",
      "Balance change",
    );
  });

  it("renders slot content", () => {
    mount(PreviewBox, {
      slots: { default: "Preview content" },
    });
    cy.get("[data-cy=preview-box-root]").should(
      "contain.text",
      "Preview content",
    );
  });
});
