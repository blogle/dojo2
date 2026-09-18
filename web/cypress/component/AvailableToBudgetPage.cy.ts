import { mount } from "cypress/vue";
import { createRouter, createMemoryHistory } from "vue-router";
import { VueQueryPlugin } from "@tanstack/vue-query";

import AvailableToBudgetPage from "../../src/dojo/pages/AvailableToBudgetPage.vue";
import { createDojoQueryClient } from "../../src/dojo/queryClient";

const month = new Date().toISOString().slice(0, 7);

const summary = {
  available_to_budget_minor: 3565000,
  budget_month: month,
  as_of_date: "2026-09-17",
  temporal_scope: "current-state" as const,
  components: [
    {
      key: "transactions",
      label: "Available to budget transactions",
      amount_minor: 3620000,
      direction: "increases" as const,
      group_count: 1,
      contribution_count: 90,
    },
    {
      key: "allocations",
      label: "Category allocations",
      amount_minor: -55000,
      direction: "decreases" as const,
      group_count: 1,
      contribution_count: 2,
    },
  ],
};

const component = {
  ...summary,
  component: summary.components[0],
  groups: [
    {
      key: "checking",
      label: "Checking",
      amount_minor: 3620000,
      direction: "increases" as const,
      record_count: 90,
    },
  ],
};

function record(offset: number) {
  return {
    id: `transaction-${offset}`,
    kind: "transaction" as const,
    record_id: `transaction-${offset}`,
    version: `version-${offset}`,
    date: "2026-09-01",
    source_label: "Available to budget transaction",
    account_name: "Checking",
    category_name: null,
    memo: `Income ${offset}`,
    contribution_minor: offset === 0 ? 60000 : 40000,
  };
}

function stubFetch(
  override?: (path: string, url: URL) => Response | undefined,
) {
  cy.stub(window, "fetch").callsFake((input: string | URL) => {
    const url = new URL(input.toString(), "http://localhost");
    const overridden = override?.(url.pathname, url);
    if (overridden) return Promise.resolve(overridden);

    if (url.pathname === "/api/budget/available-to-budget-breakdown") {
      return Promise.resolve(jsonResponse(summary));
    }
    if (
      url.pathname === "/api/budget/available-to-budget-breakdown/transactions"
    ) {
      return Promise.resolve(jsonResponse(component));
    }
    if (
      url.pathname ===
      "/api/budget/available-to-budget-breakdown/transactions/records"
    ) {
      const offset = Number(url.searchParams.get("offset") ?? 0);
      const items =
        offset === 0
          ? Array.from({ length: 50 }, (_, index) => record(index))
          : Array.from({ length: 40 }, (_, index) => record(index + 50));
      return Promise.resolve(
        jsonResponse({
          ...summary,
          component: component.component,
          group: component.groups[0],
          items,
          total: 90,
          offset,
          limit: 50,
          has_more: offset === 0,
        }),
      );
    }
    return Promise.resolve(jsonResponse({}));
  });
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

let activeRouter: ReturnType<typeof createRouter>;

function mountPage(
  override?: (path: string, url: URL) => Response | undefined,
) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/budgets", component: { template: "<div>budget</div>" } },
      {
        path: "/budgets/available-to-budget",
        component: AvailableToBudgetPage,
      },
    ],
  });
  activeRouter = router;
  stubFetch(override);
  const queryClient = createDojoQueryClient();
  return cy
    .wrap(
      router.push({ path: "/budgets/available-to-budget", query: { month } }),
    )
    .then(() =>
      mount(AvailableToBudgetPage, {
        global: {
          plugins: [router, [VueQueryPlugin, { queryClient }]],
        },
      }),
    );
}

