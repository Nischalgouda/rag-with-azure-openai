import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { expectNoViolations } from "../../test/axe";
import { answered, refused, withoutTrace } from "../../test/fixtures";
import { TracePanel } from "./TracePanel";

describe("TracePanel", () => {
  it("explains what it will show before any question is asked", () => {
    render(<TracePanel data={undefined} pending={false} selectedSource={null} />);
    expect(screen.getByText(/Ask a question to see every chunk scored/)).toBeInTheDocument();
  });

  it("summarises the similarity chart for assistive technology", () => {
    render(<TracePanel data={answered} pending={false} selectedSource={null} />);
    const list = screen.getByRole("list", { name: /3 chunks to the question\. Threshold 0\.23; 2 at or above it/ });
    expect(list).toBeInTheDocument();
  });

  it("states why the model was or was not called", () => {
    const { rerender } = render(<TracePanel data={answered} pending={false} selectedSource={null} />);
    expect(screen.getByText(/clears the threshold 0\.23/)).toBeInTheDocument();
    rerender(<TracePanel data={refused} pending={false} selectedSource={null} />);
    expect(screen.getByText(/nothing was sent to the model/i)).toBeInTheDocument();
  });

  it("marks chunks sent to the model only when the question was answered", () => {
    const { rerender } = render(<TracePanel data={answered} pending={false} selectedSource={null} />);
    expect(screen.getAllByText("sent to model").length).toBe(2);
    rerender(<TracePanel data={refused} pending={false} selectedSource={null} />);
    expect(screen.queryByText("sent to model")).toBeNull();
  });

  it("degrades gracefully when the backend returns no trace", () => {
    render(<TracePanel data={withoutTrace} pending={false} selectedSource={null} />);
    expect(screen.getByText(/did not return a detailed trace/)).toBeInTheDocument();
    expect(screen.getByText("azure_ai_search.md")).toBeInTheDocument();
  });

  it("supports keyboard navigation between stage tabs", async () => {
    const user = userEvent.setup();
    render(<TracePanel data={answered} pending={false} selectedSource={null} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(3);
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");

    tabs[0]!.focus();
    await user.keyboard("{ArrowRight}");
    expect(tabs[1]).toHaveAttribute("aria-selected", "true");
    expect(tabs[1]).toHaveFocus();
    expect(within(screen.getByRole("tabpanel")).getByRole("table")).toBeInTheDocument();

    await user.keyboard("{End}");
    expect(tabs[2]).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{Home}");
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");
  });

  it("highlights rows belonging to the selected citation", () => {
    render(<TracePanel data={answered} pending={false} selectedSource="azure_ai_search.md" />);
    const rows = screen.getAllByRole("row").filter((r) => r.getAttribute("data-selected") === "true");
    expect(rows).toHaveLength(1);
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<TracePanel data={answered} pending={false} selectedSource={null} />);
    await expectNoViolations(container);
  });
});
