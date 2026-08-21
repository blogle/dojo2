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
      ["cash", "Checking", "$20,000"],
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

describe("Tangible asset creation", () => {
  beforeEach(() => {
    cy.resetScenario("tangible-asset-creation");
    cy.visit("/assets-liabilities");
    cy.get('[data-cy="assets-liabilities-page"]').should("be.visible");
  });

  it("AL-02 creates a tangible asset that persists across surfaces", () => {
    cy.get('[data-cy="metric-net-worth"]').should("contain", "$20,000");
    cy.get('[data-cy="assets-liabilities-add-item"]').click();
    cy.location("pathname").should("equal", "/assets-liabilities/add");

    cy.get('[data-cy="entity-type-tangible-asset"]').click();
    cy.get('[data-cy="add-item-continue"]').click();
    cy.get('input[name="name"]').type("Rental property");
    cy.get('input[name="opening-valuation"]').type("25000");
    cy.get('input[name="opening-valuation-date"]').type("2026-02-15");

    cy.intercept("POST", "**/api/accounts").as("createAccount");
    cy.get('[data-cy="add-item-continue"]').click();
    cy.wait("@createAccount").its("response.statusCode").should("equal", 200);

    cy.location("pathname").should("match", /^\/assets-liabilities\/[^/]+$/);
    cy.get('[data-cy="account-detail-page"]').should(
      "contain",
      "Rental property",
    );
    cy.get('[data-cy="metric-value"]').should("contain", "$25,000");

    cy.reload();
    cy.get('[data-cy="account-detail-page"]').should(
      "contain",
      "Rental property",
    );
    cy.get('[data-cy="metric-value"]').should("contain", "$25,000");

    cy.visit("/assets-liabilities");
    cy.get(
      '[data-cy="assets-liabilities-group"][data-group-key="tangible-assets"]',
    )
      .find('[data-cy="assets-liabilities-row"]')
      .should("have.length", 1)
      .and("contain", "Rental property")
      .and("contain", "$25,000");
    cy.get('[data-cy="metric-net-worth"]').should("contain", "$45,000");

    cy.request(
      `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/net-worth`,
    )
      .its("body.current_net_worth_minor")
      .should("equal", 4500000);
  });
});

describe("Tracking snapshot correction", () => {
  beforeEach(() => {
    cy.resetScenario("tracking-snapshot-correction");
    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000201");
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
  });

  it("AL-03 corrects a same-date tracking snapshot across surfaces", () => {
    cy.get('[data-cy="metric-value"]').should("contain", "$500,000");
    cy.get('[data-cy="snapshot-history-row"]')
      .should("have.length", 1)
      .and("contain", "$500,000");

    cy.get('[data-cy="account-detail-add-snapshot"]').click();
    cy.get('input[name="value-date"]').should("have.value", "2026-02-15");
    cy.get('input[name="value-amount"]').type("510000");
    cy.get('input[name="value-notes"]').type("Updated appraisal");

    cy.intercept("POST", "**/tracking-snapshots").as("correctSnapshot");
    cy.get('[data-cy="form-modal-root"]').contains("button", "Save").click();
    cy.wait("@correctSnapshot").its("response.statusCode").should("equal", 200);

    cy.get('[data-cy="metric-value"]').should("contain", "$510,000");
    cy.get('[data-cy="snapshot-history-row"]')
      .should("have.length", 1)
      .and("contain", "$510,000");

    cy.reload();
    cy.get('[data-cy="metric-value"]').should("contain", "$510,000");
    cy.get('[data-cy="snapshot-history-row"]').should("have.length", 1);

    cy.visit("/assets-liabilities");
    cy.get(
      '[data-cy="assets-liabilities-group"][data-group-key="tracking-assets"]',
    )
      .find('[data-cy="assets-liabilities-row"]')
      .should("have.length", 1)
      .and("contain", "Home estimate")
      .and("contain", "$510,000");
    cy.get('[data-cy="metric-net-worth"]').should("contain", "$530,000");
  });
});

