import { mount } from "cypress/vue";

import TransactionLedger from "../../src/dojo/components/transactions/TransactionLedger.vue";

const currentMonth = new Date().toISOString().slice(0, 7);

const mockAccounts = [
  {
    account_id: "acc1",
    name: "Checking",
    account_class: "BUDGET",
    is_hidden: false,
    is_active: true,
    actual_balance_minor: 100000,
    pending_balance_minor: 0,
    cleared_balance_minor: 100000,
    display_balance_minor: 100000,
  },
];

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
  },
];

const mockTransactions = [
  {
    transaction_id: "t1",
    date: `${currentMonth}-03`,
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
  {
    transaction_id: "t2",
    date: `${currentMonth}-05`,
    account_id: "acc1",
    account_name: "Checking",
    amount_minor: 12000,
    category_id: null,
    category_name: null,
    system_category: null,
    status: "PENDING",
    memo: "Paycheck",
    is_hidden_entity: false,
  },
];

describe("TransactionLedger", () => {
  it("renders transaction rows", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get("[data-cy=transaction-ledger]").should("be.visible");
    cy.get(".ledger__row").should("have.length", 2);
    // Read-only rows show display text
    cy.get(".ledger__row").first().should("contain.text", "Market");
    cy.get(".ledger__row").last().should("contain.text", "Paycheck");
  });

  it("shows transfer provenance when requested", () => {
    mount(TransactionLedger, {
      props: {
        transactions: [
          {
            ...mockTransactions[1],
            account_name: "Brokerage",
            amount_minor: 100000,
            system_category: "TX_ACCOUNT_TRANSFER",
            transfer_counterparty_account_name: "Checking",
          },
        ],
        accounts: mockAccounts,
        categories: mockCategories,
        showTransferProvenance: true,
      },
    });

    cy.get("[data-cy=transaction-transfer-provenance]").should(
      "contain.text",
      "Checking → Brokerage",
    );
  });

  it("enters edit mode on row click", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get(".ledger__row").first().click();
    cy.get(".ledger__row--editing").should("have.length", 1);
    // Editing row shows form fields — the memo field retains the original value
    cy.get(".ledger__row--editing input").should("exist");
  });

  it("commits edit on click outside the table", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get(".ledger__row").first().click();
    cy.get(".ledger__row--editing").should("exist");
    // Click outside the ledger entirely
    cy.get("body").click(10, 10);
    cy.get(".ledger__row--editing").should("not.exist");
  });

  it("cancels edit on Escape key", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get(".ledger__row").first().click();
    cy.get(".ledger__row--editing").should("exist");
    // Use {esc} — Cypress syntax for Escape
    cy.get("body").type("{esc}");
    cy.get(".ledger__row--editing").should("not.exist");
  });

  it("shows status pill in edit mode and toggles on click", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get(".ledger__row").first().click();
    cy.get(".ledger__row--editing").should("exist");
    cy.get(".ledger__status-pill").scrollIntoView();
    cy.get(".ledger__status-pill").should("be.visible");
    cy.get(".ledger__status-pill").should("contain.text", "Cleared");
    cy.get(".ledger__status-pill").click();
    cy.get(".ledger__status-pill").should("contain.text", "Pending");
    cy.get(".ledger__status-pill").click();
    cy.get(".ledger__status-pill").should("contain.text", "Cleared");
  });

  it("switches edit to a different row when another is clicked", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get(".ledger__row").first().click();
    cy.get(".ledger__row--editing").should("have.length", 1);
    cy.get(".ledger__row").last().click();
    cy.get(".ledger__row--editing").should("have.length", 1);
    // The second row's memo field should have "Paycheck"
    cy.get(".ledger__row--editing input[placeholder='Memo']").should(
      "have.value",
      "Paycheck",
    );
  });

  it("does not enter edit mode on click when no transactions", () => {
    mount(TransactionLedger, {
      props: {
        transactions: [],
        accounts: mockAccounts,
        categories: mockCategories,
      },
    });
    cy.get(".ledger__empty").should("contain.text", "No transactions found");
  });

  it("shows remove button in edit mode and emits remove on click", () => {
    mount(TransactionLedger, {
      props: {
        transactions: mockTransactions,
        accounts: mockAccounts,
        categories: mockCategories,
      },
    }).as("wrapper");
    cy.get(".ledger__row").first().click();
    cy.get(".ledger__row--editing").should("exist");
    // The × button replaces the status dot in the check column
    cy.get(".ledger__row--editing .ledger__remove-btn").should("be.visible");
    cy.get(".ledger__row--editing .ledger__remove-btn").click();
  });
});
