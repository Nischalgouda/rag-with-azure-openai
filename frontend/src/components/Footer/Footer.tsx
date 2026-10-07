import styles from "./Footer.module.css";

export function Footer({ demo }: { demo: boolean }) {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <p>
          Built with FastAPI, Azure OpenAI and Azure AI Search.{" "}
          <a href="https://github.com/Nischalgouda/rag-with-azure-openai" target="_blank" rel="noreferrer noopener">
            Read the source
          </a>{" "}
          or fork it to learn how hybrid retrieval works.
        </p>
        {demo && <p>Fair-use limits apply to the hosted demo. Questions are logged for usage and cost tracking.</p>}
      </div>
    </footer>
  );
}
