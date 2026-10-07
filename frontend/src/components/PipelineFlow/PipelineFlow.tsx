import type { SearchMode } from "../../api/schema";
import type { AskResult } from "../../api/types";
import { formatInt, formatLatency, formatScore, plural } from "../../lib/format";
import { isRefused } from "../AnswerCard/AnswerCard";
import { Icon } from "../ui/Icon";
import styles from "./PipelineFlow.module.css";

const MODE_LABEL: Record<SearchMode, string> = {
  hybrid: "Hybrid (vector + BM25)",
  vector: "Vector",
  keyword: "Keyword (BM25)",
};

interface Props {
  data: AskResult;
  /** Used only when the server returned no trace. */
  fallbackMode: SearchMode;
}

/** The request as a four-step decision: what was retrieved, whether the guardrail passed, and what it cost. */
export function PipelineFlow({ data, fallbackMode }: Props) {
  const refused = isRefused(data);
  const mode = data.trace?.mode ?? fallbackMode;
  const scored = data.trace?.stages.vector.length ?? data.sources.length;
  const threshold = data.trace?.threshold;

  return (
    <section aria-labelledby="flow-heading" className={styles.section}>
      <h2 id="flow-heading" className="sr-only">
        What happened to this question
      </h2>
      <ol className={styles.steps}>
        <li className={styles.step}>
          <span className={styles.index}>1</span>
          <h3 className={styles.title}>Retrieve</h3>
          <p className={styles.main}>{plural(scored, "chunk")} scored</p>
          <p className={styles.sub}>{MODE_LABEL[mode]}</p>
        </li>

        <li className={styles.step} data-state={refused ? "refused" : "passed"}>
          <span className={styles.index}>2</span>
          <h3 className={styles.title}>Guardrail</h3>
          <p className={styles.main}>
            Best {formatScore(data.top_score)} {refused ? "<" : "≥"}{" "}
            {threshold !== undefined ? formatScore(threshold) : "threshold"}
          </p>
          <p className={styles.verdict}>
            <Icon name={refused ? "ban" : "check"} size={14} />
            {refused ? "Refused" : "Passed"}
          </p>
        </li>

        <li className={styles.step} data-state={refused ? "skipped" : undefined}>
          <span className={styles.index}>3</span>
          <h3 className={styles.title}>Generate</h3>
          <p className={styles.main}>{refused ? "Skipped" : `${formatInt(data.tokens)} tokens`}</p>
          <p className={styles.sub}>{refused ? "No model call, no cost" : "Answer from retrieved chunks only"}</p>
        </li>

        <li className={styles.step}>
          <span className={styles.index}>4</span>
          <h3 className={styles.title}>Respond</h3>
          <p className={styles.main}>{formatLatency(data.latency_ms)}</p>
          <p className={styles.sub}>
            {data.quota ? `${data.quota.remaining} of ${data.quota.limit} questions left today` : "end to end"}
          </p>
        </li>
      </ol>
    </section>
  );
}
