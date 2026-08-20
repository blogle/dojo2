import { VueQueryPlugin } from "@tanstack/vue-query";
import { mount } from "cypress/vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountDetailPage from "../../src/dojo/pages/AccountDetailPage.vue";
import AssetsLiabilitiesPage from "../../src/dojo/pages/AssetsLiabilitiesPage.vue";
import { createDojoQueryClient } from "../../src/dojo/queryClient";

const budgetAccount = {
  account_id: "acct-checking-1234",
  name: "Chase Checking",
  account_class: "BUDGET",
  is_hidden: false,
  is_active: true,
  budget_account_type: "DEPOSIT",
  linked_payment_category_id: null,
  actual_balance_minor: 684218,
  pending_balance_minor: 12543,
  cleared_balance_minor: 671675,
  display_balance_minor: 684218,
};

const transactions = [
  {
    transaction_id: "txn-1",
    date: "2026-06-02",
    account_id: budgetAccount.account_id,
    account_name: budgetAccount.name,
    amount_minor: -8743,
    category_id: "cat-groceries",
    category_name: "Groceries",
    system_category: null,
    status: "CLEARED",
    memo: "Whole Foods",
    is_hidden_entity: false,
  },
  {
    transaction_id: "txn-2",
    date: "2026-05-29",
    account_id: budgetAccount.account_id,
    account_name: budgetAccount.name,
    amount_minor: -12999,
    category_id: "cat-shopping",
    category_name: "Shopping",
    system_category: null,
    status: "PENDING",
    memo: "Household items",
    is_hidden_entity: false,
  },
  {
    transaction_id: "txn-other",
    date: "2026-06-01",
    account_id: "acct-savings-9999",
    account_name: "Savings",
    amount_minor: 10000,
    category_id: null,
    category_name: null,
    system_category: "TX_STARTING_BALANCE",
    status: "CLEARED",
    memo: "Other account",
    is_hidden_entity: false,
  },
];

