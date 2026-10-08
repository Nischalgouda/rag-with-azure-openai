import type { ApiError, ApiErrorKind } from "../../api/errors";
import { useCountdown } from "../../hooks/useCountdown";
import { Icon } from "../ui/Icon";
import styles from "./ErrorBanner.module.css";

const TITLES: Record<ApiErrorKind, string> = {
  network: "Can't reach the server",
  auth: "Access key required",
  rate_limit: "Rate limit reached",
  validation: "That question can't be processed",
  upstream: "The model service had a problem",
  contract: "Unexpected response from the server",
  unknown: "Something went wrong",
};

const ADVICE: Partial<Record<ApiErrorKind, string>> = {
  auth: "Add a valid access key with the button in the header, then ask again.",
  network: "Check your connection and that the API is running, then try again.",
  upstream: "This is usually temporary. Try again in a moment.",
};

export function ErrorBanner({ error }: { error: ApiError }) {
  const remaining = useCountdown(error.retryAfterSeconds);

  return (
    <div role="alert" className={styles.banner}>
      <Icon name="alert" size={20} />
      <div className={styles.body}>
        <h2 className={styles.title}>{TITLES[error.kind]}</h2>
        <p>{error.message}</p>
        {error.kind === "rate_limit" && error.retryAfterSeconds !== null && (
          <p className={styles.advice}>
            {remaining > 0 ? `You can ask again in ${remaining} s.` : "You can ask again now."}
          </p>
        )}
        {ADVICE[error.kind] && <p className={styles.advice}>{ADVICE[error.kind]}</p>}
      </div>
    </div>
  );
}
