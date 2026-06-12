import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AllocationPopover from "../src/dojo/components/AllocationPopover.vue";
import AccountBalanceCard from "../src/dojo/components/AccountBalanceCard.vue";
import CategoryBudgetRow from "../src/dojo/components/CategoryBudgetRow.vue";
import CategoryGroupPanel from "../src/dojo/components/CategoryGroupPanel.vue";
import HiddenEntitiesToggle from "../src/dojo/components/HiddenEntitiesToggle.vue";
import ImportValidationReport from "../src/dojo/components/ImportValidationReport.vue";
import NetWorthPage from "../src/dojo/pages/NetWorthPage.vue";
import { useAppState } from "../src/dojo/state/app";
import { sampleAccounts, sampleCategories, sampleGroup } from "./helpers";

describe("budget components", () => {
  it("renders categories in order", () => {
    const wrapper = mount(CategoryGroupPanel, {
      props: { group: sampleGroup, month: "2026-02", allCategories: sampleCategories },
    });

    expect(wrapper.text().indexOf("Grocery")).toBeLessThan(wrapper.text().indexOf("Hidden stash"));
    expect(wrapper.text()).toContain("Group Total");
    expect(wrapper.text()).toContain("Starting available");
    expect(wrapper.text()).not.toContain("Carried over");
    expect(wrapper.text()).toContain("$250.00");
  });

  it("opens allocation popover from category row", async () => {
    const wrapper = mount(CategoryBudgetRow, {
      props: { category: sampleCategories[0], categories: sampleCategories, month: "2026-02" },
    });

    expect(wrapper.findComponent(AllocationPopover).exists()).toBe(false);
    await wrapper.get("button").trigger("click");
    expect(wrapper.findComponent(AllocationPopover).exists()).toBe(true);
  });

  it("submits fund, move, and return actions", async () => {
    const wrapper = mount(AllocationPopover, {
      props: { category: sampleCategories[0], categories: sampleCategories, month: "2026-02" },
    });
    const buttons = () => wrapper.findAll("button");
    const emissions = () => (wrapper.emitted("submit") ?? []) as Array<Array<{ path: string }>>;

    await buttons()[0].trigger("click");
    await wrapper.get('input[type="text"]').setValue("$10.00");
    await buttons()[buttons().length - 1].trigger("click");
    expect(emissions()[0][0].path).toBe("/api/allocations/fund");

    await buttons()[1].trigger("click");
    await wrapper.get("select").setValue("cat-2");
    await buttons()[buttons().length - 1].trigger("click");
    expect(emissions()[1][0].path).toBe("/api/allocations/move");

    await buttons()[2].trigger("click");
    await buttons()[buttons().length - 1].trigger("click");
    expect(emissions()[2][0].path).toBe("/api/allocations/return-to-atb");
  });

  it("reveals hidden toggle state", async () => {
    const wrapper = mount(HiddenEntitiesToggle, { props: { modelValue: false } });
    await wrapper.get('input[type="checkbox"]').setValue(true);
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([true]);
  });

  it("separates hard failures from warnings", () => {
    const wrapper = mount(ImportValidationReport, {
      props: {
        report: {
          hard_failures: [{ label: "ATB mismatch", entity_name: "2026-02", absolute_delta_minor: 100 }],
          warnings: [{ message: "No live credentials" }],
          checks: [{ label: "accounts", entity_name: "Checking", passed: true, absolute_delta_minor: 0 }],
        },
      },
    });

    expect(wrapper.text()).toContain("ATB mismatch");
    expect(wrapper.text()).toContain("No live credentials");
    expect(wrapper.text()).toContain("accounts");
  });

  it("labels account balances and preserves liability display signs", () => {
    const wrapper = mount(AccountBalanceCard, {
      props: { account: sampleAccounts[1] },
    });

    expect(wrapper.text()).toContain("Balance");
    expect(wrapper.text()).toContain("$200.00");
    expect(wrapper.text()).toContain("Cleared -$200.00");
  });

  it("renders labeled net worth totals and ignored valuation sources", () => {
    const app = useAppState();
    app.resetState();
    app.state.netWorth = {
      current_net_worth_minor: 49469000,
      items: [
        {
          account_name: "Checking",
          net_worth_minor: 474000,
          source: "ledger",
          ignored_import_value: false,
        },
        {
          account_name: "Checking",
          net_worth_minor: 474000,
          source: "imported_valuation",
          ignored_import_value: true,
        },
      ],
    };

    const wrapper = mount(NetWorthPage);

    expect(wrapper.text()).toContain("Current net worth");
    expect(wrapper.text()).toContain("$494,690.00");
    expect(wrapper.text()).toContain("Ledger balance");
    expect(wrapper.text()).toContain("Imported valuation (ignored in total)");
  });
});
