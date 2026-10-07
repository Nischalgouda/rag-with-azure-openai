import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { expectNoViolations } from "../../test/axe";
import { answered, refused } from "../../test/fixtures";
import { SimilarityBars } from "./SimilarityBars";

describe("SimilarityBars", () => {
  it("renders one row per candidate chunk with its similarity printed", () => {
    render(<SimilarityBars trace={answered.trace!} selectedSource={null} />);
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(3);
    expect(within(rows[0]!).getByText("0.42")).toBeInTheDocument();
    expect(within(rows[0]!).getByText("azure_ai_search.md")).toBeInTheDocument();
  });

  it("tags the chunks sent to the model, and says so to screen readers", () => {
    render(<SimilarityBars trace={answered.trace!} selectedSource={null} />);
    expect(screen.getAllByText("prompt")).toHaveLength(2);
    expect(screen.getAllByText(/At or above the threshold, sent to the model/).length).toBeGreaterThan(0);
  });

  it("tags nothing when the question was refused", () => {
    render(<SimilarityBars trace={refused.trace!} selectedSource={null} />);
    expect(screen.queryByText("prompt")).toBeNull();
    expect(screen.getAllByText(/^Below the threshold\.$/).length).toBeGreaterThan(0);
  });

  it("explains why a chunk below the threshold can still reach the prompt", () => {
    const base = answered.trace!;
    const weak = { ...base, stages: { ...base.stages, fused: [...base.stages.fused, base.stages.vector[2]!] } };
    render(<SimilarityBars trace={weak} selectedSource={null} />);
    expect(screen.getByText(/judges the single best chunk/)).toBeInTheDocument();
  });

  it("shows no such note when every sent chunk clears the threshold", () => {
    const base = answered.trace!;
    const strong = { ...base, stages: { ...base.stages, fused: [base.stages.vector[0]!] } };
    render(<SimilarityBars trace={strong} selectedSource={null} />);
    expect(screen.queryByText(/judges the single best chunk/)).toBeNull();
  });

  it("prints the threshold on the axis", () => {
    render(<SimilarityBars trace={answered.trace!} selectedSource={null} />);
    expect(screen.getByText("threshold 0.23")).toBeInTheDocument();
  });

  it("marks the rows of the selected citation", () => {
    render(<SimilarityBars trace={answered.trace!} selectedSource="rag_concepts.md" />);
    const selected = screen.getAllByRole("listitem").filter((r) => r.getAttribute("data-selected") === "true");
    expect(selected).toHaveLength(1);
  });

  it("caps the rows and says how many more are in the table", () => {
    const base = answered.trace!;
    const many = Array.from({ length: 14 }, (_, i) => ({
      ...base.stages.vector[0]!,
      chunk_id: i,
      rank: i + 1,
      cosine: 0.5 - i * 0.02,
    }));
    render(<SimilarityBars trace={{ ...base, stages: { ...base.stages, vector: many } }} selectedSource={null} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(10);
    expect(screen.getByText(/\+ 4 more chunks in the table/)).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<SimilarityBars trace={answered.trace!} selectedSource={null} />);
    await expectNoViolations(container);
  });
});
