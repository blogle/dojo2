import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import entryFixtures from "../src/dojo/components/transactions/TransactionEntryForm.fixtures";
import TransactionEntryForm from "../src/dojo/components/transactions/TransactionEntryForm.vue";

function fixtureProps() {
  return entryFixtures.scenarios[0]?.props as InstanceType<
    typeof TransactionEntryForm
  >["$props"];
}

describe("TransactionEntryForm", () => {
  it("mounts with the fixture account selected by default", () => {
    const wrapper = mount(TransactionEntryForm, {
      props: fixtureProps(),
    });

    expect(wrapper.find('[data-cy="transaction-entry-form"]').exists()).toBe(
      true,
    );
    expect(
      wrapper.findAll('[data-cy="combobox-field-trigger"]')[0]?.text(),
    ).toContain("Maple Checking");
  });

  it("submits an Uncategorized transaction as the canonical system category", async () => {
    const wrapper = mount(TransactionEntryForm, {
      props: fixtureProps(),
    });
    const categoryTrigger = wrapper.findAll(
      '[data-cy="combobox-field-trigger"]',
    )[1];
    expect(categoryTrigger).toBeDefined();
    await categoryTrigger?.trigger("click");
    await flushPromises();
    const uncategorizedOption = wrapper
      .findAll('[role="option"]')
      .find((option) => option.text() === "Uncategorized");
    expect(uncategorizedOption).toBeDefined();
    await uncategorizedOption?.trigger("click");
    await wrapper.find('input[placeholder="0.00"]').setValue("32.00");
    const addButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "Add");
    expect(addButton).toBeDefined();
    await addButton?.trigger("click");

    expect(wrapper.emitted("submit")?.[0]?.[0]).toMatchObject({
      account_id: "account-maple-checking",
      amount_minor: -3_200,
      category_id: null,
      system_category: "TX_UNCATEGORIZED",
      status: "PENDING",
    });
  });

  it("explains missing entry fields before attempting a mutation", async () => {
    const wrapper = mount(TransactionEntryForm, {
      props: fixtureProps(),
    });
    const addButton = wrapper
      .findAll("button")
      .find((button) => button.text() === "Add");
    await addButton?.trigger("click");

    expect(wrapper.find('[role="alert"]').text()).toBe(
      "Enter a date, account, and amount.",
    );
    expect(wrapper.emitted("submit")).toBeUndefined();
  });
});
