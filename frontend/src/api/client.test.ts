import { afterEach, describe, expect, it, vi } from "vitest";

import { askQuestion } from "./client";
import { ApiError, parseRetryAfter } from "./errors";
import { answered } from "../test/fixtures";

function respond(body: unknown, init: ResponseInit = {}): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(body), { status: 200, ...init })),
  );
}

afterEach(() => vi.unstubAllGlobals());

const params = { question: "q", mode: "hybrid" as const };

describe("askQuestion", () => {
  it("returns validated data and sends the API key header", async () => {
    respond(answered);
    const data = await askQuestion({ ...params, apiKey: "rk_abc" });
    expect(data.answer).toContain("Reciprocal Rank Fusion");

    const [url, init] = vi.mocked(fetch).mock.calls[0]!;
    expect(url).toBe("/api/ask");
    expect((init!.headers as Record<string, string>)["X-API-Key"]).toBe("rk_abc");
    expect(JSON.parse(init!.body as string)).toMatchObject({ question: "q", mode: "hybrid" });
  });

  it("omits the key header when no key is set", async () => {
    respond(answered);
    await askQuestion(params);
    const init = vi.mocked(fetch).mock.calls[0]![1]!;
    expect(init.headers as Record<string, string>).not.toHaveProperty("X-API-Key");
  });

  it("maps 429 to a rate_limit error carrying Retry-After", async () => {
    respond({ detail: "Daily limit reached" }, { status: 429, headers: { "Retry-After": "42" } });
    await expect(askQuestion(params)).rejects.toMatchObject({
      kind: "rate_limit",
      status: 429,
      retryAfterSeconds: 42,
      message: "Daily limit reached",
    });
  });

  it("maps 401 to an auth error", async () => {
    respond({ detail: "Invalid or missing API key" }, { status: 401 });
    await expect(askQuestion(params)).rejects.toMatchObject({ kind: "auth", status: 401 });
  });

  it("maps 502 to an upstream error", async () => {
    respond({ detail: "Model call failed" }, { status: 502 });
    await expect(askQuestion(params)).rejects.toMatchObject({ kind: "upstream" });
  });

  it("rejects a response that violates the contract", async () => {
    respond({ answer: "missing the other fields" });
    await expect(askQuestion(params)).rejects.toMatchObject({ kind: "contract" });
  });

  it("maps a failed fetch to a network error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const error = await askQuestion(params).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ kind: "network" });
  });

  it("accepts a response without a trace (backend does not return one yet)", async () => {
    const withoutTrace = structuredClone(answered);
    delete withoutTrace.trace;
    respond(withoutTrace);
    const data = await askQuestion(params);
    expect(data.trace).toBeUndefined();
  });
});

describe("daily quota headers", () => {
  it("reads X-Daily-Limit and X-Daily-Remaining", async () => {
    respond(answered, { headers: { "X-Daily-Limit": "15", "X-Daily-Remaining": "11" } });
    const data = await askQuestion(params);
    expect(data.quota).toEqual({ limit: 15, remaining: 11 });
  });

  it("omits quota when the headers are absent (dev mode)", async () => {
    respond(answered);
    expect((await askQuestion(params)).quota).toBeUndefined();
  });
});

describe("parseRetryAfter", () => {
  it("parses delta-seconds", () => expect(parseRetryAfter("30")).toBe(30));
  it("parses an HTTP date relative to now", () => {
    const now = Date.parse("2026-10-07T10:00:00Z");
    expect(parseRetryAfter("Wed, 07 Oct 2026 10:00:20 GMT", now)).toBe(20);
  });
  it("returns null for missing or invalid values", () => {
    expect(parseRetryAfter(null)).toBeNull();
    expect(parseRetryAfter("soon")).toBeNull();
  });
});
