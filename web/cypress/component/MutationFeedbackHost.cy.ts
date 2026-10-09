import { mount } from "cypress/vue";

import MutationFeedbackHost from "../../src/dojo/layouts/MutationFeedbackHost.vue";
import {
  notifyMutationError,
  notifyMutationSuccess,
  notifyReconciledHistoryConfirmation,
  useMutationFeedback,
} from "../../src/dojo/state/mutationFeedback";

const feedback = useMutationFeedback();

function clearFeedback() {
  while (feedback.notice.value) feedback.dismiss();
}

describe("shared mutation feedback", () => {
  beforeEach(clearFeedback);

  it("announces one latest mutation and exposes LIFO Undo", () => {
    const undone: string[] = [];
    notifyMutationSuccess("Transaction added", {
      undoneMessage: "Transaction addition undone",
      run: async () => {
        undone.push("added");
      },
    });
    notifyMutationSuccess("Transaction updated", {
      undoneMessage: "Transaction edit undone",
      run: async () => {
        undone.push("updated");
      },
    });

    mount(MutationFeedbackHost);
    cy.get('[data-cy="mutation-feedback"]')
      .should("have.attr", "role", "status")
      .and("have.attr", "aria-live", "polite")
      .and("contain.text", "Transaction updated");
    cy.get('[data-cy="mutation-feedback"] button').should("have.length", 2);
    cy.get(".mutation-feedback__undo").click();
    cy.wrap(null).should(() => {
      expect(undone).to.deep.equal(["updated"]);
      expect(feedback.notice.value?.message).to.equal("Transaction added");
    });
    cy.get(".mutation-feedback__undo").click();
    cy.wrap(null).should(() => {
      expect(undone).to.deep.equal(["updated", "added"]);
      expect(feedback.notice.value?.message).to.equal(
        "Transaction addition undone",
      );
    });
  });

  it("announces async failures assertively with a keyboard-dismissible notice", () => {
    notifyMutationError(
      new Error("Dojo could not save this change. Try again."),
    );
    mount(MutationFeedbackHost);

    cy.get('[data-cy="mutation-feedback"]')
      .should("have.attr", "role", "alert")
      .and("have.attr", "aria-live", "assertive")
      .and("contain.text", "Dojo could not save this change");
    cy.get('[aria-label="Dismiss notification"]').focus().type("{enter}");
    cy.get('[data-cy="mutation-feedback"]').should("not.exist");
  });

  it("confirms a reconciled transaction change before retrying it", () => {
    const confirm = cy.stub().resolves();
    notifyReconciledHistoryConfirmation(async () => {
      await confirm();
      notifyMutationSuccess("Transaction updated");
    }, cy.stub());
    mount(MutationFeedbackHost);

    cy.get('[data-cy="mutation-feedback"]')
      .should("contain.text", "The completed reconciliation is preserved")
      .and("contain.text", "Apply anyway");
    cy.get(".mutation-feedback__confirm").click();

    cy.wrap(null).should(() => {
      expect(confirm.callCount).to.equal(1);
      expect(feedback.notice.value?.message).to.equal("Transaction updated");
    });
  });

  it("cancels a reconciled transaction change", () => {
    const cancel = cy.stub();
    notifyReconciledHistoryConfirmation(async () => {}, cancel);
    mount(MutationFeedbackHost);

    cy.get('[data-cy="mutation-feedback"]').contains("Cancel").click();

    cy.wrap(cancel).should("have.been.calledOnce");
    cy.get('[data-cy="mutation-feedback"]').should("not.exist");
  });

  it("keeps cancellation available if applying the change fails", () => {
    const cancel = cy.stub();
    notifyReconciledHistoryConfirmation(async () => {
      throw new Error("Retry failed");
    }, cancel);
    mount(MutationFeedbackHost);

    cy.get(".mutation-feedback__confirm").click();
    cy.get('[data-cy="mutation-feedback"]')
      .should("contain.text", "Dojo could not save this change")
      .contains("Cancel")
      .click();

    cy.wrap(cancel).should("have.been.calledOnce");
    cy.get('[data-cy="mutation-feedback"]').should("not.exist");
  });
});