describe("AvailableToBudgetPage", () => {
  it("zooms between one explanation workspace at a time", () => {
    mountPage();

    cy.get("[data-cy=available-to-budget-level-1]")
      .should("contain.text", "$35,650.00")
      .and("not.contain.text", "Ties to total");
    cy.get("[data-cy=calculation-footer]")
      .should("have.length", 1)
      .and("contain.text", "Available to budget")
      .and("contain.text", "$35,650.00");
    cy.get("[data-cy=available-to-budget-level-2]").should("not.exist");
    cy.get("[data-cy=available-to-budget-level-3]").should("not.exist");
    cy.get("[data-cy=atb-record-row]").should("not.exist");

    cy.get("[data-cy=atb-component-transactions]").click();
    cy.get("[data-cy=available-to-budget-level-2]")
      .should("contain.text", "accounts")
      .should("contain.text", "Checking")
      .and("contain.text", "Largest contributors first");
    cy.get("[data-cy=calculation-footer]")
      .should("have.length", 1)
      .and("contain.text", "Component total")
      .and("contain.text", "$36,200.00");
    cy.get("[data-cy=available-to-budget-level-1]").should("not.exist");
    cy.get("[data-cy=available-to-budget-level-3]").should("not.exist");
    cy.get("[data-cy=atb-record-row]").should("not.exist");

    cy.get("[data-cy=atb-group-checking]").click();
    cy.get("[data-cy=available-to-budget-level-3]").should("be.visible");
    cy.get("[data-cy=available-to-budget-level-2]").should("not.exist");
    cy.get("[data-cy=atb-record-row]")
      .should("have.length.greaterThan", 0)
      .and("have.length.lessThan", 50);
    cy.get(".available-to-budget-page__ledger")
      .should("contain.text", "Entry")
      .and("not.contain.text", "Checking");
    cy.get("[data-cy=calculation-footer]")
      .should("contain.text", "Checking total")
      .and("contain.text", "$36,200.00");
    cy.get(".available-to-budget-page__ledger").scrollTo("bottom");
    cy.contains("Showing 90 of 90 source entries").should("be.visible");
  });

  it("uses bounded virtualized scrolling for a one-page source ledger", () => {
    const recordRequests: URL[] = [];
    const onePageRecords = Array.from({ length: 30 }, (_, index) =>
      record(index),
    );
    mountPage((path, url) => {
      if (path === "/api/budget/available-to-budget-breakdown/transactions") {
        return jsonResponse({
          ...component,
          groups: [{ ...component.groups[0], record_count: 30 }],
        });
      }
      if (
        path ===
        "/api/budget/available-to-budget-breakdown/transactions/records"
      ) {
        recordRequests.push(url);
        return jsonResponse({
          ...summary,
          component: component.component,
          group: { ...component.groups[0], record_count: 30 },
          items: onePageRecords,
          total: 30,
          offset: 0,
          limit: 50,
          has_more: false,
        });
      }
      return undefined;
    });

    cy.get("[data-cy=atb-component-transactions]").click();
    cy.get("[data-cy=atb-group-checking]").click();
    cy.get("[data-cy=atb-record-row]")
      .should("have.length.greaterThan", 0)
      .and("have.length.lessThan", 30);
    cy.wrap(null).should(() => {
      expect(recordRequests).to.have.length(1);
      expect(recordRequests[0].searchParams.get("limit")).to.equal("50");
    });
    cy.get(".available-to-budget-page__ledger").scrollTo("bottom");
    cy.wrap(null).should(() => expect(recordRequests).to.have.length(1));
  });

  it("keeps the summary context when a component request fails", () => {
    mountPage((path) => {
      if (path.endsWith("/transactions")) {
        return jsonResponse({ detail: "Temporary failure" }, 503);
      }
      return undefined;
    });

    cy.get("[data-cy=atb-component-transactions]").click();
    cy.get("[data-cy=available-to-budget-level-1]").should("not.exist");
    cy.get("[data-cy=available-to-budget-level-2]").should("be.visible");
    cy.get("[data-cy=available-to-budget-component-error]")
      .should("be.visible")
      .and("contain.text", "Temporary failure");
  });

  it("allows keyboard drill-down and preserves the budget context on back", () => {
    mountPage();

    cy.get("[data-cy=atb-component-transactions]").focus().type("{enter}");
    cy.get("[data-cy=available-to-budget-level-2]").should("be.visible");
    cy.contains("button", "Back to Budget").click();
    cy.wrap(null).should(() => {
      expect(activeRouter.currentRoute.value.path).to.equal("/budgets");
      expect(activeRouter.currentRoute.value.query.month).to.equal(month);
    });
  });

  it("shows an explicit zero explanation when no records contribute", () => {
    mountPage((path) => {
      if (path !== "/api/budget/available-to-budget-breakdown")
        return undefined;
      return jsonResponse({
        ...summary,
        available_to_budget_minor: 0,
        components: summary.components.map((item) => ({
          ...item,
          amount_minor: 0,
          direction: "neutral" as const,
          group_count: 0,
          contribution_count: 0,
        })),
      });
    });

    cy.get("[data-cy=available-to-budget-empty]")
      .should("be.visible")
      .and("contain.text", "no source entries contribute");
  });

  it("keeps a summary error local and retries the summary request", () => {
    let shouldFail = true;
    mountPage((path) => {
      if (path !== "/api/budget/available-to-budget-breakdown")
        return undefined;
      if (shouldFail) {
        return jsonResponse({ detail: "Temporary summary failure" }, 503);
      }
      return undefined;
    });

    cy.get("[data-cy=available-to-budget-summary-error]")
      .should("be.visible")
      .and("contain.text", "Temporary summary failure")
      .then(() => {
        shouldFail = false;
        cy.contains("button", "Retry").click();
      });
    cy.get("[data-cy=available-to-budget-level-1]").should("be.visible");
  });
});
