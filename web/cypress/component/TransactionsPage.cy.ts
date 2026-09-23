import { mount } from "cypress/vue";
import { createRouter, createMemoryHistory } from "vue-router";
import { VueQueryPlugin } from "@tanstack/vue-query";

import TransactionsPage from "../../src/dojo/pages/TransactionsPage.vue";
import { createDojoQueryClient } from "../../src/dojo/queryClient";

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: "/", component: { template: "<div>home</div>" } },
    { path: "/transactions", component: TransactionsPage },
    { path: "/dev/design-system", component: { template: "<div>ds</div>" } },
  ],
});

const currentMonth = new Date().toISOString().slice(0, 7);
const today = new Date();
const currentDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

const mockCategories = [
  {
    category_id: "c1",
    bucket_id: "b1",
    group_id: "g1",
    group_name: "Essentials",
    name: "Groceries",
    category_kind: "STANDARD",
    sort_order: 0,
    is_hidden: false,
    is_active: true,
    target_amount_minor: null,
    due_date_rule: null,
    goal_type: "RECURRING",
    goal_amount_minor: 15000,
    goal_frequency: "MONTHLY",
    goal_due_date: null,
    available_minor: 20000,
    month_activity_minor: -5000,
    month_budgeted_minor: 20000,
    starting_available_minor: 0,
    monthly_funding_minor: 15000,
    linked_account_id: null,
  },
];

const mockAccounts = [
  {
    account_id: "acc1",
    name: "Checking",
    account_class: "BUDGET",
    is_hidden: false,
    is_active: true,
    actual_balance_minor: 100000,
    pending_balance_minor: 0,
    cleared_balance_minor: 100000,
    display_balance_minor: 100000,
  },
  {
    account_id: "investment-1",
    name: "Brokerage",
    account_class: "INVESTMENT",
    is_hidden: false,
    is_active: true,
    actual_balance_minor: 0,
    pending_balance_minor: 0,
    cleared_balance_minor: 0,
    display_balance_minor: 0,
  },
  {
    account_id: "tracking-1",
    name: "Legacy Loan",
    account_class: "TRACKING",
    is_hidden: false,
    is_active: true,
    actual_balance_minor: 0,
    pending_balance_minor: 0,
    cleared_balance_minor: 0,
    display_balance_minor: 0,
  },
];

const mockTransactions = [
  {
    transaction_id: "t1",
    version: "11111111-1111-4111-8111-111111111111",
    date: `${currentMonth}-03`,
    account_id: "acc1",
    account_name: "Checking",
    amount_minor: -5000,
    category_id: "c1",
    category_name: "Groceries",
    system_category: null,
    status: "CLEARED",
    memo: "Market",
    is_hidden_entity: false,
  },
  {
    transaction_id: "t2",
    version: "22222222-2222-4222-8222-222222222222",
    date: `${currentMonth}-04`,
    account_id: "investment-1",
    account_name: "Brokerage",
    amount_minor: 10_000,
    category_id: null,
    category_name: null,
    system_category: "TX_ACCOUNT_TRANSFER",
    status: "PENDING",
    memo: "Investment contribution",
    is_hidden_entity: false,
  },
];

