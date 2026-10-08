import { SAMPLE_QUESTION, SAMPLE_TRACE } from "../../lib/sample";
import { SimilarityBars } from "../SimilarityBars/SimilarityBars";
import styles from "./SampleTrace.module.css";

/** Shown before the first question: an illustrative X-ray, clearly labelled as an example. */
export function SampleTrace() {
  return (
    <section className={styles.section} aria-labelledby="sample-heading">
      <div className={styles.copy}>
        <p className={styles.badge}>Example, not a live result</p>
        <h2 id="sample-heading" className={styles.heading}>
          Every answer starts with a decision
        </h2>
        <p className={styles.lead}>
          A RAG system scores every chunk of your documents against the question, then decides whether
          anything is relevant enough to show a model. This is what that decision looks like.
        </p>
        <ul className={styles.points}>
          <li>
            <span>
              <strong>Each bar</strong> is a chunk, scored by how close its meaning is to the question.
            </span>
          </li>
          <li>
            <span>
              <strong>The vertical rule</strong> is the refusal threshold. Nothing past it, no answer.
            </span>
          </li>
          <li>
            <span>
              <strong>Tagged chunks</strong> are the ones actually placed in the model&rsquo;s prompt.
            </span>
          </li>
        </ul>
      </div>

      <div className={styles.chart}>
        <p className={styles.question}>
          <span>Question</span> {SAMPLE_QUESTION}
        </p>
        <SimilarityBars trace={SAMPLE_TRACE} selectedSource={null} />
      </div>
    </section>
  );
}
