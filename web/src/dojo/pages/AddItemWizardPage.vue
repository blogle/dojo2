<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { computed, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import {
  createAccount,
  fetchAccounts,
  fetchCategories,
} from "@/dojo/api/client";
import Button from "@/dojo/components/actions/Button.vue";
import CurrencyField from "@/dojo/components/forms/CurrencyField.vue";
import DatePicker from "@/dojo/components/forms/DatePicker.vue";
import InstitutionCombobox from "@/dojo/components/forms/InstitutionCombobox.vue";
import SelectField from "@/dojo/components/forms/SelectField.vue";
import TextField from "@/dojo/components/forms/TextField.vue";
import AssetsLiabilitiesPage from "@/dojo/pages/AssetsLiabilitiesPage.vue";
import { institutionSuggestions } from "@/dojo/utils/institutions";

type EntityType =
  | "budget-account"
  | "tracking-account"
  | "investment-account"
  | "loan"
  | "tangible-asset";

interface EntityTypeOption {
  key: EntityType;
  title: string;
  summary: string;
  detail: string;
  icon: "wallet" | "tag" | "trend" | "bank" | "home";
}

const entityTypes: EntityTypeOption[] = [
  {
    key: "budget-account",
    title: "Budget account",
    summary: "Inside the budget boundary.",
    detail: "Balances and transactions flow from your budget.",
    icon: "wallet",
  },
  {
    key: "tracking-account",
    title: "Tracking account",
    summary: "Track items outside the budget boundary.",
    detail: "Balances are for reference only.",
    icon: "tag",
  },
  {
    key: "investment-account",
    title: "Investment account",
    summary: "Outside the budget boundary.",
    detail: "Supports linked contribution categories.",
    icon: "trend",
  },
  {
    key: "loan",
    title: "Loan",
    summary: "Liability with a payment category and payment split tracking.",
    detail: "",
    icon: "bank",
  },
  {
    key: "tangible-asset",
    title: "Tangible asset",
    summary: "Physical asset with a value you track over time.",
    detail: "",
    icon: "home",
  },
];

const entityTypeKeys = new Set(entityTypes.map((type) => type.key));

const route = useRoute();
const router = useRouter();
const queryClient = useQueryClient();
const currentDate = new Date().toISOString().slice(0, 10);

const { data: existingAccounts } = useQuery({
  queryKey: ["accounts", { showHidden: true }],
  queryFn: () => fetchAccounts(true),
});

const suggestedInstitutions = computed(() =>
  institutionSuggestions(
    existingAccounts.value?.map((account) => account.institution) ?? [],
  ),
);
const { data: categoriesResponse } = useQuery({
  queryKey: ["categories", currentDate.slice(0, 7)],
  queryFn: () => fetchCategories(currentDate.slice(0, 7), false),
});
const categoryOptions = computed(() =>
  (categoriesResponse.value?.items ?? [])
    .filter((category) => category.category_kind === "STANDARD")
    .map((category) => ({ value: category.category_id, label: category.name })),
);
const investmentCategoryOptions = computed(() => [
  { value: "", label: "Do not link a category yet" },
  ...categoryOptions.value,
]);

const initialType = Array.isArray(route.query.type)
  ? route.query.type[0]
  : route.query.type;

const selectedType = ref<EntityType | null>(
  initialType && entityTypeKeys.has(initialType as EntityType)
    ? (initialType as EntityType)
    : null,
);
const step = ref<1 | 2 | 3>(1);
const submitError = ref<string | null>(null);

const form = reactive({
  name: "",
  institution: "",
  accountNumberLast4: "",
  budgetAccountType: "DEPOSIT",
  trackingPolarity: "ASSET",
  apyPercent: "",
  investmentSelfManaged: "false",
  investmentTaxTreatment: "TAXABLE_BROKERAGE",
  investmentContributionCategoryId: "",
  loanPaymentCategoryId: "",
  currentPrincipal: "",
  currentPrincipalAsOf: currentDate,
  originalAmount: "",
  originationDate: "",
  ratePercent: "",
  rateType: "FIXED",
  scheduledPrincipalInterest: "",
  paymentFrequency: "MONTHLY",
  nextPaymentDate: "",
  maturityDate: "",
  remainingTermMonths: "",
  recurringExtraPrincipal: "",
  openingValuation: "",
  openingValuationDate: "",
});

watch(
  () => route.query.type,
  (value) => {
    const queryType = Array.isArray(value) ? value[0] : value;
    if (queryType && entityTypeKeys.has(queryType as EntityType)) {
      selectedType.value = queryType as EntityType;
    }
  },
);

const selectedEntity = computed(() =>
  entityTypes.find((type) => type.key === selectedType.value),
);

const canContinue = computed(() => {
  if (step.value === 1) {
    return selectedType.value !== null;
  }
  if (step.value === 2) {
    const hasRequiredCategory =
      selectedType.value === "loan"
        ? form.loanPaymentCategoryId.length > 0 &&
          parseCurrencyMinor(form.currentPrincipal) !== undefined &&
          form.currentPrincipalAsOf.length > 0
        : true;
    return form.name.trim().length > 0 && hasRequiredCategory;
  }
  return true;
});

const typeSelectOptions = entityTypes.map((type) => ({
  value: type.key,
  label: type.title,
}));

const budgetTypeOptions = [
  { value: "DEPOSIT", label: "Deposit account" },
  { value: "CREDIT_CARD", label: "Credit card" },
];

const polarityOptions = [
  { value: "ASSET", label: "Asset" },
  { value: "LIABILITY", label: "Liability" },
];

const taxTreatmentOptions = [
  { value: "TAXABLE_BROKERAGE", label: "Taxable brokerage" },
  { value: "TRADITIONAL_IRA", label: "Traditional IRA" },
  { value: "ROTH_IRA", label: "Roth IRA" },
  { value: "SEP_IRA", label: "SEP IRA" },
  { value: "SIMPLE_IRA", label: "SIMPLE IRA" },
  { value: "TRADITIONAL_401K", label: "Traditional 401(k)" },
  { value: "ROTH_401K", label: "Roth 401(k)" },
  { value: "TRADITIONAL_403B", label: "Traditional 403(b)" },
  { value: "ROTH_403B", label: "Roth 403(b)" },
  { value: "TRADITIONAL_457B", label: "Traditional 457(b)" },
  { value: "ROTH_457B", label: "Roth 457(b)" },
  { value: "HSA", label: "HSA" },
  { value: "EDUCATION_529", label: "529 education account" },
  { value: "CUSTODIAL", label: "Custodial account" },
  { value: "OTHER_TAX_ADVANTAGED", label: "Other tax-advantaged" },
];

const managementStyleOptions = [
  { value: "false", label: "Managed" },
  { value: "true", label: "Self-managed" },
];

const parseCurrencyMinor = (value: string) => {
  const normalized = value.replace(/[$,]/g, "").trim();
  if (!normalized) return undefined;
  const amount = Number(normalized);
  if (!Number.isFinite(amount)) return undefined;
  return Math.round(amount * 100);
};

const parsePercentMinor = (value: string) => {
  const normalized = value.replace(/%/g, "").trim();
  if (!normalized) return undefined;
  const amount = Number(normalized);
  if (!Number.isFinite(amount)) return undefined;
  return Math.round(amount * 100);
};

const nonEmpty = (value: string) => {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : undefined;
};

const accountClassForType = (type: EntityType) => {
  const accountClasses: Record<EntityType, string> = {
    "budget-account": "BUDGET",
    "tracking-account": "TRACKING",
    "investment-account": "INVESTMENT",
    loan: "LOAN",
    "tangible-asset": "TANGIBLE_ASSET",
  };
  return accountClasses[type];
};

const buildPayload = () => {
  if (!selectedType.value) {
    throw new Error("Choose an entity type before continuing.");
  }

  const payload: Record<string, unknown> = {
    name: form.name.trim(),
    account_class: accountClassForType(selectedType.value),
  };

  const institution = nonEmpty(form.institution);
  const accountNumberLast4 = nonEmpty(form.accountNumberLast4);
  if (institution) payload.institution = institution;
  if (accountNumberLast4) payload.account_number_last4 = accountNumberLast4;

  if (selectedType.value === "budget-account") {
    payload.budget_account_type = form.budgetAccountType;
    const apyMinor = parsePercentMinor(form.apyPercent);
    if (apyMinor !== undefined) payload.apy_minor = apyMinor;
  } else if (selectedType.value === "tracking-account") {
    payload.polarity = form.trackingPolarity;
  } else if (selectedType.value === "investment-account") {
    payload.self_managed = form.investmentSelfManaged === "true";
    payload.tax_treatment = form.investmentTaxTreatment;
    if (form.investmentContributionCategoryId) {
      payload.investment_contribution_category_id =
        form.investmentContributionCategoryId;
    }
  } else if (selectedType.value === "loan") {
    payload.current_principal_minor = parseCurrencyMinor(form.currentPrincipal);
    payload.current_principal_as_of = form.currentPrincipalAsOf;
    const originalAmountMinor = parseCurrencyMinor(form.originalAmount);
    const rateMinor = parsePercentMinor(form.ratePercent);
    const scheduledPaymentMinor = parseCurrencyMinor(
      form.scheduledPrincipalInterest,
    );
    const recurringExtraMinor = parseCurrencyMinor(
      form.recurringExtraPrincipal,
    );
    if (originalAmountMinor !== undefined) {
      payload.original_amount_minor = originalAmountMinor;
    }
    if (form.originationDate) payload.origination_date = form.originationDate;
    if (rateMinor !== undefined) payload.rate_minor = rateMinor;
    if (rateMinor !== undefined) payload.rate_type = form.rateType;
    if (scheduledPaymentMinor !== undefined) {
      payload.scheduled_principal_interest_minor = scheduledPaymentMinor;
    }
    if (form.nextPaymentDate) {
      payload.next_payment_date = form.nextPaymentDate;
      payload.payment_frequency = form.paymentFrequency;
    }
    if (form.maturityDate) payload.maturity_date = form.maturityDate;
    if (form.remainingTermMonths) {
      payload.remaining_term_months = Number(form.remainingTermMonths);
    }
    if (recurringExtraMinor !== undefined) {
      payload.recurring_extra_principal_minor = recurringExtraMinor;
    }
    payload.status = "IN_REPAYMENT";
    payload.loan_payment_category_id = form.loanPaymentCategoryId;
  } else if (selectedType.value === "tangible-asset") {
    const openingValuationMinor = parseCurrencyMinor(form.openingValuation);
    if (openingValuationMinor !== undefined) {
      payload.opening_valuation_minor = openingValuationMinor;
    }
    if (form.openingValuationDate) {
      payload.opening_valuation_date = form.openingValuationDate;
    }
  }

  return payload;
};

const createAccountMutation = useMutation({
  mutationFn: createAccount,
  onSuccess: async ({ account_id }) => {
    step.value = 3;
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["assets-liabilities"] }),
      queryClient.invalidateQueries({ queryKey: ["accounts"] }),
      queryClient.invalidateQueries({ queryKey: ["net-worth"] }),
    ]);
    await router.push(`/assets-liabilities/${account_id}`);
  },
  onError: (error) => {
    submitError.value =
      error instanceof Error ? error.message : "Unable to add item.";
  },
});

