import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import App from "../src/dojo/App.vue";

describe("dojo app", () => {
  it("renders the frontend reset placeholder", () => {
    const wrapper = mount(App);

    expect(wrapper.text()).toContain("UI rebuild pending");
    expect(wrapper.text()).toContain("SPEC.md");
  });
});
