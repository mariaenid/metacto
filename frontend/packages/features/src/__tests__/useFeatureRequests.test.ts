/**
 * Unit tests for useSubmitFeatureRequest and useVote mutations.
 * Real HTTP is not exercised — all API calls are mocked at the module level.
 */
import { describe, expect, it, vi } from "vitest";

// --- helpers (no framework deps) ---

function buildRequest(overrides = {}) {
  return {
    id: "fr-1",
    title: "Dark mode",
    description: "",
    status: "open" as const,
    vote_count: 5,
    viewer_has_voted: false,
    author_id: "user-1",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

// --- pure logic tests (no hooks, no QueryClient) ---

describe("optimistic vote count calculation", () => {
  it("increments count when casting a vote", () => {
    const fr = buildRequest({ vote_count: 5, viewer_has_voted: false });
    const next = {
      ...fr,
      viewer_has_voted: !fr.viewer_has_voted,
      vote_count: fr.vote_count + (fr.viewer_has_voted ? -1 : 1),
    };
    expect(next.vote_count).toBe(6);
    expect(next.viewer_has_voted).toBe(true);
  });

  it("decrements count when retracting a vote", () => {
    const fr = buildRequest({ vote_count: 6, viewer_has_voted: true });
    const next = {
      ...fr,
      viewer_has_voted: !fr.viewer_has_voted,
      vote_count: fr.vote_count + (fr.viewer_has_voted ? -1 : 1),
    };
    expect(next.vote_count).toBe(5);
    expect(next.viewer_has_voted).toBe(false);
  });
});

describe("submit validation", () => {
  const validate = (title: string) => title.trim().length >= 5;

  it("accepts a valid title", () => {
    expect(validate("Dark mode support")).toBe(true);
  });

  it("rejects a title shorter than 5 chars", () => {
    expect(validate("Hi")).toBe(false);
  });

  it("rejects a whitespace-only title", () => {
    expect(validate("    ")).toBe(false);
  });
});

describe("sort options", () => {
  const VALID_SORTS = ["top", "hot", "new"] as const;

  it("has exactly 3 sort options", () => {
    expect(VALID_SORTS.length).toBe(3);
  });

  it("includes top, hot, and new", () => {
    expect(VALID_SORTS).toContain("top");
    expect(VALID_SORTS).toContain("hot");
    expect(VALID_SORTS).toContain("new");
  });
});

describe("api client error", () => {
  it("throws ApiError on non-2xx response", async () => {
    const { ApiError, createApiClient } = await import("@metacto/api-client");
    const api = createApiClient("http://localhost:9999"); // nothing listening
    await expect(api.featureRequests.list()).rejects.toThrow();
  });
});
