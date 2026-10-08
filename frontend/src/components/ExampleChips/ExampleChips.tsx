import examplesFile from "../../data/examples.json";
import styles from "./ExampleChips.module.css";

export interface Example {
  question: string;
  kind: "answerable" | "off-topic";
}

/**
 * The same list is read by scripts/capture_saved_runs.py, which records a real answer for each one, so a
 * click replays instantly and costs nothing. Taken from the evaluation set: answerable questions plus one
 * the corpus cannot answer.
 */
export const EXAMPLES = examplesFile as readonly Example[];

interface Props {
  onPick: (question: string) => void;
  disabled?: boolean;
}

export function ExampleChips({ onPick, disabled = false }: Props) {
  return (
    <section aria-labelledby="examples-heading" className={styles.section}>
      <h2 id="examples-heading" className={styles.heading}>
        Try an example
      </h2>
      <ul className={styles.list}>
        {EXAMPLES.map((example) => (
          <li key={example.question}>
            <button
              type="button"
              className={styles.chip}
              disabled={disabled}
              onClick={() => onPick(example.question)}
            >
              <span>{example.question}</span>
              <span className={styles.tag} data-kind={example.kind}>
                {example.kind === "off-topic" ? "should be refused" : "answerable"}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
