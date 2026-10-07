import { expect } from "vitest";
import { configureAxe } from "vitest-axe";

/**
 * axe configured for jsdom. The color-contrast rule needs a real rendering engine (canvas),
 * which jsdom lacks, so it is disabled here. Contrast is instead guaranteed at the source:
 * every text/background token pair in styles/tokens.css is chosen to meet WCAG 2.2 AA.
 */
const runAxe = configureAxe({ rules: { "color-contrast": { enabled: false } } });

/** Fails with a readable list of violated rules, e.g. ["label: Form elements must have labels"]. */
export async function expectNoViolations(container: Element): Promise<void> {
  const results = await runAxe(container);
  expect(results.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
}
