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
];

const mockTransactions = [
  {
    transaction_id: "t1",
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
];

function stubFetch() {
  cy.stub(window, "fetch").callsFake((url: string) => {
    const path = new URL(url, "http://localhost").pathname;

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
            total: 1,
            offset: 0,
            limit: 10000,
            has_more: false,
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
      return Promise.resolve(
        new Response(null, { status: 204, headers: {} }),
      );
    }

    return Promise.resolve(
      new Response(JSON.stringify({}), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountPage() {
  stubFetch();
  const queryClient = createDojoQueryClient();
  return mount(TransactionsPage, {
    global: {
      plugins: [
        router,
        [VueQueryPlugin, { queryClient }],
      ],
    },
  });
}

describe("TransactionsPage", () => {
  it("renders the page with navigation and header", () => {
    mountPage();
    cy.get("[data-cy=transactions-page-root]").should("be.visible");
    cy.get("[data-cy=navigation-rail-root]").should("be.visible");
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Transactions",
    );
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
});
