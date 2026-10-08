import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SettingsDialog } from "./SettingsDialog";

describe("SettingsDialog", () => {
  it("tells visitors a key is optional and where to request one", () => {
    render(<SettingsDialog open={false} onClose={() => {}} />);
    const link = screen.getByText(/Request a key on LinkedIn/i).closest("a");
    expect(link).toHaveAttribute("href", expect.stringContaining("linkedin.com/in/"));
    expect(link).toHaveAttribute("rel", expect.stringContaining("noopener"));
    expect(document.body.textContent).toMatch(/You do not need a key/);
    expect(document.body.textContent).toMatch(/not an OpenAI/);
  });
});
