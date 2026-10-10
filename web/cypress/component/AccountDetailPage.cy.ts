import { VueQueryPlugin } from "@tanstack/vue-query";
import { defineComponent, h } from "vue";
import { mount } from "cypress/vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AccountDetailPage from "../../src/dojo/pages/AccountDetailPage.vue";
import AssetsLiabilitiesPage from "../../src/dojo/pages/AssetsLiabilitiesPage.vue";
import MutationFeedbackHost from "../../src/dojo/layouts/MutationFeedbackHost.vue";
import { createDojoQueryClient } from "../../src/dojo/queryClient";
import { useMutationFeedback } from "../../src/dojo/state/mutationFeedback";

const budgetAccount = {
  account_id: "acct-checking-1234",
  name: "Chase Checking",
  account_class: "BUDGET",
  is_hidden: false,
  is_active: true,
  budget_account_type: "DEPOSIT",
  linked_payment_category_id: null,
  actual_balance_minor: 684218,
  pending_balance_minor: 12543,
  cleared_balance_minor: 671675,
  display_balance_minor: 684218,
};

const transactions = [
  {
    transaction_id: "txn-1",
    version: "version-1",
    date: "2026-06-02",
    account_id: budgetAccount.account_id,
    account_name: budgetAccount.name,
    amount_minor: -8743,
    category_id: "cat-groceries",
    category_name: "Groceries",
    system_category: null,
    status: "CLEARED",
    memo: "Whole Foods",
    is_hidden_entity: false,
  },
  {
    transaction_id: "txn-2",
    version: "version-1",
    date: "2026-05-29",
    account_id: budgetAccount.account_id,
    account_name: budgetAccount.name,
    amount_minor: -12999,
    category_id: "cat-shopping",
    category_name: "Shopping",
    system_category: null,
    status: "PENDING",
    memo: "Household items",
    is_hidden_entity: false,
  },
  {
    transaction_id: "txn-uncategorized-legacy",
    version: "version-legacy",
    date: "2026-06-26",
    account_id: budgetAccount.account_id,
    account_name: budgetAccount.name,
    amount_minor: -3200,
    category_id: null,
    category_name: null,
    system_category: null,
    status: "PENDING",
    memo: "Uncategorized market purchase",
    is_hidden_entity: false,
  },
  {
    transaction_id: "txn-other",
    version: "version-1",
    date: "2026-06-01",
    account_id: "acct-savings-9999",
    account_name: "Savings",
    amount_minor: 10000,
    category_id: null,
    category_name: null,
    system_category: "TX_STARTING_BALANCE",
    status: "CLEARED",
    memo: "Other account",
    is_hidden_entity: false,
  },
];

