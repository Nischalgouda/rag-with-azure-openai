# Deploying the hosted demo (Azure Container Apps)

One container serves the UI and the API (`app.server`). It talks to the Azure OpenAI and Azure AI Search
resources you already created. Nothing here is deployed yet; this is the runbook.

> **Status:** the container's behaviour was verified by running the same entrypoint locally against live
> Azure (UI, `/api`, CSP, limits, refusals). The Docker image build, the CI workflow and `deploy_azure.ps1`
> have **not** been run end to end yet: treat the first run as a test and watch each step.

## What gets protected, and how

| Risk | Protection | Where |
|---|---|---|
| Strangers running up the Azure bill | per-visitor burst limit, per-visitor daily cap, shared daily token budget | `app/limits.py`, `DEMO_MODE=true` |
| Anyone re-indexing or reading usage | `/ingest` and `/usage` need an admin key | `limits.require_admin` |
| Runaway cost despite the above | kill switch, budget alert, Azure credit as a hard ceiling | below |
| Leaked keys | keys are Container Apps secrets, never in the image or the repo | `deploy_azure.ps1` |
| Upstream error text leaking | generic 502 message in demo mode | `app/main.py` |

**Limits to know about** (all fixable, none hidden):
- Rate-limit state is in memory and the daily counters are in a SQLite file inside the container. They reset when
  the container restarts, so the script runs **one always-on replica** (`--min-replicas 1`) instead of scaling to
  zero (a scaled-to-zero app would forget the day's usage on every cold start). An idle replica costs little but
  not nothing: check current Container Apps pricing. A shared store (Redis or a database) is the proper fix.
- Your account runs on free credit. If it has not been upgraded to pay-as-you-go, Azure stops paid services
  when the credit is used up, which is a hard ceiling on the worst case. The credit expires **3 Nov 2026**.

## Fastest path (no GitHub package needed)
The default `-Registry acr` mode builds the image **inside Azure** from your local folder (`az acr build`) and
deploys it, so you only need `az login`:
```powershell
az login
.\scripts\deploy_azure.ps1 -DryRun     # read what it will do (keys are masked)
.\scripts\deploy_azure.ps1             # build in Azure + deploy; prints the public URL
```
It creates an Azure Container Registry (Basic tier, a few dollars a month; delete it later if you move to the
GitHub-published image below). The Dockerfile was verified locally: the image builds in about 45 s (387 MB), runs as
a non-root user, serves the UI and API, keeps `/ingest` closed (401) and answers real questions through live Azure.

## One-time setup (CI-published image route)

1. **Push the repo and tag a release** so CI builds the image:
   ```powershell
   git push -u origin release/v0.2-demo        # open a pull request, let CI pass, merge to main
   git tag v0.2.0; git push origin v0.2.0      # CI builds ghcr.io/nischalgouda/rag-with-azure-openai:0.2.0
   ```
   In GitHub: Packages, then the image, then **Package settings**: make it **public** so Container Apps can pull
   it without credentials (the image contains no secrets).
2. **Install the Azure CLI**, then `az login`.
3. **Dry run**, then deploy:
   ```powershell
   .\scripts\deploy_azure.ps1 -DryRun
   .\scripts\deploy_azure.ps1 -Image ghcr.io/nischalgouda/rag-with-azure-openai:0.2.0
   ```
   It prints the public URL when it finishes.
4. **Create an admin key** inside the running container (the key is shown once):
   ```powershell
   az containerapp exec -n rag-xray -g rg-rag-demo --command "python -m scripts.create_key admin"
   ```
   The `rag-chunks` index already exists in Azure AI Search, so no re-ingest is needed.
5. **Set a budget alert** in Cost Management (for example 5 USD) with an email action.

## Check it worked
```powershell
curl https://<fqdn>/api/health          # {"status":"ok","demo_mode":true,...}
```
Open the URL, ask a question, then ask the sourdough one: the second must show "Skipped, no model call".
Then try `curl -X POST https://<fqdn>/api/ingest -H "Content-Type: application/json" -d "{}"`: it must return **401**.

## Operating it

| Need | Command |
|---|---|
| Switch the demo off immediately | `az containerapp update -n rag-xray -g rg-rag-demo --set-env-vars DEMO_ENABLED=false` |
| Switch it back on | same, with `DEMO_ENABLED=true` |
| Tighten the daily budget | `--set-env-vars DAILY_TOKEN_BUDGET=50000` |
| Roll out a new version | tag `v0.2.1`, wait for CI, then `az containerapp update -n rag-xray -g rg-rag-demo --image ghcr.io/nischalgouda/rag-with-azure-openai:0.2.1` |
| See logs | `az containerapp logs show -n rag-xray -g rg-rag-demo --follow` |
| Take it all down | `az containerapp delete -n rag-xray -g rg-rag-demo` (or delete the resource group) |

## If something fails
- **Image pull error:** the package is still private. Make it public (step 1).
- **Everything returns 502:** read the logs; usually a wrong deployment name or key in the secrets.
- **Every visitor shares one rate limit:** the app is not seeing real client IPs. The image sets
  `TRUSTED_PROXY_HOPS=1`, so the visitor is the last `X-Forwarded-For` entry (the one the platform appended;
  earlier entries can be forged, which `tests/test_client_ip.py` pins). If you put another proxy in front
  (for example Front Door), raise the hop count to match.
- **First model call is slow:** expected for the first request after a restart (client setup).
