import { mount } from "cypress/vue";

import MutationFeedbackHost from "../../src/dojo/layouts/MutationFeedbackHost.vue";
import {
  notifyMutationError,
  notifyMutationSuccess,
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
});
