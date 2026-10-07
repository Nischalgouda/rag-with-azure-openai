import { describe, expect, it } from "vitest";

import { splitCitations } from "./citations";

describe("splitCitations", () => {
  it("splits text and citations in order", () => {
    expect(splitCitations("Uses RRF [azure_ai_search.md] and more [rag_concepts.md].")).toEqual([
      { type: "text", value: "Uses RRF " },
      { type: "cite", source: "azure_ai_search.md" },
      { type: "text", value: " and more " },
      { type: "cite", source: "rag_concepts.md" },
      { type: "text", value: "." },
    ]);
  });

  it("returns a single text segment when there are no citations", () => {
    expect(splitCitations("I don't know.")).toEqual([{ type: "text", value: "I don't know." }]);
  });

  it("does not treat arbitrary bracketed text as a citation", () => {
    expect(splitCitations("See [note] and [1].")).toEqual([{ type: "text", value: "See [note] and [1]." }]);
  });

  it("returns nothing for an empty answer", () => {
    expect(splitCitations("")).toEqual([]);
  });
});
