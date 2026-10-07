import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { SearchMode } from "../api/schema";

export type ThemePreference = "system" | "light" | "dark";

interface SettingsState {
  mode: SearchMode;
  theme: ThemePreference;
  setMode: (mode: SearchMode) => void;
  setTheme: (theme: ThemePreference) => void;
}

/** Non-sensitive preferences, persisted in localStorage. */
export const useSettings = create<SettingsState>()(
  persist(
    (set) => ({
      mode: "hybrid",
      theme: "system",
      setMode: (mode) => set({ mode }),
      setTheme: (theme) => set({ theme }),
    }),
    { name: "rag-xray-settings", storage: createJSONStorage(() => localStorage) },
  ),
);

interface SessionState {
  apiKey: string;
  setApiKey: (key: string) => void;
  clearApiKey: () => void;
}

/**
 * The API key is kept in sessionStorage only: it lives for this browser tab, is sent only as the
 * X-API-Key header to this app's own API, and is never written to localStorage.
 */
export const useSession = create<SessionState>()(
  persist(
    (set) => ({
      apiKey: "",
      setApiKey: (apiKey) => set({ apiKey: apiKey.trim() }),
      clearApiKey: () => set({ apiKey: "" }),
    }),
    { name: "rag-xray-session", storage: createJSONStorage(() => sessionStorage) },
  ),
);

/** Apply the theme preference to <html data-theme>. "system" removes the override. */
export function applyTheme(theme: ThemePreference): void {
  const root = document.documentElement;
  if (theme === "system") delete root.dataset.theme;
  else root.dataset.theme = theme;
}
