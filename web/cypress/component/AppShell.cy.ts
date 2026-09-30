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
      backup: { state: "degraded", action: "retry", message: "Backup failed." },
      latest_backup_run: null,
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

  it("owns and restores the rail expansion preference", () => {
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

    cy.window().then((window) => {
      window.localStorage.removeItem("dojo.navigation-rail-expanded");
    });

    router.push("/transactions");
    router.isReady().then(() => {
      mount(AppShell, { global: { plugins: [router] } });

      cy.get("[data-cy=navigation-rail-toggle]").click();
      cy.window().should((window) => {
        expect(
          window.localStorage.getItem("dojo.navigation-rail-expanded"),
        ).to.equal("true");
      });

      mount(AppShell, { global: { plugins: [router] } });
      cy.get("[data-cy=navigation-rail-root]").should(
        "have.class",
        "navigation-rail--expanded",
      );
    });
  });

  it("polls and completes the exact manual backup run", () => {
    const runId = "00000000-0000-4000-8000-000000000040";
    cy.clock();
    cy.intercept("POST", "/api/settings/backup/run", {
      statusCode: 202,
      body: {
        status: "QUEUED",
        job_name: "dojo-backup-manual-test",
        run_id: runId,
      },
    }).as("queueBackup");
    cy.intercept(
      {
        method: "GET",
        url: `/api/settings/backup/runs/${runId}`,
        middleware: true,
        times: 1,
      },
      (request) =>
        request.reply({
          statusCode: 200,
          body: {
            backup_run_id: runId,
            trigger_kind: "MANUAL",
            status: "RUNNING",
            phase: "UPLOADING",
            error_message: null,
          },
        }),
    ).as("backupRunRunning");
    cy.intercept("GET", `/api/settings/backup/runs/${runId}`, {
      statusCode: 200,
      body: {
        backup_run_id: runId,
        trigger_kind: "MANUAL",
        status: "SUCCEEDED",
        phase: "COMPLETE",
        error_message: null,
      },
    }).as("backupRunTerminal");
    cy.intercept("GET", "/api/app/status", {
      statusCode: 200,
      body: {
        app: "dojo",
        ready: true,
        mode: "ready",
        needs_onboarding: false,
        needs_backup_setup: false,
        backup: {
          state: "degraded",
          action: "retry",
          message: "Backup failed.",
        },
        latest_backup_run: {
          backup_run_id: "00000000-0000-4000-8000-000000000099",
          trigger_kind: "SCHEDULED",
          status: "FAILED",
          phase: "VERIFYING",
        },
        latest_import_batch: null,
        latest_import_run: null,
      },
    }).as("appStatus");

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
      mode: "ready",
      needs_onboarding: false,
      needs_backup_setup: false,
      backup: { state: "degraded", action: "retry", message: "Backup failed." },
      latest_backup_run: null,
      latest_import_batch: null,
      latest_import_run: null,
    };
    router.push("/transactions");
    cy.wrap(router.isReady()).then(() => {
      mount(AppShell, { global: { plugins: [router] } });
      cy.contains("button", "Retry backup").click();
      cy.wait("@queueBackup");

      cy.tick(2000);
      cy.wait("@backupRunRunning");
      cy.wait("@appStatus");
      cy.get("[data-cy=persistent-warning-banner-root]").should(
        "contain.text",
        "A backup retry is in progress.",
      );

      cy.tick(2000);
      cy.wait("@backupRunTerminal");
      cy.wait("@appStatus");
      cy.contains("button", "Retry backup").should("be.visible");
      cy.get("@backupRunRunning.all").should("have.length", 1);
      cy.get("@backupRunTerminal.all").should("have.length", 1);
    });
  });
});
