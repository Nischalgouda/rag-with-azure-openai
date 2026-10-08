import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { useSession } from "./store/settings";
import { expectNoViolations } from "./test/axe";
import { answered, refused } from "./test/fixtures";

function mockFetch(handler: () => Response) {
  vi.stubGlobal("fetch", vi.fn(async () => handler()));
}

const json = (body: unknown, init: ResponseInit = {}) =>
  new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" }, ...init });

function renderApp() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.unstubAllGlobals());

describe("App", () => {
  it("shows a labelled example before the first question", () => {
    renderApp();
    expect(screen.getByText("Example, not a live result")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: /See why a RAG system/ })).toBeInTheDocument();
  });

  it("asks a question with Enter and shows the answer and the trace", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByLabelText(/Ask a question/), "How does hybrid search work?{Enter}");

    expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
    expect(screen.getByText(/clears the threshold/)).toBeInTheDocument();
    expect(screen.queryByText("Example, not a live result")).toBeNull();
    const body = JSON.parse(vi.mocked(fetch).mock.calls[0]![1]!.body as string);
    expect(body).toMatchObject({ question: "How does hybrid search work?", mode: "hybrid" });
  });

  it("does not submit on Shift+Enter or when empty", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    expect(screen.getByRole("button", { name: "Ask" })).toBeDisabled();

    await user.type(screen.getByLabelText(/Ask a question/), "line one{Shift>}{Enter}{/Shift}line two");
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/Ask a question/)).toHaveValue("line one\nline two");
  });

  it("sends the chosen search mode", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole("radio", { name: "Keyword" }));
    await user.type(screen.getByLabelText(/Ask a question/), "RRF{Enter}");
    await screen.findByRole("heading", { name: "Answer" });
    expect(JSON.parse(vi.mocked(fetch).mock.calls[0]![1]!.body as string)).toMatchObject({ mode: "keyword" });
  });

  it("replays a saved real run for an example: instant, no request, no quota", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole("button", { name: /hybrid search combine/ }));
    expect(await screen.findByRole("heading", { name: "Answer" })).toBeInTheDocument();
    expect(screen.getByText(/Saved run\./)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("presents a refusal as a first-class outcome, not an error (saved off-topic example)", async () => {
    mockFetch(() => json(refused));
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole("button", { name: /bake a sourdough loaf/ }));
    expect(await screen.findByRole("heading", { name: /declined/i })).toBeInTheDocument();
    expect(screen.getByText("No model call, no cost")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("'Run it live' sends a real request for the same question and drops the saved label", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole("button", { name: /hybrid search combine/ }));
    await user.click(await screen.findByRole("button", { name: "Run it live" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    const body = JSON.parse(vi.mocked(fetch).mock.calls[0]![1]!.body as string);
    expect(body.question).toMatch(/hybrid search combine/);
    await waitFor(() => expect(screen.queryByText(/Saved run\./)).toBeNull());
  });

  it("runs an example live when a mode other than hybrid is selected (saved runs are hybrid)", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole("radio", { name: "Vector" }));
    await user.click(screen.getByRole("button", { name: /hybrid search combine/ }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(JSON.parse(vi.mocked(fetch).mock.calls[0]![1]!.body as string)).toMatchObject({ mode: "vector" });
    expect(screen.queryByText(/Saved run\./)).toBeNull();
  });

  it("a typed question always goes live, even if it equals an example", async () => {
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    await user.type(screen.getByLabelText(/Ask a question/), "Why is managed identity preferred over API keys?{Enter}");
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    expect(screen.queryByText(/Saved run\./)).toBeNull();
  });

  it("shows an actionable message for a rate limit", async () => {
    mockFetch(() => json({ detail: "Daily demo limit reached" }, { status: 429, headers: { "Retry-After": "42" } }));
    const user = userEvent.setup();
    renderApp();
    await user.type(screen.getByLabelText(/Ask a question/), "anything{Enter}");
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Rate limit reached");
    expect(alert).toHaveTextContent("Daily demo limit reached");
    expect(alert).toHaveTextContent("You can ask again in 42 s.");
  });

  it("sends the API key from session settings as X-API-Key", async () => {
    useSession.getState().setApiKey("rk_test");
    mockFetch(() => json(answered));
    const user = userEvent.setup();
    renderApp();
    await user.type(screen.getByLabelText(/Ask a question/), "hello{Enter}");
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    const headers = vi.mocked(fetch).mock.calls[0]![1]!.headers as Record<string, string>;
    expect(headers["X-API-Key"]).toBe("rk_test");
  });

  it("has no detectable accessibility violations in its initial state", async () => {
    const { container } = renderApp();
    await expectNoViolations(container);
  });
});