function stubFetch(
  override?: (
    path: string,
    init?: RequestInit,
    requestUrl?: string,
  ) => Response | undefined,
) {
  let reconciliationCommitted = false;
  let reconciliationVoided = false;
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    const overridden = override?.(path, init, url);
    if (overridden) return Promise.resolve(overridden);

    if (path === "/api/accounts") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [budgetAccount] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (path === "/api/transactions") {
      const requestUrl = new URL(url, "http://localhost");
      const accountId = requestUrl.searchParams.get("account_id");
      const scopedTransactions = transactions.filter(
        (transaction) => !accountId || transaction.account_id === accountId,
      );
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: scopedTransactions,
            total: scopedTransactions.length,
            offset: 0,
            limit: 100,
            has_more: false,
            status_counts: { PENDING: 4, CLEARED: 42 },
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    }

    if (path === "/api/categories") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [], groups: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (path === `/api/accounts/${budgetAccount.account_id}/reconciliations`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: reconciliationCommitted
              ? [
                  {
                    reconciliation_id: "attempt-1",
                    evidence_id: "evidence-1",
                    committed_at: "2026-06-30T12:00:00Z",
                    entity_class: "BUDGET",
                    undone: reconciliationVoided,
                  },
                ]
              : [],
            history: reconciliationCommitted
              ? [
                  {
                    history_id: "history-commit",
                    event_type: "COMMITTED",
                    reconciliation_id: "attempt-1",
                    recorded_at: "2026-06-30T12:00:00Z",
                  },
                  ...(reconciliationVoided
                    ? [
                        {
                          history_id: "history-void",
                          event_type: "VOID",
                          reconciliation_id: "attempt-1",
                          recorded_at: "2026-06-30T12:01:00Z",
                        },
                      ]
                    : []),
                ]
              : [],
          }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    }

    if (path === "/api/reconciliations/attempt-1") {
      return Promise.resolve(
        jsonResponse({
          reconciliation_id: "attempt-1",
          committed_at: "2026-06-30T12:00:00Z",
          source_as_of: "2026-06-29T00:00:00Z",
          evidence: {
            evidence_kind: "BANK_STATEMENT",
            source_adapter: "manual",
            normalized_payload: {
              cleared_minor: 671675,
              pending_minor: 12543,
              actual_minor: 684218,
            },
            records: [],
          },
        }),
      );
    }

    if (
      path === `/api/accounts/${budgetAccount.account_id}/reconciliations/draft`
    ) {
      const body = JSON.parse(init?.body as string);
      const cleared =
        body.source_cleared_minor ??
        body.source_actual_minor - body.source_pending_minor;
      const pending =
        body.source_pending_minor ??
        body.source_actual_minor - body.source_cleared_minor;
      const actual =
        body.source_actual_minor ??
        body.source_cleared_minor + body.source_pending_minor;
      const clearedDelta = cleared - budgetAccount.cleared_balance_minor;
      const pendingDelta = pending - budgetAccount.pending_balance_minor;
      return Promise.resolve(
        new Response(
          JSON.stringify({
            reconciliation_id: "attempt-1",
            account_id: budgetAccount.account_id,
            state: "READY",
            cutoff: body.cutoff,
            source: {
              cleared_minor: cleared,
              pending_minor: pending,
              actual_minor: actual,
              derived:
                body.source_actual_minor === undefined ? "actual" : "pending",
            },
            dojo: {
              cleared_minor: budgetAccount.cleared_balance_minor,
              pending_minor: budgetAccount.pending_balance_minor,
              actual_minor: budgetAccount.display_balance_minor,
            },
            deltas: {
              cleared_delta_minor: clearedDelta,
              pending_delta_minor: pendingDelta,
              actual_delta_minor: clearedDelta + pendingDelta,
            },
            certification_allowed: clearedDelta === 0 && pendingDelta === 0,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/reconciliations/attempt-1/apply`) {
      reconciliationCommitted = true;
      return Promise.resolve(
        new Response(JSON.stringify({ state: "SUCCESSFUL" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (
      path ===
        `/api/accounts/${budgetAccount.account_id}/reconciliations/undo` &&
      init?.method === "POST"
    ) {
      reconciliationVoided = true;
      return Promise.resolve(
        new Response(
          JSON.stringify({
            account_id: budgetAccount.account_id,
            effective_reconciliation_id: null,
            items: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path.startsWith("/api/transactions/") && init?.method === "PUT") {
      return Promise.resolve(
        new Response(
          JSON.stringify({ transaction_id: "txn-1", version: "version-2" }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (
      path ===
      `/api/accounts/${budgetAccount.account_id}/reconciliation-working-set`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: [
              {
                transaction_id: "txn-1",
                classification: "EDITED",
                baseline: { amount_minor: -8743 },
                current: { amount_minor: -9000 },
                changed_fields: ["amount_minor"],
              },
              {
                transaction_id: "txn-2",
                classification: "CARRIED_PENDING",
                baseline: { status: "PENDING" },
                current: { status: "PENDING" },
                changed_fields: [],
              },
              {
                transaction_id: "txn-removed",
                classification: "REMOVED",
                baseline: {
                  date: "2026-05-18",
                  amount_minor: -4500,
                  memo: "Removed market row",
                  status: "CLEARED",
                },
                current: null,
                changed_fields: [],
              },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (
      path === `/api/accounts/${budgetAccount.account_id}/transactions/summary`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            inflow_minor: 100000,
            outflow_minor: -50000,
            net_flow_minor: 50000,
            transaction_count: 3,
            average_daily_balance_minor: 600000,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${budgetAccount.account_id}/balance-trend`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            points: [
              { date: "2026-06-01", balance_minor: 650000 },
              { date: "2026-06-30", balance_minor: 684218 },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${budgetAccount.account_id}`) {
      return Promise.resolve(
        new Response(JSON.stringify({ account_id: budgetAccount.account_id }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    return Promise.resolve(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountPage(
  override?: (
    path: string,
    init?: RequestInit,
    requestUrl?: string,
  ) => Response | undefined,
  stubs: Record<string, unknown> = {},
  includeFeedbackHost = false,
) {
  stubFetch(override);
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${budgetAccount.account_id}`);
  cy.wrap(router.isReady());

  const queryClient = createDojoQueryClient();
  const component = includeFeedbackHost
    ? AccountDetailPageWithFeedback
    : AccountDetailPage;
  mount(component, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
      stubs,
    },
  });
}

// This root keeps the global feedback host and page in the same test app.
// eslint-disable-next-line vue/one-component-per-file
const AccountDetailPageWithFeedback = defineComponent({
  name: "AccountDetailPageWithFeedback",
  setup: () => () => h("div", [h(AccountDetailPage), h(MutationFeedbackHost)]),
});

// eslint-disable-next-line vue/one-component-per-file
const accountEntryMutationStub = defineComponent({
  name: "TransactionEntryForm",
  emits: ["submit"],
  setup(_props, { emit, expose }) {
    expose({ resetForm: () => undefined });
    return () =>
      h(
        "button",
        {
          "data-cy": "test-create-account-transaction",
          onClick: () => emit("submit", accountEntryPayload),
        },
        "Create account transaction",
      );
  },
});

// These lightweight children isolate the page's mutation wiring from its input and ledger components.
// eslint-disable-next-line vue/one-component-per-file
const accountLedgerMutationStub = defineComponent({
  name: "TransactionLedger",
  props: { transactions: { type: Array, default: () => [] } },
  emits: ["commit", "remove", "loadMore"],
  setup(props, { emit }) {
    return () => {
      const transaction = (props.transactions as typeof transactions)[0];
      if (!transaction) return h("div", { "data-cy": "test-ledger-loading" });
      return h("div", [
        h(
          "button",
          {
            "data-cy": "test-edit-account-transaction",
            onClick: () =>
              emit(
                "commit",
                "txn-1",
                { ...accountEntryPayload, memo: "Edited account transaction" },
                () => undefined,
              ),
          },
          "Edit account transaction",
        ),
        h(
          "button",
          {
            "data-cy": "test-remove-account-transaction",
            onClick: () => emit("remove", transaction, () => undefined),
          },
          "Remove account transaction",
        ),
      ]);
    };
  },
});

const accountEntryPayload = {
  date: "2026-06-26",
  account_id: budgetAccount.account_id,
  amount_minor: -3200,
  category_id: "cat-groceries",
  system_category: null,
  status: "PENDING" as const,
  memo: "New account transaction",
};

function clearMutationFeedback() {
  const feedback = useMutationFeedback();
  while (feedback.notice.value) feedback.dismiss();
}

function feedbackNotice() {
  return useMutationFeedback().notice.value;
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("AccountDetailPage", () => {
  it("renders the budget account detail contract", () => {
    mountPage();

    cy.get("[data-cy=account-detail-page]").should("be.visible");
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Chase Checking",
    );
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Budget account",
    );
    cy.get("[data-cy=account-detail-reconcile]").should("be.visible");
    cy.get("[data-cy=account-detail-edit-configuration]").should("be.visible");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Current balance",
    );
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "4 transactions",
    );
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "42 transactions",
    );
    cy.get("[data-cy=transactions-section]").should(
      "contain.text",
      "Transactions",
    );
    cy.get("[data-cy=transactions-section]").should("contain.text", "Memo");
    cy.get("[data-cy=transactions-section]").should(
      "contain.text",
      "Whole Foods",
    );
    cy.get("[data-cy=transactions-section]").should(
      "not.contain.text",
      "Other account",
    );
    cy.get("[data-cy=transaction-filter-bar]").should("be.visible");
    cy.get("[data-cy=transaction-ledger]").should("be.visible");
    cy.get("[data-cy=account-details-section]").should("not.exist");
    cy.get("[data-cy=reconciliation-section]").should("not.exist");
    cy.get("[data-cy=reconciliation-history-section]").should("be.visible");
    cy.contains("Reconcile statement").should("not.exist");
    cy.contains("Apply statement").should("not.exist");
    cy.contains("View reconciliation").should("not.exist");
    cy.get("[data-cy=reconciliation-history-section]").should(
      "contain.text",
      "Never reconciled",
    );
    cy.get("[data-cy=account-detail-reconcile-loan]").should("not.exist");
    cy.get("[data-cy=account-detail-reconcile-investment]").should("not.exist");
    cy.contains("View reconciliation").should("not.exist");
    cy.contains("Apply statement").should("not.exist");
    cy.get("[data-cy=transaction-entry-form]").should("be.visible");
    cy.get("[data-cy=history-section]").should("not.exist");
    cy.get("[data-cy=configuration-section]").should("not.exist");
    cy.get("[data-cy=summary-section]").should(
      "contain.text",
      "Summary & notes",
    );
    cy.get("[data-cy=balance-trend-chart]").should("be.visible");
  });

  it("shows immutable evidence history and confirms latest-only undo", () => {
    mountPage((path) => {
      if (
        path === `/api/accounts/${budgetAccount.account_id}/reconciliations`
      ) {
        return jsonResponse({
          items: [
            {
              reconciliation_id: "committed-1",
              evidence_id: "evidence-1",
              committed_at: "2026-06-05T12:00:00Z",
              entity_class: "BUDGET",
            },
          ],
          history: [
            {
              history_id: "history-1",
              event_type: "COMMITTED",
              reconciliation_id: "committed-1",
              recorded_at: "2026-06-05T12:00:00Z",
            },
          ],
        });
      }
      if (path === "/api/reconciliations/committed-1") {
        return jsonResponse({
          reconciliation_id: "committed-1",
          committed_at: "2026-06-05T12:00:00Z",
          source_as_of: "2026-06-04T00:00:00Z",
          evidence: {
            evidence_kind: "BANK_STATEMENT",
            source_adapter: "manual",
            normalized_payload: {
              cleared_minor: 671675,
              pending_minor: 12543,
              actual_minor: 684218,
            },
            records: [],
          },
        });
      }
      return undefined;
    });

    cy.get("[data-cy=reconciliation-history-row]")
      .should("contain.text", "Cleared $6,716.75")
      .and("contain.text", "Source as of")
      .and("contain.text", "Committed");
    cy.get("[data-cy=undo-last-reconciliation]").click();
    cy.get("[data-cy=form-modal-root]")
      .should("contain.text", "does not revert")
      .contains("button", "Undo last reconciliation")
      .click();
    cy.get("[data-cy=mutation-feedback]").should(
      "contain.text",
      "Reconciliation undone",
    );
  });

  it("composes current attention and historical-edit warning with history", () => {
    mountPage((path) => {
      if (
        path === `/api/accounts/${budgetAccount.account_id}/reconciliations`
      ) {
        return jsonResponse({
          items: [
            {
              reconciliation_id: "committed-1",
              evidence_id: "evidence-1",
              committed_at: "2026-06-05T12:00:00Z",
              entity_class: "BUDGET",
              undone: false,
            },
          ],
          history: [],
        });
      }
      if (path === "/api/reconciliations/committed-1") {
        return jsonResponse({
          reconciliation_id: "committed-1",
          committed_at: "2026-06-05T12:00:00Z",
          source_as_of: "2026-06-04T00:00:00Z",
          evidence: {
            evidence_kind: "BANK_STATEMENT",
            source_adapter: "manual",
            normalized_payload: { cleared_minor: 671_675 },
            records: [],
          },
        });
      }
      if (
        path ===
        `/api/accounts/${budgetAccount.account_id}/reconciliation-working-set`
      ) {
        return jsonResponse({
          items: [],
          attention: {
            changes_since: 3,
            carried_pending: 1,
            reconciled_history_changed: 2,
          },
        });
      }
      return undefined;
    });

    cy.get("[data-cy=reconciliation-attention]")
      .should("contain.text", "3 changes since last reconciliation")
      .and("contain.text", "1 carried pending");
    cy.get("[data-cy=reconciled-history-warning]").should(
      "contain.text",
      "Historical transaction records changed after reconciliation",
    );
  });

  it("keeps a legacy missing-category transaction unchanged until categorized", () => {
    mountPage();
    cy.contains(".ledger__row", "Uncategorized market purchase").click();
    cy.get(".ledger__row--editing .ledger__status-pill").click();
    cy.get("[data-cy=page-header-root]").click();

    cy.get(".ledger__row--editing .ledger__status-pill").should(
      "contain.text",
      "Cleared",
    );
    cy.get("[data-cy=transaction-ledger]")
      .find('[role="alert"]')
      .should(
        "contain.text",
        "Choose a category or select Uncategorized before saving.",
      );
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      expect(
        calls.some(
          (call) =>
            new URL(call.args[0], "http://localhost").pathname ===
              `/api/transactions/txn-uncategorized-legacy` &&
            call.args[1]?.method === "PUT",
        ),
      ).to.equal(false);
    });

    cy.get(".ledger__row--editing select").first().select("__uncategorized__");
    cy.get("[data-cy=page-header-root]").click();
    cy.get(".ledger__row--editing").should("not.exist");
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const update = calls.find(
        (call) =>
          new URL(call.args[0], "http://localhost").pathname ===
            `/api/transactions/txn-uncategorized-legacy` &&
          call.args[1]?.method === "PUT",
      );
      expect(JSON.parse(update?.args[1]?.body as string)).to.include({
        category_id: null,
        system_category: "TX_UNCATEGORIZED",
        status: "CLEARED",
      });
    });
  });

  it("opens the account-local reconciliation balance action", () => {
    mountPage();

    cy.get("[data-cy=account-detail-reconcile]").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Reconcile account",
    );
    cy.get('input[name="reconciliation-cutoff"]').should("be.visible");
    cy.get('input[name="source-cleared"]').should("be.visible");
    cy.get('input[name="source-pending"]').should("be.visible");
    cy.get('input[name="source-actual"]').should("be.visible");
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Compare balances",
    );
  });

  it("derives the third source balance and commits an instant match", () => {
    const feedback = useMutationFeedback();
    while (feedback.notice.value) feedback.dismiss();
    mountPage();
    mount(MutationFeedbackHost);
    cy.get("[data-cy=account-detail-reconcile]").click();
    cy.get('input[name="source-cleared"]').type("6716.75");
    cy.get('input[name="source-pending"]').type("125.43");
    cy.get('input[name="source-actual"]')
      .should("be.disabled")
      .and("have.value", "6842.18");
    cy.get("[data-cy=form-modal-root]").contains("Compare balances").click();
    cy.get("[data-cy=budget-reconciliation-proof]").should(
      "contain.text",
      "Balances match",
    );
    cy.get("[data-cy=form-modal-root]")
      .contains("button", "Reconcile account")
      .click();
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      expect(
        calls.some((call) => {
          const requestUrl = new URL(call.args[0], "http://localhost");
          return (
            requestUrl.pathname === "/api/reconciliations/attempt-1/apply" &&
            call.args[1]?.method === "POST"
          );
        }),
      ).to.equal(true);
    });
    cy.get('[data-cy="mutation-feedback"]').should(
      "contain.text",
      "Account reconciled",
    );
    cy.get("body").should(($body) => {
      const remainingModals = Array.from(
        $body[0].querySelectorAll<HTMLElement>('[data-cy="form-modal-root"]'),
      ).map((modal) => modal.innerText.trim());
      expect(remainingModals).to.deep.equal([]);
    });
    cy.get("[data-cy=undo-last-reconciliation]").click();
    cy.get("[data-cy=form-modal-root]")
      .should("contain.text", "does not revert")
      .contains("button", "Undo last reconciliation")
      .click();
    cy.get('[data-cy="mutation-feedback"]').should(
      "contain.text",
      "Reconciliation undone",
    );
    cy.get("[data-cy=reconciliation-history-row]").should(
      "contain.text",
      "Undone",
    );
    cy.get("[data-cy=undo-last-reconciliation]").should("not.exist");
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const undoCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${budgetAccount.account_id}/reconciliations/undo` &&
          call.args[1]?.method === "POST"
        );
      });
      expect(JSON.parse(undoCall?.args[1]?.body as string)).to.include({
        expected_reconciliation_id: "attempt-1",
      });
    });
  });

  it("keeps an equal-and-opposite discrepancy blocked and opens the investigation ledger", () => {
    mountPage();
    cy.get("[data-cy=account-detail-reconcile]").click();
    cy.get('input[name="source-cleared"]').type("6717.75");
    cy.get('input[name="source-pending"]').type("124.43");
    cy.get("[data-cy=form-modal-root]").contains("Compare balances").click();
    cy.get("[data-cy=budget-reconciliation-proof]").should(
      "contain.text",
      "Differences found",
    );
    cy.get("[data-cy=budget-reconciliation-proof]").should(
      "contain.text",
      "Actual Δ $0.00",
    );
    cy.get("[data-cy=form-modal-root]").contains("Review differences").click();
    cy.get("[data-cy=reconciliation-investigation]").should("be.visible");
    cy.get("[data-cy=active-reconciliation-banner]").within(() => {
      cy.contains("button", "Edit source balances").should("be.visible");
      cy.contains("button", "Exit reconciliation").should("be.visible");
      cy.get("button").should("have.length", 2);
    });
    cy.get("[data-cy=transaction-ledger]").should("contain.text", "Edited");
    cy.get("[data-cy=transaction-ledger]").should("contain.text", "Pending");
    cy.get("[data-cy=transaction-ledger]")
      .should("contain.text", "Removed market row")
      .and("contain.text", "Removed");
    cy.contains(".ledger__row", "Removed market row")
      .click()
      .should("not.have.class", "ledger__row--editing");
  });

  it("exits without a warning when no canonical transaction was changed", () => {
    mountPage();
    cy.get("[data-cy=account-detail-reconcile]").click();
    cy.get('input[name="source-cleared"]').type("6717.75");
    cy.get('input[name="source-pending"]').type("124.43");
    cy.get("[data-cy=form-modal-root]").contains("Compare balances").click();
    cy.get("[data-cy=form-modal-root]").contains("Review differences").click();
    cy.get("[data-cy=active-reconciliation-banner]")
      .contains("Exit reconciliation")
      .click();
    cy.get("[data-cy=form-modal-root]").should("not.exist");
    cy.get("[data-cy=active-reconciliation-banner]").should("not.exist");
  });

  it("replaces temporary source balances and recomputes the independent deltas", () => {
    mountPage();
    cy.get("[data-cy=account-detail-reconcile]").click();
    cy.get('input[name="source-cleared"]').type("6717.75");
    cy.get('input[name="source-pending"]').type("124.43");
    cy.get("[data-cy=form-modal-root]").contains("Compare balances").click();
    cy.get("[data-cy=form-modal-root]").contains("Review differences").click();
    cy.get("[data-cy=active-reconciliation-banner]")
      .contains("Edit source balances")
      .click();
    cy.get('input[name="source-cleared"]').should("have.value", "6717.75");
    cy.get('input[name="source-pending"]').clear().type("125.43");
    cy.get("[data-cy=form-modal-root]").contains("Compare balances").click();
    cy.get("[data-cy=budget-reconciliation-proof]")
      .should("contain.text", "Cleared Δ $1.00")
      .and("contain.text", "Pending Δ $0.00");
    cy.get("[data-cy=form-modal-root]").contains("Review differences").click();
    cy.get("[data-cy=active-reconciliation-banner]").within(() => {
      cy.contains("button", "Edit source balances").should("be.visible");
      cy.contains("button", "Exit reconciliation").should("be.visible");
    });
  });

  it("warns after a persistent canonical edit and describes it as already saved", () => {
    mountPage();
    cy.get("[data-cy=account-detail-reconcile]").click();
    cy.get('input[name="source-cleared"]').type("6717.75");
    cy.get('input[name="source-pending"]').type("124.43");
    cy.get("[data-cy=form-modal-root]").contains("Compare balances").click();
    cy.get("[data-cy=form-modal-root]").contains("Review differences").click();
    cy.get(".ledger__row").first().click();
    cy.get('.ledger__row--editing input[placeholder="Memo"]')
      .clear()
      .type("Corrected memo");
    cy.get("[data-cy=reconciliation-investigation]").click();
    cy.get("[data-cy=active-reconciliation-banner]")
      .contains("Exit reconciliation")
      .click();
    cy.get("[data-cy=form-modal-root]")
      .should("contain.text", "already been saved")
      .and("contain.text", "no reconciliation recorded for this account");
  });

  it("opens edit configuration and submits account metadata", () => {
    mountPage();

    cy.get("[data-cy=account-detail-edit-configuration]").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Edit account configuration",
    );
    cy.get('input[name="institution"]').type("Chase");
    cy.get("[data-cy=form-modal-root]").contains("Save").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const updateCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname === `/api/accounts/${budgetAccount.account_id}`
        );
      });
      expect(updateCall).not.to.eq(undefined);
      const body = JSON.parse(updateCall?.args[1]?.body as string);
      expect(body).to.include({ institution: "Chase" });
      expect(body).not.to.have.property("include_in_net_worth");
    });
  });
});

describe("AccountDetailPage transaction Undo", () => {
  beforeEach(clearMutationFeedback);

  it("undoes an added transaction using the version returned by the API", () => {
    const deleteUrls: URL[] = [];
    mountPage(
      (path, init, requestUrl) => {
        if (path === "/api/transactions" && init?.method === "POST") {
          return jsonResponse({
            transaction_id: "account-created-transaction",
            version: "created-version",
          });
        }
        if (
          path === "/api/transactions/account-created-transaction" &&
          init?.method === "DELETE"
        ) {
          deleteUrls.push(new URL(requestUrl ?? path, "http://localhost"));
          return jsonResponse({ ok: true });
        }
        return undefined;
      },
      { TransactionEntryForm: accountEntryMutationStub },
      true,
    );

    cy.get("[data-cy=test-create-account-transaction]").click();
    cy.get('[data-cy="mutation-feedback"]')
      .should("contain.text", "Transaction added")
      .find("button")
      .contains("Undo")
      .click();

    cy.wrap(null).should(() => {
      expect(deleteUrls[0]?.searchParams.get("expected_version")).to.equal(
        "created-version",
      );
      expect(feedbackNotice()?.message).to.equal("Transaction addition undone");
    });
  });

  it("undoes an account-ledger edit with the latest persisted version", () => {
    const updateRequests: Array<Record<string, unknown>> = [];
    mountPage(
      (path, init) => {
        if (path === "/api/transactions/txn-1" && init?.method === "PUT") {
          updateRequests.push(JSON.parse(String(init.body)));
          return jsonResponse({
            transaction_id: "txn-1",
            version:
              updateRequests.length === 1 ? "edited-version" : "undo-version",
          });
        }
        return undefined;
      },
      { TransactionLedger: accountLedgerMutationStub },
      true,
    );

    cy.get("[data-cy=test-edit-account-transaction]").click();
    cy.get('[data-cy="mutation-feedback"]')
      .should("contain.text", "Transaction updated")
      .find("button")
      .contains("Undo")
      .click();

    cy.wrap(null).should(() => {
      expect(updateRequests).to.have.length(2);
      expect(updateRequests[0]).to.include({
        expected_version: "version-1",
        memo: "Edited account transaction",
      });
      expect(updateRequests[1]).to.include({
        expected_version: "edited-version",
        memo: "Whole Foods",
        acknowledge_reconciled_history_change: true,
      });
      expect(feedbackNotice()?.message).to.equal("Transaction edit undone");
    });
  });

  it("restores a removed account-ledger transaction from its deleted version", () => {
    const restoreBodies: Array<Record<string, unknown>> = [];
    mountPage(
      (path, init) => {
        if (path === "/api/transactions/txn-1" && init?.method === "DELETE") {
          return jsonResponse({ ok: true });
        }
        if (
          path === "/api/transactions/txn-1/restore" &&
          init?.method === "POST"
        ) {
          restoreBodies.push(JSON.parse(String(init.body)));
          return jsonResponse({
            transaction_id: "txn-1",
            version: "restored-version",
          });
        }
        return undefined;
      },
      { TransactionLedger: accountLedgerMutationStub },
      true,
    );

    cy.get("[data-cy=test-remove-account-transaction]").click();
    cy.get('[data-cy="mutation-feedback"]')
      .should("contain.text", "Transaction removed")
      .find("button")
      .contains("Undo")
      .click();

    cy.wrap(null).should(() => {
      expect(restoreBodies).to.deep.equal([{ expected_version: "version-1" }]);
      expect(feedbackNotice()?.message).to.equal("Transaction removal undone");
    });
  });
});

const trackingAccount = {
  account_id: "acct-tracking-0001",
  name: "Legacy Brokerage",
  account_class: "TRACKING",
  is_hidden: false,
  is_active: true,
  institution: null,
  account_number_last4: null,
  budget_account_type: null,
  linked_payment_category_id: null,
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 9843221,
  tracking_polarity: "ASSET",
  tracking_source: "import",
  latest_valuation_minor: 9843221,
  latest_valuation_date: "2026-06-02",
  current_value_minor: 9843221,
  net_worth_contribution_minor: 9843221,
  value_source: "imported_valuation",
  value_effective_date: "2026-06-02",
  reconciliation_status: "NOT_RECONCILED",
  metadata: '{"imported_from_net_worth": true}',
};

const trackingSnapshots = [
  {
    valuation_id: "snap-1",
    account_id: trackingAccount.account_id,
    effective_date: "2026-06-02",
    amount_minor: 9843221,
    notes: "",
  },
  {
    valuation_id: "snap-2",
    account_id: trackingAccount.account_id,
    effective_date: "2026-06-01",
    amount_minor: 9745108,
    notes: "",
  },
  {
    valuation_id: "snap-3",
    account_id: trackingAccount.account_id,
    effective_date: "2026-05-31",
    amount_minor: 9720433,
    notes: "",
  },
];

function stubTrackingFetch() {
  let promotedAccount: typeof trackingAccount | null = null;
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;

    if (path === "/api/accounts") {
      return Promise.resolve(
        new Response(
          JSON.stringify({ items: [promotedAccount ?? trackingAccount] }),
          {
            status: 200,
            headers: { "Content-Type": "application/json" },
          },
        ),
      );
    }

    if (
      path === `/api/accounts/${trackingAccount.account_id}/cutovers` &&
      init?.method === "POST"
    ) {
      const body = JSON.parse(init.body as string);
      const successorIds = body.successors.map(
        (_successor: unknown, index: number) => `successor-${index + 1}`,
      );
      if (successorIds.length === 1) {
        promotedAccount = {
          ...trackingAccount,
          account_id: successorIds[0],
          name: body.successors[0].name,
          account_class: body.successors[0].account_class,
          tracking_polarity: undefined,
          tracking_source: undefined,
        } as typeof trackingAccount;
      }
      return Promise.resolve(
        new Response(
          JSON.stringify({
            operation_id: body.operation_id,
            predecessor_account_id: trackingAccount.account_id,
            cutover_date: body.cutover_date,
            prior_value_minor: body.final_predecessor_value_minor,
            successor_total_minor: body.final_predecessor_value_minor,
            variance_minor: 0,
            successor_account_ids: successorIds,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === "/api/accounts/successor-1/investment-statements/latest") {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            effective_date: null,
            cash_balance_minor: null,
            holdings: [],
            holdings_value_minor: null,
            holdings_cost_basis_minor: null,
            unrealized_gain_minor: null,
            current_value_minor: null,
            provisional_transfer_minor: 0,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (
      path === `/api/accounts/${trackingAccount.account_id}/tracking-snapshots`
    ) {
      return Promise.resolve(
        new Response(JSON.stringify({ items: trackingSnapshots }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }

    if (
      path ===
      `/api/accounts/${trackingAccount.account_id}/transactions/summary`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            inflow_minor: 0,
            outflow_minor: 0,
            net_flow_minor: 0,
            transaction_count: 0,
            average_daily_balance_minor: 9843221,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${trackingAccount.account_id}/balance-trend`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            points: [
              { date: "2026-05-01", balance_minor: 9467130 },
              { date: "2026-06-02", balance_minor: 9843221 },
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    if (path === `/api/accounts/${trackingAccount.account_id}`) {
      return Promise.resolve(
        new Response(
          JSON.stringify({ account_id: trackingAccount.account_id }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }

    return Promise.resolve(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });
}

function mountTrackingPage() {
  stubTrackingFetch();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${trackingAccount.account_id}`);
  cy.wrap(router.isReady());

  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  });
  return router;
}

describe("AccountDetailPage — tracking account", () => {
  it("renders the tracking account detail contract", () => {
    mountTrackingPage();

    cy.get("[data-cy=account-detail-page]").should("be.visible");
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Legacy Brokerage",
    );
    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Tracking account",
    );
    cy.get("[data-cy=account-detail-add-snapshot]").should(
      "contain.text",
      "Reconcile",
    );
    cy.get("[data-cy=account-detail-create-richer]").should("be.visible");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Current value",
    );
    cy.get("[data-cy=metric-strip-root]").should("contain.text", "Polarity");
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Latest snapshot",
    );
    cy.get("[data-cy=metric-strip-root]").should(
      "contain.text",
      "Source / migration",
    );
    cy.get("[data-cy=tracking-import-banner]").should("be.visible");
    cy.get("[data-cy=snapshot-history-section]").should(
      "contain.text",
      "Snapshot history",
    );
    cy.get("[data-cy=snapshot-history-section]").should(
      "contain.text",
      "3 snapshots",
    );
    cy.get("[data-cy=tracking-summary-section]").should(
      "contain.text",
      "Valuation history",
    );
    cy.get("[data-cy=account-details-section]").should(
      "contain.text",
      "$98,432.21",
    );
    cy.get("[data-cy=migration-context-section]").should(
      "contain.text",
      "Migration / import context",
    );
    cy.get("[data-cy=migration-context-section]").should(
      "contain.text",
      "Aspire Budgeting",
    );
    cy.get("[data-cy=history-config-section]").should(
      "contain.text",
      "History / configuration",
    );
    cy.get("[data-cy=balance-trend-chart]").should("be.visible");
    cy.get("[data-cy=reconciliation-section]").should("not.exist");
    cy.get("[data-cy=transactions-section]").should("not.exist");
    cy.get("[data-cy=summary-section]").should("not.exist");
  });

  it("submits a tracking snapshot correction", () => {
    mountTrackingPage();

    cy.get("[data-cy=account-detail-add-snapshot]").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Reconcile valuation",
    );
    cy.get('input[name="value-date"]').should(
      "have.attr",
      "max",
      new Date().toISOString().slice(0, 10),
    );
    cy.get('input[name="value-date"]').clear().type("2026-06-02");
    cy.get('input[name="value-amount"]').type("123.45");
    cy.get('input[name="value-notes"]').type("Statement correction");
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const snapshotCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${trackingAccount.account_id}/valuation-reconciliations` &&
          call.args[1]?.method === "POST"
        );
      });
      expect(snapshotCall).not.to.eq(undefined);
      const body = JSON.parse(snapshotCall?.args[1]?.body as string);
      expect(body).to.include({
        amount_minor: 12345,
        source: "manual",
        notes: "Statement correction",
      });
      expect(body.client_operation_id).to.be.a("string");
    });
  });

  it("records evidence for an unchanged tracking value", () => {
    mountTrackingPage();
    cy.get("[data-cy=account-detail-add-snapshot]").click();
    cy.get('input[name="value-date"]').clear().type("2026-06-02");
    cy.get('input[name="value-amount"]').type("98432.21");
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const valuation = calls.find((call) =>
        new URL(call.args[0], "http://localhost").pathname.endsWith(
          "/valuation-reconciliations",
        ),
      );
      expect(JSON.parse(valuation?.args[1]?.body as string)).to.include({
        effective_date: "2026-06-02",
        amount_minor: 9_843_221,
      });
    });
  });

  it("opens and closes the cutover modal", () => {
    const router = mountTrackingPage();

    cy.get("[data-cy=account-detail-create-richer]").click();
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Replace tracking account",
    );
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "representation change",
    );
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Entity type");
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Cutover date");
    cy.get("[data-cy=form-modal-root]").should("contain.text", "Name");
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Opening cash balance",
    );
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Contribution category",
    );
    cy.contains("button", "Add successor").click();
    cy.get("[data-cy=cutover-successor]").should("have.length", 2);
    cy.get('select[name="cutover-type-1"]').select("TANGIBLE_ASSET");
    cy.get('input[name="cutover-opening-1"]').type("100");
    cy.get('input[name="cutover-final-tracking-value"]').type("98532.21");
    cy.get("[data-cy=form-modal-root]").contains("Apply cutover").click();
    cy.get("[data-cy=form-modal-root]").should("not.exist");
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.path).to.equal("/assets-liabilities");
    });
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const cutoverCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${trackingAccount.account_id}/cutovers` &&
          call.args[1]?.method === "POST"
        );
      });
      expect(cutoverCall).not.to.eq(undefined);
      const body = JSON.parse(cutoverCall?.args[1]?.body as string);
      expect(body.successors).to.have.length(2);
      expect(body.successors[1]).to.include({
        account_class: "TANGIBLE_ASSET",
        opening_value_minor: 10_000,
      });
      expect(body).to.include({ final_predecessor_value_minor: 9_853_221 });
    });
  });

  it("routes a single current cutover to the successor account", () => {
    const router = mountTrackingPage();
    cy.get("[data-cy=account-detail-create-richer]").click();
    cy.get('input[name="cutover-final-tracking-value"]').type("98432.21");
    cy.get("[data-cy=form-modal-root]").contains("Apply cutover").click();
    cy.wrap(null).should(() => {
      expect(router.currentRoute.value.path).to.equal(
        "/assets-liabilities/successor-1",
      );
    });
  });

  it("explains a cutover difference with the investment breakdown", () => {
    mountTrackingPage();
    cy.get("[data-cy=account-detail-create-richer]").click();
    cy.get('input[name="cutover-final-tracking-value"]').type("98432.21");
    cy.contains("button", "Add holding").click();
    cy.get('input[name="cutover-ticker-0-0"]').type("VTI");
    cy.get('input[name="cutover-quantity-0-0"]').type("0.001");
    cy.get('input[name="cutover-price-0-0"]').type("250");
    cy.get('input[name="cutover-basis-0-0"]').type("200");

    cy.get("[data-cy=cutover-value-reconciliation]")
      .should("contain.text", "Final tracking value: $98,432.21")
      .and("contain.text", "Successor total: $98,432.46")
      .and("contain.text", "cash $98,432.21 + holdings $0.25")
      .and("contain.text", "Successor total is $0.25 above")
      .and("contain.text", "Reduce asset or cash values");
  });
});

const tangibleAccount = {
  account_id: "acct-tangible-0001",
  name: "Home",
  account_class: "TANGIBLE_ASSET",
  is_hidden: false,
  is_active: true,
  institution: null,
  account_number_last4: null,
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 0,
  current_value_minor: 42500000,
  net_worth_contribution_minor: 42500000,
  value_source: "manual_valuation",
  value_effective_date: "2026-06-02",
  reconciliation_status: "NOT_RECONCILED",
};

function mountTangiblePage() {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    if (path === "/api/accounts") {
      return Promise.resolve(
        new Response(JSON.stringify({ items: [tangibleAccount] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
    if (
      path === `/api/accounts/${tangibleAccount.account_id}/tangible-valuations`
    ) {
      return Promise.resolve(
        new Response(
          JSON.stringify(
            init?.method === "POST"
              ? { valuation_id: "valuation-new" }
              : {
                  items: [
                    {
                      valuation_id: "valuation-1",
                      account_id: tangibleAccount.account_id,
                      effective_date: "2026-06-02",
                      amount_minor: 42500000,
                      source: "manual",
                      notes: "County assessment",
                    },
                  ],
                },
          ),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (path.endsWith("/transactions/summary")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            inflow_minor: 0,
            outflow_minor: 0,
            net_flow_minor: 0,
            transaction_count: 1,
            average_daily_balance_minor: 42500000,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (path.endsWith("/balance-trend")) {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            points: [{ date: "2026-06-02", balance_minor: 42500000 }],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    if (path === "/api/transactions") {
      return Promise.resolve(
        new Response(
          JSON.stringify({
            items: [],
            total: 0,
            offset: 0,
            limit: 100,
            has_more: false,
            status_counts: { PENDING: 0, CLEARED: 0 },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );
    }
    return Promise.resolve(
      new Response(JSON.stringify({ items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${tangibleAccount.account_id}`);
  cy.wrap(router.isReady());
  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: { plugins: [router, [VueQueryPlugin, { queryClient }]] },
  });
}