function stubFetch() {
  cy.stub(window, "fetch").callsFake((url: string) => {
    const path = new URL(url, "http://localhost").pathname;

    if (path === "/api/accounts") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [budgetAccount] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (path === "/api/transactions") {
      const requestUrl = new URL(url, "http://localhost");
      const accountId = requestUrl.searchParams.get("account_id");
      const scopedTransactions = transactions.filter(
        (transaction) => !accountId || transaction.account_id === accountId,
      );
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: scopedTransactions,
            total: scopedTransactions.length,
            offset: 0,
            limit: 100,
            has_more: false,
            status_counts: { PENDING: 4, CLEARED: 42 },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    }

    if (path === "/api/categories") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], groups: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (
      path === `/api/accounts/${budgetAccount.account_id}/transactions/summary`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            inflow_minor: 100000,
            outflow_minor: -50000,
            net_flow_minor: 50000,
            transaction_count: 3,
            average_daily_balance_minor: 600000,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${budgetAccount.account_id}/balance-trend`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            points: [
              { date: "2026-06-01", balance_minor: 650000 },
              { date: "2026-06-30", balance_minor: 684218 },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${budgetAccount.account_id}`) {
      return Promise.resolve(
        new Response(JSON.stringify({ account_id: budgetAccount.account_id }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    return Promise.resolve(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountPage() {
  stubFetch();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${budgetAccount.account_id}`);
  cy.wrap(router.isReady());

  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  });
}

describe("AccountDetailPage", () => {
  it("renders the budget account detail contract", () => {
    mountPage();

    cy.get("[data-cy=account-detail-page]").should("be.visible");
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Chase Checking",
    );
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Budget account",
    );
    cy.get("[data-cy=account-detail-reconcile]").should("be.visible");
    cy.get("[data-cy=account-detail-edit-configuration]").should("be.visible");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Current balance",
    );
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "4 transactions",
    );
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "42 transactions",
    );
    cy.get("[data-cy=transactions-section]").should(
      "contain.text",
      "Transactions",
    );
    cy.get("[data-cy=transactions-section]").should("contain.text", "Memo");
    cy.get("[data-cy=transactions-section]").should(
      "contain.text",
      "Whole Foods",
    );
    cy.get("[data-cy=transactions-section]").should(
      "not.contain.text",
      "Other account",
    );
    cy.get("[data-cy=transaction-filter-bar]").should("be.visible");
    cy.get("[data-cy=transaction-ledger]").should("be.visible");
    cy.get("[data-cy=account-details-section]").should(
      "not.contain.text",
      "View budgeting details",
    );
    cy.get("[data-cy=reconciliation-section]").should(
      "contain.text",
      "View reconciliation",
    );
    cy.get("[data-cy=history-section]").should("not.exist");
    cy.get("[data-cy=configuration-section]").should("not.exist");
    cy.get("[data-cy=summary-section]").should(
      "contain.text",
      "Summary & notes",
    );
    cy.get("[data-cy=balance-trend-chart]").should("be.visible");
  });

  it("opens edit configuration and submits account metadata", () => {
    mountPage();

    cy.get("[data-cy=account-detail-edit-configuration]").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Edit account configuration",
    );
    cy.get('input[name="institution"]').type("Chase");
    cy.get("[data-cy=form-modal-root]").contains("Save").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const updateCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname === `/api/accounts/${budgetAccount.account_id}`
        );
      });
      expect(updateCall).not.to.eq(undefined);
      const body = JSON.parse(updateCall?.args[1]?.body as string);
      expect(body).to.include({ institution: "Chase" });
      expect(body).not.to.have.property("include_in_net_worth");
    });
  });
});

const trackingAccount = {
  account_id: "acct-tracking-0001",
  name: "Legacy Brokerage",
  account_class: "TRACKING",
  is_hidden: false,
  is_active: true,
  institution: null,
  account_number_last4: null,
  budget_account_type: null,
  linked_payment_category_id: null,
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 9843221,
  tracking_polarity: "ASSET",
  tracking_source: "import",
  latest_valuation_minor: 9843221,
  latest_valuation_date: "2026-06-02",
  current_value_minor: 9843221,
  net_worth_contribution_minor: 9843221,
  value_source: "imported_valuation",
  value_effective_date: "2026-06-02",
  reconciliation_status: "NOT_RECONCILED",
  metadata: '{"imported_from_net_worth": true}',
};

const trackingSnapshots = [
  {
    valuation_id: "snap-1",
    account_id: trackingAccount.account_id,
    effective_date: "2026-06-02",
    amount_minor: 9843221,
    notes: "",
  },
  {
    valuation_id: "snap-2",
    account_id: trackingAccount.account_id,
    effective_date: "2026-06-01",
    amount_minor: 9745108,
    notes: "",
  },
  {
    valuation_id: "snap-3",
    account_id: trackingAccount.account_id,
    effective_date: "2026-05-31",
    amount_minor: 9720433,
    notes: "",
  },
];

function stubTrackingFetch() {
  cy.stub(window, "fetch").callsFake((url: string) => {
    const path = new URL(url, "http://localhost").pathname;

    if (path === "/api/accounts") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [trackingAccount] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (
      path === `/api/accounts/${trackingAccount.account_id}/tracking-snapshots`
    ) {
      return Promise.resolve(
        new Response(JSON.stringify({ items: trackingSnapshots }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (
      path ===
      `/api/accounts/${trackingAccount.account_id}/transactions/summary`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            inflow_minor: 0,
            outflow_minor: 0,
            net_flow_minor: 0,
            transaction_count: 0,
            average_daily_balance_minor: 9843221,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${trackingAccount.account_id}/balance-trend`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            points: [
              { date: "2026-05-01", balance_minor: 9467130 },
              { date: "2026-06-02", balance_minor: 9843221 },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${trackingAccount.account_id}`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({ account_id: trackingAccount.account_id }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    return Promise.resolve(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountTrackingPage() {
  stubTrackingFetch();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${trackingAccount.account_id}`);
  cy.wrap(router.isReady());

  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  });
}

describe("AccountDetailPage — tracking account", () => {
  it("renders the tracking account detail contract", () => {
    mountTrackingPage();

    cy.get("[data-cy=account-detail-page]").should("be.visible");
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Legacy Brokerage",
    );
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Tracking account",
    );
    cy.get("[data-cy=account-detail-add-snapshot]").should("be.visible");
    cy.get("[data-cy=account-detail-create-richer]").should("be.visible");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Current value",
    );
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Polarity");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Latest snapshot",
    );
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Source / migration",
    );
    cy.get("[data-cy=tracking-import-banner]").should("be.visible");
    cy.get("[data-cy=snapshot-history-section]").should(
      "contain.text",
      "Snapshot history",
    );
    cy.get("[data-cy=snapshot-history-section]").should(
      "contain.text",
      "3 snapshots",
    );
    cy.get("[data-cy=tracking-summary-section]").should(
      "contain.text",
      "Valuation history",
    );
    cy.get("[data-cy=account-details-section]").should(
      "contain.text",
      "$98,432.21",
    );
    cy.get("[data-cy=migration-context-section]").should(
      "contain.text",
      "Migration / import context",
    );
    cy.get("[data-cy=migration-context-section]").should(
      "contain.text",
      "Aspire Budgeting",
    );
    cy.get("[data-cy=history-config-section]").should(
      "contain.text",
      "History / configuration",
    );
    cy.get("[data-cy=balance-trend-chart]").should("be.visible");
    cy.get("[data-cy=reconciliation-section]").should("not.exist");
    cy.get("[data-cy=transactions-section]").should("not.exist");
    cy.get("[data-cy=summary-section]").should("not.exist");
  });

  it("submits a tracking snapshot correction", () => {
    mountTrackingPage();

    cy.get("[data-cy=account-detail-add-snapshot]").click();
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Add snapshot");
    cy.get('input[name="value-date"]').should(
      "have.attr",
      "max",
      new Date().toISOString().slice(0, 10),
    );
    cy.get('input[name="value-amount"]').type("123.45");
    cy.get('input[name="value-notes"]').type("Statement correction");
    cy.get("[data-cy=form-modal-root]").contains("Save").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const snapshotCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${trackingAccount.account_id}/tracking-snapshots` &&
          call.args[1]?.method === "POST"
        );
      });
      expect(snapshotCall).not.to.eq(undefined);
      const body = JSON.parse(snapshotCall?.args[1]?.body as string);
      expect(body).to.include({
        amount_minor: 12345,
        source: "manual",
        notes: "Statement correction",
      });
    });
  });

  it("opens and closes the cutover modal", () => {
    mountTrackingPage();

    cy.get("[data-cy=account-detail-create-richer]").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Replace tracking account",
    );
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "representation change",
    );
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Entity type");
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Cutover date");
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Name");
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Opening cash balance",
    );
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Contribution category",
    );
    cy.contains("button", "Add successor").click();
    cy.get("[data-cy=cutover-successor]").should("have.length", 2);
    cy.get('select[name="cutover-type-1"]').select("TANGIBLE_ASSET");
    cy.get('input[name="cutover-opening-1"]').type("100");
    cy.get("[data-cy=form-modal-root]").contains("Apply cutover").click();
    cy.get("[data-cy=form-modal-root]").should("not.exist");
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const cutoverCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${trackingAccount.account_id}/cutovers` &&
          call.args[1]?.method === "POST"
        );
      });
      expect(cutoverCall).not.to.eq(undefined);
      const body = JSON.parse(cutoverCall?.args[1]?.body as string);
      expect(body.successors).to.have.length(2);
      expect(body.successors[1]).to.include({
        account_class: "TANGIBLE_ASSET",
        opening_value_minor: 10_000,
      });
    });
  });
});

