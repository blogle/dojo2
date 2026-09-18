import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/dev/design-system",
      component: () => import("./pages/DesignSystemPage.vue"),
    },
    {
      path: "/onboarding",
      component: () => import("./pages/OnboardingPage.vue"),
    },
    {
      path: "/",
      component: () => import("./layouts/AppShell.vue"),
      children: [
        {
          path: "",
          component: () => import("./pages/BudgetsPage.vue"),
        },
        {
          path: "budgets",
          component: () => import("./pages/BudgetsPage.vue"),
        },
        {
          path: "budgets/available-to-budget",
          component: () => import("./pages/AvailableToBudgetPage.vue"),
        },
        {
          path: "transactions",
          component: () => import("./pages/TransactionsPage.vue"),
        },
        {
          path: "assets-liabilities",
          component: () => import("./layouts/AssetsLiabilitiesLayout.vue"),
          children: [
            {
              path: "",
              component: () => import("./pages/AssetsLiabilitiesPage.vue"),
            },
            {
              path: "add",
              component: () => import("./pages/AddItemWizardPage.vue"),
            },
            {
              path: ":id",
              component: () => import("./pages/AccountDetailPage.vue"),
            },
          ],
        },
      ],
    },
  ],
});

export default router;
