import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import App from "../src/dojo/App.vue";
import { useAppState } from "../src/dojo/state/app";

describe("dojo app", () => {
  beforeEach(() => {
    useAppState().resetState();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the app shell with router-view", async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: "/dev/test",
          component: { template: "<div>budget page</div>" },
        },
      ],
    });

    router.push("/dev/test");
    await router.isReady();

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    });

    expect(wrapper.text()).toContain("budget page");
  });

  it("routes a fresh database to onboarding", async () => {
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = String(input);
      const payloads: Record<string, object> = {
        "/api/bootstrap": {
          app_status: {
            app: "dojo",
            ready: false,
            mode: "onboarding",
            needs_onboarding: true,
            latest_import_batch: null,
            latest_import_run: null,
          },
          import_status: null,
          default_budget_month: "2026-08",
        },
        "/api/onboarding/google/status": {
          configured: true,
          fixture_mode: false,
          authorized: false,
          message: "Google OAuth is configured and ready.",
        },
      };
      const payload = payloads[url];
      if (!payload) throw new Error(`Unexpected request: ${url}`);
      return {
        ok: true,
        json: async () => payload,
      } as Response;
    });
    vi.stubGlobal("fetch", fetchMock);

    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", component: { template: "<div>budget page</div>" } },
        {
          path: "/onboarding",
          component: { template: "<div>onboarding page</div>" },
        },
      ],
    });
    router.push("/");
    await router.isReady();

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    });
    await flushPromises();

    expect(router.currentRoute.value.path).toBe("/onboarding");
    expect(wrapper.text()).toContain("onboarding page");
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/bootstrap",
      expect.any(Object),
    );
  });
});
