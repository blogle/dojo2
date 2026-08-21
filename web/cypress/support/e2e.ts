/// <reference types="cypress" />

declare global {
  // Cypress augments Chainable through its namespace-based type contract.
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      resetScenario(scenario: string): Chainable<void>;
    }
  }
}

Cypress.Commands.add("resetScenario", (scenario: string) => {
  const apiBaseUrl = String(Cypress.env("apiBaseUrl")).replace(/\/$/, "");
  const token = Cypress.env("e2eToken");

  return cy
    .request({
      method: "POST",
      url: `${apiBaseUrl}/__e2e/reset`,
      headers: { "X-Dojo-E2E-Token": token },
      body: { scenario },
    })
    .then((response) => {
      expect(response.body).to.include({ scenario });
      expect(response.body).to.have.property("fixture_fingerprint");
      expect(response.body).to.have.property("restore_ms");
      expect(response.body).to.have.property("reopen_ms");
      Cypress.env("resetMetrics", response.body);
    });
});

let apiRequests: Array<{ url: string; statusCode: number }> = [];

beforeEach(() => {
  apiRequests = [];
  cy.clock(new Date("2026-02-15T12:00:00Z").getTime(), ["Date"]);
  const apiBaseUrl = String(Cypress.env("apiBaseUrl")).replace(/\/$/, "");
  cy.intercept(`${apiBaseUrl}/api/**`, (request) => {
    request.on("response", (response) => {
      apiRequests.push({ url: request.url, statusCode: response.statusCode });
    });
  });
});

Cypress.on("window:before:load", (window) => {
  const style = window.document.createElement("style");
  style.textContent =
    "*, *::before, *::after { animation: none !important; transition: none !important; }";
  window.document.head.appendChild(style);
});

afterEach(function () {
  cy.task("recordE2eTest", {
    spec: Cypress.spec.relative,
    title: this.currentTest?.title,
    state: this.currentTest?.state,
    durationMs: this.currentTest?.duration,
    requestCount: apiRequests.length,
    failedRequestCount: apiRequests.filter(
      (request) => request.statusCode >= 400,
    ).length,
    reset: Cypress.env("resetMetrics"),
  });
});

export {};
