import { createApp } from "vue";

import App from "./dojo/App.vue";
import { router } from "./dojo/router";
import "./dojo/styles/tokens.css";
import "./dojo/styles/main.css";

createApp(App).use(router).mount("#app");
