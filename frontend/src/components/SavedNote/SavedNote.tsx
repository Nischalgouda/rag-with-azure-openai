import styles from "./SavedNote.module.css";

interface Props {
  recordedOn: string;
  onRunLive: () => void;
  disabled?: boolean;
}

const formatDate = (iso: string): string => {
  const d = new Date(`${iso}T00:00:00Z`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
};

/** Says plainly that this is a replayed real run, and offers the live path. */
export function SavedNote({ recordedOn, onRunLive, disabled = false }: Props) {
  return (
    <div className={styles.note} role="note">
      <p>
        <strong>Saved run.</strong> Real output captured on {formatDate(recordedOn)}, replayed instantly. It used no
        quota, and the token and time figures are from when it was recorded.
      </p>
      <button type="button" className={styles.button} onClick={onRunLive} disabled={disabled}>
        Run it live
      </button>
    </div>
  );
}
