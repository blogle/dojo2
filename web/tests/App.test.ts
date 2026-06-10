import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "../src/dojo/App.vue";
import { router } from "../src/dojo/router";

describe("dojo app", () => {
  beforeEach(async () => {
    router.push("/");
    await router.isReady();
  });

  it("renders dojo skeleton and reports API reachability", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ app: "dojo", ready: false, mode: "skeleton" }),
      }),
    );

    const wrapper = mount(App, {
      global: {
        plugins: [router],
      },
    });

    expect(wrapper.text()).toContain("dojo");
    expect(wrapper.text()).toContain("Project skeleton is running.");
    expect(wrapper.text()).toContain("Checking API reachability...");

    await vi.waitFor(() => {
      expect(wrapper.text()).toContain("API reachable: skeleton mode");
    });
  });
});
