import { useMutation } from "@tanstack/react-query";

import { askQuestion } from "../api/client";
import { ApiError } from "../api/errors";
import type { AskResult } from "../api/types";
import { useSession, useSettings } from "../store/settings";

/** Server state for one question. The mutation holds pending / data / error for the UI. */
export function useAsk() {
  const mode = useSettings((s) => s.mode);
  const apiKey = useSession((s) => s.apiKey);

  return useMutation<AskResult, ApiError, string>({
    mutationFn: (question) => askQuestion({ question, mode, apiKey: apiKey || undefined }),
    retry: false,
  });
}
