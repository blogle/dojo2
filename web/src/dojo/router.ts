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
      component: () => import("./pages/BudgetsPage.vue"),
    },
    {
      path: "/budgets",
      component: () => import("./pages/BudgetsPage.vue"),
    },
    {
      path: "/transactions",
      component: () => import("./pages/TransactionsPage.vue"),
    },
    {
      path: "/assets-liabilities",
      component: () => import("./pages/AssetsLiabilitiesPage.vue"),
    },
    {
      path: "/assets-liabilities/add",
      component: () => import("./pages/AddItemWizardPage.vue"),
    },
    {
      path: "/assets-liabilities/:id",
      component: () => import("./pages/AccountDetailPage.vue"),
    },
  ],
});

export default router;
