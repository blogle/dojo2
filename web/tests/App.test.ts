import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../src/dojo/App.vue";
import { router } from "../src/dojo/router";
import { useAppState } from "../src/dojo/state/app";

function stubApi(ready: boolean): void {
  const budgetResponse = {
    month: "2026-02",
    available_to_budget_minor: 404000,
    summary: {
      month_activity_minor: -7000,
      month_budgeted_minor: 18000,
      carried_over_minor: 49000,
      reportable_income_minor: 100000,
      spent_minor: 7000,
    },
    groups: [
      {
        group_id: "group-1",
        name: "Living",
        sort_order: 10,
        is_hidden: false,
        is_system: false,
        is_deletable: true,
        categories: [
          {
            category_id: "cat-1",
            bucket_id: "bucket-1",
            group_id: "group-1",
            group_name: "Living",
            name: "Grocery",
            category_kind: "STANDARD",
            sort_order: 10,
            is_hidden: false,
            is_active: true,
            target_amount_minor: 0,
            due_date_rule: null,
            available_minor: 20000,
            month_activity_minor: 0,
            month_budgeted_minor: 10000,
            carried_over_minor: 10000,
          },
        ],
      },
    ],
  };

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string) => {
      if (input.includes("/api/app/status")) {
        return { ok: true, json: async () => ({ app: "dojo", ready, mode: ready ? "ready" : "onboarding", needs_onboarding: !ready, latest_import_batch: null, latest_import_run: null }) };
      }
      if (input.includes("/api/bootstrap")) {
        return {
          ok: true,
          json: async () => ({
            app_status: { app: "dojo", ready, mode: ready ? "ready" : "onboarding", needs_onboarding: !ready, latest_import_batch: null, latest_import_run: null },
            import_status: null,
            accounts: [],
            category_groups: budgetResponse.groups,
            categories: budgetResponse.groups[0].categories,
            budget_buckets: [],
            current_atb_minor: 404000,
            current_budget_month_summary: budgetResponse.summary,
            recent_transactions: [{ date: "2026-02-03" }],
          }),
        };
      }
      if (input.includes("/api/budget")) {
        return { ok: true, json: async () => budgetResponse };
      }
      if (input.includes("/api/transactions")) {
        return { ok: true, json: async () => ({ items: [] }) };
      }
      if (input.includes("/api/accounts")) {
        return { ok: true, json: async () => ({ items: [] }) };
      }
      if (input.includes("/api/net-worth")) {
        return { ok: true, json: async () => ({ current_net_worth_minor: 0, items: [] }) };
      }
      if (input.includes("/api/categories")) {
        return { ok: true, json: async () => ({ groups: budgetResponse.groups, items: budgetResponse.groups[0].categories }) };
      }
      return { ok: true, json: async () => ({}) };
    }),
  );
}

describe("dojo app", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    useAppState().resetState();
  });

  it("renders onboarding when the app is not ready", async () => {
    stubApi(false);
    router.push("/onboarding");
    await router.isReady();

    const wrapper = mount(App, {
      global: { plugins: [router] },
    });

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain("Dojo onboarding");
    });
  });

  it("renders budget data when the app is ready", async () => {
    stubApi(true);
    router.push("/budget");
    await router.isReady();

    const wrapper = mount(App, {
      global: { plugins: [router] },
    });

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain("Budget");
      expect(wrapper.text()).toContain("Available To Budget");
      expect(wrapper.text()).toContain("Grocery");
    });
  });
});
