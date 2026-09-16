describe("Assets & Liabilities recording", () => {
  it("shows the rich account list and opens an account detail", () => {
    cy.resetScenario("assets-liabilities-overview");

    cy.visit("/assets-liabilities");
    cy.get('[data-cy="assets-liabilities-page"]').should("be.visible");
    cy.get('[data-cy="assets-liabilities-groups"]').should("be.visible");
    cy.get('[data-cy="assets-liabilities-row"]')
      .should("have.length.greaterThan", 0)
      .and("contain", "Checking");
    cy.presentationCheckpoint("assets-liabilities-list");
    cy.presentationPause();

    cy.get(
      '[data-cy="assets-liabilities-group"][data-group-key="tracking-assets"] [data-cy="assets-liabilities-row"]',
    )
      .should("be.visible")
      .and("contain", "Tracking asset")
      .click();
    cy.get('[data-cy="account-detail-page"]')
      .should("be.visible")
      .and("contain", "Tracking asset");
    cy.get('[data-cy="metric-value"]').should("contain", "$500,000");
    cy.presentationCheckpoint("tracking-asset-detail");
    cy.presentationPause();
  });

  it("adds a tangible asset and shows its detail", () => {
    cy.resetScenario("tangible-asset-creation");

    cy.visit("/assets-liabilities");
    cy.get('[data-cy="assets-liabilities-page"]').should("be.visible");
    cy.get('[data-cy="assets-liabilities-groups"]').should("be.visible");
    cy.get('[data-cy="assets-liabilities-add-item"]')
      .should("be.visible")
      .click();
    cy.location("pathname").should("equal", "/assets-liabilities/add");
    cy.get('[data-cy="add-item-wizard-page"]').should("be.visible");
    cy.presentationCheckpoint("add-item-type-selection");
    cy.presentationPause();

    cy.get('[data-cy="entity-type-tangible-asset"]')
      .should("be.visible")
      .click();
    cy.get('[data-cy="entity-type-tangible-asset"]').should(
      "have.class",
      "add-item-modal__type-card--selected",
    );
    cy.presentationCheckpoint("tangible-asset-type-selected");
    cy.presentationPause();

    cy.get('[data-cy="add-item-continue"]').should("be.visible").click();
    cy.get('input[name="name"]').should("be.visible");
    cy.presentationCheckpoint("tangible-asset-details");
    cy.presentationPause();

    cy.get('input[name="name"]')
      .should("be.visible")
      .type("Rental property")
      .should("have.value", "Rental property");
    cy.presentationCheckpoint("tangible-asset-name");
    cy.presentationPause();

    cy.get('input[name="opening-valuation"]')
      .should("be.visible")
      .type("25000")
      .should("have.value", "25000");
    cy.presentationCheckpoint("tangible-asset-valuation");
    cy.presentationPause();

    cy.get('input[name="opening-valuation-date"]')
      .should("be.visible")
      .type("2026-02-15")
      .should("have.value", "2026-02-15");
    cy.presentationCheckpoint("tangible-asset-date");
    cy.presentationPause();

    cy.intercept("POST", "**/api/accounts").as("createAccount");
    cy.get('[data-cy="add-item-continue"]').should("be.visible").click();
    cy.wait("@createAccount").its("response.statusCode").should("equal", 200);
    cy.location("pathname").should("match", /^\/assets-liabilities\/[^/]+$/);
    cy.get('[data-cy="account-detail-page"]')
      .should("be.visible")
      .and("contain", "Rental property");
    cy.get('[data-cy="metric-value"]').should("contain", "$25,000");
    cy.presentationCheckpoint("tangible-asset-detail");
    cy.presentationPause();
  });
});
