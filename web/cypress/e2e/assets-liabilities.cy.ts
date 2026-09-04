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

    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000101");
    cy.get('[data-cy="metric-balance"]').should("contain", "$19,000");

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

describe("Linked loan payment activity", () => {
  beforeEach(() => {
    cy.resetScenario("linked-loan-payment");
    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000501");
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
  });

  it("AL-06 shows one mortgage payment across transaction, budget, and loan views", () => {
    cy.get('[data-cy="metric-obligation"]').should("contain", "$200,000");
    cy.get('[data-cy="loan-escrow-section"]').should("contain", "$4,000");

    cy.get('[data-cy="account-detail-record-payment"]').click();
    cy.get('[data-cy="form-modal-root"]')
      .should("contain", "Payment category: Mortgage")
      .find('input[name="loan-principal"]')
      .should("not.exist");
    cy.get('input[name="loan-payment-amount"]').type("5000");
    cy.get('input[name="loan-payment-memo"]')
      .clear()
      .type("February mortgage payment");

    cy.intercept("POST", "**/loan-payments").as("recordPayment");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Record payment")
      .click();
    cy.wait("@recordPayment").its("response.statusCode").should("equal", 200);

    cy.get('[data-cy="loan-payment-row"]')
      .should("have.length", 1)
      .and("contain", "2026-02-15")
      .and("contain", "Checking")
      .and("contain", "February mortgage payment")
      .and("contain", "Cleared")
      .and("contain", "$5,000");

    cy.visit("/transactions");
    cy.get('[data-cy="transaction-row"]').should((rows) => {
      const matchingRows = [...rows].filter((row) =>
        row.textContent?.includes("February mortgage payment"),
      );
      expect(matchingRows).to.have.length(1);
      expect(matchingRows[0]?.textContent).to.include("02/15/2026");
      expect(matchingRows[0]?.textContent).to.include("Mortgage");
      expect(matchingRows[0]?.textContent).to.include("-$5,000");
    });

    cy.visit("/budgets");
    cy.get(
      '[data-cy="category-row"][data-row-key="00000000-0000-0000-0000-000000000011"]',
    ).click();
    cy.get('[data-cy="full-screen-trouser-root"]')
      .should("contain", "Mortgage")
      .and("contain", "-$5,000.00")
      .and("contain", "$0.00");
    cy.get('[data-cy="full-screen-trouser-root"]')
      .contains('[role="tab"]', "Spending history")
      .click();
    cy.get('[data-cy="category-spending-history"]')
      .should("contain", "Checking")
      .and("contain", "February mortgage payment")
      .and("contain", "-$5,000.00");

    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000501");
    cy.get('[data-cy="loan-escrow-section"]').should("contain", "$4,000");
    cy.get('[data-cy="account-detail-reconcile-loan"]').click();
    cy.get('input[name="loan-principal"]').clear().type("198000");
    cy.get('input[name="loan-escrow"]').should("have.value", "4000");
    cy.intercept("POST", "**/loan-snapshots").as("reconcileLoan");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Apply statement")
      .click();
    cy.wait("@reconcileLoan").its("response.statusCode").should("equal", 200);

    cy.get('[data-cy="loan-summary-section"]')
      .should("contain", "$198,000.00")
      .and("contain", "$2,000.00")
      .and("contain", "$3,000.00");
    cy.get('[data-cy="loan-escrow-section"]').should("contain", "$4,000.00");
    cy.get('[data-cy="loan-estimate-section"]').should(
      "contain",
      "Estimated amortization",
    );

    cy.visit("/assets-liabilities");
    cy.get(
      '[data-cy="assets-liabilities-group"][data-group-key="loans"]',
    ).should("contain", "$198,000");
    cy.get(
      '[data-cy="assets-liabilities-group"][data-group-key="restricted-assets"]',
    ).should("contain", "$4,000");
    cy.get('[data-cy="metric-net-worth"]').should("contain", "-$179,000");
  });
});

describe("Tracking cutover", () => {
  let transactionsBefore = 0;
  let allocationsBefore = 0;

  beforeEach(() => {
    cy.resetScenario("tracking-cutover");
    const apiBaseUrl = String(Cypress.env("apiBaseUrl")).replace(/\/$/, "");
    cy.request(`${apiBaseUrl}/api/transactions?limit=10`).then((response) => {
      transactionsBefore = response.body.total;
    });
    cy.request(`${apiBaseUrl}/api/allocations`).then((response) => {
      allocationsBefore = response.body.items.length;
    });
    cy.visit("/assets-liabilities/00000000-0000-0000-0000-000000000201");
    cy.get('[data-cy="account-detail-page"]').should("be.visible");
  });

  it("AL-07 replaces one tracking asset with three signed successors", () => {
    cy.get('[data-cy="metric-value"]').should("contain", "$500,000");
    cy.get('[data-cy="account-detail-create-richer"]').click();
    cy.get('[data-cy="cutover-successor"]').should("have.length", 1);

    cy.get('input[name="cutover-name-0"]').clear().type("Brokerage");
    cy.get('input[name="cutover-opening-0"]').clear().type("200000");
    cy.get('input[name="cutover-final-tracking-value"]').type("500000");

    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Add successor")
      .click();
    cy.get('select[name="cutover-type-1"]').select("TANGIBLE_ASSET");
    cy.get('input[name="cutover-name-1"]').clear().type("Rental property");
    cy.get('input[name="cutover-opening-1"]').type("350000");

    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Add successor")
      .click();
    cy.get('select[name="cutover-type-2"]').select("LOAN");
    cy.get('input[name="cutover-name-2"]').clear().type("Mortgage");
    cy.get('input[name="cutover-opening-2"]').type("50000");
    cy.get('select[name="cutover-category-2"]').select(
      "00000000-0000-0000-0000-000000000011",
    );

    cy.get('[data-cy="cutover-successor"]').should("have.length", 3);
    cy.get('[data-cy="form-modal-root"]')
      .should("contain", "Successor total: $500,000.00")
      .and("contain", "Exact match");

    cy.intercept("POST", "**/cutovers").as("applyCutover");
    cy.get('[data-cy="form-modal-root"]')
      .contains("button", "Apply cutover")
      .click();
    cy.wait("@applyCutover").its("response.statusCode").should("equal", 200);

    cy.visit("/assets-liabilities");
    cy.get('[data-cy="assets-liabilities-groups"]').should(
      "not.contain",
      "Legacy portfolio",
    );
    const successors = [
      ["investments", "Brokerage", "$200,000"],
      ["tangible-assets", "Rental property", "$350,000"],
      ["loans", "Mortgage", "$50,000"],
    ];
    successors.forEach(([group, name, value]) => {
      cy.get(`[data-cy="assets-liabilities-group"][data-group-key="${group}"]`)
        .find('[data-cy="assets-liabilities-row"]')
        .should("have.length", 1)
        .and("contain", name)
        .and("contain", value);
    });
    cy.get('[data-cy="metric-net-worth"]').should("contain", "$520,000");

    cy.reload();
    successors.forEach(([group]) => {
      cy.get(`[data-cy="assets-liabilities-group"][data-group-key="${group}"]`)
        .find('[data-cy="assets-liabilities-row"]')
        .should("have.length", 1);
    });

    const apiBaseUrl = String(Cypress.env("apiBaseUrl")).replace(/\/$/, "");
    cy.request(`${apiBaseUrl}/api/transactions?limit=10`)
      .its("body.total")
      .should("equal", transactionsBefore);
    cy.request(`${apiBaseUrl}/api/allocations`)
      .its("body.items")
      .should("have.length", allocationsBefore);
  });
});
