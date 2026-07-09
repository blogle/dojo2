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
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: transactions,
            total: 3,
            offset: 0,
            limit: 50,
            has_more: false,
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
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
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Current balance",
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
    cy.get("[data-cy=account-details-section]").should(
      "contain.text",
      "View budgeting details",
    );
    cy.get("[data-cy=reconciliation-section]").should(
      "contain.text",
      "View reconciliation",
    );
    cy.get("[data-cy=history-section]").should("contain.text", "View history");
    cy.get("[data-cy=configuration-section]").should(
      "contain.text",
      "Edit configuration",
    );
    cy.get("[data-cy=summary-section]").should(
      "contain.text",
      "Summary & notes",
    );
  });
});
