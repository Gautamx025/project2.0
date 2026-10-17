# Current state: Snap-2-Store

Last updated: 2026-10-17

## Scope and checkpoint

- Built the full local app requested by the user, replacing the imported static mock at `70eab0c`. The original pasted brief remains local; repository requirements are in `instructions.md` and `COVERAGE.md`.
- M1–M6 are implemented and verified in order, each with a milestone commit. Essential files were pushed to the original GitHub repository's `main` on 2026-10-17; remote commit `7b35336` was independently confirmed with `git ls-remote` after the successful fast-forward push.
- Delivery retains all six milestones and excludes generated QA artifacts and local-only notes from every outgoing commit. Original unpublished milestone history remains on local branch `local/pre-publish-milestones`; all excluded files remain on disk.
- All requested screens and provider paths are implemented. The offline production-server flow is verified. Authenticated cloud/store operation is not verified without team credentials.
- Requirements: [instructions.md](instructions.md). Choices/provenance: [decisions.md](decisions.md). Requirement map: [COVERAGE.md](COVERAGE.md), 44 checked items with explicit verification limits.
- Current task: deploy on Vercel. Production is READY at **https://snap-2-store.vercel.app**. Next.js and FastAPI share one Vercel Services deployment; free managed Redis holds scoped records/locks and private Blob stores immutable photos. Cloud integrations are managed through the deployment environment and the hosted app runs in labeled demo mode.
- Vercel CLI/plugin/MCP onboarding is complete. The MCP documentation search works, but its current account grant cannot access the target team (403); the independently authenticated CLI has verified owner access and performs deployment operations. The project/storage are provisioned and linked. CLI GitHub linking needs the account's GitHub login connection; manual CLI deployment works and is verified.

## Implemented

- Next.js 16.4.2 App Router, React, TypeScript, Tailwind; local Fraunces/DM Sans/JetBrains Mono fonts and paper/ink/tomato editorial design.
- Routes: `/`, `/create`, `/bulk`, `/history`, `/settings`, `/impact`, `/under-the-hood`.
- 1–3 photo validation/camera/previews; six separately timed stages and live SSE; cancellation, per-stage retry/backoff and durable job recovery.
- Hosted SAM/FLUX, optional selectable vision/search providers, CPU rembg, labeled offline/precomputed fallbacks, four background variants, strict trilingual copy and source-linked INR prices/cache.
- Keyboard before/after slider, editable copy/SEO/tags/price with all-language persistence, precise fractional INR preview, draft preview and saved JSON payload.
- Explicit approval and revision checks before Shopify/WooCommerce DRAFT creation; local duplicate approvals are idempotent. Demo receipts link directly to the saved job. No draft is published to shoppers.
- Bulk per-item/selected-batch review and approval, persistent ledger, masked integration settings/connection tests and measured impact math.
- Inline architecture SVG, projected-figure disclosures, setup/store guides, two-minute judge script and screenshot critique.

## Important source locations

- `frontend/app/`: routes and design system; `frontend/components/Studio.tsx`: core UI; `frontend/lib/api.ts`: typed API boundary.
- `backend/app/main.py`: API/SSE/approval; `pipeline.py`: timed stages; `adapters.py`: provider interfaces and HTTP contracts; `repository.py`: atomic persistence; `queueing.py`/`worker.py`: queue interface and RQ.
- `frontend/public/samples/`: 3 licensed JPEGs and 3 rembg-precomputed cutouts. Exact bundled-file uploads use fixtures by content hash; this is not visual recognition.
- `.env.example`: configuration names. Ignored `.env` is initialized for demo mode. `data/`, `.venv/`, node_modules and build artifacts are ignored.
- Compose shares durable data and server `.env` across API/worker. Manual mode uses root `.env`. Root npm workspace and both dependency locks are provided.

## Local M1–M6 verification on 2026-10-17

- `.venv/Scripts/python -m pytest -q`: **29 passed**. Real orchestration/image output, schema/errors, retry/cancel/restart, queue race/fallback, exact edit/payload approval behavior, provider HTTP contracts and multilingual persistence. External network boundaries are mocked.
- `npm run build`: **passed**, including TypeScript and all 7 routes. Uses the documented Webpack path because restricted compiler workers stalled under the initial sandbox.
- `PLAYWRIGHT_PRODUCTION=true npm run test:e2e`: **11 passed in 25.0 s**, starting both real servers with isolated demo settings/data. Includes third-party-network-blocked sample flow, WCAG A/AA scans on all pages + review, 390px/mobile, real file upload, six stages, fractional-price/edit/payload approval, language preservation, reset/retry, bulk/history/settings and independently specified calculator math.
- Actual CPU rembg live adapter: alpha mask verified, 4.18 s including startup. All three derived sample masks generated and visually inspected. Runtime sample demos require no model download.
- Final landing, processing, review and 390px screenshots opened and inspected after fixes. `docs/screenshots` and `docs/visual-qa.md` remain local, ignored QA artifacts; browser tests regenerate screenshots.
- `docker compose config --quiet`, `pip check`, env-lint and Git whitespace checks passed. No missing/extra environment keys; unused secrets are intentionally empty.
- GitHub delivery: 79 tracked files; 151 unique outgoing file versions scanned for credential signatures and excluded paths before push. Final tracked runtime tree was unchanged by history cleanup. Delivery changes touched only documentation and ignore rules; application tests were not rerun for those edits.
- Browser test servers were shut down by Playwright after verification. Local servers can be started using README's two-terminal commands; the Vercel deployment is available at the URL above.

## Limits and next action

- Docker engine was unavailable, so container image/broker execution was not tested. Manual production servers are the verified run path; queue fallback/races have tests.
- No authenticated cloud model/search request or real store write was made. Live media import requires public HTTPS; inspect any partial/uncertain store result before retrying.
- General demo-image isolation remains approximate; sample masks are precomputed. Physical phone capture, full screen-reader/cross-browser testing and multi-tenant production operation remain outside verified scope.
- Latest deployment checks, 2026-10-17: **33 backend tests passed** (including cross-instance storage, visitor isolation, immutable retries, distributed locks and timeout recovery); production build/TypeScript passed locally and on Vercel. The existing **11 browser checks passed**; the added large-photo check then passed separately, rejecting the original >4.5 MB file and accepting it through the real photo picker after client preparation. All 12 browser checks have passed against the production frontend.
- Online `python -m backend.scripts.smoke_cloud https://snap-2-store.vercel.app`: **PASS**. All seven pages returned 200; all six processing stages completed. Original/processed private media, stranger denial, exact saved title/875.50 payload, approval boundary, idempotent demo receipt and returning-visitor persistence were verified on the hosted services. No live provider or store call was made.
- Deployment uses the pinned root `requirements.txt` cloud profile and `server.py`; CPU rembg remains in the full local install. The Python function explicitly includes sample JPEGs/masks. `.vercelignore` excludes credentials, dependencies, build output, agent installations and QA artifacts.
- Hosted browser inspection also passed: a real uploaded watch photo completed all six stages and displayed its processed variants and editable listing. The live landing screenshot was saved locally and inspected.
- Deployment is complete. The deployment delivery commit contains essential source, tests and configuration; generated files and credentials remain excluded. Next optional action: connect the Vercel account's GitHub login if automatic Git-triggered builds are desired. Cloud runs are bounded to 300 seconds and interrupted records become retryable. Browser workspaces rely on the signed cookie; clearing it starts a separate ledger. Private live merchant operation needs account authentication and an explicit store media-import strategy before enabling live credentials.
