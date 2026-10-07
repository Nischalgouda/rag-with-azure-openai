import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { expectNoViolations } from "../../test/axe";
import { answered, refused, withoutTrace } from "../../test/fixtures";
import { PipelineFlow } from "./PipelineFlow";

describe("PipelineFlow", () => {
  it("shows an answered question as retrieve, pass, generate, respond", () => {
    render(<PipelineFlow data={answered} fallbackMode="hybrid" />);
    expect(screen.getByText("3 chunks scored")).toBeInTheDocument();
    expect(screen.getByText("Best 0.42 ≥ 0.23")).toBeInTheDocument();
    expect(screen.getByText("Passed")).toBeInTheDocument();
    expect(screen.getByText("589 tokens")).toBeInTheDocument();
    expect(screen.getByText("4.4 s")).toBeInTheDocument();
  });

  it("shows a refusal as a skipped generation with no cost", () => {
    render(<PipelineFlow data={refused} fallbackMode="hybrid" />);
    expect(screen.getByText("Best 0.15 < 0.23")).toBeInTheDocument();
    expect(screen.getByText("Refused")).toBeInTheDocument();
    expect(screen.getByText("Skipped")).toBeInTheDocument();
    expect(screen.getByText("No model call, no cost")).toBeInTheDocument();
  });

  it("shows the daily allowance when the server reports it", () => {
    render(<PipelineFlow data={{ ...answered, quota: { limit: 15, remaining: 12 } }} fallbackMode="hybrid" />);
    expect(screen.getByText("12 of 15 questions left today")).toBeInTheDocument();
  });

  it("still renders without a trace, falling back to the sources", () => {
    render(<PipelineFlow data={withoutTrace} fallbackMode="vector" />);
    expect(screen.getByText("1 chunk scored")).toBeInTheDocument();
    expect(screen.getByText("Vector")).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<PipelineFlow data={answered} fallbackMode="hybrid" />);
    await expectNoViolations(container);
  });
});
