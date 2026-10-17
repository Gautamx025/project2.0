# Requirement coverage — Snap-2-Store

Checked means the requirement has a concrete implementation and the cited verification layer was exercised. It does **not** imply authenticated third-party services or a physical mobile camera were tested. Live HTTP contracts use mocked network boundaries; offline/manual production-server operation is the verified end-to-end path. Final results are recorded in current-state.md and README.md.

## Pipeline

- [x] 1–3 photos, drag/drop, picker, camera capture, MIME/size/decode validation and previews — `frontend/components/Studio.tsx`, `backend/app/main.py`, `imaging.py`; backend invalid-input tests and core/recovery browser tests.
- [x] Hosted SAM on fal.ai/Replicate with CPU rembg fallback — `backend/app/adapters.py` (`Segmentation`); fal HTTP-contract tests, actual rembg runtime alpha-mask check, three precomputed sample masks.
- [x] FLUX background editing with white studio, shadow, lifestyle and colored variants — `adapters.py` (`Background`), `imaging.py`; image contract tests and actual four-image demo output tests.
- [x] Strict JSON vision material/color/category/title/tags/bullets/description/SEO — `models.py`, `adapters.py` (`Vision`); schema-rejection tests and Gemini/GPT-4o HTTP-contract tests.
- [x] Tavily/SerpAPI INR low/median/high with comparable URLs/ticks — `adapters.py` (`Price`), `PricePlot.tsx`; parser/source/cache tests and review browser flow. Illustrative fallback prices have no fabricated live links.
- [x] Draft payload and explicit approved Shopify GraphQL/WooCommerce REST sync — `store_payload`, `Store`, `main.publish`; exact draft/price/tag-ID network-contract tests, approval/revision/idempotency tests and browser demo receipt checks.
- [x] Every processing stage has real status, one-line description and elapsed time — `pipeline.py`, developing trays and stopwatch in `Studio.tsx`; six-stage assertions and processing screenshot. Draft assembly is timed before approval; actual store sync is separately timed afterward.

## Required stack and architecture

- [x] Next.js App Router + TypeScript + Tailwind, mobile first — `frontend/app`, `tsconfig.json`, `postcss.config.mjs`, tokenized `globals.css`; production build/type check and 390px screenshots.
- [x] Stateless FastAPI coordination — `backend/app/main.py`, `pipeline.py`; durable repository holds job state, not an API instance; real-server browser tests.
- [x] SegmentationProvider, BackgroundProvider, VisionProvider, PriceProvider, StoreProvider interfaces and environment selection — `adapters.py`, `config.py`, `.env.example`; adapter/schema tests and settings browser test.
- [x] Redis + RQ behind a queue interface; BackgroundTasks substitution — `queueing.py`, `worker.py`, Compose; fallback and fast-worker race regression tests. Real Redis broker/container operation is a verification limit in this environment.
- [x] Live SSE stage progress and reconnection reconciliation — `main.events`, `Studio.tsx`; SSE integration test and real browser flow, terminal stream cleanup.
- [x] DEMO_MODE, missing-key and failed-call fallback with visible provenance — `execute`, per-variant provenance, stage/source badges and store receipt modes; retry/fallback tests and offline browser flow.
- [x] Per-stage retry/backoff and retry buttons — `execute`, retry endpoint and tray controls; failure/recovery tests and UI retry test. Non-idempotent store creates are deliberately not blindly retried.
- [x] Measured stage and total time, no fabricated speed — `time.perf_counter` in pipeline/publish and actual UI clock; timing assertions and calculator tests with independent known measurements.
- [x] Price cache and reused HTTP/rembg clients — `adapters.py`; cache and client-boundary tests, actual local rembg execution.
- [x] Secrets only in ignored environment files, environment example, no stored secrets returned — `config.py`, `.gitignore`, `.dockerignore`, `.env.example`; settings privacy/preservation tests and env-lint.
- [x] Three offline photos and mask provenance — `frontend/public/samples`, `docs/sample-provenance.md`, D-005/D-006 in `decisions.md`; assets opened and inspected, exact-file fixture recognition documented.

## Screens and features

