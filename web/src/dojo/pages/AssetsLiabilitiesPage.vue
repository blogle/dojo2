<script setup lang="ts">
import { useQuery } from "@tanstack/vue-query";
import { computed } from "vue";
import { useRouter } from "vue-router";

import { fetchAssetsLiabilities } from "@/dojo/api/client";
import Button from "@/dojo/components/actions/Button.vue";
import MetricStrip from "@/dojo/components/data/MetricStrip.vue";
import NavigationRail from "@/dojo/components/navigation/NavigationRail.vue";
import PageHeader from "@/dojo/components/data/PageHeader.vue";
import StackedEntityCard from "@/dojo/components/data/StackedEntityCard.vue";
import { formatCurrency } from "@/dojo/utils/currency";

const router = useRouter();

const navItems = computed(() => [
  {
    kind: "route" as const,
    key: "home",
    label: "Home",
    icon: "foundations",
    href: "/",
  },
  {
    kind: "route" as const,
    key: "budget",
    label: "Budget",
    icon: "budget",
    href: "/budgets",
  },
  {
    kind: "route" as const,
    key: "transactions",
    label: "Transactions",
    icon: "transactions",
    href: "/transactions",
  },
  {
    kind: "route" as const,
    key: "assets-liabilities",
    label: "Assets",
    icon: "assets",
    href: "/assets-liabilities",
    current: true,
  },
]);

const { data, isLoading } = useQuery({
  queryKey: ["assets-liabilities"],
  queryFn: fetchAssetsLiabilities,
});

const metricItems = computed(() => {
  if (!data.value) {
    return [
      { key: "net-worth", label: "Net worth", loading: true },
      { key: "assets", label: "Total assets", loading: true },
      { key: "liabilities", label: "Total liabilities", loading: true },
    ];
  }

  return [
    {
      key: "net-worth",
      label: "Net worth",
      value: formatCurrency(data.value.net_worth_minor),
    },
    {
      key: "assets",
      label: "Total assets",
      value: formatCurrency(data.value.assets_minor),
    },
    {
      key: "liabilities",
      label: "Total liabilities",
      value: formatCurrency(data.value.liabilities_minor),
    },
  ];
});

const groupLabels: Record<string, string> = {
  CASH: "Cash and equivalents",
  INVESTMENTS: "Investments",
  TANGIBLE_ASSETS: "Tangible assets",
  CREDIT: "Credit",
  LOANS: "Loans",
};

const handleAddItem = () => {
  router.push("/assets-liabilities/add");
};

const handleCardSelect = (accountId: string) => {
  router.push(`/assets-liabilities/${accountId}`);
};
</script>

<template>
  <div class="assets-liabilities-page" data-cy="assets-liabilities-page">
    <NavigationRail
      :items="navItems"
      brand="dojo"
      aria-label="Main navigation"
    />

    <main class="assets-liabilities-page__main">
      <PageHeader
        title="Assets & Liabilities"
        subtitle="Track your complete net worth across all accounts and assets."
        :primary-actions="true"
      >
        <template #actions>
          <Button variant="primary" @click="handleAddItem"> Add item </Button>
        </template>
      </PageHeader>

      <MetricStrip
        :items="metricItems"
        class="assets-liabilities-page__metrics"
      />

      <div
        v-if="isLoading"
        class="assets-liabilities-page__loading"
        data-cy="assets-liabilities-loading"
      >
        Loading...
      </div>

      <div
        v-else-if="data?.groups"
        class="assets-liabilities-page__groups"
        data-cy="assets-liabilities-groups"
      >
        <section
          v-for="group in data.groups"
          :key="group.key"
          class="assets-liabilities-page__group"
          :data-cy="`group-${group.key.toLowerCase()}`"
        >
          <div class="assets-liabilities-page__group-header">
            <h2 class="assets-liabilities-page__group-title">
              {{ groupLabels[group.key] || group.key }}
            </h2>
            <span class="assets-liabilities-page__group-total">
              {{ formatCurrency(group.total_minor) }}
            </span>
          </div>

          <div class="assets-liabilities-page__group-items">
            <StackedEntityCard
              v-for="item in group.items"
              :key="item.account_id"
              :name="item.name"
              :primary-value="formatCurrency(item.value_minor)"
              :metadata="item.metadata"
              :source-of-truth="item.source_of_truth"
              :clickable="true"
              @select="handleCardSelect(item.account_id)"
            />
          </div>
        </section>
      </div>

      <div
        v-else
        class="assets-liabilities-page__empty"
        data-cy="assets-liabilities-empty"
      >
        <p>No accounts or assets configured yet.</p>
        <p class="assets-liabilities-page__empty-hint">
          Need to bring in Aspire data? Use Onboarding.
        </p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.assets-liabilities-page {
  display: flex;
  min-height: 100vh;
  background: var(--color-background);
}

.assets-liabilities-page__main {
  flex: 1;
  display: grid;
  gap: var(--space-xl);
  padding: var(--space-xl);
  max-width: var(--layout-page-max-width);
  margin: 0 auto;
  min-width: 0;
}

.assets-liabilities-page__metrics {
  width: 100%;
}

.assets-liabilities-page__loading {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  padding: var(--space-xl) 0;
}

.assets-liabilities-page__groups {
  display: grid;
  gap: var(--space-2xl);
}

.assets-liabilities-page__group {
  display: grid;
  gap: var(--space-lg);
}

.assets-liabilities-page__group-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-lg);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-outline);
}

.assets-liabilities-page__group-title {
  margin: 0;
  color: var(--color-on-surface);
  font-family: var(--text-headline-md-font-family);
  font-size: var(--text-headline-md-font-size);
  font-weight: var(--text-headline-md-font-weight);
  line-height: var(--text-headline-md-line-height);
  letter-spacing: var(--text-headline-md-letter-spacing);
}

.assets-liabilities-page__group-total {
  color: var(--color-on-surface-muted);
  font-family: var(--text-metric-md-font-family);
  font-size: var(--text-metric-md-font-size);
  font-weight: var(--text-metric-md-font-weight);
  line-height: var(--text-metric-md-line-height);
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.assets-liabilities-page__group-items {
  display: grid;
  gap: var(--space-sm);
}

.assets-liabilities-page__empty {
  color: var(--color-on-surface-muted);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  padding: var(--space-2xl) 0;
  text-align: center;
}

.assets-liabilities-page__empty-hint {
  margin-top: var(--space-sm);
  font-style: italic;
}
</style>
