describe("Transactions recording", () => {
  it("creates, edits, and clears a categorized transaction", () => {
    cy.resetScenario("assets-liabilities-overview");

    cy.visit("/transactions");
    cy.get('[data-cy="transactions-page-root"]').should("be.visible");
    cy.get('[data-cy="transaction-entry-form"]')
      .should("be.visible")
      .and("contain", "Add transaction");
    cy.presentationCheckpoint("transactions-entry-form");
    cy.presentationPause();

    cy.get('[data-cy="transaction-entry-form"]').within(() => {
      cy.contains("label", "Account")
        .find("select")
        .select("00000000-0000-0000-0000-000000000101");
      cy.contains("label", "Category")
        .find("select")
        .select("00000000-0000-0000-0000-000000000011");
      cy.contains("label", "Amount").find("input").type("12.34");
      cy.contains("label", "Memo")
        .find("input")
        .type("February groceries")
        .should("have.value", "February groceries");
    });
    cy.presentationCheckpoint("transactions-new-entry");
    cy.presentationPause();

    cy.intercept("POST", "**/transactions").as("createTransaction");
    cy.get('[data-cy="transaction-entry-form"]')
      .contains("button", "Add")
      .should("be.visible")
      .click();
    cy.wait("@createTransaction")
      .its("response.statusCode")
      .should("equal", 200);
    cy.get('[data-cy="transaction-row"]').should(
      "contain",
      "February groceries",
    );
    cy.presentationCheckpoint("transactions-created-pending");
    cy.presentationPause();

    cy.contains('[data-cy="transaction-row"]', "February groceries")
      .should("be.visible")
      .click();
    cy.get('[data-cy="transaction-row"].ledger__row--editing')
      .should("be.visible")
      .find('input[placeholder="Memo"]')
      .clear()
      .type("February market")
      .should("have.value", "February market");
    cy.presentationCheckpoint("transactions-editing");
    cy.presentationPause();

    cy.intercept("PUT", "**/transactions/*").as("updateTransaction");
    cy.get('[data-cy="transaction-row"].ledger__row--editing')
      .find(".ledger__status-pill")
      .should("contain", "Pending")
      .click()
      .should("contain", "Cleared");
    cy.get('[data-cy="transaction-row"].ledger__row--editing')
      .find('input[placeholder="Memo"]')
      .type("{enter}");
    cy.wait("@updateTransaction")
      .its("response.statusCode")
      .should("equal", 200);
    cy.contains('[data-cy="transaction-row"]', "February market")
      .should("contain", "Cleared")
      .and("contain", "-$12.34");
    cy.presentationCheckpoint("transactions-edited-cleared");
    cy.presentationPause();
  });
});
