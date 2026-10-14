import { mount } from "cypress/vue";

import fixtures from "../../src/dojo/components/transactions/TransactionEntryForm.fixtures";

const fixtureScenario = fixtures.scenarios[0];
const testedWidths = [976, 1152, 1303, 1440];

function mountEntryForm(onSubmit?: Cypress.Agent<sinon.SinonSpy>) {
  mount(fixtures.component, {
    props: {
      ...fixtureScenario?.props,
      ...(onSubmit ? { onSubmit } : {}),
    },
  });
}

describe("TransactionEntryForm responsive layout", () => {
  for (const width of testedWidths) {
    for (const mode of ["Transaction", "Transfer"] as const) {
      it(`contains every ${mode.toLowerCase()} control at ${width}px`, () => {
        cy.viewport(width, 900);
        mountEntryForm();
        cy.get("[data-cy=transaction-entry-form]").then(($form) => {
          $form[0]!.style.width = `${width}px`;
        });
        if (mode === "Transfer") cy.contains("button", "Transfer").click();

        cy.get("[data-cy=transaction-entry-form]").should("be.visible");
        cy.get(".entry-form__row").should(($row) => {
          const row = $row[0];
          const rowBounds = row.getBoundingClientRect();
          const form = row.closest<HTMLElement>(".entry-form");
          expect(form).not.to.equal(null);
          const formBounds = form!.getBoundingClientRect();
          const items = Array.from(row.children) as HTMLElement[];
          const itemBounds = items.map((item) => item.getBoundingClientRect());
          const readingOrder = items.map(
            (item) =>
              item
                .querySelector(
                  ".field__label, .combobox-field__label, .memo-autocomplete__label, .binary-toggle__label",
                )
                ?.textContent?.trim() ?? "Add",
          );
          expect(readingOrder).to.deep.equal(
            mode === "Transaction"
              ? [
                  "Date",
                  "Account",
                  "Category",
                  "Amount",
                  "Direction",
                  "Memo",
                  "Status",
                  "Add",
                ]
              : [
                  "Date",
                  "From account",
                  "To account",
                  "Amount",
                  "Memo",
                  "Status",
                  "Add",
                ],
          );

          expect(row.scrollWidth).to.be.at.most(row.clientWidth + 1);
          expect(rowBounds.left).to.be.at.least(formBounds.left - 1);
          expect(rowBounds.right).to.be.at.most(formBounds.right + 1);
          for (const bounds of itemBounds) {
            expect(bounds.left).to.be.at.least(rowBounds.left - 1);
            expect(bounds.right).to.be.at.most(rowBounds.right + 1);
          }
          for (let first = 0; first < itemBounds.length; first += 1) {
            for (
              let second = first + 1;
              second < itemBounds.length;
              second += 1
            ) {
              const a = itemBounds[first]!;
              const b = itemBounds[second]!;
              const overlapsHorizontally =
                Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1;
              const overlapsVertically =
                Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1;
              expect(
                overlapsHorizontally && overlapsVertically,
                `grid items ${first} and ${second} intersect`,
              ).to.equal(false);
            }
          }

          const expectedRows = width <= 1152 ? 2 : 1;
          expect(
            new Set(itemBounds.map((bounds) => Math.round(bounds.bottom))).size,
          ).to.equal(expectedRows);

          for (const item of items) {
            const label = item.querySelector<HTMLElement>(
              ".field__label, .combobox-field__label, .memo-autocomplete__label, .binary-toggle__label",
            );
            if (!label) continue;
            const control = item.querySelector<HTMLElement>(
              "input, .combobox-field__trigger, .binary-toggle__button",
            );
            expect(control, "labeled field has a control").not.to.equal(null);
            const labelBounds = label.getBoundingClientRect();
            const controlBounds = control!.getBoundingClientRect();
            const minimumWidths: Record<string, number> = {
              Date: 112,
              Account: 120,
              "From account": 120,
              "To account": 120,
              Category: 120,
              Amount: 112,
              Direction: 100,
              Memo: 120,
              Status: 100,
            };
            expect(labelBounds.left).to.be.at.least(
              item.getBoundingClientRect().left - 1,
            );
            expect(controlBounds.left).to.be.at.least(
              item.getBoundingClientRect().left - 1,
            );
            expect(controlBounds.right).to.be.at.most(
              item.getBoundingClientRect().right + 1,
            );
            expect(controlBounds.top).to.be.at.least(labelBounds.bottom - 1);
            expect(controlBounds.width).to.be.at.least(
              minimumWidths[label.textContent?.trim() ?? ""] ?? 0,
            );
          }
        });
        cy.get("[data-cy=binary-toggle-status]")
          .should("be.visible")
          .and("be.enabled");
        cy.get('input[type="date"]').should(($input) => {
          expect($input[0]!.getBoundingClientRect().width).to.be.at.least(112);
        });
        cy.get('input[placeholder="0.00"]').should(($input) => {
          expect($input[0]!.getBoundingClientRect().width).to.be.at.least(112);
        });
        cy.get('[data-cy="binary-toggle-status"]').should(($button) => {
          expect($button[0]!.getBoundingClientRect().width).to.be.at.least(100);
        });
        if (mode === "Transaction") {
          cy.get('[data-cy="binary-toggle-direction"]').should(($button) => {
            expect($button[0]!.getBoundingClientRect().width).to.be.at.least(
              100,
            );
          });
        }
        cy.get("[data-cy=transaction-entry-form]")
          .contains("button", "Add")
          .should("be.visible")
          .and("be.enabled");
        cy.document().should((document) => {
          expect(document.documentElement.scrollWidth).to.be.at.most(
            document.documentElement.clientWidth + 1,
          );
        });
      });
    }
  }

  it("keeps keyboard submission available after responsive reflow", () => {
    cy.viewport(976, 900);
    const submit = cy.stub().as("entrySubmit");
    mountEntryForm(submit);

    cy.get(".entry-form__row .combobox-field__trigger").eq(1).click();
    cy.contains('[role="option"]', "Uncategorized").click();
    cy.get('input[placeholder="0.00"]').type("12.34{enter}");
    cy.get("@entrySubmit").should("have.been.calledOnce");
  });
});
