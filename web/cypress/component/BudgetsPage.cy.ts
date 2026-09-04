import { mount } from "cypress/vue";
import { createRouter, createMemoryHistory } from "vue-router";
import { VueQueryPlugin } from "@tanstack/vue-query";

import BudgetsPage from "../../src/dojo/pages/BudgetsPage.vue";
import { createDojoQueryClient } from "../../src/dojo/queryClient";

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: "/", component: { template: "<div>home</div>" } },
    { path: "/budgets", component: BudgetsPage },
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
    underfunded_minor: 0,
  },
  {
    category_id: "c2",
    bucket_id: "b2",
    group_id: "g1",
    group_name: "Essentials",
    name: "Rent",
    category_kind: "STANDARD",
    sort_order: 1,
    is_hidden: false,
    is_active: true,
    target_amount_minor: null,
    due_date_rule: null,
    goal_type: null,
    goal_amount_minor: null,
    goal_frequency: null,
    goal_due_date: null,
    available_minor: 10000,
    month_activity_minor: -3000,
    month_budgeted_minor: 10000,
    starting_available_minor: 0,
    monthly_funding_minor: 0,
    linked_account_id: null,
    underfunded_minor: 0,
  },
];

const mockGroups = [
  { group_id: "g1", name: "Essentials", is_system: false, sort_order: 0 },
  { group_id: "g2", name: "Savings", is_system: false, sort_order: 1 },
];

const mockBudget = {
  month: currentMonth,
  available_to_budget_minor: 50000,
  overspent_minor: 0,
  underfunded_minor: 0,
  month_activity_minor: -12000,
  month_budgeted_minor: 50000,
  unconfigured_goal_count: 1,
  summary: { month_activity_minor: -12000, month_budgeted_minor: 50000 },
  groups: [
    {
      ...mockGroups[0],
      totals: {
        available_minor: 30000,
        month_activity_minor: -8000,
        month_budgeted_minor: 30000,
      },
      categories: mockCategories.filter((c) => c.group_id === "g1"),
    },
    {
      ...mockGroups[1],
      totals: {
        available_minor: 20000,
        month_activity_minor: -4000,
        month_budgeted_minor: 20000,
      },
      categories: [],
    },
  ],
};

const mockAllocations = [
  {
    allocation_id: "a1",
    date: "2026-06-01",
    from_bucket_id: "atb",
    to_bucket_id: "b1",
    from_bucket_name: "Available to budget",
    to_bucket_name: "Groceries",
    from_category_id: null,
    to_category_id: "c1",
    amount_minor: 20000,
    memo: "Monthly funding",
  },
];

