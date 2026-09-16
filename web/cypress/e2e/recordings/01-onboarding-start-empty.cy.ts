describe("Start empty onboarding recording", () => {
  it("creates an empty workspace and reaches the required backup setup", () => {
    cy.resetScenario("onboarding-empty");
    cy.visit("/onboarding");
    cy.get('[data-cy="onboarding-root"]')
      .should("be.visible")
      .and("contain", "Start empty");
    cy.presentationCheckpoint("onboarding-choice");
    cy.presentationPause();

    cy.intercept("POST", "**/onboarding/start-empty").as("startEmpty");
    cy.contains("button", "Start empty").click();
    cy.wait("@startEmpty").its("response.statusCode").should("equal", 200);
    cy.contains("h1", "Back up dojo to Google Drive").should("be.visible");
    cy.contains("button", "Connect Google Drive").should("be.visible");
    cy.presentationCheckpoint("onboarding-backup-setup");
    cy.presentationPause();

    cy.request(
      `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/app/status`,
    )
      .its("body.needs_backup_setup")
      .should("equal", true);
  });
});