const selectType = (type: EntityType) => {
  selectedType.value = type;
  submitError.value = null;
  router.replace({ path: "/assets-liabilities/add", query: { type } });
};

const closeWizard = () => {
  router.push("/assets-liabilities");
};

const continueWizard = () => {
  submitError.value = null;
  if (step.value === 1 && selectedType.value) {
    step.value = 2;
  } else if (step.value === 2) {
    createAccountMutation.mutate(buildPayload());
  }
};

const backWizard = () => {
  submitError.value = null;
  if (step.value === 2) {
    step.value = 1;
  } else {
    closeWizard();
  }
};
</script>

<template>
  <div class="add-item-page" data-cy="add-item-wizard-page">
    <AssetsLiabilitiesPage />

    <div class="add-item-page__scrim" role="presentation">
      <section
        class="add-item-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-item-title"
        data-cy="add-item-wizard"
      >
        <header class="add-item-modal__header">
          <h1 id="add-item-title" class="add-item-modal__title">Add item</h1>
          <button
            type="button"
            class="add-item-modal__close"
            aria-label="Close"
            data-cy="add-item-close"
            @click="closeWizard"
          >
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="M5 5l10 10M15 5L5 15"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
              />
            </svg>
          </button>
        </header>

        <ol class="add-item-modal__steps" aria-label="Add item steps">
          <li class="add-item-modal__step add-item-modal__step--active">
            <span class="add-item-modal__step-number">1</span>
            <span class="add-item-modal__step-label">Choose entity type</span>
          </li>
          <li
            class="add-item-modal__step"
            :class="{ 'add-item-modal__step--active': step >= 2 }"
          >
            <span class="add-item-modal__step-line"></span>
            <span class="add-item-modal__step-number">2</span>
            <span class="add-item-modal__step-label">Enter details</span>
          </li>
          <li
            class="add-item-modal__step"
            :class="{ 'add-item-modal__step--active': step >= 3 }"
          >
            <span class="add-item-modal__step-line"></span>
            <span class="add-item-modal__step-number">3</span>
            <span class="add-item-modal__step-label">Confirm & add</span>
          </li>
        </ol>

        <div v-if="step === 1" class="add-item-modal__body">
          <p class="add-item-modal__intro">
            Select the type of item you want to add to Assets & Liabilities.
          </p>

          <div class="add-item-modal__type-list">
            <button
              v-for="type in entityTypes"
              :key="type.key"
              type="button"
              class="add-item-modal__type-card"
              :class="{
                'add-item-modal__type-card--selected':
                  selectedType === type.key,
              }"
              :data-cy="`entity-type-${type.key}`"
              @click="selectType(type.key)"
            >
              <span class="add-item-modal__type-icon" aria-hidden="true">
                <svg
                  v-if="type.icon === 'wallet'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <rect x="4" y="7" width="16" height="11" rx="2" />
                  <path d="M7 7V5h12v4M16 13h.01" />
                </svg>
                <svg
                  v-else-if="type.icon === 'tag'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path d="M4 12l8-8h6l2 2v6l-8 8-8-8z" />
                  <circle cx="16" cy="8" r="1.3" />
                </svg>
                <svg
                  v-else-if="type.icon === 'trend'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path d="M4 18l5-5 4 3 6-8" />
                  <path d="M15 8h4v4M4 12v6M10 14v4M16 11v7" />
                </svg>
                <svg
                  v-else-if="type.icon === 'bank'"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path d="M4 10h16L12 5 4 10z" />
                  <path d="M6 10v8M10 10v8M14 10v8M18 10v8M4 20h16" />
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none">
                  <path d="M4 11l8-7 8 7" />
                  <path d="M6 10v10h12V10M10 20v-6h4v6" />
                </svg>
              </span>
              <span class="add-item-modal__type-copy">
                <span class="add-item-modal__type-title">{{ type.title }}</span>
                <span class="add-item-modal__type-summary">{{
                  type.summary
                }}</span>
                <span v-if="type.detail" class="add-item-modal__type-detail">
                  {{ type.detail }}
                </span>
              </span>
              <svg
                class="add-item-modal__type-arrow"
                viewBox="0 0 20 20"
                fill="none"
              >
                <path
                  d="M7.5 4.5L13 10l-5.5 5.5"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </button>
          </div>

          <aside class="add-item-modal__boundary-note">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <circle cx="10" cy="10" r="8" />
              <path d="M10 9.5v4M10 6.5h.01" />
            </svg>
            <div>
              <strong>About the budget boundary</strong>
              <p>
                Budget accounts live inside the budget boundary and are driven
                by your budget and transactions.
              </p>
              <p>
                Other accounts, investments, loans, and tangible assets live
                outside the budget boundary and are managed separately. This
                keeps your budget clean while giving you a complete financial
                picture.
              </p>
            </div>
          </aside>
        </div>

        <form
          v-else
          class="add-item-modal__body"
          @submit.prevent="continueWizard"
        >
          <p class="add-item-modal__intro">
            Enter the basic details for
            {{ selectedEntity?.title.toLowerCase() || "this item" }}. You can
            add valuations, payments, transactions, and reconciliation details
            later.
          </p>

          <div class="add-item-modal__form-grid">
            <SelectField
              :model-value="selectedType ?? ''"
              label="Entity type"
              :options="typeSelectOptions"
              name="entity-type"
              @update:model-value="selectType($event as EntityType)"
            />
            <TextField
              v-model="form.name"
              label="Name"
              name="name"
              placeholder="Account or item name"
              data-cy="add-item-name"
            />
            <InstitutionCombobox
              v-model="form.institution"
              name="institution"
              :options="suggestedInstitutions"
            />
            <TextField
              v-model="form.accountNumberLast4"
              label="Account / ID"
              name="account-number-last4"
              placeholder="Last 4 digits, optional"
              inputmode="numeric"
            />

            <template v-if="selectedType === 'budget-account'">
              <SelectField
                v-model="form.budgetAccountType"
                label="Budget account type"
                name="budget-account-type"
                :options="budgetTypeOptions"
              />
              <TextField
                v-model="form.apyPercent"
                label="APY"
                name="apy"
                placeholder="Optional percent"
                inputmode="decimal"
              />
            </template>

            <template v-else-if="selectedType === 'tracking-account'">
              <SelectField
                v-model="form.trackingPolarity"
                label="Polarity"
                name="polarity"
                :options="polarityOptions"
              />
            </template>

            <template v-else-if="selectedType === 'investment-account'">
              <SelectField
                v-model="form.investmentSelfManaged"
                label="Management style"
                name="self-managed"
                :options="managementStyleOptions"
              />
              <SelectField
                v-model="form.investmentTaxTreatment"
                label="Tax treatment"
                name="tax-treatment"
                :options="taxTreatmentOptions"
              />
              <SelectField
                v-model="form.investmentContributionCategoryId"
                label="Contribution category"
                name="investment-contribution-category"
                :options="investmentCategoryOptions"
              />
            </template>

            <template v-else-if="selectedType === 'loan'">
              <SelectField
                v-model="form.loanPaymentCategoryId"
                label="Payment category"
                name="loan-payment-category"
                :options="categoryOptions"
              />
              <CurrencyField
                v-model="form.currentPrincipal"
                label="Current principal"
                name="current-principal"
              />
              <DatePicker
                v-model="form.currentPrincipalAsOf"
                label="Principal as of"
                name="current-principal-as-of"
                :max="currentDate"
              />
              <CurrencyField
                v-model="form.originalAmount"
                label="Original amount"
                name="original-amount"
                placeholder="Optional"
              />
              <DatePicker
                v-model="form.originationDate"
                label="Origination date"
                name="origination-date"
              />
              <TextField
                v-model="form.ratePercent"
                label="Rate"
                name="rate"
                placeholder="Optional percent"
                inputmode="decimal"
              />
              <SelectField
                v-model="form.rateType"
                label="Rate type"
                name="rate-type"
                :options="[
                  { value: 'FIXED', label: 'Fixed' },
                  { value: 'VARIABLE', label: 'Variable' },
                ]"
              />
              <CurrencyField
                v-model="form.scheduledPrincipalInterest"
                label="Scheduled principal and interest"
                name="scheduled-principal-interest"
                placeholder="Optional"
              />
              <SelectField
                v-model="form.paymentFrequency"
                label="Payment frequency"
                name="payment-frequency"
                :options="[
                  { value: 'MONTHLY', label: 'Monthly' },
                  { value: 'BIWEEKLY', label: 'Every two weeks' },
                  { value: 'WEEKLY', label: 'Weekly' },
                ]"
              />
              <DatePicker
                v-model="form.nextPaymentDate"
                label="Next payment date"
                name="next-payment-date"
              />
              <DatePicker
                v-model="form.maturityDate"
                label="Maturity date"
                name="maturity-date"
              />
              <TextField
                v-model="form.remainingTermMonths"
                label="Remaining term in months"
                name="remaining-term-months"
                placeholder="Optional"
                inputmode="numeric"
              />
              <CurrencyField
                v-model="form.recurringExtraPrincipal"
                label="Recurring extra principal"
                name="recurring-extra-principal"
                placeholder="Optional"
              />
            </template>

            <template v-else-if="selectedType === 'tangible-asset'">
              <CurrencyField
                v-model="form.openingValuation"
                label="Opening valuation"
                name="opening-valuation"
                placeholder="Optional"
              />
              <DatePicker
                v-model="form.openingValuationDate"
                label="Valuation date"
                name="opening-valuation-date"
                :max="currentDate"
              />
            </template>
          </div>

          <p
            v-if="submitError"
            class="add-item-modal__error"
            data-cy="add-item-error"
          >
            {{ submitError }}
          </p>
        </form>

        <footer class="add-item-modal__footer">
          <div class="add-item-modal__actions">
            <Button variant="secondary" @click="backWizard">
              {{ step === 1 ? "Cancel" : "Back" }}
            </Button>
            <Button
              :disabled="!canContinue"
              :loading="createAccountMutation.isPending.value"
              data-cy="add-item-continue"
              @click="continueWizard"
            >
              {{ step === 1 ? "Continue" : "Add item" }}
            </Button>
          </div>
        </footer>
      </section>
    </div>
  </div>
