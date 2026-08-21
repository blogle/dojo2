describe("Assets & Liabilities", () => {
  beforeEach(() => {
    cy.resetScenario("assets-liabilities-overview");
    cy.visit("/assets-liabilities");
    cy.get('[data-cy="assets-liabilities-page"]').should("be.visible");
    cy.get('[data-cy="assets-liabilities-groups"]').should("be.visible");
  });

  it("AL-01 shows truthful grouped totals across surfaces", () => {
    cy.get('[data-cy="assets-liabilities-metrics"]')
      .find('[data-cy="metric-assets"]')
      .should("contain", "$561,000");
    cy.get('[data-cy="assets-liabilities-metrics"]')
      .find('[data-cy="metric-liabilities"]')
      .should("contain", "$200,000");
    cy.get('[data-cy="assets-liabilities-metrics"]')
      .find('[data-cy="metric-net-worth"]')
      .should("contain", "$361,000");

    const groups = [
      ["cash", "Cash", "$20,000"],
      ["tracking-assets", "Tracking asset", "$500,000"],
      ["tangible-assets", "Tangible asset", "$25,000"],
      ["investments", "Investment", "$12,000"],
      ["restricted-assets", "Loan escrow", "$4,000"],
      ["loans", "Loan", "$200,000"],
    ];
    cy.get('[data-cy="assets-liabilities-group"]').should(
      "have.length",
      groups.length,
    );
    groups.forEach(([group, name, value]) => {
      cy.get(`[data-cy="assets-liabilities-group"][data-group-key="${group}"]`)
        .find('[data-cy="assets-liabilities-row"]')
        .should("have.length", 1)
        .and("contain", name)
        .and("contain", value);
    });

    cy.get(
      '[data-cy="assets-liabilities-group"][data-group-key="tracking-assets"]',
    )
      .find('[data-cy="assets-liabilities-row"]')
      .click();
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
    cy.location("pathname").should(
      "equal",
      "/assets-liabilities/00000000-0000-0000-0000-000000000201",
    );
    cy.get('[data-cy="metric-value"]').should("contain", "$500,000");

    cy.request({
      url: `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/net-worth`,
      headers: { Accept: "application/json" },
    })
      .its("body.current_net_worth_minor")
      .should("equal", 36100000);
  });
});
