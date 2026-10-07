// Applies the saved theme before first paint, to avoid a flash of the wrong theme.
// Kept as an external file (not an inline script) so the Content-Security-Policy can forbid inline scripts.
try {
  var saved = JSON.parse(localStorage.getItem("rag-xray-settings") || "{}").state;
  if (saved && (saved.theme === "light" || saved.theme === "dark")) {
    document.documentElement.dataset.theme = saved.theme;
  }
} catch {
  /* storage unavailable: fall back to the OS preference */
}
