import styles from "./ExampleChips.module.css";

interface Example {
  question: string;
  kind: "answerable" | "off-topic";
}

/** Taken from the project's evaluation set: answerable questions plus one the corpus can't answer. */
const EXAMPLES: readonly Example[] = [
  { question: "How does hybrid search combine keyword and vector results?", kind: "answerable" },
  { question: "Why is managed identity preferred over API keys?", kind: "answerable" },
  { question: "What is the purpose of overlap between chunks?", kind: "answerable" },
  { question: "How do I bake a sourdough loaf?", kind: "off-topic" },
];

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
