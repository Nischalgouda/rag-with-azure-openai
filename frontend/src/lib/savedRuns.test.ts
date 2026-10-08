import { describe, expect, it } from "vitest";

import { EXAMPLES } from "../components/ExampleChips/ExampleChips";
import { getSavedRun, savedQuestions } from "./savedRuns";

describe("saved runs", () => {
  it("has a real captured run for every example question, so a chip never silently goes live", () => {
    for (const example of EXAMPLES) {
      expect(getSavedRun(example.question), example.question).toBeDefined();
    }
  });

  it("captured exactly the example questions (re-run scripts/capture_saved_runs.py if this fails)", () => {
    expect([...savedQuestions].sort()).toEqual(EXAMPLES.map((e) => e.question).sort());
  });

  it("marks replayed runs with the date they were recorded", () => {
    const run = getSavedRun(EXAMPLES[0]!.question)!;
    expect(run.saved?.at).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("records answerable examples as answered and the off-topic example as refused", () => {
    for (const example of EXAMPLES) {
      const run = getSavedRun(example.question)!;
      expect(run.trace?.decision).toBe(example.kind === "off-topic" ? "refused" : "answered");
    }
  });

  it("returns nothing for a question that was not captured", () => {
    expect(getSavedRun("something nobody saved")).toBeUndefined();
  });
});
