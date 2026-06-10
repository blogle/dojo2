import { createRouter, createWebHistory } from "vue-router";

import StaticWelcome from "./components/StaticWelcome.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: StaticWelcome,
    },
  ],
});
