# Current state: Snap-2-Store

Last updated: 2026-10-17

## Scope

Build [BUILD-BRIEF.md](BUILD-BRIEF.md) in six verified, committed milestones. This replaces the initial static demo at imported commit 70eab0c. See instructions.md and decisions.md.

## Checkpoint: M2 verified

- Next.js 16.4.2 App Router / React / TypeScript / Tailwind scaffold in frontend/. Local Fraunces, DM Sans and JetBrains Mono fonts; paper/ink/tomato tokens in frontend/app/globals.css.
- FastAPI health scaffold in backend/app/main.py; Python virtual environment and dependencies installed.
- compose.yaml contains frontend, backend, Redis and RQ worker services with shared data volume. Worker implementation follows in M2.
- .env.example covers all providers and optional secrets. Ignored .env initialized in DEMO_MODE=true. Env-lint: no missing/extra keys, optional secrets intentionally empty.
- Three local sample photos and licensing at docs/sample-provenance.md; official API contracts at docs/provider-reference.md.
- Verified: npm run build (Webpack production build including TypeScript), backend health function assertion, docker compose config --quiet.
- Restricted sandbox compiler workers stalled; escalated build passed. No visual app QA or end-to-end feature checks yet.
- Browser Chromium installation in progress. No provider/store credentials or external write calls used.

## Structure

- frontend/: Next.js app, public samples, frontend Dockerfile.
- backend/: FastAPI application and Python requirements; adapters/tests next.
- Root npm workspace, package-lock.json, Compose, ignored .venv and .env.
- Canonical context: current-state.md, decisions.md, instructions.md, known-issues.md.

## Next action

Implement and verify M2: adapter interfaces + visible fallback, orchestrator/timing/retries, SSE, draft-only stores, queue and tests. Then M3 core UI, M4 support screens, M5 landing/architecture, M6 polish and end-to-end verification. Historical I-001â€“I-005 remain open until their replacement behavior is tested.

## M2 backend

- Implemented adapter protocols and real HTTP contracts for fal/Replicate SAM + FLUX, optional rembg, Gemini/OpenAI strict vision JSON, Tavily/SerpAPI INR comparable extraction, Shopify GraphQL draft + variant pricing, WooCommerce REST drafts.
- Visible per-adapter fallback metadata; no fabricated source links; local actual image validation/compositing, trilingual sample copy, measured stage times, bounded retries/backoff, price cache and shared HTTP clients.
- Durable atomic job repository, cancellation guards, retry from a chosen stage, SSE snapshots, edit/payload API, explicit approval + revision checks and locally idempotent draft sync. Redis/RQ queue and BackgroundTasks fallback with notices.
- Verified: .venv/Scripts/python -m pytest -q: 23 passed. Tests exercise real orchestration and image output, edit-to-payload consistency, cancellation/recovery, queue races, malformed inputs/schema, adapter fallback/cache, and mocked external HTTP contracts. No authenticated provider or real store writes performed.
- Known test dependency warning: latest Starlette deprecates httpx in TestClient; tests pass. Real provider account/model behavior remains unverified without keys.
- Next: M3 core Next.js upload → SSE → review/edit → approved demo draft, with Playwright verification.

## M3 core flow verified

- /create implements upload/camera/samples, responsive setup, measured live stopwatch and six developing trays, SSE + durable polling recovery, cancellation, stage retries, before/after keyboard slider, four background variants, editable trilingual copy/SEO, comparable-price ticks, saved JSON payload, explicit draft approval and demo/live result IDs.
- Fixed screenshot-observed mobile action overlap and spurious terminal SSE warning.
- Verified npm run build and npm run typecheck. Playwright started both real servers: 2 tests passed, including actual file upload → six stages → title/price edit → saved payload → explicit demo approval, keyboard slider, Hindi/Marathi switches and 390px no-horizontal-overflow checks.
- Screenshots captured and inspected: docs/screenshots/processing.png, review.png, mobile.png. M6 will refresh final screenshots and critique.
- Offline custom isolation is an edge-color heuristic and can retain original background; this is disclosed as demo compositing. Live SAM/rembg quality needs provider/model validation.
- Next: M4 bulk, persistent history, integrations/settings and measured impact calculator.

## M4 support screens verified

- /bulk accepts up to 20 products, one photo/listing each, shows per-item queue/stage state, review links, per-item approvals and explicit selected-batch draft approval. Batch IDs persist locally; listing history persists server-side.
- /history filters and reopens drafts, synced draft receipts, failures and cancelled jobs.
- /settings persists provider/demo/store preferences and masked secrets only to a server .env, with read-only connection tests and honest demo labels. Compose shares data/config/.env across API and RQ worker; manual mode uses root .env.
- /impact computes modeled monthly time/cost savings using average stored processing times and seller-selected 25–40 minute baseline; fee/manual-review caveats are visible.
- Next.js generated frontend/AGENTS.md during dev. Read its local component/layout/search-param guides before further frontend changes.
- Verified TypeScript, 3 supporting Playwright flows (bulk/history, settings, calculator), plus a strengthened calculator test with 60s/120s stored times: 120 products at 30 min baseline yields 57h and INR 28,500 at INR 500/hour; per-photo basis yields INR 11,400 at INR 100/photo. Backend 23 tests and Compose config still pass.
- Next: M5 editorial landing, projected impact story, architecture diagram and Under the hood.
