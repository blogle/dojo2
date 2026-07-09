import { mount } from "cypress/vue";

import ImportDetailsModal from "../../src/dojo/pages/onboarding/ImportDetailsModal.vue";
import type { ImportResult } from "../../src/dojo/types";

const importResult: ImportResult = {
  ok: true,
  validation_report: {
    passed: true,
    checks: Array.from({ length: 108 }, (_, index) => ({
      label: `check-${index}`,
      entity_type: "fixture",
      entity_name: "fixture",
      month: null,
      expected_value: null,
      actual_value: null,
      expected_minor: null,
      actual_minor: null,
      absolute_delta_minor: null,
      passed: true,
      source_reference: [],
      notes: "",
    })),
    hard_failures: [],
    warnings: [
      { code: "missing-payee", message: "2 transactions have missing payees." },
      {
        code: "missing-attachments",
        message: "15 transactions are missing attachments.",
      },
    ],
    summary: {
      group_count: 9,
      category_count: 34,
      account_count: 12,
      transaction_count: 2486,
      allocation_count: 620,
      valuation_count: 18,
    },
  },
};

describe("Onboarding import details modal", () => {
  it("renders imported counts and a compact validation summary", () => {
    cy.viewport(1600, 900);
    mount(ImportDetailsModal, {
      props: {
        visible: true,
        result: importResult,
      },
    });

    cy.get("[data-cy=large-detail-modal-root]").should(
      "contain.text",
      "Import details",
    );
    cy.get("[data-cy=import-records]").within(() => {
      cy.contains("Category groups").should("be.visible");
      cy.contains("9").should("be.visible");
      cy.contains("Transactions").should("be.visible");
      cy.contains("2,486").should("be.visible");
      cy.contains("Allocations").should("be.visible");
      cy.contains("620").should("be.visible");
      cy.get(".import-details__record-label").should("have.length", 6);
    });

    cy.get("[data-cy=validation-summary]").within(() => {
      cy.contains("108 checks passed").should("be.visible");
      cy.contains("2 warnings").should("be.visible");
      cy.contains("0 blocking issues").should("be.visible");
      cy.get(".import-details__validation-row").should("have.length", 3);
    });

    cy.get("[data-cy=validation-summary]").then(($summary) => {
      expect($summary[0].getBoundingClientRect().height).to.be.lessThan(150);
    });

    cy.get("[data-cy=import-records]").then(($records) => {
      cy.get("[data-cy=validation-summary]").then(($summary) => {
        const recordsTop = $records[0].getBoundingClientRect().top;
        const summaryTop = $summary[0].getBoundingClientRect().top;
        expect(Math.abs(recordsTop - summaryTop)).to.be.lessThan(8);
      });
    });

    cy.get("[data-cy=warning-list]").within(() => {
      cy.get(".import-details__warning-row").should("have.length", 2);
      cy.contains("2 transactions have missing payees.").should("be.visible");
    });
  });

  it("renders imported counts for review-based imports without validation details", () => {
    const reviewResult: ImportResult = {
      ok: true,
      import_summary: {
        group_count: 9,
        category_count: 34,
        account_count: 12,
        transaction_count: 2486,
        allocation_count: 620,
        valuation_count: 18,
      },
      decisions_summary: {
        duplicates_excluded: 2,
        tracking_created: 4,
        skipped: 1,
        low_confidence_accepted: 0,
      },
    };

    cy.viewport(1600, 900);
    mount(ImportDetailsModal, {
      props: {
        visible: true,
        result: reviewResult,
      },
    });

    cy.get("[data-cy=import-records]").within(() => {
      cy.contains("Transactions").should("be.visible");
      cy.contains("2,486").should("be.visible");
      cy.contains("Accounts").should("be.visible");
      cy.contains("12").should("be.visible");
    });
    cy.get("[data-cy=decisions-summary]").within(() => {
      cy.contains("Net-worth categories matched to budget accounts").should(
        "be.visible",
      );
      cy.contains("Tracking accounts created from net-worth categories").should(
        "be.visible",
      );
      cy.contains("4").should("be.visible");
    });
  });
});
