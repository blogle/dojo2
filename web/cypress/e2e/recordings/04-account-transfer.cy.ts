describe("Account transfer recording", () => {
  it("records a paired investment contribution across both accounts", () => {
    cy.resetScenario("investment-contribution");

    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000401");
    cy.get('[data-cy="account-detail-page"]')
      .should("be.visible")
      .and("contain", "Brokerage");
    cy.get('[data-cy="metric-value"]').should("contain", "$10,000");
    cy.presentationCheckpoint("account-transfer-destination");
    cy.presentationPause();

    cy.get('[data-cy="account-detail-contribute"]')
      .should("be.visible")
      .click();
    cy.get('[data-cy="form-modal-root"]')
      .should("be.visible")
      .and("contain", "Investment Contributions")
      .and("contain", "$1,500.00 available");
    cy.presentationCheckpoint("account-transfer-form");
    cy.presentationPause();

    cy.get('input[name="investment-transfer-amount"]')
      .should("be.visible")
      .type("1000")
      .should("have.value", "1000");
    cy.presentationCheckpoint("account-transfer-amount");
    cy.presentationPause();

    cy.get('input[name="investment-transfer-memo"]')
      .should("be.visible")
      .clear()
      .type("February contribution")
      .should("have.value", "February contribution");
    cy.get('[data-cy="form-modal-root"]').should("contain", "$500.00");
    cy.presentationCheckpoint("account-transfer-memo");
    cy.presentationPause();

    cy.intercept("POST", "**/investment-transfers").as("contribute");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Save contribution")
      .should("be.visible")
      .click();
    cy.wait("@contribute").its("response.statusCode").should("equal", 200);
    cy.get('[data-cy="metric-value"]')
      .should("contain", "$11,000")
      .and("contain", "Provisional");
    cy.get('[data-cy="transactions-section"]')
      .find('[data-cy="transaction-row"]')
      .should("have.length", 1)
      .and("contain", "February contribution")
      .and("contain", "Checking → Brokerage");
    cy.presentationCheckpoint("account-transfer-complete");
    cy.presentationPause();

    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000101");
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
    cy.get('[data-cy="metric-balance"]').should("contain", "$19,000");
    cy.presentationCheckpoint("account-transfer-source");
    cy.presentationPause();

    cy.visit("/transactions");
    cy.get('[data-cy="transactions-page-root"]').should("be.visible");
    cy.get('[data-cy="transaction-row"]').should((rows) => {
      const matchingRows = [...rows].filter((row) =>
        row.textContent?.includes("February contribution"),
      );
      expect(matchingRows).to.have.length(2);
    });
    cy.presentationCheckpoint("account-transfer-paired-ledger");
    cy.presentationPause();
  });
});