const tangibleAccount = {
  account_id: "acct-tangible-0001",
  name: "Home",
  account_class: "TANGIBLE_ASSET",
  is_hidden: false,
  is_active: true,
  institution: null,
  account_number_last4: null,
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 0,
  current_value_minor: 42500000,
  net_worth_contribution_minor: 42500000,
  value_source: "manual_valuation",
  value_effective_date: "2026-06-02",
  reconciliation_status: "NOT_RECONCILED",
};

function mountTangiblePage() {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    if (path === "/api/accounts") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [tangibleAccount] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
    if (
      path === `/api/accounts/${tangibleAccount.account_id}/tangible-valuations`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify(
            init?.method === "POST"
              ? { valuation_id: "valuation-new" }
              : {
                  items: [
                    {
                      valuation_id: "valuation-1",
                      account_id: tangibleAccount.account_id,
                      effective_date: "2026-06-02",
                      amount_minor: 42500000,
                      source: "manual",
                      notes: "County assessment",
                    },
                  ],
                },
          ),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (path.endsWith("/transactions/summary")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            inflow_minor: 0,
            outflow_minor: 0,
            net_flow_minor: 0,
            transaction_count: 1,
            average_daily_balance_minor: 42500000,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (path.endsWith("/balance-trend")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            points: [{ date: "2026-06-02", balance_minor: 42500000 }],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (path === "/api/transactions") {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: [],
            total: 0,
            offset: 0,
            limit: 100,
            has_more: false,
            status_counts: { PENDING: 0, CLEARED: 0 },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    return Promise.resolve(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${tangibleAccount.account_id}`);
  cy.wrap(router.isReady());
  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: { plugins: [router, [VueQueryPlugin, { queryClient }]] },
  });
}

describe("AccountDetailPage — tangible asset", () => {
  it("renders valuation history and submits a valuation", () => {
    mountTangiblePage();

    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Tangible asset",
    );
    cy.get("[data-cy=snapshot-history-section]").should(
      "contain.text",
      "Valuation history",
    );
    cy.get("[data-cy=transactions-section]").should("not.exist");
    cy.get("[data-cy=account-detail-add-snapshot]").should(
      "contain.text",
      "Add valuation",
    );
    cy.get("[data-cy=account-detail-add-snapshot]").click();
    cy.get('input[name="value-amount"]').type("430000");
    cy.get("[data-cy=form-modal-root]").contains("Save").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const valuationCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${tangibleAccount.account_id}/tangible-valuations` &&
          call.args[1]?.method === "POST"
        );
      });
      const body = JSON.parse(valuationCall?.args[1]?.body as string);
      expect(body).to.include({ amount_minor: 43000000, source: "manual" });
    });
  });
});

