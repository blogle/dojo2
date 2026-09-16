describe("Budget recording", () => {
  it("shows a category group and funds a category", () => {
    cy.resetScenario("linked-loan-payment");

    cy.visit("/budgets");
    cy.get('[data-cy="budgets-page-root"]').should("be.visible");
    cy.get('[data-cy="hierarchical-category-table-root"]')
      .should("be.visible")
      .and("contain", "E2E categories")
      .and("contain", "Mortgage");
    cy.presentationCheckpoint("budget-overview");
    cy.presentationPause();

    cy.get(
      '[data-cy="category-row"][data-row-key="00000000-0000-0000-0000-000000000010"]',
    )
      .should("be.visible")
      .and("contain", "E2E categories")
      .click();
    cy.get('[data-cy="full-screen-trouser-root"]')
      .should("be.visible")
      .and("contain", "Category group")
      .and("contain", "E2E categories");
    cy.presentationCheckpoint("budget-category-group");
    cy.presentationPause();

    cy.get('[data-cy="full-screen-trouser-root"]')
      .contains("button", "Close")
      .click();
    cy.get('[data-cy="full-screen-trouser-root"]').should("not.exist");
    cy.get(
      '[data-cy="category-row"][data-row-key="00000000-0000-0000-0000-000000000011"]',
    )
      .should("be.visible")
      .and("contain", "Mortgage")
      .click();
    cy.get('[data-cy="full-screen-trouser-root"]')
      .should("be.visible")
      .and("contain", "Mortgage");
    cy.presentationCheckpoint("budget-category-detail");
    cy.presentationPause();

    cy.get('[data-cy="full-screen-trouser-root"]')
      .contains("button", "Fund")
      .should("be.visible")
      .click();
    cy.get('[data-cy="form-modal-root"]')
      .should("be.visible")
      .and("contain", "Fund");
    cy.presentationCheckpoint("budget-funding-form");
    cy.presentationPause();

    cy.get('[data-cy="form-modal-root"]').within(() => {
      cy.contains("label", "Funding option")
        .parent()
        .find("select")
        .select("custom");
      cy.contains("label", "Custom amount")
        .parent()
        .find("input")
        .type("1000")
        .should("have.value", "1000");
    });
    cy.presentationCheckpoint("budget-funding-amount");
    cy.presentationPause();

    cy.intercept("POST", "**/allocations/fund").as("fundCategory");
    cy.get('[data-cy="form-modal-root"]').contains("button", "Save").click();
    cy.wait("@fundCategory").its("response.statusCode").should("equal", 200);
    cy.get('[data-cy="form-modal-root"]').should("not.exist");
    cy.request(
      `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/budget?month=2026-02`,
    )
      .its("body.groups")
      .should((groups) => {
        const mortgage = groups
          .flatMap(
            (group: {
              categories: { name: string; month_budgeted_minor: number }[];
            }) => group.categories,
          )
          .find((category: { name: string }) => category.name === "Mortgage");
        expect(mortgage?.month_budgeted_minor).to.equal(600000);
      });
    cy.reload();
    cy.get(
      '[data-cy="category-row"][data-row-key="00000000-0000-0000-0000-000000000011"]',
    )
      .should("contain", "Mortgage")
      .and("contain", "$6,000.00");
    cy.presentationCheckpoint("budget-category-funded");
    cy.presentationPause();
  });
});
