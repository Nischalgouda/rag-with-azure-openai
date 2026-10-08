# RAG X-ray (frontend)

A React + TypeScript UI that shows *why* a RAG system answers a question, or refuses: every chunk
scored against the question, the refusal threshold, the vector / keyword / fused rankings, and which
chunks reached the model.

## Run

```bash
npm install
npm run mock      # UI with simulated responses, no backend or Azure needed
npm run dev       # UI against the real API (FastAPI on http://localhost:8000, proxied at /api)
```

In mock mode, put `error401`, `error429` or `error502` in a question to see each error state.

## Checks

```bash
npm run typecheck   # tsc, strict mode
npm run lint        # eslint with jsx-a11y accessibility rules
npm test            # vitest + Testing Library, including automated axe accessibility checks
npm run build       # production build (~110 KB gzipped JS)
```

## Engineering decisions

- **Contract first.** `src/api/schema.ts` defines the API contract with zod and validates every response
  at the network boundary (`docs/api-contract.md` is the backend's copy). Drift fails loudly.
- **Typed error model.** `ApiError` classifies failures (network, auth, rate limit with `Retry-After`,
  upstream, contract) so the UI can show a specific, actionable message.
- **Refusal is a first-class outcome**, not an error: it has its own state, explanation and styling.
- **Design tokens.** All colours, spacing, type and motion come from `src/styles/tokens.css`; light and
  dark themes are a swap of those values. Text and UI colours are chosen for WCAG 2.2 AA contrast.
- **Visual language.** A quiet instrument readout: Geist and Geist Mono (self-hosted), ink as the primary action
  colour, elevation by a 1px ring plus stacked soft shadows, and one polarity-flipped decision panel as the focal
  object. Informed by studying the Vercel and Linear design-system write-ups in the awesome-design-md collection
  (type pairing, shadow-as-border elevation, surface ladder, no gradients); the Vercel mesh gradient was
  deliberately not used. Input boundaries keep a 3:1 contrast border (WCAG 1.4.11) instead of a near-invisible hairline.
- **Accessibility.** Landmarks and a skip link, labelled form controls, native radio inputs and `<dialog>`,
  the WAI-ARIA tabs pattern with arrow-key navigation, a live region for async results, visible focus,
  `prefers-reduced-motion` respected, charts that are never colour-only (fill and ring also encode state)
  and have table equivalents.
- **Safe rendering.** Model output is rendered as text nodes, never HTML, so it cannot inject markup.
- **Secrets.** An optional access key (issued on request by the owner) lives in `sessionStorage` (this tab only) and is sent only as `X-API-Key`. The server stores only its hash. It is the app's own pass, not a model key.
- **State.** Server state in TanStack Query; small UI preferences in Zustand (theme and mode persist,
  the key does not go to `localStorage`).
- **Performance.** No webfonts or UI framework; the mock layer is code-split out of the production bundle.

## Structure

```
src/
  api/          schema (zod), client, errors, mock
  components/   Header, AskForm, ExampleChips, AnswerCard, TracePanel (ScoreStrip, RankTable), ...
  hooks/        useAsk, useCountdown
  store/        settings (zustand)
  styles/       tokens.css, global.css
  test/         setup, fixtures, axe helper
```