const mockTransactions = [
  {
    transaction_id: "t1",
    date: "2026-06-03",
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

function stubFetch(
  responseOverride?: (path: string, init?: RequestInit) => Response | undefined,
) {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    const overridden = responseOverride?.(path, init);
    if (overridden) return Promise.resolve(overridden);
    let body: unknown;

    if (path === "/api/bootstrap") {
      body = {
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
      };
    } else if (path.startsWith("/api/budget")) {
      body = mockBudget;
    } else if (
      path === "/api/categories" ||
      path.startsWith("/api/categories?")
    ) {
      body = { groups: mockGroups, items: mockCategories };
    } else if (path.startsWith("/api/category-groups")) {
      body = mockGroups;
    } else if (path === "/api/category-activity") {
      body = {
        items: [
          {
            activity_id: mockTransactions[0].transaction_id,
            category_id: mockTransactions[0].category_id,
            date: mockTransactions[0].date,
            account_name: mockTransactions[0].account_name,
            amount_minor: mockTransactions[0].amount_minor,
            status: mockTransactions[0].status,
            memo: mockTransactions[0].memo,
            is_derived: false,
          },
          {
            activity_id: "derived-investment-contribution",
            category_id: mockTransactions[0].category_id,
            date: mockTransactions[0].date,
            account_name: "Brokerage",
            amount_minor: -10_000,
            status: "CLEARED",
            memo: "Investment contribution",
            is_derived: true,
          },
        ],
      };
    } else if (path.startsWith("/api/transactions")) {
      body = {
        items: mockTransactions,
        total: 1,
        offset: 0,
        limit: 20,
        has_more: false,
        status_counts: { PENDING: 0, CLEARED: 1 },
      };
    } else if (path.startsWith("/api/allocations")) {
      body = { items: mockAllocations };
    } else if (path.startsWith("/api/accounts")) {
      body = [];
    } else if (path.startsWith("/api/net-worth")) {
      body = { net_worth_minor: 0, by_account: [] };
    } else if (path === "/api/months") {
      body = [];
    } else {
      body = {};
    }

    return Promise.resolve(
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountPage(
  responseOverride?: (path: string, init?: RequestInit) => Response | undefined,
) {
  stubFetch(responseOverride);
  const queryClient = createDojoQueryClient();
  return mount(BudgetsPage, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  });
}

describe("BudgetsPage", () => {
  it("renders the budget page with navigation and header", () => {
    mountPage();
    cy.get("[data-cy=budgets-page-root]").should("be.visible");
    cy.get("[data-cy=navigation-rail-root]").should("be.visible");
    cy.get("[data-cy=page-header-root]").should("contain.text", "Budget");
  });

  it("displays metric strip with budget summary", () => {
    mountPage();
    cy.get("[data-cy=metric-strip-root]").should("be.visible");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Available to budget",
    );
  });

  it("displays the hierarchical category table", () => {
    mountPage();
    cy.get("[data-cy=hierarchical-category-table-root]").should("be.visible");
  });

  it("can toggle reorder mode", () => {
    mountPage();
    cy.contains("button", "Reorder").should("be.visible").click();
    cy.get("[data-cy=reorder-mode-banner-root]").should("be.visible");
    cy.contains("button", "Cancel").click();
    cy.get("[data-cy=reorder-mode-banner-root]").should("not.exist");
  });

  it("opens Add Group modal from dropdown", () => {
    mountPage();
    cy.get("[data-cy=dropdown-button-root] .dropdown-button__toggle").click();
    cy.get("[role=menu]")
      .should("be.visible")
      .contains("Add category group")
      .click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Add category group",
    );
  });

  it("opens Add Category modal from dropdown", () => {
    mountPage();
    cy.get("[data-cy=dropdown-button-root] .dropdown-button__toggle").click();
    cy.get("[role=menu]").should("be.visible").contains("Add category").click();
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Add category");
  });

  it("opens Retired categories modal", () => {
    mountPage();
    cy.contains("button", "Retired categories").click();
    cy.get("[data-cy=large-detail-modal-root]").should(
      "contain.text",
      "Retired",
    );
  });

  it("opens category review from the unconfigured goals warning", () => {
    mountPage();
    cy.get("[data-cy=hierarchical-category-table-root]").should("be.visible");
    cy.contains("td", "Rent").should("be.visible");
    cy.contains("button", "Review categories").should("be.visible").click();
    cy.get("[data-cy=full-screen-trouser-root]").should("contain.text", "Rent");
    cy.get("[data-cy=full-screen-trouser-root]").should(
      "contain.text",
      "Goal progress",
    );
  });

  it("shows filtered funding and spending history in category detail", () => {
    mountPage();
    cy.contains("Groceries").click();
    cy.contains("button", "Funding history").click();
    cy.get("[data-cy=table-shell-root]").should(
      "contain.text",
      "Monthly funding",
    );
    cy.contains("button", "Spending history").click();
    cy.get("[data-cy=table-shell-root]").should("contain.text", "Market");
    cy.get("[data-cy=table-shell-root]").should(
      "contain.text",
      "Investment contribution",
    );
  });

  it("funds a category through a persisted allocation", () => {
    mountPage();
    cy.contains("Groceries").click();
    cy.contains("button", "Fund").click();
    cy.get("[data-cy=form-modal-root]").within(() => {
      cy.contains("label", "Funding option")
        .parent()
        .find("select")
        .select("custom");
      cy.contains("label", "Custom amount").parent().find("input").type("1000");
      cy.contains("button", "Save").click();
    });

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const fundingCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname === "/api/allocations/fund" &&
          call.args[1]?.method === "POST"
        );
      });
      expect(fundingCall).not.to.eq(undefined);
      const body = JSON.parse(fundingCall?.args[1]?.body as string);
      expect(body).to.include({
        category_id: "c1",
        amount_minor: 100_000,
      });
      expect(body.client_operation_id).to.be.a("string");
      expect(body.client_operation_id).not.to.equal("");
      const categoryUpdate = calls.find((call) =>
        new URL(call.args[0], "http://localhost").pathname.startsWith(
          "/api/categories/c1",
        ),
      );
      expect(categoryUpdate).to.eq(undefined);
    });
  });

  it("preserves the funding draft and operation id for a retry", () => {
    let fundingAttempts = 0;
    mountPage((path, init) => {
      if (path !== "/api/allocations/fund" || init?.method !== "POST") {
        return undefined;
      }
      fundingAttempts += 1;
      if (fundingAttempts === 1) {
        return new Response(JSON.stringify({ detail: "Temporary failure" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ allocation_id: "a2" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    cy.contains("Groceries").click();
    cy.contains("button", "Fund").click();
    cy.get("[data-cy=form-modal-root]").within(() => {
      cy.get("select").select("custom");
      cy.get("input").type("1000");
      cy.contains("button", "Save").click();
      cy.get("input").should("have.value", "1000");
      cy.contains("button", "Save").should("not.be.disabled").click();
    });

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      )
        .getCalls()
        .filter((call) => {
          const requestUrl = new URL(call.args[0], "http://localhost");
          return (
            requestUrl.pathname === "/api/allocations/fund" &&
            call.args[1]?.method === "POST"
          );
        });
      expect(calls).to.have.length(2);
      const firstBody = JSON.parse(calls[0].args[1]?.body as string);
      const secondBody = JSON.parse(calls[1].args[1]?.body as string);
      expect(secondBody.client_operation_id).to.equal(
        firstBody.client_operation_id,
      );
    });
  });

  it("moves funds through one persisted allocation", () => {
    mountPage();
    cy.contains("Groceries").click();
    cy.contains("button", "Move funds").click();
    cy.get("[data-cy=form-modal-root]").within(() => {
      cy.contains("label", "From").find("select").select("c1");
      cy.contains("label", "To").find("select").select("c2");
      cy.contains("label", "Amount").find("input").type("10");
      cy.contains("button", "Move funds").click();
    });
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const move = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return requestUrl.pathname === "/api/allocations/move";
      });
      expect(move).not.to.eq(undefined);
      const body = JSON.parse(move?.args[1]?.body as string);
      expect(body).to.include({
        from_bucket_id: "b1",
        to_bucket_id: "b2",
        amount_minor: 1_000,
      });
      expect(body.client_operation_id).to.be.a("string");
    });
  });

  it("opens category groups in the detail trouser", () => {
    mountPage();
    cy.contains("Essentials").click();
    cy.get("[data-cy=full-screen-trouser-root]").should(
      "contain.text",
      "Category group",
    );
    cy.get("[data-cy=full-screen-trouser-root]").should(
      "contain.text",
      "Goal progress",
    );
  });

  it("opens edit configuration from category detail", () => {
    mountPage();
    cy.contains("Groceries").click();
    cy.contains("button", "Edit configuration").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Edit category configuration",
    );
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Retire category",
    );
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Icon");
  });
});
