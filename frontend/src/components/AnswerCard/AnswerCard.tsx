import type { AskResponse } from "../../api/schema";
import { formatInt, formatLatency, formatScore } from "../../lib/format";
import { splitCitations } from "../../lib/citations";
import { Icon } from "../ui/Icon";
import styles from "./AnswerCard.module.css";

interface Props {
  data: AskResponse;
  selectedSource: string | null;
  onSelectSource: (source: string | null) => void;
}

/** A question is "refused" when no sources were sent to the model (the guardrail fired). */
export function isRefused(data: AskResponse): boolean {
  return data.trace ? data.trace.decision === "refused" : data.sources.length === 0;
}

export function AnswerCard({ data, selectedSource, onSelectSource }: Props) {
  const refused = isRefused(data);
  const segments = splitCitations(data.answer);

  return (
    <article className={styles.card} data-refused={refused} aria-labelledby="answer-heading">
      <header className={styles.header}>
        <h2 id="answer-heading" className={styles.heading}>
          {refused ? "No answer: question declined" : "Answer"}
        </h2>
        <span className={styles.pill} data-refused={refused}>
          <Icon name={refused ? "ban" : "check"} size={14} />
          {refused ? "Refused before calling the model" : "Grounded in retrieved sources"}
        </span>
      </header>

      <p className={styles.answer}>
        {segments.map((segment, index) =>
          segment.type === "text" ? (
            <span key={index}>{segment.value}</span>
          ) : (
            <button
              key={index}
              type="button"
              className={styles.citation}
              aria-pressed={selectedSource === segment.source}
              aria-label={`Citation ${segment.source}: highlight in the retrieval trace`}
              onClick={() => onSelectSource(selectedSource === segment.source ? null : segment.source)}
            >
              {segment.source}
            </button>
          ),
        )}
      </p>

      {refused && (
        <p className={styles.explain}>
          The best match scored {formatScore(data.top_score)}
          {data.trace ? `, below the threshold of ${formatScore(data.trace.threshold)}` : ""}. Declining is
          cheaper and safer than asking the model to guess from irrelevant text.
        </p>
      )}

      <dl className={styles.stats}>
        <div>
          <dt>Best similarity</dt>
          <dd>{formatScore(data.top_score)}</dd>
        </div>
        <div>
          <dt>Tokens used</dt>
          <dd>{formatInt(data.tokens)}</dd>
        </div>
        <div>
          <dt>Latency</dt>
          <dd>{formatLatency(data.latency_ms)}</dd>
        </div>
      </dl>
    </article>
  );
}
