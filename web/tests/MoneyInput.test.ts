import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import MoneyInput from "../src/dojo/components/MoneyInput.vue";

describe("MoneyInput", () => {
  it("parses signed and currency-like values", async () => {
    const wrapper = mount(MoneyInput, {
      props: { modelValue: null, label: "Amount" },
    });

    await wrapper.get("input").setValue("-$12.34");
    const firstEmission = wrapper.emitted("update:modelValue") ?? [];
    expect(firstEmission[firstEmission.length - 1]).toEqual([-1234]);

    await wrapper.get("input").setValue("$1,234.56");
    const secondEmission = wrapper.emitted("update:modelValue") ?? [];
    expect(secondEmission[secondEmission.length - 1]).toEqual([123456]);
  });
});
