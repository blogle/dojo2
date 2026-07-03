import { VueQueryPlugin } from "@tanstack/vue-query";
import { createApp } from "vue";

import App from "./dojo/App.vue";
import router from "./dojo/router";
import { createDojoQueryClient } from "./dojo/queryClient";
import "./dojo/design-system/tokens.css";
import "./dojo/styles/main.css";

const queryClient = createDojoQueryClient();

createApp(App).use(VueQueryPlugin, { queryClient }).use(router).mount("#app");
