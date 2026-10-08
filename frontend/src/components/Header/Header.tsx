import { useSession, useSettings, type ThemePreference } from "../../store/settings";
import { Icon } from "../ui/Icon";
import { Logo } from "../ui/Logo";
import { SegmentedControl, type SegmentedOption } from "../ui/SegmentedControl";
import styles from "./Header.module.css";

const THEMES: readonly SegmentedOption<ThemePreference>[] = [
  { value: "system", label: "Auto" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];

interface Props {
  onOpenSettings: () => void;
}

export function Header({ onOpenSettings }: Props) {
  const theme = useSettings((s) => s.theme);
  const setTheme = useSettings((s) => s.setTheme);
  const hasKey = useSession((s) => s.apiKey.length > 0);

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <a className={styles.brand} href="/" aria-label="RAG X-ray, home">
          <Logo size={28} className={styles.logo} />
          <span className={styles.name}>
            RAG<span className={styles.nameSoft}> X-ray</span>
          </span>
        </a>

        <div className={styles.actions}>
          <SegmentedControl legend="Theme" name="theme" value={theme} options={THEMES} onChange={setTheme} />
          <button type="button" className={styles.button} onClick={onOpenSettings}>
            <Icon name="key" />
            <span>{hasKey ? "Access key set" : "Access key"}</span>
          </button>
          <a
            className={styles.button}
            href="https://github.com/Nischalgouda/rag-with-azure-openai"
            target="_blank"
            rel="noreferrer noopener"
          >
            <span>Source</span>
            <Icon name="external" size={14} />
            <span className="sr-only">(opens in a new tab)</span>
          </a>
        </div>
      </div>
    </header>
  );
}
