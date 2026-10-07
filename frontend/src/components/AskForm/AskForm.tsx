import { useId, type FormEvent, type KeyboardEvent } from "react";

import type { SearchMode } from "../../api/schema";
import type { Quota } from "../../api/types";
import { MAX_QUESTION_LENGTH } from "../../lib/limits";
import { useSettings } from "../../store/settings";
import { SegmentedControl, type SegmentedOption } from "../ui/SegmentedControl";
import styles from "./AskForm.module.css";

const MODES: readonly SegmentedOption<SearchMode>[] = [
  { value: "hybrid", label: "Hybrid" },
  { value: "vector", label: "Vector" },
  { value: "keyword", label: "Keyword" },
];

const MODE_HELP: Record<SearchMode, string> = {
  hybrid: "Meaning and exact terms together, fused with Reciprocal Rank Fusion.",
  vector: "Meaning only: nearest chunks by embedding similarity.",
  keyword: "Exact terms only: BM25 keyword matching.",
};

interface Props {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: (question: string) => void;
  pending: boolean;
  quota?: Quota | undefined;
}

export function AskForm({ question, onQuestionChange, onSubmit, pending, quota }: Props) {
  const uid = useId();
  const mode = useSettings((s) => s.mode);
  const setMode = useSettings((s) => s.setMode);

  const trimmed = question.trim();
  const canSubmit = trimmed.length > 0 && !pending;
  const nearLimit = question.length > MAX_QUESTION_LENGTH * 0.8;

  function submit(event: FormEvent) {
    event.preventDefault();
    if (canSubmit) onSubmit(trimmed);
  }

  // Enter submits; Shift+Enter inserts a newline (the chat convention).
  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      if (canSubmit) onSubmit(trimmed);
    }
  }

  return (
    <form className={styles.card} onSubmit={submit} aria-busy={pending}>
      <label htmlFor={`${uid}-q`} className="sr-only">
        Ask a question about the indexed documents
      </label>
      <textarea
        id={`${uid}-q`}
        className={styles.textarea}
        value={question}
        onChange={(e) => onQuestionChange(e.target.value)}
        onKeyDown={onKeyDown}
        maxLength={MAX_QUESTION_LENGTH}
        rows={2}
        placeholder="Ask anything about the sample documents…"
        aria-describedby={`${uid}-hint`}
      />

      <div className={styles.toolbar}>
        <div className={styles.mode}>
          <SegmentedControl
            legend="Search mode"
            name="mode"
            value={mode}
            options={MODES}
            onChange={setMode}
            disabled={pending}
          />
          <p className={styles.modeHelp}>{MODE_HELP[mode]}</p>
        </div>

        <div className={styles.actions}>
          <div className={styles.meta}>
            {quota && (
              <p className={styles.quota} data-low={quota.remaining <= 3}>
                {quota.remaining} of {quota.limit} questions left today
              </p>
            )}
            <p id={`${uid}-hint`} className={styles.hint}>
              <kbd>Enter</kbd> to ask · <kbd>Shift</kbd>+<kbd>Enter</kbd> new line
              {nearLimit && (
                <span className={styles.counter}>
                  {" "}
                  · {question.length}/{MAX_QUESTION_LENGTH}
                </span>
              )}
            </p>
          </div>
          <button type="submit" className={styles.submit} disabled={!canSubmit}>
            {pending ? (
              <>
                <span className={styles.spinner} aria-hidden="true" />
                Searching…
              </>
            ) : (
              "Ask"
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
