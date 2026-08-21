import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createRouter, createMemoryHistory } from "vue-router";

import App from "../src/dojo/App.vue";

describe("dojo app", () => {
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
});
