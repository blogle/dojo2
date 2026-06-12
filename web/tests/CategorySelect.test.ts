import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CategoryOrSystemSelect from "../src/dojo/components/CategoryOrSystemSelect.vue";
import CategorySelect from "../src/dojo/components/CategorySelect.vue";
import { sampleCategories } from "./helpers";

describe("Category selectors", () => {
  it("hides hidden categories by default", () => {
    const wrapper = mount(CategorySelect, {
      props: { modelValue: "", categories: sampleCategories },
    });

    expect(wrapper.text()).toContain("Grocery");
    expect(wrapper.text()).not.toContain("Hidden stash");
  });

  it("can show hidden categories", () => {
    const wrapper = mount(CategorySelect, {
      props: { modelValue: "", categories: sampleCategories, showHidden: true },
    });

    expect(wrapper.text()).toContain("Hidden stash");
  });

  it("prevents invalid system category use by switching options", async () => {
    const wrapper = mount(CategoryOrSystemSelect, {
      props: {
        categories: sampleCategories,
        categoryId: "",
        systemCategory: "",
        useSystemCategory: false,
      },
    });

    expect(wrapper.text()).toContain("Grocery");
    expect(wrapper.text()).not.toContain("TX_ACCOUNT_TRANSFER");

    await wrapper.get('input[type="checkbox"]').setValue(true);
    expect(wrapper.emitted("update:useSystemCategory")?.[0]).toEqual([true]);
  });
});
