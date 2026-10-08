import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import { useSession } from "../../store/settings";
import styles from "./SettingsDialog.module.css";

const REQUEST_URL = "https://linkedin.com/in/nischalgouda-patil-39b439279";

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
          Access key
        </h2>
        <p className={styles.text}>
          You do not need a key. Anyone can ask a limited number of questions a day for free. If you would like more,
          for example to evaluate it properly, message me and I will send you a key if it makes sense. It is not an OpenAI
          or Azure key: the models are provided, and no model credentials ever reach this page.
        </p>
        <p className={styles.text}>
          <a className={styles.link} href={REQUEST_URL} target="_blank" rel="noreferrer noopener">
            Request a key on LinkedIn<span className="sr-only"> (opens in a new tab)</span>
          </a>
        </p>
        <p className={styles.fine}>
          A key you paste stays in this browser tab only (session storage) and is sent as the <code>X-API-Key</code>{" "}
          header to this app&rsquo;s own API. The server keeps only a one-way hash of keys, never the key itself.
        </p>
        <label htmlFor={`${uid}-key`} className={styles.label}>
          Access key
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
