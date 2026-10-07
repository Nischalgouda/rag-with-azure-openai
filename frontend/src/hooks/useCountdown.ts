import { useEffect, useState } from "react";

/** Counts down from `seconds` to 0, once per second. Resets when `seconds` changes. */
export function useCountdown(seconds: number | null): number {
  const [remaining, setRemaining] = useState(seconds ?? 0);

  useEffect(() => {
    setRemaining(seconds ?? 0);
    if (!seconds) return;
    const id = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(id);
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [seconds]);

  return remaining;
}