describe("AccountDetailPage — tangible asset", () => {
  it("renders valuation history and submits a valuation", () => {
    mountTangiblePage();

    cy.get("[data-cy=page-header-root]").should(
      "contain.text",
      "Tangible asset",
    );
    cy.get("[data-cy=snapshot-history-section]").should(
      "contain.text",
      "Valuation history",
    );
    cy.get("[data-cy=transactions-section]").should("not.exist");
    cy.get("[data-cy=account-detail-add-snapshot]").should(
      "contain.text",
      "Reconcile",
    );
    cy.get("[data-cy=account-detail-add-snapshot]").click();
    cy.get('input[name="value-date"]').clear().type("2026-06-02");
    cy.get('input[name="value-amount"]').type("430000");
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const valuationCall = calls.find((call) => {
        const requestUrl = new URL(call.args[0], "http://localhost");
        return (
          requestUrl.pathname ===
            `/api/accounts/${tangibleAccount.account_id}/valuation-reconciliations` &&
          call.args[1]?.method === "POST"
        );
      });
      const body = JSON.parse(valuationCall?.args[1]?.body as string);
      expect(body).to.include({ amount_minor: 43000000, source: "manual" });
      expect(body.client_operation_id).to.be.a("string");
    });
  });

  it("records evidence for an unchanged tangible valuation", () => {
    mountTangiblePage();
    cy.get("[data-cy=account-detail-add-snapshot]").click();
    cy.get('input[name="value-date"]').clear().type("2026-06-02");
    cy.get('input[name="value-amount"]').type("425000");
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();
    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const valuation = calls.find((call) =>
        new URL(call.args[0], "http://localhost").pathname.endsWith(
          "/valuation-reconciliations",
        ),
      );
      expect(JSON.parse(valuation?.args[1]?.body as string)).to.include({
        effective_date: "2026-06-02",
        amount_minor: 42_500_000,
      });
    });
  });
});

