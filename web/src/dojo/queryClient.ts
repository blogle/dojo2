import { MutationCache, QueryClient } from "@tanstack/vue-query";

import {
  notifyMutationError,
  notifyMutationSuccess,
} from "./state/mutationFeedback";

export function createDojoQueryClient(): QueryClient {
  return new QueryClient({
    mutationCache: new MutationCache({
      onError: (error) => notifyMutationError(error),
      onSuccess: (_data, _variables, _context, mutation) => {
        const message = mutation.meta?.successMessage;
        if (typeof message === "string") notifyMutationSuccess(message);
      },
    }),
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
