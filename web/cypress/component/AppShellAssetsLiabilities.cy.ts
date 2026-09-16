import { VueQueryPlugin } from "@tanstack/vue-query";
import { mount } from "cypress/vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";

import AppShell from "../../src/dojo/layouts/AppShell.vue";
import AssetsLiabilitiesLayout from "../../src/dojo/layouts/AssetsLiabilitiesLayout.vue";
import AccountDetailPage from "../../src/dojo/pages/AccountDetailPage.vue";
import AddItemWizardPage from "../../src/dojo/pages/AddItemWizardPage.vue";
import AssetsLiabilitiesPage from "../../src/dojo/pages/AssetsLiabilitiesPage.vue";
import BudgetsPage from "../../src/dojo/pages/BudgetsPage.vue";
import TransactionsPage from "../../src/dojo/pages/TransactionsPage.vue";
import { createDojoQueryClient } from "../../src/dojo/queryClient";

const account = {
  account_id: "account-1",
  name: "Checking",
  account_class: "BUDGET",
  institution: "Bank",
  account_number_last4: "1234",
  is_hidden: false,
  is_active: true,
  budget_account_type: "DEPOSIT",
  actual_balance_minor: 100000,
  pending_balance_minor: 0,
  cleared_balance_minor: 100000,
  display_balance_minor: 100000,
};

function response(body: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function stubFetch() {
  cy.stub(window, "fetch").callsFake((url: string) => {
    const path = new URL(url, "http://localhost").pathname;

    if (path === "/api/budget") {
      return response({
        month: "2026-09",
        available_to_budget_minor: 100000,
        summary: {
          month_activity_minor: 0,
          month_budgeted_minor: 0,
          starting_available_minor: 0,
          reportable_income_minor: 0,
          spent_minor: 0,
        },
        groups: [],
        unconfigured_goal_count: 0,
      });
    }

    if (path === "/api/assets-liabilities") {
      return response({
        assets_minor: 100000,
        liabilities_minor: 0,
        net_worth_minor: 100000,
        change_30d_minor: 0,
        needs_attention_count: 0,
        groups: [
          {
            key: "CASH",
            total_minor: 100000,
            items: [
              {
                ...account,
                value_minor: 100000,
                source_of_truth: "ledger",
                attention_status: "CURRENT",
                value_effective_date: "2026-09-16",
                change_30d_minor: 0,
              },
            ],
          },
        ],
      });
    }

    if (path === "/api/accounts" || path === "/api/accounts/") {
      return response({ items: [account] });
    }

    if (path === "/api/categories") {
      return response({ groups: [], items: [] });
    }

    if (path === "/api/transactions") {
      return response({
        items: [],
        total: 0,
        offset: 0,
        limit: 100,
        has_more: false,
        status_counts: { PENDING: 0, CLEARED: 0 },
      });
    }

    if (path.endsWith("/transactions/summary")) {
      return response({
        inflow_minor: 0,
        outflow_minor: 0,
        net_flow_minor: 0,
        transaction_count: 0,
        average_daily_balance_minor: 100000,
      });
    }

    if (path.endsWith("/balance-trend")) {
      return response({ points: [] });
    }

    if (path === "/api/allocations") {
      return response({ items: [] });
    }

    if (path === "/api/category-activity") {
      return response({ items: [] });
    }

    if (path === "/api/net-worth") {
      return response({ current_net_worth_minor: 100000, items: [] });
    }

    return response({});
  });
}

function mountShell(initialPath: string) {
  stubFetch();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/",
        component: AppShell,
        children: [
          { path: "budgets", component: BudgetsPage },
          { path: "transactions", component: TransactionsPage },
          {
            path: "assets-liabilities",
            component: AssetsLiabilitiesLayout,
            children: [
              { path: "", component: AssetsLiabilitiesPage },
              { path: "add", component: AddItemWizardPage },
              { path: ":id", component: AccountDetailPage },
            ],
          },
        ],
      },
    ],
  });

  router.push(initialPath);
  cy.wrap(router.isReady()).then(() => {
    mount(RouterView, {
      global: {
        plugins: [
          router,
          [VueQueryPlugin, { queryClient: createDojoQueryClient() }],
        ],
      },
    });
  });

  return router;
}

describe("Assets & Liabilities shell composition", () => {
  it("keeps the overview behind the Add Item wizard and returns to it on close", () => {
    const router = mountShell("/assets-liabilities/add");

    cy.get('[data-cy="add-item-wizard"]').should("be.visible");
    cy.get('[data-cy="assets-liabilities-page"]').should("be.visible");
    cy.get('[data-cy="navigation-rail-root"]').should("have.length", 1);

    cy.get('[data-cy="add-item-close"]').click();
    cy.wrap(router.currentRoute)
      .its("value.path")
      .should("eq", "/assets-liabilities");
    cy.get('[data-cy="add-item-wizard"]').should("not.exist");
    cy.get('[data-cy="assets-liabilities-page"]').should("be.visible");
  });
});
