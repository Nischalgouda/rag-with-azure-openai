import { useEffect, useState } from "react";

import { ApiError } from "./api/errors";
import type { Quota } from "./api/types";
import styles from "./App.module.css";
import { AnswerCard, isRefused } from "./components/AnswerCard/AnswerCard";
import { AskForm } from "./components/AskForm/AskForm";
import { ErrorBanner } from "./components/ErrorBanner/ErrorBanner";
import { ExampleChips } from "./components/ExampleChips/ExampleChips";
import { Footer } from "./components/Footer/Footer";
import { Header } from "./components/Header/Header";
import { PipelineFlow } from "./components/PipelineFlow/PipelineFlow";
import { SampleTrace } from "./components/SampleTrace/SampleTrace";
import { SettingsDialog } from "./components/SettingsDialog/SettingsDialog";
import { TracePanel } from "./components/TracePanel/TracePanel";
import { useAsk } from "./hooks/useAsk";
import { applyTheme, useSettings } from "./store/settings";

const IS_MOCK = import.meta.env.MODE === "mock";

export function App() {
  const [question, setQuestion] = useState("");
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [quota, setQuota] = useState<Quota | undefined>();
  const theme = useSettings((s) => s.theme);
  const mode = useSettings((s) => s.mode);
  const ask = useAsk();

  useEffect(() => applyTheme(theme), [theme]);

  function submit(q: string) {
    setSelectedSource(null);
    ask.mutate(q, { onSuccess: (result) => setQuota(result.quota) });
  }

  function pick(q: string) {
    setQuestion(q);
    submit(q);
  }

  const error = ask.error instanceof ApiError ? ask.error : null;
  const data = ask.data;
  const liveMessage = ask.isPending
    ? "Searching the indexed documents."
    : error
      ? error.message
      : data
        ? isRefused(data)
          ? "The question was declined: no relevant chunks were found."
          : "Answer ready. See the retrieval trace for the sources."
        : "";

  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header onOpenSettings={() => setSettingsOpen(true)} />

      {IS_MOCK && (
        <p className={styles.mockBanner} role="note">
          Mock mode: responses are simulated in the browser and no model is called.
        </p>
      )}

      <main id="main" className={styles.main}>
        <section className={styles.hero} aria-labelledby="hero-title">
          <p className={styles.kicker}>Retrieval-augmented generation, made visible</p>
          <h1 id="hero-title" className={styles.title}>
            See why a RAG system answers, <span className={styles.soft}>or refuses.</span>
          </h1>
          <p className={styles.lead}>
            Ask a question. Watch every chunk get scored, see where the refusal threshold falls, and find out
            whether the model was ever called.
          </p>

          <AskForm
            question={question}
            onQuestionChange={setQuestion}
            onSubmit={submit}
            pending={ask.isPending}
            quota={quota}
          />
          <ExampleChips onPick={pick} disabled={ask.isPending} />
        </section>

        <div role="status" aria-live="polite" className="sr-only">
          {liveMessage}
        </div>

        {error && <ErrorBanner error={error} />}

        {ask.isPending && <div className={styles.skeleton} aria-hidden="true" />}

        {data && !ask.isPending && (
          <div className={styles.results}>
            <PipelineFlow data={data} fallbackMode={mode} />
            <div className={styles.grid}>
              <AnswerCard data={data} selectedSource={selectedSource} onSelectSource={setSelectedSource} />
              <TracePanel data={data} pending={false} selectedSource={selectedSource} />
            </div>
          </div>
        )}

        {!data && !error && !ask.isPending && <SampleTrace />}
      </main>

      <Footer demo={!IS_MOCK} />
      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </>
  );
}
