import type { AskResponse } from "../../api/schema";
import { formatScore } from "../../lib/format";
import { Tabs } from "../ui/Tabs";
import { RankTable } from "./RankTable";
import { SimilarityBars } from "../SimilarityBars/SimilarityBars";
import styles from "./TracePanel.module.css";

interface Props {
  data: AskResponse | undefined;
  pending: boolean;
  selectedSource: string | null;
}

export function TracePanel({ data, pending, selectedSource }: Props) {
  return (
    <section className={styles.panel} aria-labelledby="trace-heading" aria-busy={pending}>
      <h2 id="trace-heading" className={styles.heading}>
        Retrieval trace
      </h2>
      <Body data={data} pending={pending} selectedSource={selectedSource} />
    </section>
  );
}

function Body({ data, pending, selectedSource }: Props) {
  if (pending) return <p className={styles.muted}>Scoring every chunk against your question…</p>;

  if (!data) {
    return (
      <p className={styles.muted}>
        Ask a question to see every chunk scored against it, where the refusal threshold sits, and which
        chunks reached the model.
      </p>
    );
  }

  const { trace } = data;
  if (!trace) {
    return (
      <div className={styles.stack}>
        <p className={styles.note}>
          This server did not return a detailed trace, so only the sources used are shown.
        </p>
        {data.sources.length === 0 ? (
          <p className={styles.muted}>No sources were used.</p>
        ) : (
          <ul className={styles.sources}>
            {data.sources.map((s, i) => (
              <li key={`${s.source}-${i}`}>
                <strong>{s.source}</strong> <span>similarity {formatScore(s.score)}</span>
                <p>{s.text}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  const refused = trace.decision === "refused";
  const sentIds = new Set(refused ? [] : trace.stages.fused.map((c) => c.chunk_id));

  return (
    <div className={styles.stack}>
      <p className={styles.verdict} data-refused={refused}>
        {refused
          ? `Best similarity ${formatScore(trace.top_score)} is below the threshold ${formatScore(trace.threshold)}, so nothing was sent to the model.`
          : `Best similarity ${formatScore(trace.top_score)} clears the threshold ${formatScore(trace.threshold)}, so the top chunks were sent to the model.`}
      </p>

      <SimilarityBars trace={trace} selectedSource={selectedSource} />

      <Tabs
        label="Ranking by retrieval stage"
        defaultId="fused"
        tabs={[
          {
            id: "fused",
            label: "Fused top results",
            count: trace.stages.fused.length,
            panel: (
              <RankTable
                caption="Chunks after fusion, in rank order"
                scoreLabel="RRF score"
                chunks={trace.stages.fused}
                selectedSource={selectedSource}
                sentIds={sentIds}
                emptyMessage="Nothing matched."
              />
            ),
          },
          {
            id: "vector",
            label: "Vector",
            count: trace.stages.vector.length,
            panel: (
              <RankTable
                caption="Chunks ranked by embedding similarity"
                scoreLabel="Cosine"
                chunks={trace.stages.vector}
                selectedSource={selectedSource}
                emptyMessage="No vector results."
              />
            ),
          },
          {
            id: "keyword",
            label: "Keyword",
            count: trace.stages.keyword.length,
            panel: (
              <RankTable
                caption="Chunks ranked by BM25 keyword score"
                scoreLabel="BM25"
                chunks={trace.stages.keyword}
                selectedSource={selectedSource}
                emptyMessage="No chunk shares a term with the question."
              />
            ),
          },
        ]}
      />
    </div>
  );
}
