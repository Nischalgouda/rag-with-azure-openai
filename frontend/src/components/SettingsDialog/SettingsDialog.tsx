import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import { useSession } from "../../store/settings";
import styles from "./SettingsDialog.module.css";

interface Props {
  open: boolean;
  onClose: () => void;
}

/** Uses the native <dialog>: focus trapping, Escape to close and the backdrop come from the browser. */
export function SettingsDialog({ open, onClose }: Props) {
  const uid = useId();
  const ref = useRef<HTMLDialogElement>(null);
  const apiKey = useSession((s) => s.apiKey);
  const setApiKey = useSession((s) => s.setApiKey);
  const clearApiKey = useSession((s) => s.clearApiKey);
  const [draft, setDraft] = useState(apiKey);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setDraft(apiKey);
      dialog.showModal?.();
    }
    if (!open && dialog.open) dialog.close?.();
  }, [open, apiKey]);

  function save(event: FormEvent) {
    event.preventDefault();
    setApiKey(draft);
    onClose();
  }

  return (
    <dialog ref={ref} className={styles.dialog} aria-labelledby={`${uid}-title`} onClose={onClose}>
      <form onSubmit={save} className={styles.form}>
        <h2 id={`${uid}-title`} className={styles.title}>
          API key
        </h2>
        <p className={styles.text}>
          The demo may require a key. It is kept in this browser tab only (session storage), is sent only
          as the <code>X-API-Key</code> header to this app&rsquo;s own API, and is never stored on a server
          by this page.
        </p>
        <label htmlFor={`${uid}-key`} className={styles.label}>
          Key
        </label>
        <input
          id={`${uid}-key`}
          className={styles.input}
          type="password"
          autoComplete="off"
          spellCheck={false}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="rk_…"
        />
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.secondary}
            onClick={() => {
              clearApiKey();
              setDraft("");
              onClose();
            }}
          >
            Remove key
          </button>
          <span className={styles.spacer} />
          <button type="button" className={styles.secondary} onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className={styles.primary}>
            Save
          </button>
        </div>
      </form>
    </dialog>
  );
}
