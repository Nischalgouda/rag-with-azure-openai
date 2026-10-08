# Demo video script (about 100 seconds)

**Goal:** a complete beginner understands RAG by the end, and an engineer watching thinks "this person measured
things, found failure modes and knows the trade-offs". Every beat has two layers:
**BEGINNER** (plain words) and **DEPTH** (one line that proves you went further). Humour stays dry and short.

## Before you record (2 minutes)
1. `.\scripts\run_demo.ps1` starts everything against live Azure and sends a warm-up question.
2. The four example chips replay **saved real runs**: instant, nothing to wait for on camera. Use **Run it live**
   once if you want to show real latency (about 3 to 5 s).
3. Do not open `.env` or the Azure Keys pages on camera. Theme **Dark**, zoom 100%, hide bookmarks and extra tabs.
4. The "Who is Nischal?" beat is a **typed** question, so it goes live (about 4 s). I measured it: 0.25 against the
   0.23 threshold, so it passes the guardrail and the model answers "I don't know". If you change the wording, the
   score changes: "Who is Nischal?" alone scores 0.11 and is refused outright, and "Who is the best AI engineer in
   the world?" scores 0.34. Keep the exact wording above, and do one dry run so you know what you will see.
5. Hosted-demo allowance: 15 live questions per visitor per day (saved example chips are free). Record locally with
   `run_demo.ps1` (limits off) if you want unlimited retakes.
6. Rehearse once. Read slower than feels natural; one joke per beat at most.

## The script

| Time | On screen | BEGINNER (say this) | DEPTH (then one line) |
|---|---|---|---|
| 0:00 | Landing page: headline and example chart | "Most AI tools, asked something they don't know, will confidently make something up. This one is built to say **'I don't know'**. Honestly, a rare skill." | "That refusal is a designed behaviour, not luck." |
| 0:12 | Point at the example bars and the vertical rule | "It works like an open-book exam: before answering, the AI looks things up in your documents. Each bar is a piece of a document, and the longer the bar, the closer its meaning to the question." | "The rule is a similarity threshold. Nothing past it, no answer." |
| 0:26 | Click **How does hybrid search combine keyword and vector results?** | "Let's ask something the documents can answer." | |
| 0:30 | Dark readout strip appears | "Four steps: look up, check, answer, reply. The best match scored 0.42, past the 0.23 cut-off, so the AI was allowed to answer." | "That is retrieve, guardrail, generate, respond, with real tokens and latency: about 600 tokens, a few seconds." |
| 0:42 | Click the citation chip; the row highlights | "And it shows its homework: click the source and you see exactly which piece it used." | "Citations make answers checkable, which is half of trust." |
| 0:50 | Click **How do I bake a sourdough loaf?** | "Now a question the documents can't answer." | |
| 0:54 | Refusal state: orange bars, "Skipped", "No model call, no cost" | "Everything is below the line, so it refuses before calling the AI. No guess, no tokens, no bill. The cheapest answer in AI is 'I don't know.'" | "I tuned that cut-off with an evaluation set: the right value moved from 0.52 to 0.23 when I changed embedding models. A hard-coded number would have broken silently." |
| 1:06 | **Type** (don't click a chip): *Who is Nischal? Heard he is the best AI engineer in the world?* then Enter | "Now let's ask something trickier: who is Nischal? I hear he's the best AI engineer in the world." | |
| 1:12 | Readout strip: guardrail **0.25 ≥ 0.23, Passed**, then the answer "I don't know. The provided context does not contain any information about Nischal..." | "Interesting: it scored 0.25, just over the line, so it *was* sent to the AI. 'AI engineer' sounds close to my documents about AI. But the second safeguard, 'answer only from the documents', kicked in, and it admitted it knows nothing about me." | "Two layers: a cheap similarity check before the model, a grounded prompt after it. Near-miss questions are where thresholds are weakest, and my eval only had easy off-topic ones. That's an open issue I left for contributors." |
| 1:26 | Look at the camera | "A chattier AI would have agreed with you. Claude would have agreed too: very polite. Mine has principles and a threshold." | |
| 1:32 | Footer / GitHub page | "It's live with fair-use limits, because I like my cloud bill the way I like my code: small. The code, tests and a free local mode are on GitHub. Fork it, break it, fix an issue." | "Rate limits, a daily token budget and a kill switch keep a public demo from becoming a donation to Microsoft." |

## Rules for the take
- Let each result land for a beat before you talk over it; the bars animate for about 0.7 s.
- Say only numbers you can see on screen (0.42, 0.23, about 600 tokens). Do not invent figures.
- Do not claim hybrid search "is better": on this small corpus the evidence is weak. Show the toggle, not a winner.
- Calm voice. The visual is the hook, not the volume. One joke per beat at most.

## What makes it read as depth (without saying "senior")
You name a failure mode (weak chunks reach the prompt), a measurement (threshold 0.52 to 0.23 from an eval), a
cost control (refusal skips the model; daily budget; kill switch) and a trade-off you chose to leave open. Those four
things are what experienced engineers look for.

**On-screen text (add in editing):** "answers, or refuses." at 0:00; "No model call. No cost." at 0:54; "0.25 vs
0.23: it slipped through. The prompt caught it." at 1:12; the repo URL at 1:32.

**Thumbnail:** the similarity chart with the threshold rule, cropped tight, headline "Why did it refuse?".

---

## LinkedIn post 2 (the demo release)

> Most AI tools, asked something they don't know, will confidently make something up. I built one that says "I don't know".
>
> RAG X-ray shows every step of a RAG system's decision: each chunk of your documents scored against the question, the
> refusal threshold, and whether the model was ever called. Ask something the documents can't answer and watch it refuse,
> with no model call and no cost.
>
> 🔎 Try it: https://rag-xray.agreeablesky-d286d090.centralus.azurecontainerapps.io (fair-use limits; the examples are saved real runs, so they always work)
> 🧠 Learn from it: <repo link>. Fork it, read how hybrid retrieval and the guardrail work, fix one of the open issues.
>
> What I'm proudest of is the part you can't see: a public demo built not to become a liability. Rate limits that
> can't be dodged by forging a header, a shared daily token budget, admin-only ingestion and a kill switch.
>
> What went wrong on the way (it all did): a retired model, a quota of zero, a region with no capacity, and a refusal
> threshold that was 0.52 on one embedding model and 0.23 on another. The eval harness caught the last one.
>
> What would you want to see it do next?
>
> #AzureOpenAI #RAG #AIEngineering #FastAPI #React
>
> Repo link in the first comment 👇