describe("Cash-only investment reconciliation", () => {
  beforeEach(() => {
    cy.resetScenario("cash-only-investment");
    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000401");
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
  });

  it("AL-04 reconciles an investment statement without holdings", () => {
    cy.get('[data-cy="holdings-summary-section"]').should(
      "contain",
      "No statement recorded.",
    );
    cy.get('[data-cy="account-detail-reconcile-investment"]').click();
    cy.get('input[name="investment-statement-date"]').should(
      "have.value",
      "2026-02-15",
    );
    cy.get('input[name="investment-statement-cash"]').type("12000");
    cy.get('[data-cy="form-modal-root"]')
      .should("contain", "No holdings")
      .find('input[name^="holding-ticker-"]')
      .should("not.exist");

    cy.intercept("POST", "**/investment-statements").as("reconcileInvestment");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Apply statement")
      .click();
    cy.wait("@reconcileInvestment")
      .its("response.statusCode")
      .should("equal", 200);

    cy.get('[data-cy="metric-value"]').should("contain", "$12,000");
    cy.get('[data-cy="holdings-summary-section"]').should(
      "contain",
      "No holdings in latest statement.",
    );

    cy.visit("/assets-liabilities");
    cy.get('[data-cy="assets-liabilities-group"][data-group-key="investments"]')
      .find('[data-cy="assets-liabilities-row"]')
      .should("have.length", 1)
      .and("contain", "Cash brokerage")
      .and("contain", "$12,000");
    cy.get('[data-cy="metric-net-worth"]').should("contain", "$32,000");
  });
});

describe("Investment contribution provenance", () => {
  beforeEach(() => {
    cy.resetScenario("investment-contribution");
    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000401");
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
  });

  it("AL-05 preserves contribution provenance and net worth", () => {
    cy.get('[data-cy="metric-value"]').should("contain", "$10,000");
    cy.get('[data-cy="account-detail-contribute"]').click();
    cy.get('input[name="investment-transfer-amount"]').type("1000");
    cy.get('input[name="investment-transfer-memo"]')
      .clear()
      .type("February contribution");
    cy.get('[data-cy="form-modal-root"]')
      .should("contain", "Investment Contributions")
      .and("contain", "$1,500.00 available")
      .and("contain", "$500.00");

    cy.intercept("POST", "**/investment-transfers").as("contribute");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Save contribution")
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

    cy.visit("/transactions");
    cy.get('[data-cy="transaction-row"]').should((rows) => {
      const matchingRows = [...rows].filter((row) =>
        row.textContent?.includes("February contribution"),
      );
      expect(matchingRows).to.have.length(2);
    });

    cy.visit("/budgets");
    cy.get(
      '[data-cy="category-row"][data-row-key="00000000-0000-0000-0000-000000000011"]',
    ).click();
    cy.get('[data-cy="full-screen-trouser-root"]')
      .should("contain", "Investment Contributions")
      .and("contain", "-$1,000.00")
      .and("contain", "$500.00");
    cy.get('[data-cy="full-screen-trouser-root"]')
      .contains('[role="tab"]', "Spending history")
      .click();
    cy.get('[data-cy="category-spending-history"]')
      .should("contain", "Brokerage")
      .and("contain", "February contribution")
      .and("contain", "-$1,000.00");

    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000401");
    cy.get('[data-cy="account-detail-reconcile-investment"]').click();
    cy.get('input[name="investment-statement-cash"]').clear().type("11000");
    cy.intercept("POST", "**/investment-statements").as("includeContribution");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Apply statement")
      .click();
    cy.wait("@includeContribution")
      .its("response.statusCode")
      .should("equal", 200);

    cy.get('[data-cy="metric-value"]')
      .should("contain", "$11,000")
      .and("not.contain", "Provisional");
    cy.request(
      `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/accounts/00000000-0000-0000-0000-000000000401/investment-statements/latest`,
    )
      .its("body.provisional_transfer_minor")
      .should("equal", 0);
    cy.request(
      `${String(Cypress.env("apiBaseUrl")).replace(/\/$/, "")}/api/net-worth`,
    )
      .its("body.current_net_worth_minor")
      .should("equal", 3000000);
  });
});
