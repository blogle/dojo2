describe("Aspire migration recording", () => {
  it("imports a synthetic Aspire sheet through Dojo's authorized path", () => {
    cy.resetScenario("onboarding-empty");
    const apiBaseUrl = String(Cypress.env("apiBaseUrl")).replace(/\/$/, "");
    const syntheticSheetId = "e2e-aspire-sheet";
    cy.request(`${apiBaseUrl}/api/onboarding/google/status`);
    cy.request("POST", `${apiBaseUrl}/__e2e/google-sheets`, {
      spreadsheet_id: syntheticSheetId,
    });
    cy.request("POST", `${apiBaseUrl}/__e2e/google-session`, {
      scopes: [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
      ],
    });
    cy.visit("/onboarding");
    cy.get('[data-cy="onboarding-root"]').should("be.visible");
    cy.contains("button", "Migrate from Aspire").click();
    cy.contains("h1", "Migrate from Aspire").should("be.visible");
    cy.presentationCheckpoint("aspire-migration-form");
    cy.presentationPause();

    cy.contains("label", "Google Sheet ID")
      .find("input")
      .type(syntheticSheetId)
      .should("have.value", syntheticSheetId);
    cy.intercept("POST", "**/import/google-sheet/analyze").as("analyzeSheet");
    cy.contains("button", "Submit").click();
    cy.wait("@analyzeSheet").its("response.statusCode").should("equal", 200);
    cy.request(`${apiBaseUrl}/__e2e/google-sheets`)
      .its("body")
      .should("deep.equal", {
        spreadsheet_id: syntheticSheetId,
        call_count: 1,
        requested_spreadsheet_ids: [syntheticSheetId],
      });
    cy.get('[data-cy="net-worth-review-table"]')
      .should("be.visible")
      .and("contain", "House Value");
    cy.presentationCheckpoint("aspire-migration-review");
    cy.presentationPause();

    cy.intercept("POST", "**/import/google-sheet/commit").as("commitSheet");
    cy.contains("button", "Continue").click();
    cy.wait("@commitSheet").its("response.statusCode").should("equal", 200);
    cy.contains("h1", "Migration complete").should("be.visible");
    cy.contains(
      "Your Aspire data was imported and validated successfully.",
    ).should("be.visible");
    cy.presentationCheckpoint("aspire-migration-complete");
    cy.presentationPause();

    cy.request(
      `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/app/status`,
    )
      .its("body.latest_import_batch")
      .should("not.be.null");
  });
});
