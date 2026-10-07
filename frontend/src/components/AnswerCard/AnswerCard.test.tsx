import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { expectNoViolations } from "../../test/axe";
import { answered, refused, withoutTrace } from "../../test/fixtures";
import { AnswerCard, isRefused } from "./AnswerCard";

describe("AnswerCard", () => {
  it("renders the answer with citations as buttons and the stats", () => {
    render(<AnswerCard data={answered} selectedSource={null} onSelectSource={() => {}} />);
    expect(screen.getByRole("heading", { name: "Answer" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /azure_ai_search\.md/ })).toBeInTheDocument();
    expect(screen.getByText("589")).toBeInTheDocument();
    expect(screen.getByText("4.4 s")).toBeInTheDocument();
  });

  it("selects and deselects a citation", async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    const { rerender } = render(<AnswerCard data={answered} selectedSource={null} onSelectSource={onSelect} />);
    await user.click(screen.getByRole("button", { name: /azure_ai_search\.md/ }));
    expect(onSelect).toHaveBeenLastCalledWith("azure_ai_search.md");

    rerender(<AnswerCard data={answered} selectedSource="azure_ai_search.md" onSelectSource={onSelect} />);
    expect(screen.getByRole("button", { name: /azure_ai_search\.md/ })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: /azure_ai_search\.md/ }));
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });

  it("explains a refusal using the threshold", () => {
    render(<AnswerCard data={refused} selectedSource={null} onSelectSource={() => {}} />);
    expect(screen.getByRole("heading", { name: /declined/i })).toBeInTheDocument();
    expect(screen.getByText(/below the threshold of 0\.23/)).toBeInTheDocument();
    expect(screen.getByText(/Refused before calling the model/)).toBeInTheDocument();
  });

  it("infers refusal from empty sources when there is no trace", () => {
    expect(isRefused({ ...refused, trace: undefined })).toBe(true);
    expect(isRefused(withoutTrace)).toBe(false);
  });

  it("renders model output as text, never as HTML", () => {
    const hostile = { ...answered, answer: "<img src=x onerror=alert(1)> hello", trace: undefined };
    const { container } = render(<AnswerCard data={hostile} selectedSource={null} onSelectSource={() => {}} />);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.getByText(/<img src=x/)).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<AnswerCard data={answered} selectedSource={null} onSelectSource={() => {}} />);
    await expectNoViolations(container);
  });
});