const loanAccount = {
  account_id: "acct-loan-0001",
  name: "Mortgage",
  account_class: "LOAN",
  is_hidden: false,
  is_active: true,
  institution: "Chase",
  account_number_last4: "1234",
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 0,
  current_value_minor: 19_900_000,
  net_worth_contribution_minor: -18_650_000,
  value_source: "loan_statement",
  value_effective_date: "2026-06-01",
  reconciliation_status: "CURRENT",
  loan_rate_minor: 600,
  loan_rate_type: "FIXED",
  loan_scheduled_principal_interest_minor: 200_000,
  loan_payment_frequency: "MONTHLY",
  loan_next_payment_date: "2026-07-01",
  loan_remaining_term_months: 120,
};

function mountLoanPage() {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    let body: unknown = { items: [] };
    if (path === "/api/accounts") {
      body = {
        items: [
          loanAccount,
          {
            ...budgetAccount,
            account_id: "acct-cash-0001",
            name: "Checking",
          },
        ],
      };
    } else if (path === "/api/categories") {
      body = {
        groups: [],
        items: [
          {
            category_id: "cat-mortgage",
            name: "Mortgage payment",
            category_kind: "STANDARD",
            available_minor: 250_000,
          },
        ],
      };
    } else if (path.endsWith("/budget-links")) {
      body = {
        items: [
          {
            account_id: loanAccount.account_id,
            category_id: "cat-mortgage",
            link_behavior: "LOAN_PAYMENT",
            derivation_method: "TRANSFER_IN_ONLY",
            effective_date: "2026-01-01",
          },
        ],
      };
    } else if (path.endsWith("/loan-snapshots")) {
      body = {
        items: [
          {
            snapshot_id: "loan-snapshot-1",
            account_id: loanAccount.account_id,
            effective_date: "2026-06-01",
            principal_balance_minor: 19_800_000,
            accrued_interest_minor: 100_000,
            escrow_balance_minor: 1_200_000,
            unapplied_credit_minor: 50_000,
            ytd_principal_paid_minor: 200_000,
            ytd_interest_paid_minor: 300_000,
            attributed_payment_minor: 500_000,
            principal_reduction_minor: 200_000,
            unknown_nonprincipal_minor: 300_000,
            notes: "",
          },
        ],
      };
    } else if (path.endsWith("/loan-projection")) {
      body = {
        available: true,
        missing: [],
        rate_assumption: "Current fixed rate",
        estimated_accrued_interest_minor: 32_548,
        projected_payoff_date: "2036-05-01",
        projected_total_interest_minor: 4_000_000,
        remaining_principal_at_horizon_minor: 0,
        rows: [
          {
            payment_number: 1,
            payment_date: "2026-07-01",
            payment_minor: 200_000,
            principal_minor: 101_000,
            interest_minor: 99_000,
            remaining_principal_minor: 19_699_000,
          },
        ],
      };
    } else if (path.endsWith("/loan-payments")) {
      body =
        init?.method === "POST"
          ? { transaction_id: "payment-new" }
          : { items: [] };
    } else if (path.endsWith("/transactions/summary")) {
      body = {
        inflow_minor: 0,
        outflow_minor: 0,
        net_flow_minor: 0,
        transaction_count: 0,
        average_daily_balance_minor: 0,
      };
    } else if (path.endsWith("/balance-trend")) {
      body = { points: [] };
    } else if (path === "/api/transactions") {
      body = {
        items: [],
        total: 0,
        offset: 0,
        limit: 100,
        has_more: false,
        status_counts: { PENDING: 0, CLEARED: 0 },
      };
    }
    return Promise.resolve(
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${loanAccount.account_id}`);
  cy.wrap(router.isReady());
  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: { plugins: [router, [VueQueryPlugin, { queryClient }]] },
  });
}

describe("AccountDetailPage — loan", () => {
  it("separates actual, restricted, estimated, and payment configuration", () => {
    mountLoanPage();

    cy.get("[data-cy=loan-summary-section]").should(
      "contain.text",
      "Lender actual and balance-derived",
    );
    cy.get("[data-cy=loan-escrow-section]").should(
      "contain.text",
      "Restricted escrow asset",
    );
    cy.get("[data-cy=loan-estimate-section]").should(
      "contain.text",
      "Next 12 estimated payments",
    );

    cy.get("[data-cy=account-detail-record-payment]").click();
    cy.get('select[name="loan-payment-category"]').should("not.exist");
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Payment category: Mortgage payment",
    );
    cy.get("[data-cy=form-modal-root]").contains("Cancel").click();

    cy.get("[data-cy=account-detail-reconcile-loan]").click();
    cy.get('input[name="loan-principal"]').should("be.visible");
    cy.get('input[name="loan-escrow"]').should("be.visible");
    cy.get('input[name="loan-interest"]').should("not.exist");
    cy.contains("button", "Show optional fields").click();
    cy.get('input[name="loan-interest"]').should("exist");
    cy.get('input[name="loan-ytd-interest"]').should("exist");
  });
});
