import { VueQueryPlugin } from "@tanstack/vue-query";
import { mount } from "cypress/vue";
import { createMemoryHistory, createRouter } from "vue-router";

import { createDojoQueryClient } from "../../src/dojo/queryClient";
import AddItemWizardPage from "../../src/dojo/pages/AddItemWizardPage.vue";
import AssetsLiabilitiesPage from "../../src/dojo/pages/AssetsLiabilitiesPage.vue";

const emptyAssetsLiabilities = {
  assets_minor: 0,
  liabilities_minor: 0,
  net_worth_minor: 0,
  needs_attention_count: 0,
  groups: [],
};

function stubFetch() {
  cy.stub(window, "fetch")
    .callsFake((url: string, init?: RequestInit) => {
      const path = new URL(url, "http://localhost").pathname;

      if (path === "/api/assets-liabilities") {
        return Promise.resolve(
          new Response(JSON.stringify(emptyAssetsLiabilities), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }

      if (path === "/api/accounts" && init?.method === "POST") {
        return Promise.resolve(
          new Response(JSON.stringify({ account_id: "new-account" }), {
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
    })
    .as("fetch");
}

function mountPage(initialPath = "/assets-liabilities/add") {
  stubFetch();
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/assets-liabilities", component: AssetsLiabilitiesPage },
      { path: "/assets-liabilities/add", component: AddItemWizardPage },
      {
        path: "/assets-liabilities/:id",
        component: { template: "<div>detail</div>" },
      },
      { path: "/onboarding", component: { template: "<div>onboarding</div>" } },
    ],
  });
  router.push(initialPath);
  cy.wrap(router.isReady());

  const queryClient = createDojoQueryClient();
  mount(AddItemWizardPage, {
    global: {
      plugins: [router, [VueQueryPlugin, { queryClient }]],
    },
  });
  return router;
}

describe("AddItemWizardPage", () => {
  it("renders the type-selection modal over the overview page", () => {
    mountPage();
    cy.get("[data-cy=add-item-wizard]").should("be.visible");
    cy.get("[data-cy=add-item-wizard]").should("contain.text", "Add item");
    cy.get("[data-cy=add-item-wizard]").should(
      "contain.text",
      "Choose entity type",
    );
    cy.get("[data-cy=entity-type-budget-account]").should(
      "contain.text",
      "Budget account",
    );
    cy.get("[data-cy=add-item-wizard]").should(
      "contain.text",
      "Need to bring in Aspire data? Use Onboarding.",
    );
  });

  it("keeps add route distinct from account detail route", () => {
    const router = mountPage();
    cy.wrap(null).then(() => {
      expect(router.currentRoute.value.path).to.eq("/assets-liabilities/add");
    });
    cy.get("[data-cy=add-item-wizard]").should("be.visible");
  });

  it("selects a type, enters details, and posts an account payload", () => {
    const router = mountPage("/assets-liabilities/add?type=loan");
    cy.get("[data-cy=entity-type-loan]").should(
      "have.class",
      "add-item-modal__type-card--selected",
    );
    cy.get("[data-cy=add-item-continue]").click();
    cy.get('input[name="name"]').type("Mortgage");
    cy.get('input[name="institution"]').type("Local Credit Union");
    cy.get('input[name="original-amount"]').type("250000");
    cy.get("[data-cy=add-item-continue]").click();

    cy.get("@fetch").should((fetchStub) => {
      const calls = (
        fetchStub as unknown as {
          getCalls: () => Array<{ args: [string, RequestInit?] }>;
        }
      ).getCalls();
      const postCall = calls.find((call) => {
        const path = new URL(call.args[0], "http://localhost").pathname;
        return path === "/api/accounts" && call.args[1]?.method === "POST";
      });
      expect(postCall, "POST /api/accounts").not.to.eq(undefined);
      if (!postCall) throw new Error("POST /api/accounts was not called");
      const body = JSON.parse(postCall.args[1]?.body as string);
      expect(body).to.include({
        name: "Mortgage",
        account_class: "LOAN",
        institution: "Local Credit Union",
        status: "IN_REPAYMENT",
      });
      expect(body.original_amount_minor).to.eq(25000000);
    });
    cy.wrap(null).then(() => {
      expect(router.currentRoute.value.path).to.eq(
        "/assets-liabilities/new-account",
      );
    });
  });
});