const investmentAccount = {
  account_id: "acct-investment-0001",
  name: "Index Brokerage",
  account_class: "INVESTMENT",
  is_hidden: false,
  is_active: true,
  institution: "Fidelity",
  account_number_last4: "5678",
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 10_000,
  current_value_minor: 10_000,
  value_effective_date: "2026-06-02",
  net_worth_contribution_minor: 10_000,
  investment_self_managed: true,
  investment_tax_treatment: "TAXABLE",
};

function mountInvestmentPage(
  draftResponse: Record<string, unknown> = {
    reconciliation_id: "investment-attempt-1",
    certification_allowed: true,
    diffs: [],
    price_only_changes: [
      {
        instrument_id: "instrument-fund",
        canonical_price_minor: 8_900,
        source_price_minor: 9_000,
      },
    ],
  },
) {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    let body: unknown = { items: [] };
    if (path === "/api/accounts") {
      body = { items: [investmentAccount] };
    } else if (path === "/api/categories") {
      body = { groups: [], items: [] };
    } else if (path.endsWith("/investment-statements/latest")) {
      body = {
        effective_date: "2026-06-02",
        cash_balance_minor: 1_000,
        holdings: [
          {
            position_id: "position-fund",
            ticker: "FND",
            quantity_micros: 1_000_000,
            average_basis_minor: 8_000,
            price_minor: 9_000,
            value_minor: 9_000,
            cost_basis_minor: 8_000,
            unrealized_gain_minor: 1_000,
          },
        ],
        holdings_value_minor: 9_000,
        holdings_cost_basis_minor: 8_000,
        unrealized_gain_minor: 1_000,
        current_value_minor: 10_000,
        provisional_transfer_minor: 0,
      };
    } else if (path === "/api/investment-instruments") {
      body = {
        items: [
          {
            instrument_id: "instrument-fund",
            symbol: "FND",
            name: "Fund",
            is_cash_equivalent: false,
          },
        ],
      };
    } else if (
      path ===
        `/api/accounts/${investmentAccount.account_id}/reconciliations/draft` &&
      init?.method === "POST"
    ) {
      body = draftResponse;
    } else if (path === "/api/reconciliations/investment-attempt-1/apply") {
      body = { state: "SUCCESSFUL", reconciliation_id: "investment-commit-1" };
    } else if (path.endsWith("/transactions/summary")) {
      body = {
        inflow_minor: 0,
        outflow_minor: 0,
        net_flow_minor: 0,
        transaction_count: 0,
        average_daily_balance_minor: 10_000,
      };
    } else if (path.endsWith("/balance-trend")) {
      body = { points: [] };
    } else if (path === "/api/transactions") {
      body = {
        items: [],
        total: 0,
        offset: 0,
        limit: 100,
        has_more: false,
        status_counts: { PENDING: 0, CLEARED: 0 },
      };
    }
    return Promise.resolve(jsonResponse(body));
  });

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${investmentAccount.account_id}`);
  cy.wrap(router.isReady());
  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: { plugins: [router, [VueQueryPlugin, { queryClient }]] },
  });
}

describe("AccountDetailPage — investment account", () => {
  it("compares coherent reported source value and reconciles price-only movement", () => {
    mountInvestmentPage();
    cy.contains("Reconcile statement").should("not.exist");
    cy.contains("Apply statement").should("not.exist");
    cy.contains("View reconciliation").should("not.exist");
    cy.get("[data-cy=account-detail-reconcile-investment]").click();
    cy.get('input[name="investment-statement-total"]').should(
      "have.value",
      "100",
    );
    cy.get('input[name="holding-value-0"]').should("have.value", "90");
    cy.get("[data-cy=form-modal-root]").contains("Compare statement").click();
    cy.get("[data-cy=investment-reconciliation-proof]")
      .should("contain.text", "Balances match")
      .and("contain.text", "1 price-only changes");
    cy.get("[data-cy=form-modal-root]").contains("Reconcile account").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const draft = calls.find(
        (call) =>
          new URL(call.args[0], "http://localhost").pathname ===
            `/api/accounts/${investmentAccount.account_id}/reconciliations/draft` &&
          call.args[1]?.method === "POST",
      );
      const body = JSON.parse(draft?.args[1]?.body as string);
      expect(body).to.include({
        source_kind: "INVESTMENT_STATEMENT",
        source_cash_minor: 1_000,
        source_total_value_minor: 10_000,
        source_as_of: "2026-06-02T12:00:00Z",
      });
      expect(body.source_positions[0]).to.include({
        instrument_id: "instrument-fund",
        quantity_micros: 1_000_000,
        total_cost_basis_minor: 8_000,
        source_price_minor: 9_000,
        source_value_minor: 9_000,
      });
      expect(
        calls.some(
          (call) =>
            new URL(call.args[0], "http://localhost").pathname ===
            "/api/reconciliations/investment-attempt-1/apply",
        ),
      ).to.equal(true);
    });
  });

  it("routes structural differences to normal holdings investigation without applying", () => {
    mountInvestmentPage({
      reconciliation_id: "investment-attempt-1",
      certification_allowed: false,
      diffs: [
        { field: "quantity_micros", source: 900_000, canonical: 1_000_000 },
      ],
      price_only_changes: [],
    });
    cy.get("[data-cy=account-detail-reconcile-investment]").click();
    cy.get("[data-cy=form-modal-root]").contains("Compare statement").click();
    cy.get("[data-cy=investment-reconciliation-proof]").should(
      "contain.text",
      "Differences found",
    );
    cy.get("[data-cy=form-modal-root]").contains("Review holdings").click();
    cy.get("[data-cy=holdings-summary-section]").should("be.visible");
    cy.get("[data-cy=account-detail-page]").should(
      "contain.text",
      "No holdings were changed",
    );
  });
});

const loanAccount = {
  account_id: "acct-loan-0001",
  name: "Mortgage",
  account_class: "LOAN",
  is_hidden: false,
  is_active: true,
  institution: "Chase",
  account_number_last4: "1234",
  actual_balance_minor: 0,
  pending_balance_minor: 0,
  cleared_balance_minor: 0,
  display_balance_minor: 0,
  current_value_minor: 19_900_000,
  net_worth_contribution_minor: -18_650_000,
  value_source: "loan_statement",
  value_effective_date: "2026-06-01",
  reconciliation_status: "CURRENT",
  loan_rate_minor: 600,
  loan_rate_type: "FIXED",
  loan_scheduled_principal_interest_minor: 200_000,
  loan_payment_frequency: "MONTHLY",
  loan_next_payment_date: "2026-07-01",
  loan_remaining_term_months: 120,
};

function mountLoanPage(
  override?: (path: string, init?: RequestInit) => Response | undefined,
) {
  cy.stub(window, "fetch").callsFake((url: string, init?: RequestInit) => {
    const path = new URL(url, "http://localhost").pathname;
    const overridden = override?.(path, init);
    if (overridden) return Promise.resolve(overridden);
    let body: unknown = { items: [] };
    if (path === "/api/accounts") {
      body = {
        items: [
          loanAccount,
          {
            ...budgetAccount,
            account_id: "acct-cash-0001",
            name: "Checking",
          },
        ],
      };
    } else if (path === "/api/categories") {
      body = {
        groups: [],
        items: [
          {
            category_id: "cat-mortgage",
            name: "Mortgage payment",
            category_kind: "STANDARD",
            available_minor: 250_000,
          },
        ],
      };
    } else if (path.endsWith("/budget-links")) {
      body = {
        items: [
          {
            account_id: loanAccount.account_id,
            category_id: "cat-mortgage",
            link_behavior: "LOAN_PAYMENT",
            derivation_method: "TRANSFER_IN_ONLY",
            effective_date: "2026-01-01",
          },
        ],
      };
    } else if (path.endsWith("/loan-snapshots")) {
      body = {
        items: [
          {
            snapshot_id: "loan-snapshot-1",
            account_id: loanAccount.account_id,
            effective_date: "2026-06-01",
            principal_balance_minor: 19_800_000,
            accrued_interest_minor: 100_000,
            escrow_balance_minor: 1_200_000,
            unapplied_credit_minor: 50_000,
            ytd_principal_paid_minor: 200_000,
            ytd_interest_paid_minor: 300_000,
            attributed_payment_minor: 500_000,
            principal_reduction_minor: 200_000,
            unknown_nonprincipal_minor: 300_000,
            notes: "",
          },
        ],
      };
    } else if (path.endsWith("/loan-projection")) {
      body = {
        available: true,
        missing: [],
        rate_assumption: "Current fixed rate",
        estimated_accrued_interest_minor: 32_548,
        projected_payoff_date: "2036-05-01",
        projected_total_interest_minor: 4_000_000,
        remaining_principal_at_horizon_minor: 0,
        rows: [
          {
            payment_number: 1,
            payment_date: "2026-07-01",
            payment_minor: 200_000,
            principal_minor: 101_000,
            interest_minor: 99_000,
            remaining_principal_minor: 19_699_000,
          },
        ],
      };
    } else if (path.endsWith("/loan-payments")) {
      body =
        init?.method === "POST"
          ? { transaction_id: "payment-new" }
          : { items: [] };
    } else if (path.endsWith("/transactions/summary")) {
      body = {
        inflow_minor: 0,
        outflow_minor: 0,
        net_flow_minor: 0,
        transaction_count: 0,
        average_daily_balance_minor: 0,
      };
    } else if (path.endsWith("/balance-trend")) {
      body = { points: [] };
    } else if (path === "/api/transactions") {
      body = {
        items: [],
        total: 0,
        offset: 0,
        limit: 100,
        has_more: false,
        status_counts: { PENDING: 0, CLEARED: 0 },
      };
    }
    return Promise.resolve(
      new Response(JSON.stringify(body), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  });

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/:id", component: AccountDetailPage },
    ],
  });
  router.push(`/assets-liabilities/${loanAccount.account_id}`);
  cy.wrap(router.isReady());
  const queryClient = createDojoQueryClient();
  mount(AccountDetailPage, {
    global: { plugins: [router, [VueQueryPlugin, { queryClient }]] },
  });
}

describe("AccountDetailPage — loan", () => {
  it("separates actual, restricted, estimated, and payment configuration", () => {
    mountLoanPage();
    cy.contains("Reconcile statement").should("not.exist");
    cy.contains("Apply statement").should("not.exist");
    cy.contains("View reconciliation").should("not.exist");
    cy.get("[data-cy=reconciliation-history-section]").should("be.visible");

    cy.get("[data-cy=loan-summary-section]").should(
      "contain.text",
      "Lender actual and balance-derived",
    );
    cy.get("[data-cy=loan-escrow-section]").should(
      "contain.text",
      "Restricted escrow asset",
    );
    cy.get("[data-cy=loan-estimate-section]").should(
      "contain.text",
      "Next 12 estimated payments",
    );

    cy.get("[data-cy=account-detail-record-payment]").click();
    cy.get('select[name="loan-payment-category"]').should("not.exist");
    cy.get("[data-cy=form-modal-root]").should(
      "contain.text",
      "Payment category: Mortgage payment",
    );
    cy.get("[data-cy=form-modal-root]").contains("Cancel").click();

    cy.get("[data-cy=account-detail-reconcile-loan]").click();
    cy.get('input[name="loan-principal"]').should("be.visible");
    cy.get('input[name="loan-escrow"]').should("be.visible");
    cy.get('input[name="loan-interest"]').should("not.exist");
    cy.contains("button", "Show optional fields").click();
    cy.get('input[name="loan-interest"]').should("exist");
    cy.get('input[name="loan-ytd-interest"]').should("exist");
  });

  it("keeps blank lender facts unknown and records principal-only evidence", () => {
    mountLoanPage();
    cy.get("[data-cy=account-detail-reconcile-loan]").click();
    cy.get('input[name="loan-escrow"]').clear();
    cy.contains("button", "Show optional fields").click();
    [
      "loan-interest",
      "loan-unapplied",
      "loan-ytd-principal",
      "loan-ytd-interest",
    ].forEach((name) => cy.get(`input[name="${name}"]`).clear());
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const request = calls.find((call) =>
        new URL(call.args[0], "http://localhost").pathname.endsWith(
          "/loan-reconciliations",
        ),
      );
      const body = JSON.parse(request?.args[1]?.body as string);
      expect(body).to.include({
        principal_balance_minor: 19_800_000,
        source_as_of: "2026-06-01T12:00:00Z",
      });
      for (const optional of [
        "accrued_interest_minor",
        "escrow_balance_minor",
        "unapplied_credit_minor",
        "ytd_principal_paid_minor",
        "ytd_interest_paid_minor",
      ]) {
        expect(body).not.to.have.property(optional);
      }
      expect(
        calls.some(
          (call) =>
            new URL(call.args[0], "http://localhost").pathname.endsWith(
              "/loan-payments",
            ) && call.args[1]?.method === "POST",
        ),
      ).to.equal(false);
    });
  });

  it("preserves an explicitly asserted optional zero", () => {
    mountLoanPage();
    cy.get("[data-cy=account-detail-reconcile-loan]").click();
    cy.get('input[name="loan-escrow"]').clear();
    cy.contains("button", "Show optional fields").click();
    cy.get('input[name="loan-interest"]').clear().type("0");
    cy.get('input[name="loan-unapplied"]').clear();
    cy.get('input[name="loan-ytd-principal"]').clear();
    cy.get('input[name="loan-ytd-interest"]').clear();
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const request = calls.find((call) =>
        new URL(call.args[0], "http://localhost").pathname.endsWith(
          "/loan-reconciliations",
        ),
      );
      const body = JSON.parse(request?.args[1]?.body as string);
      expect(body).to.have.property("accrued_interest_minor", 0);
      expect(body).not.to.have.property("escrow_balance_minor");
      expect(body).not.to.have.property("unapplied_credit_minor");
    });
  });

  it("corrects only supplied canonical facts before retrying reconciliation", () => {
    let reconciliationRequests = 0;
    mountLoanPage((path, init) => {
      if (
        path.endsWith("/loan-reconciliations") &&
        init?.method === "POST" &&
        reconciliationRequests++ === 0
      ) {
        return jsonResponse(
          {
            detail: {
              code: "loan_snapshot_mismatch",
              fields: {
                principal_balance_minor: {
                  lender: 19_800_000,
                  dojo: 19_900_000,
                },
              },
            },
          },
          409,
        );
      }
      if (path.endsWith("/loan-reconciliations")) {
        return jsonResponse({ reconciliation_id: "loan-reconciliation-1" });
      }
      return undefined;
    });
    cy.get("[data-cy=account-detail-reconcile-loan]").click();
    cy.get("[data-cy=form-modal-root]").contains("Reconcile").click();
    cy.get("[data-cy=loan-correct-canonical-snapshot]").click();

    cy.window().then((win) => {
      const calls = (
        win.fetch as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const correction = calls.find(
        (call) =>
          new URL(call.args[0], "http://localhost").pathname.endsWith(
            "/loan-snapshots",
          ) && call.args[1]?.method === "POST",
      );
      const body = JSON.parse(correction?.args[1]?.body as string);
      expect(body).to.include({
        effective_date: "2026-06-01",
        principal_balance_minor: 19_800_000,
        accrued_interest_minor: 100_000,
        escrow_balance_minor: 1_200_000,
      });
      expect(reconciliationRequests).to.equal(2);
      expect(
        calls.some(
          (call) =>
            new URL(call.args[0], "http://localhost").pathname.endsWith(
              "/loan-payments",
            ) && call.args[1]?.method === "POST",
        ),
      ).to.equal(false);
    });
  });
});
