import type { RankedChunk } from "../../api/schema";
import { formatScore } from "../../lib/format";
import styles from "./RankTable.module.css";

interface Props {
  caption: string;
  scoreLabel: string;
  chunks: readonly RankedChunk[];
  selectedSource: string | null;
  /** Chunk ids that were placed in the prompt (shown as a badge). */
  sentIds?: ReadonlySet<number>;
  emptyMessage: string;
}

export function RankTable({ caption, scoreLabel, chunks, selectedSource, sentIds, emptyMessage }: Props) {
  if (chunks.length === 0) return <p className={styles.empty}>{emptyMessage}</p>;

  return (
    // A scrollable region must be focusable so keyboard users can scroll it.
    // eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex
    <div className={styles.scroll} role="region" aria-label={caption} tabIndex={0}>
      <table className={styles.table}>
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Chunk</th>
            <th scope="col" className={styles.num}>
              Similarity
            </th>
            <th scope="col" className={styles.num}>
              {scoreLabel}
            </th>
          </tr>
        </thead>
        <tbody>
          {chunks.map((chunk) => (
            <tr key={chunk.chunk_id} data-selected={selectedSource === chunk.source}>
              <td className={styles.rank}>{chunk.rank}</td>
              <td>
                <div className={styles.source}>
                  <span>{chunk.source}</span>
                  {sentIds?.has(chunk.chunk_id) && <span className={styles.badge}>sent to model</span>}
                </div>
                <div className={styles.preview}>{chunk.text_preview}</div>
              </td>
              <td className={styles.num}>{formatScore(chunk.cosine)}</td>
              <td className={styles.num}>{chunk.stage_score.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
