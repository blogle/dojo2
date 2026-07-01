import { defineComponent, h } from "vue";

import type {
  ComponentFixtureScenario,
  ComponentFixtureSet,
} from "@/dojo/components/fixtures";

const createSlots = (slots: Record<string, string> | undefined) => {
  if (!slots) {
    return undefined;
  }

  return Object.fromEntries(
    Object.entries(slots).map(([name, content]) => [
      name,
      () => h("span", { style: "display: contents", innerHTML: content }),
    ]),
  );
};

export default defineComponent({
  name: "FixtureScenarioRenderer",
  props: {
    fixture: {
      type: Object as () => ComponentFixtureSet,
      required: true,
    },
    scenario: {
      type: Object as () => ComponentFixtureScenario,
      required: true,
    },
  },
  setup(props) {
    return () =>
      h(
        props.fixture.component,
        props.scenario.props ?? {},
        createSlots(props.scenario.slots),
      );
  },
});
