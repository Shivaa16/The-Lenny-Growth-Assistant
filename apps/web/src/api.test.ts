import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, getProviderInfo } from "./api";

describe("API error handling", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("turns a network failure into an actionable offline error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(getProviderInfo()).rejects.toMatchObject({
      code: "offline",
      status: 0,
      message: "The API is unavailable. Start FastAPI and PostgreSQL, then retry."
    } satisfies Partial<ApiError>);
  });

  it("explains an unstructured server failure instead of showing a generic message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("Bad Gateway", { status: 502 })));

    await expect(getProviderInfo()).rejects.toMatchObject({
      status: 502,
      message: "The API or one of its required services is unavailable. Start FastAPI and PostgreSQL, then retry."
    } satisfies Partial<ApiError>);
  });

  it("preserves a structured error message returned by the API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json(
          { error: { code: "persistence_unavailable", message: "Conversation storage is temporarily unavailable." } },
          { status: 503 }
        )
      )
    );

    await expect(getProviderInfo()).rejects.toMatchObject({
      code: "persistence_unavailable",
      status: 503,
      message: "Conversation storage is temporarily unavailable."
    } satisfies Partial<ApiError>);
  });
});
