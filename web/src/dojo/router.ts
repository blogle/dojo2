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
  ],
});

export default router;
