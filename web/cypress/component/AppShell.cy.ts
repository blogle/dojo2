import { mount } from "cypress/vue";
import { createMemoryHistory, createRouter } from "vue-router";

import AppShell from "../../src/dojo/layouts/AppShell.vue";
import { useAppState } from "../../src/dojo/state/app";

describe("AppShell", () => {
  it("renders one pinned rail and scopes backup attention to content", () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/transactions",
          component: {
            template: '<div data-cy="shell-page">Transactions</div>',
          },
        },
      ],
    });
    const { state } = useAppState();
    state.appStatus = {
      app: "dojo",
      ready: true,
      mode: "local",
      needs_onboarding: false,
      needs_backup_setup: false,
      backup: { state: "degraded", message: "Backup failed." },
      latest_import_batch: null,
      latest_import_run: null,
    };

    router.push("/transactions");
    router.isReady().then(() => {
      mount(AppShell, { global: { plugins: [router] } });

      cy.get("[data-cy=app-shell]").within(() => {
        cy.get("[data-cy=navigation-rail-root]").should("have.length", 1);
        cy.get("[data-cy=navigation-rail-item-account]").should("not.exist");
        cy.get("[data-cy=app-shell-content]").within(() => {
          cy.get("[data-cy=persistent-warning-banner-root]").should(
            "contain.text",
            "Backup failed.",
          );
          cy.get("[data-cy=shell-page]").should("contain.text", "Transactions");
        });
      });

      cy.get("[data-cy=navigation-rail-root]").then(($rail) => {
        cy.get("[data-cy=persistent-warning-banner-root]").then(($banner) => {
          expect($banner[0].getBoundingClientRect().left).to.be.at.least(
            $rail[0].getBoundingClientRect().right,
          );
        });
      });
    });
  });
});