</template>

<style scoped>
.add-item-page {
  min-height: 100vh;
  background: var(--color-background);
}

.add-item-page__scrim {
  position: fixed;
  inset: 0;
  z-index: 300;
  display: grid;
  place-items: center;
  padding: var(--space-xl);
  background: var(--color-scrim);
}

.add-item-modal {
  width: min(100%, 760px);
  max-height: calc(100vh - var(--space-xl) * 2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-modal);
}

.add-item-modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding: var(--space-lg) var(--space-xl) var(--space-sm);
}

.add-item-modal__title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-lg-font-family);
  font-size: var(--text-headline-lg-font-size);
  font-weight: var(--text-headline-lg-font-weight);
  line-height: var(--text-headline-lg-line-height);
  letter-spacing: var(--text-headline-lg-letter-spacing, -0.018em);
}

.add-item-modal__close {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-surface);
  cursor: pointer;
}

.add-item-modal__close:hover {
  background: var(--color-surface-muted);
}

.add-item-modal__close svg {
  width: 20px;
  height: 20px;
}

.add-item-modal__steps {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  align-items: center;
  gap: var(--space-sm);
  margin: 0;
  padding: 0 var(--space-xl) var(--space-md);
  list-style: none;
}

.add-item-modal__step {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  min-width: 0;
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
  line-height: var(--text-label-md-line-height);
}

