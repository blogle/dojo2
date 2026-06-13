import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TransactionEntryBar from "../src/dojo/components/TransactionEntryBar.vue";
import TransactionStatusToggle from "../src/dojo/components/TransactionStatusToggle.vue";
import VirtualTransactionTable from "../src/dojo/components/VirtualTransactionTable.vue";
import {
  sampleAccounts,
  sampleCategories,
  sampleTransactions,
} from "./helpers";

describe("transaction components", () => {
  it("submits a valid transaction payload", async () => {
    const wrapper = mount(TransactionEntryBar, {
      props: {
        accounts: sampleAccounts,
        categories: sampleCategories,
        showHidden: false,
        editingTransaction: {
          ...sampleTransactions[0],
          memo: "groceries",
          amount_minor: -1234,
        },
      },
    });

    await wrapper.get("form").trigger("submit.prevent");

    expect(wrapper.emitted("submit")?.[0]?.[0]).toMatchObject({
      account_id: "account-1",
      amount_minor: -1234,
      category_id: "cat-1",
      status: "CLEARED",
      memo: "groceries",
    });
  });

  it("emits status toggle", async () => {
    const wrapper = mount(TransactionStatusToggle, {
      props: { status: "PENDING" },
    });
    await wrapper.get("button").trigger("click");
    expect(wrapper.emitted("toggle")).toHaveLength(1);
  });

  it("renders only visible rows plus overscan", () => {
    const manyTransactions = Array.from({ length: 1000 }, (_, index) => ({
      ...sampleTransactions[0],
      transaction_id: `tx-${index}`,
      memo: `memo-${index}`,
    }));
    const wrapper = mount(VirtualTransactionTable, {
      props: { transactions: manyTransactions },
    });

    expect(wrapper.findAll("[data-transaction-id]").length).toBeLessThan(40);
  });
});
