# Demo video script (about 75 seconds)

**Goal:** a viewer who has never heard of RAG understands, in under 90 seconds, that this system makes a *decision*
about every question, and can see the decision.

**Before you record (2 minutes)**
1. `.\scripts\run_demo.ps1` starts everything (UI + API, live Azure) and sends one warm-up question so the first
   on-camera answer is not the slow one. Add `-Rebuild` if you changed the frontend.
2. Rehearse the whole script once with the browser open. Answers take about 3 to 5 s; refusals about 1 to 2 s.
3. Do not open `.env` or the Azure Keys pages on camera. Close the API-key dialog.
4. Set the theme to **Dark**, zoom to 100%, hide bookmarks and extra tabs.
5. Locally the daily limit is off, so you can retake as often as you like. On the hosted URL each visitor gets 15 a day.

**Recording setup:** browser window 1280x720 or 1920x1080. Recording the hosted URL looks more credible once it is live;
until then `localhost:8010` is fine as long as the address bar is cropped out.

| Time | On screen | You say |
|---|---|---|
| 0:00 | The landing page: headline and the example chart | "Most RAG demos show you an answer. This one shows you the decision behind it." |
| 0:08 | Point at the example bars and the black rule | "Every chunk of the documents is scored against the question. The black line is the refusal threshold." |
| 0:16 | Click **How does hybrid search combine keyword and vector results?** | "Let's ask something the documents can answer." |
| 0:22 | The four-step strip appears; hover along it | "Retrieve, guardrail, generate, respond. The best chunk scored 0.42, past the 0.23 threshold, so the model was called." |
| 0:34 | Click the citation chip; the row highlights in the chart and table | "The answer cites its source, and clicking the citation shows exactly which chunk it came from." |
| 0:42 | Switch the mode to **Keyword**, ask again | "I can compare vector, keyword and hybrid retrieval on the same question." |
| 0:52 | Click **How do I bake a sourdough loaf?** | "Now a question the documents cannot answer." |
| 0:58 | Refusal state: orange bars, "Skipped", "No model call, no cost" | "Everything is below the line, so it refuses before calling the model. No guess, no tokens, no cost." |
| 1:06 | Footer, then the GitHub page | "It runs on Azure OpenAI and Azure AI Search. The code, the tests and a free local mode are on GitHub, so you can fork it and see how it works." |

**Rules for the take**
- Let each result land for a beat before you talk over it; the bars animate for about 0.7 s.
- Say the numbers you can see (0.42 vs 0.23); do not invent numbers.
- Do not claim the hybrid mode "is better": on this small corpus the evidence is weak. Show the toggle, not a winner.
- Keep the voice calm. The visual is the hook, not the volume.

**On-screen text (add in editing):** "Answers, or refuses" at 0:00; "No model call, no cost" at 0:58;
the repo URL at 1:06.

**Thumbnail:** the similarity chart with the threshold rule, cropped tight, headline text "Why did it refuse?".

---

## LinkedIn post 2 (the demo release; post when it is live)

> Most RAG demos show you an answer. I wanted to show the decision behind it.
>
> RAG X-ray scores every chunk of your documents against a question, draws the refusal threshold, and shows
> whether the model was called at all. Ask something the documents can't answer and you can watch it refuse, with
> no model call and no cost.
>
> 🔎 Try it: <live link>  (fair-use limits apply)
> 🧠 Learn from it: <repo link>. Fork it and read how hybrid retrieval, RRF and the guardrail work, with tests and an eval harness. It also has a free local mode (local embeddings and any OpenAI-compatible chat model).
>
> What's under the hood: FastAPI, Azure OpenAI, Azure AI Search hybrid retrieval, a token-bucket rate limiter, a
> daily cost budget with a kill switch, an evaluation harness and a CI pipeline.
>
> The part I'm proudest of is the part you can't see: the demo is built to be public without being a liability.
> Rate limits, a shared daily token budget, admin-only ingestion and a kill switch.
>
> What would you want to see it do next?
>
> #AzureOpenAI #RAG #AIEngineering #FastAPI #React
>
> Link to the repo in the first comment 👇
