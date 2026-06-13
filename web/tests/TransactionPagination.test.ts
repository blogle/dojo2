import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAppState } from "../src/dojo/state/app";
import type { Transaction } from "../src/dojo/types";
import { sampleTransactions } from "./helpers";

function buildTransactions(offset: number, count: number): Transaction[] {
  return Array.from({ length: count }, (_, index) => ({
    ...sampleTransactions[0],
    transaction_id: `tx-${offset + index}`,
    memo: `memo-${offset + index}`,
  }));
}

describe("transaction pagination state", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    useAppState().resetState();
  });

  it("requests a bounded initial page and replaces rows when paging", async () => {
    const total = 320;
    const fetchMock = vi.fn(async (input: string | URL | Request) => {
      const url = new URL(String(input));
      if (!url.pathname.endsWith("/api/transactions")) {
        throw new Error(`Unexpected request: ${url.toString()}`);
      }
      const offset = Number(url.searchParams.get("offset") ?? "0");
      const limit = Number(url.searchParams.get("limit") ?? "0");
      const remaining = Math.max(0, total - offset);
      const count = Math.min(limit, remaining);
      return {
        ok: true,
        json: async () => ({
          items: buildTransactions(offset, count),
          total,
          offset,
          limit,
          has_more: offset + count < total,
        }),
      };
    });

    vi.stubGlobal("fetch", fetchMock);

    const app = useAppState();
    await app.refreshTransactions();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const firstUrl = new URL(String(fetchMock.mock.calls[0]?.[0]));
    expect(firstUrl.searchParams.get("offset")).toBe("0");
    expect(firstUrl.searchParams.get("limit")).toBe("100");
    expect(app.state.transactions).toHaveLength(100);
    expect(app.state.transactions[0]?.transaction_id).toBe("tx-0");

    await app.loadMoreTransactions();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const secondUrl = new URL(String(fetchMock.mock.calls[1]?.[0]));
    expect(secondUrl.searchParams.get("offset")).toBe("100");
    expect(secondUrl.searchParams.get("limit")).toBe("100");
    expect(app.state.transactions).toHaveLength(100);
    expect(app.state.transactions[0]?.transaction_id).toBe("tx-100");
    expect(app.state.transactions[app.state.transactions.length - 1]?.transaction_id).toBe("tx-199");
  });
});
