import { QueryClient } from "@tanstack/vue-query";

export function createDojoQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: 1,
      },
      mutations: {
        retry: false,
      },
    },
  });
}
