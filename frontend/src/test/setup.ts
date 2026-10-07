import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import { useSession, useSettings } from "../store/settings";

afterEach(() => {
  cleanup();
  // Zustand stores are module singletons: reset them so tests cannot leak state into each other.
  useSession.setState({ apiKey: "" });
  useSettings.setState({ mode: "hybrid", theme: "system" });
  sessionStorage.clear();
  localStorage.clear();
});