function stubFetch(
  override?: (path: string, init?: RequestInit) => Response | undefined,
) {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    const overridden = override?.(path, init);
    if (overridden) return Promise.resolve(overridden);

    if (path === "/api/bootstrap") {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            app_status: {
              app: "dojo",
              ready: true,
              mode: "lived",
              needs_onboarding: false,
              latest_import_batch: null,
              latest_import_run: null,
            },
            import_status: null,
            default_budget_month: currentMonth,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === "/api/transactions" || path.startsWith("/api/transactions?")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: mockTransactions,
            total: 2,
            offset: 0,
            limit: 10000,
            has_more: false,
            status_counts: { PENDING: 1, CLEARED: 1 },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === "/api/accounts" || path.startsWith("/api/accounts?")) {
      return Promise.resolve(
        new Response(JSON.stringify({ items: mockAccounts }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (path === "/api/categories" || path.startsWith("/api/categories?")) {
      return Promise.resolve(
        new Response(JSON.stringify({ groups: [], items: mockCategories }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (path.startsWith("/api/transactions/")) {
      return Promise.resolve(new Response(null, { status: 204, headers: {} }));
    }

    return Promise.resolve(
      new Response(JSON.stringify({}), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountPage(
  override?: (path: string, init?: RequestInit) => Response | undefined,
) {
  stubFetch(override);
  const queryClient = createDojoQueryClient();
  return mount(TransactionsPage, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  });
}

describe("TransactionsPage", () => {
  it("renders the page and header without owning navigation", () => {
    mountPage();
    cy.get("[data-cy=transactions-page-root]").should("be.visible");
    cy.get("[data-cy=navigation-rail-root]").should("not.exist");
    cy.get("[data-cy=page-header-root]").should("contain.text", "Transactions");
  });

  it("displays metric strip with inflow, outflow, and net", () => {
    mountPage();
    cy.get("[data-cy=metric-strip-root]").should("be.visible");
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Inflow");
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Outflow");
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Net");
  });

  it("displays the transaction ledger with fetched transactions", () => {
    mountPage();
    cy.get("[data-cy=transaction-ledger]").should("be.visible");
    cy.get("[data-cy=transaction-ledger]").should("contain.text", "Market");
  });

  it("shows the transaction entry form", () => {
    mountPage();
    cy.get("[data-cy=transaction-entry-form]").should("be.visible");
    cy.get("[data-cy=transaction-entry-form]").should(
      "contain.text",
      "Add transaction",
    );
  });

  it("shows the filter bar", () => {
    mountPage();
    cy.get("[data-cy=transaction-filter-bar]").should("be.visible");
  });

  it("removes Entry type and offers compatible counterparty accounts in transfer mode", () => {
    mountPage();
    cy.get("[data-cy=transaction-entry-form]").within(() => {
      cy.contains("label", "Entry type").should("not.exist");
      cy.contains("button", "Transaction").should("be.visible");
      cy.contains("button", "Transfer").click();
      cy.contains("label", "Account")
        .find("option")
        .should("contain.text", "Checking");
      cy.contains("label", "From account")
        .find("option")
        .should("not.contain.text", "Brokerage");
      cy.contains("label", "Counterparty")
        .find("option")
        .should("contain.text", "Brokerage");
      cy.contains("label", "Counterparty")
        .find("option")
        .should("not.contain.text", "Legacy Loan");
      cy.contains("label", "Category").should("not.exist");
    });
  });

  it("offers Available to budget as a category and submits its system semantic", () => {
    let submitted: Record<string, unknown> | undefined;
    mountPage((path, init) => {
      if (path === "/api/transactions" && init?.method === "POST") {
        submitted = JSON.parse(String(init.body)) as Record<string, unknown>;
        return new Response("{}", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return undefined;
    });
    cy.get("[data-cy=transaction-entry-form]").within(() => {
      cy.contains("label", "Category")
        .find("select")
        .select("__available_to_budget__");
      cy.contains("label", "Account").find("select").select("acc1");
      cy.contains("label", "Amount").find("input").type("12");
      cy.contains("label", "Memo").find("input").type("Budget adjustment");
      cy.contains("button", "Add").click();
    });
    cy.wrap(null).should(() => {
      expect(submitted).to.include({
        account_id: "acc1",
        category_id: null,
        system_category: "TX_AVAILABLE_TO_BUDGET",
      });
    });
  });

  it("submits an atomic transfer with inherited counterparty details", () => {
    let submitted: Record<string, unknown> | undefined;
    mountPage((path, init) => {
      if (path === "/api/transfers" && init?.method === "POST") {
        submitted = JSON.parse(String(init.body)) as Record<string, unknown>;
        return new Response("{}", {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      return undefined;
    });
    cy.get("[data-cy=transaction-entry-form]").within(() => {
      cy.contains("button", "Transfer").click();
      cy.contains("label", "From account").find("select").select("acc1");
      cy.contains("label", "Counterparty")
        .find("select")
        .select("investment-1");
      cy.contains("label", "Amount").find("input").type("25");
      cy.contains("label", "Status").find("select").select("CLEARED");
      cy.contains("label", "Memo").find("input").type("Move funds");
      cy.contains("button", "Counterparty details").click();
      cy.contains("label", "Counterparty posted date")
        .find("input")
        .should("have.value", currentDate);
      cy.contains("label", "Counterparty status")
        .find("select")
        .should("have.value", "CLEARED");
      cy.contains("label", "Counterparty memo")
        .find("input")
        .should("have.value", "Move funds");
      cy.contains("label", "Counterparty status")
        .find("select")
        .select("PENDING");
      cy.contains("label", "Counterparty memo")
        .find("input")
        .clear()
        .type("Investment contribution");
      cy.contains("button", "Add").click();
    });
    cy.wrap(null).should(() => {
      expect(submitted).to.include({
        from_account_id: "acc1",
        to_account_id: "investment-1",
        amount_minor: 2500,
        source_date: submitted?.date,
        destination_date: submitted?.date,
        source_status: "CLEARED",
        destination_status: "PENDING",
        source_memo: "Move funds",
        destination_memo: "Investment contribution",
      });
    });
  });

  it("filters the all-activity ledger without hiding transfers by default", () => {
    mountPage();
    cy.get("[data-cy=transaction-row]").should("have.length", 2);
    cy.get("[data-cy=transaction-filter-bar]")
      .contains("label", "Activity")
      .find("select")
      .select("transfers");
    cy.get("[data-cy=transaction-row]").should("have.length", 1);
    cy.get("[data-cy=transaction-ledger]").should(
      "contain.text",
      "Investment contribution",
    );
  });

  it("retains a transaction draft until creation succeeds", () => {
    mountPage((path, init) => {
      if (path === "/api/transactions" && init?.method === "POST") {
        return new Response(JSON.stringify({ detail: "Temporary failure" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        });
      }
      return undefined;
    });
    cy.get("[data-cy=transaction-entry-form]").within(() => {
      cy.contains("label", "Account").find("select").select("acc1");
      cy.contains("label", "Category").find("select").select("c1");
      cy.contains("label", "Amount").find("input").type("12.34");
      cy.contains("label", "Memo").find("input").type("Keep this draft{enter}");
      cy.contains("label", "Amount")
        .find("input")
        .should("have.value", "12.34");
      cy.contains("label", "Memo")
        .find("input")
        .should("have.value", "Keep this draft");
    });
  });
});