- [x] Landing problem, solution, target sellers, six steps, demo CTA and exact closing line — `/`, `frontend/app/page.tsx`; presentation browser test and desktop/mobile screenshot inspection.
- [x] Projected 98% time reduction, 90% cost savings and +15–25% conversion potential labeled unmeasured — landing projection spread; presentation test and visible per-figure caveats.
- [x] Snap & Create upload → live stages → results — `/create`, `Studio.tsx`; core upload flow.
- [x] Review & Edit before/after, variants, copy/tags/bullets/SEO, source price ticks, editable final price and store preview — `Compare.tsx`, `PricePlot.tsx`, `Studio.tsx`; keyboard slider, exact saved-title/price payload assertions and review screenshots.
- [x] Publish destination, collapsible JSON, explicit approval, draft ID/link — publish sheet and backend approval endpoint; core browser and idempotent API tests. Woo taxonomy IDs are resolved after approval; portable SEO fields are retained as metadata.
- [x] Bulk batch upload, per-item queue/status, individual review/approval and selected-batch approval — `/bulk`; real two-product browser batch flow.
- [x] Integrations/settings forms, connection tests, provider choice and demo toggle — `/settings`; settings backend/privacy and browser persistence/demo-test assertions.
- [x] Impact calculator with product count, hourly/per-photo costs, 25–40 minute baseline and measured processing time — `/impact` and landing `ImpactCalculator.tsx`; deterministic browser test rejects hard-coded speed and checks both cost modes.
- [x] Under the hood inline SVG, tool roles, feasibility, horizontal scaling caveats, queue/cache optimization and roadmap — `/under-the-hood`, `frontend/public/architecture.svg`; valid XML and presentation/browser checks.
- [x] Working English/Hindi/Marathi generated copy toggle — `VisionOutput`, `demo.py`, language editor; actual browser switches and translated-value assertions. Edited copy is saved per chosen language.
- [x] Durable history with draft-ready, synced draft, failed, queued/processing and cancelled status — `/history`, `Repository`; browser reload/filter and backend failure/cancel tests.
- [x] Real empty/loading/error/success feedback — empty desk/ledger/calculator states, inline job/settings errors, pending/saving labels, receipt states, shared App Router loading/error/not-found pages; recovery browser tests and route checks. Static editorial content does not invent a data-loading state.

## Design and accessibility

- [x] Warm paper/near-black/one tomato accent defined first as tokens — `globals.css`; contrast calculations: main text 13.51:1, muted on paper 5.52:1, muted on tray 4.95:1, action text 5.60:1.
- [x] Fraunces headlines, DM Sans body, JetBrains Mono labels, all local — layout imports from Fontsource; no runtime font-CDN requests.
- [x] Editorial grid, contact sheets, thin ink borders, crop marks, sharp corners, paper grain and hard offset shadows — landing/studio CSS; inspected local screenshots and visual QA notes (generated artifacts are excluded from GitHub delivery).
- [x] Avoid prohibited AI/SaaS motifs and banned marketing copy — source audit and visual critique; no gradients/neon/glass/blob/emoji-icon/identical-card hero.
- [x] Actual large stopwatch, developing trays, keyboard slider and comparable price ticks — core components and browser assertions.
- [x] Mobile tap targets and sticky primary action; no 390px body overflow — responsive rules and mobile/presentation tests.
- [x] Focus styles, labels, alt text, language context, reduced-motion preference and automated WCAG AA checks — global CSS, semantic controls and `accessibility.spec.ts`. Physical camera and complete assistive-technology testing remain limits.

## Delivery and verification

- [x] M1–M6 implemented in order with milestone commits and maintained project context — Git history and four canonical root context files.
- [x] Compose frontend/backend/Redis/worker configuration, persistent volumes and lockfile-based builds — `compose.yaml`, Dockerfiles; `docker compose config --quiet`. Engine/image execution unavailable; manual production path verified.
- [x] Backend pytest and frontend production build/type checking — `backend/tests`, root npm scripts; final command results in current-state.md.
- [x] Real two-server Playwright upload → six stages → edit → approved mock-store draft — `core.spec.ts`, isolated demo config/storage.
- [x] Landing, processing, review and 390px screenshots saved and visually inspected, then refreshed after fixes — local ignored `docs/screenshots` and `docs/visual-qa.md`; browser tests regenerate screenshots.
- [x] Exact setup commands, environment/provider guidance, free Shopify dev-store and Woo test-store steps — `README.md`, official links and provider reference.
- [x] Two-minute judges' script, mocked-vs-real explanation and known limitations — `docs/demo-script.md`, README and known-issues.md.

## External verification boundary

No paid/authenticated model request or real store write was made. Current provider APIs are implemented from official contracts, validated against typed responses and mocked HTTP tests, and fall back visibly when unavailable. Account access, provider latency/quality, public image ingestion and production infrastructure require a credentialed smoke test before a real merchant rollout. These limits are explicit in the UI/docs rather than hidden behind checked boxes.

## Vercel deployment checkpoint — 17 October 2026

- [x] One Services deployment routes Next.js and FastAPI on the same origin; production READY at https://snap-2-store.vercel.app.
- [x] Lean Python 3.12 runtime fits the function bundle; sample photos/masks are explicitly packaged.
- [x] Free managed Redis records and distributed locks, private immutable Blob media, signed visitor workspace isolation and read-only cloud integration settings — four cloud regression tests plus the live smoke check.
- [x] Large-photo preparation is verified against an enforced transport limit: the original >4.5 MB PNG receives 413, and the same file succeeds through the photo picker and all six stages.
- [x] Current checks: 33 backend tests, 12 production-frontend browser checks (11 existing + the focused large-photo check), local/remote production build and TypeScript.
- [x] Live cloud sample processing, private media and stranger rejection, exact edited payload, explicit approved demo draft, idempotency and returning-visitor persistence — `backend/scripts/smoke_cloud.py`.
- [ ] Automatic GitHub-triggered deployments — optional account login connection is missing; manual CLI production deployment is verified (I-011).

Hosted provider/store behavior remains labeled demo. Cloud records/media are durable, while its local search cache is best-effort. Anonymous browser cookies isolate visitors; production merchant account authentication and store-accessible media remain separate work before enabling live store credentials.