.add-item-modal__step-line {
  flex: 1;
  height: 1px;
  background: var(--color-outline);
}

.add-item-modal__step-number {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-full);
  background: var(--color-surface-raised);
  color: var(--color-on-surface-muted);
}

.add-item-modal__step--active {
  color: var(--color-on-surface);
}

.add-item-modal__step--active .add-item-modal__step-number {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.add-item-modal__body {
  display: grid;
  gap: var(--space-sm);
  padding: 0 var(--space-xl) var(--space-md);
  overflow-y: auto;
}

.add-item-modal__intro {
  margin: 0 0 var(--space-xs);
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.add-item-modal__type-list {
  display: grid;
  gap: var(--space-sm);
}

.add-item-modal__type-card {
  display: grid;
  grid-template-columns: 52px 1fr 24px;
  align-items: center;
  gap: var(--space-md);
  width: 100%;
  min-height: 72px;
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-sm);
  background: var(--color-surface-raised);
  color: var(--color-on-surface);
  text-align: left;
  cursor: pointer;
  transition:
    background var(--transition-fast) var(--ease-out),
    border-color var(--transition-fast) var(--ease-out);
}

.add-item-modal__type-card:hover,
.add-item-modal__type-card--selected {
  border-color: var(--color-primary);
  background: var(--color-surface-selected);
}

.add-item-modal__type-icon {
  color: var(--color-primary);
}

.add-item-modal__type-icon svg {
  width: 36px;
  height: 36px;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.add-item-modal__type-copy {
  display: grid;
  gap: var(--space-micro);
}

.add-item-modal__type-title {
  color: var(--color-on-surface);
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.add-item-modal__type-summary,
.add-item-modal__type-detail {
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.add-item-modal__type-arrow {
  width: 22px;
  height: 22px;
  justify-self: end;
  color: var(--color-on-surface);
}

.add-item-modal__boundary-note {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: var(--space-sm);
  margin-top: var(--space-xs);
  padding: var(--space-md) var(--space-lg);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-sm);
  background: color-mix(in srgb, var(--color-surface-muted) 45%, transparent);
  color: var(--color-on-surface);
}

.add-item-modal__boundary-note svg,
.add-item-modal__onboarding-note svg {
  width: 20px;
  height: 20px;
  stroke: var(--color-primary);
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.add-item-modal__boundary-note strong {
  display: block;
  margin-bottom: var(--space-xs);
  font-family: var(--text-label-md-font-family);
  font-size: var(--text-label-md-font-size);
  font-weight: var(--text-label-md-font-weight);
}

.add-item-modal__boundary-note p {
  margin: 0;
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.add-item-modal__boundary-note p + p {
  margin-top: var(--space-xs);
}

.add-item-modal__form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-md);
}

.add-item-modal__error {
  margin: 0;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
  background: var(--color-error-container);
  color: var(--color-error);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
}

.add-item-modal__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-sm) var(--space-xl) var(--space-lg);
}

.add-item-modal__onboarding-note {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  color: var(--color-on-surface);
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  font-weight: var(--text-body-sm-font-weight);
  line-height: var(--text-body-sm-line-height);
}

.add-item-modal__onboarding-note a {
  color: var(--color-primary);
  font-weight: 600;
}

.add-item-modal__onboarding-note small {
  display: block;
  margin-top: var(--space-xs);
  color: var(--color-on-surface-muted);
  font: inherit;
}

.add-item-modal__actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

@media (max-width: 760px) {
  .add-item-page__scrim {
    align-items: end;
    padding: var(--space-sm);
  }

  .add-item-modal {
    max-height: calc(100vh - var(--space-md));
  }

  .add-item-modal__header,
  .add-item-modal__steps,
  .add-item-modal__body,
  .add-item-modal__footer {
    padding-left: var(--space-lg);
    padding-right: var(--space-lg);
  }

  .add-item-modal__steps {
    grid-template-columns: 1fr;
  }

  .add-item-modal__step-line {
    display: none;
  }

  .add-item-modal__type-card,
  .add-item-modal__boundary-note,
  .add-item-modal__form-grid {
    grid-template-columns: 1fr;
  }

  .add-item-modal__type-arrow {
    display: none;
  }

  .add-item-modal__footer {
    align-items: stretch;
    flex-direction: column;
  }

  .add-item-modal__actions {
    justify-content: flex-end;
  }
}
</style>
