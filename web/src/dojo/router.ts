import { createRouter, createWebHistory } from "vue-router";

import AccountsPage from "./pages/AccountsPage.vue";
import BudgetPage from "./pages/BudgetPage.vue";
import CategoriesPage from "./pages/CategoriesPage.vue";
import NetWorthPage from "./pages/NetWorthPage.vue";
import OnboardingPage from "./pages/OnboardingPage.vue";
import TransactionsPage from "./pages/TransactionsPage.vue";
import { useAppState } from "./state/app";

const routes = [
  { path: "/", redirect: "/budget" },
  { path: "/onboarding", name: "onboarding", component: OnboardingPage },
  { path: "/budget", name: "budget", component: BudgetPage },
  { path: "/transactions", name: "transactions", component: TransactionsPage },
  { path: "/accounts", name: "accounts", component: AccountsPage },
  { path: "/categories", name: "categories", component: CategoriesPage },
  { path: "/net-worth", name: "net-worth", component: NetWorthPage },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const app = useAppState();
  if (!app.state.appStatus) {
    await app.initialize();
  }
  if (!app.ready.value && to.name !== "onboarding") {
    return { name: "onboarding" };
  }
  if (app.ready.value && to.name === "onboarding") {
    return { name: "budget" };
  }
  return true;
});
