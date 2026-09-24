import { mount } from "cypress/vue";
import { computed, defineComponent, h, ref } from "vue";

import fixtures from "../../src/dojo/components/forms/MemoAutocompleteField.fixtures";
import MemoAutocompleteField from "../../src/dojo/components/forms/MemoAutocompleteField.vue";

const controlledMemoField = defineComponent({
  setup() {
    const memo = ref("");
    const suggestions = computed(() =>
      memo.value.toLocaleLowerCase().includes("groc")
        ? ["Groceries", "Grocery market"]
        : [],
    );
    return () =>
      h(MemoAutocompleteField, {
        label: "Memo",
        modelValue: memo.value,
        suggestions: suggestions.value,
        "onUpdate:modelValue": (value: string) => (memo.value = value),
      });
  },
});

describe("MemoAutocompleteField", () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      mount(fixtures.component, { props: scenario.props });
      cy.get('[data-cy="memo-autocomplete-input"]')
        .should("be.visible")
        .and("have.value", "Grocery market")
        .and("have.attr", "type", "text");
      cy.get('[data-cy="memo-autocomplete-field"] button').should("not.exist");
    });
  });

  it("shows fuzzy suggestions, selects a prior memo, preserves free text, and dismisses without losing input", () => {
    mount(controlledMemoField);

    cy.get('[data-cy="memo-autocomplete-input"]').type("groc");
    cy.get('[role="listbox"]').should("be.visible");
    cy.get('[role="option"]').should("have.length", 2);
    cy.get('[role="option"]').contains("Groceries").click();
    cy.get('[data-cy="memo-autocomplete-input"]').should(
      "have.value",
      "Groceries",
    );
    cy.get('[role="listbox"]').should("not.exist");

    cy.get('[data-cy="memo-autocomplete-input"]')
      .clear()
      .type("Brand new memo");
    cy.get('[data-cy="memo-autocomplete-input"]').should(
      "have.value",
      "Brand new memo",
    );

    cy.get('[data-cy="memo-autocomplete-input"]').clear().type("groc{esc}");
    cy.get('[data-cy="memo-autocomplete-input"]')
      .should("have.value", "groc")
      .and("have.attr", "aria-expanded", "false");
    cy.get('[role="listbox"]').should("not.exist");
  });
});
