import type { RankedChunk, Trace } from "../../api/schema";
import { formatScore, plural } from "../../lib/format";
import styles from "./SimilarityBars.module.css";

const ROW_HEIGHT = 34;
const BAR_HEIGHT = 14;
const BAR_Y = (ROW_HEIGHT - BAR_HEIGHT) / 2;
const GRID = [0.25, 0.5, 0.75];
const MAX_ROWS = 10;

const pct = (v: number) => `${Math.min(1, Math.max(0, v)) * 100}%`;

interface Props {
  trace: Trace;
  selectedSource: string | null;
}

/**
 * Every candidate chunk as a bar of its cosine similarity to the question, with the refusal threshold
 * as a rule through all rows. Bars at or past the rule are blue, bars short of it are orange; chunks
 * that were sent to the model carry a "prompt" tag. Meaning never rests on colour alone: position
 * against the rule, the printed value and the tag say the same thing, and the list is read aloud
 * with the same facts.
 *
 * Built from SVG attributes (no inline styles), so it works under a strict CSP.
 */
export function SimilarityBars({ trace, selectedSource }: Props) {
  const all = trace.stages.vector;
  const rows = all.slice(0, MAX_ROWS);
  const hidden = all.length - rows.length;
  const sentIds = new Set(trace.decision === "answered" ? trace.stages.fused.map((c) => c.chunk_id) : []);
  const aboveCount = all.filter((c) => c.cosine >= trace.threshold).length;
  const weakSent = rows.some((c) => sentIds.has(c.chunk_id) && c.cosine < trace.threshold);

  return (
    <figure className={styles.figure}>
      <ul
        className={styles.rows}
        aria-label={`Similarity of ${plural(all.length, "chunk")} to the question. Threshold ${formatScore(trace.threshold)}; ${aboveCount} at or above it.`}
      >
        {rows.map((chunk, index) => (
          <Row
            key={chunk.chunk_id}
            chunk={chunk}
            index={index}
            threshold={trace.threshold}
            sent={sentIds.has(chunk.chunk_id)}
            selected={selectedSource === chunk.source}
          />
        ))}
      </ul>

      <Axis threshold={trace.threshold} />

      <figcaption className={styles.legend}>
        <span className={styles.key}>
          <i className={styles.swatchAbove} aria-hidden="true" /> at or above threshold
        </span>
        <span className={styles.key}>
          <i className={styles.swatchBelow} aria-hidden="true" /> below threshold
        </span>
        {hidden > 0 && <span className={styles.more}>+ {plural(hidden, "more chunk")} in the table</span>}
      </figcaption>

      {weakSent && (
        <p className={styles.note}>
          Some tagged chunks sit below the threshold. The guardrail judges the single best chunk, then the top
          results fill the prompt, weak ones included. Trimming those is a known improvement.
        </p>
      )}
    </figure>
  );
}

function Row({
  chunk,
  index,
  threshold,
  sent,
  selected,
}: {
  chunk: RankedChunk;
  index: number;
  threshold: number;
  sent: boolean;
  selected: boolean;
}) {
  const above = chunk.cosine >= threshold;
  return (
    <li className={styles.row} data-selected={selected}>
      <div className={styles.label}>
        <span className={styles.source}>{chunk.source}</span>
        <span className={styles.chunk}>chunk {chunk.chunk_id}</span>
      </div>

      <svg className={styles.plot} width="100%" height={ROW_HEIGHT} aria-hidden="true" focusable="false">
        {GRID.map((g) => (
          <line key={g} className={styles.grid} x1={pct(g)} x2={pct(g)} y1="0" y2={ROW_HEIGHT} />
        ))}
        <g className={styles.bar} data-above={above} data-i={Math.min(index, 9)}>
          <rect y={BAR_Y} width={pct(chunk.cosine)} height={BAR_HEIGHT} rx="4" />
          {/* square at the baseline: the 4px rounding belongs only at the data end */}
          <rect y={BAR_Y} width="6" height={BAR_HEIGHT} />
        </g>
        <line className={styles.threshold} x1={pct(threshold)} x2={pct(threshold)} y1="0" y2={ROW_HEIGHT} />
      </svg>

      <div className={styles.value}>
        <span className={styles.num}>{formatScore(chunk.cosine)}</span>
        {sent && <span className={styles.sent}>prompt</span>}
      </div>

      <span className="sr-only">
        {above ? "At or above" : "Below"} the threshold{sent ? ", sent to the model" : ""}.
      </span>
    </li>
  );
}

function Axis({ threshold }: { threshold: number }) {
  return (
    <div className={styles.axisRow} aria-hidden="true">
      <span />
      <svg className={styles.axis} width="100%" height="34" focusable="false">
        <line className={styles.axisLine} x1="0" x2="100%" y1="1" y2="1" />
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <text
            key={t}
            className={styles.tick}
            x={pct(t)}
            y="26"
            textAnchor={t === 0 ? "start" : t === 1 ? "end" : "middle"}
          >
            {t === 0 || t === 1 ? t.toFixed(0) : t.toFixed(2)}
          </text>
        ))}
        <line className={styles.thresholdTick} x1={pct(threshold)} x2={pct(threshold)} y1="1" y2="9" />
      </svg>
      <span className={styles.thresholdLabel}>threshold {formatScore(threshold)}</span>
    </div>
  );
}
