import { VueQueryPlugin } from "@tanstack/vue-query";
import { mount } from "cypress/vue";
import { createMemoryHistory, createRouter, RouterView } from "vue-router";

import AppShell from "../../src/dojo/layouts/AppShell.vue";
import AssetsLiabilitiesLayout from "../../src/dojo/layouts/AssetsLiabilitiesLayout.vue";
import AccountDetailPage from "../../src/dojo/pages/AccountDetailPage.vue";
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
        groups: [],
      });
    }

    if (path === "/api/accounts") {
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

    if (path === "/api/allocations" || path === "/api/category-activity") {
      return response({ items: [] });
    }

    if (path === "/api/net-worth") {
      return response({ current_net_worth_minor: 100000, items: [] });
    }

    return response({});
  });
}

const surfaces = [
  {
    name: "Budget",
    path: "/budgets",
    selector: "[data-cy=budgets-page-root]",
  },
  {
    name: "Transactions",
    path: "/transactions",
    selector: "[data-cy=transactions-page-root]",
  },
  {
    name: "Assets & Liabilities",
    path: "/assets-liabilities",
    selector: "[data-cy=assets-liabilities-page]",
  },
  {
    name: "Account detail",
    path: "/assets-liabilities/account-1",
    selector: "[data-cy=account-detail-page]",
  },
] as const;

function mountShell(path: string) {
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
              { path: ":id", component: AccountDetailPage },
            ],
          },
        ],
      },
    ],
  });

  router.push(path);
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
}

describe("AppShell document overflow", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
  });

  surfaces.forEach((surface) => {
    [1200, 1440].forEach((width) => {
      [false, true].forEach((expanded) => {
        it(`${surface.name} at ${width}px with the rail ${expanded ? "expanded" : "collapsed"} has no document overflow`, () => {
          cy.viewport(width, 900);
          mountShell(surface.path);

          cy.get(surface.selector).should("be.visible");
          if (expanded) {
            cy.get('[data-cy="navigation-rail-toggle"]').click();
            cy.get('[data-cy="app-shell"]').should(
              "have.class",
              "app-shell--expanded",
            );
          }

          cy.document().should((document) => {
            expect(document.documentElement.scrollWidth).to.be.at.most(
              document.documentElement.clientWidth,
            );
          });
        });
      });
    });
  });
});
