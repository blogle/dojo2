import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/overlays/FormModal.fixtures";
import FormModal from "../../src/dojo/components/overlays/FormModal.vue";

describe("FormModal", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      });
      cy.get("[data-cy=form-modal-root]").should("be.visible");
    });
  });

  it("renders the title", () => {
    mount(FormModal, {
      props: { visible: true, contained: true, title: "Edit item" },
    });
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Edit item");
  });

  it("renders body slot content", () => {
    mount(FormModal, {
      props: { visible: true, contained: true },
      slots: { default: '<input data-cy="test-input" />' },
    });
    cy.get("[data-cy=test-input]").should("be.visible");
  });

  it("renders the submit button with custom text", () => {
    mount(FormModal, {
      props: { visible: true, contained: true, submitText: "Create" },
    });
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Create");
  });

  it("emits submit when the submit button is clicked", () => {
    const onSubmit = cy.spy().as("onSubmit");
    mount(FormModal, {
      props: { visible: true, contained: true, onSubmit },
    });
    cy.get("[data-cy=form-modal-root]").contains("Save").click();
    cy.get("@onSubmit").should("have.been.called");
  });

  it("emits cancel when the cancel button is clicked", () => {
    const onCancel = cy.spy().as("onCancel");
    mount(FormModal, {
      props: { visible: true, contained: true, onCancel },
    });
    cy.get("[data-cy=form-modal-root]").contains("Cancel").click();
    cy.get("@onCancel").should("have.been.called");
  });

  it("disables submit when submitDisabled is true", () => {
    mount(FormModal, {
      props: { visible: true, contained: true, submitDisabled: true },
    });
    cy.get("[data-cy=form-modal-root]").contains("Save").should("be.disabled");
  });
});
