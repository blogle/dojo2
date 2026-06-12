import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import AllocationPopover from "../src/dojo/components/AllocationPopover.vue";
import CategoryBudgetRow from "../src/dojo/components/CategoryBudgetRow.vue";
import CategoryGroupPanel from "../src/dojo/components/CategoryGroupPanel.vue";
import HiddenEntitiesToggle from "../src/dojo/components/HiddenEntitiesToggle.vue";
import ImportValidationReport from "../src/dojo/components/ImportValidationReport.vue";
import { sampleCategories, sampleGroup } from "./helpers";

describe("budget components", () => {
  it("renders categories in order", () => {
    const wrapper = mount(CategoryGroupPanel, {
      props: { group: sampleGroup, month: "2026-02", allCategories: sampleCategories },
    });

    expect(wrapper.text().indexOf("Grocery")).toBeLessThan(wrapper.text().indexOf("Hidden stash"));
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
          hard_failures: [{ label: "ATB mismatch" }],
          warnings: [{ message: "No live credentials" }],
          checks: [{ label: "accounts", passed: true }],
        },
      },
    });

    expect(wrapper.text()).toContain("ATB mismatch");
    expect(wrapper.text()).toContain("No live credentials");
    expect(wrapper.text()).toContain("accounts");
  });
});
