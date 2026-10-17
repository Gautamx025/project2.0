# Known issues: Snap-2-Store

Last updated: 2026-10-17

## Active defects

No confirmed blocking defects remain in the verified offline workflow. External-service and platform verification limits are listed below; they are not represented as successful live checks.

## Resolved history

### I-001: Static mock advertised live services
- Status: resolved, 2026-10-17.
- Original impact: imported `70eab0c` showed FastAPI/AI/store success without any backend or store call (`script.js:151-250`, `index.html:29`).
- Resolution: real provider/store adapter paths and explicit local-vs-live fallback provenance. Demo results and draft receipts are labeled. Stage 6 assembles a draft; only explicit approval invokes a store.
- Evidence: backend contract/fallback/approval tests and the production browser upload-to-demo-draft flow passed. Authenticated calls remain unverified, not silently asserted.

### I-002: Reset retained or revived an active run
- Status: resolved, 2026-10-17.
- Original impact: imported reset cleared global inputs without cancelling timers/processing; a run could hang or repopulate mismatched results (`script.js:144-275`).
- Resolution: per-job records, cancellation under a write lock, guards against late stage saves, UI generation identities and disposed streams.
- Evidence: backend cancellation/recovery tests plus browser reset during an in-flight upload and UI retry checks passed.

### I-003: Editable fields never reached the payload
- Status: resolved, 2026-10-17.
- Original impact: imported form edits left generatedData/JSON/publish unchanged (`script.js:208-254`).
- Resolution: typed edit API, saved payload serialization and revision-checked approval.
- Evidence: backend exact-title/price/description assertions and browser merchant edit → JSON → persisted approved receipt passed.

### I-004: New input retained an old publishable listing
- Status: resolved, 2026-10-17.
- Original impact: imported setRawImage changed the preview without invalidating output (`script.js:66-91`).
- Resolution: separate jobs and explicit new-listing/reset UI; old requests cannot replace the current view.
- Evidence: distinct bottle/bag result tests and in-flight reset browser check passed.

### I-005: Invalid image decoding left processing stuck
- Status: resolved, 2026-10-17.
- Original impact: imported FileReader/Image promises had no validation/decode recovery (`script.js:66-140`).
- Resolution: MIME/size/pixel/decode validation before job creation and recoverable failed stages.
- Evidence: corrupt/non-image/oversized/multi-file rejection tests, failed-stage retry and browser invalid-file feedback passed.

### I-006: Muted copy and inline link accessibility
- Status: resolved, 2026-10-17.
- Impact: axe measured mode-panel text at 4.44:1 and found a review settings link distinguished only by color.
- Resolution: muted token darkened to #626158 (4.86:1 on that panel); in-text links persistently underlined.
- Evidence: final WCAG A/AA axe scans on all seven routes and the ready review screen report zero violations. Focus/slider checks and 390px overflow assertions passed.

### I-007: Saving one language discarded edits in another
- Status: resolved, 2026-10-17.
- Impact: local language switching retained edits, but the first edit API sent only the active language, so saving could overwrite other unsaved locale work.
- Resolution: validate and persist the complete edited translation set along with the active copy.
- Evidence: backend English/Hindi edits saved while Marathi is active, and the mobile browser language-switch/save/preservation regression passed.

### I-008: Fractional INR rounded in the store preview
- Status: resolved, 2026-10-17.
- Impact: the original formatter used zero fractional digits, so a final price of 875.50 could display as 876 while the payload retained 875.50.
- Resolution: retain two decimal places for fractional values, while whole INR amounts stay compact.
- Evidence: final browser flow checks ₹875.50 in the preview, 875.50 in the store JSON and numeric 875.5 in the saved receipt.

## Remaining limitations and verification boundaries

### I-009: Vercel picked the full local Python dependency set
- Status: resolved, 2026-10-17.
- Impact: the first Python bundle was 518.38 MB, above Vercel's 500 MB function limit; an indirect requirements include also failed the cloud parser.
- Resolution: root `server.py` entrypoint and self-contained pinned root `requirements.txt` containing the lean cloud runtime. Local rembg and its model dependencies remain in the separate full local install.
- Evidence: Vercel built Python 3.12 and the complete Services deployment reached READY; the online six-stage demo passed.

### I-010: Python's sample assets were not traced into the cloud bundle
- Status: resolved, 2026-10-17.
- Impact: the initial ready deployment served pages/health but `/api/jobs/sample` returned 503 because its sample file was absent.
- Resolution: explicitly include `frontend/public/samples/**` in the Python function configuration.
- Evidence: redeployment reached READY; online sample ingestion, mask isolation, four variants, editable result and approved demo receipt passed. Private media returns 200 only for its owning browser workspace.

### I-011: Automatic GitHub deployment linking is not configured
- Status: open; non-blocking hosting configuration.
- Impact/evidence: Vercel CLI could not link `Gautamx025/project2.0` because the Vercel account lacks a GitHub login connection. CLI source uploads build/deploy successfully.
- Workaround: use `vercel deploy --prod` from the linked checkout.
- Next action: the account owner can add the GitHub login connection/repository access in Vercel, then link the repository if automatic Git-triggered builds are wanted. No connection or repository permissions were changed silently.

- Real cloud/model/search/store credentials were not supplied. HTTP contracts have tests and official source references, but account access, latency and quality need authenticated smoke tests.
- Docker Desktop's Linux engine was unavailable. Compose syntax/configuration passed; no full container build or real Redis broker run was claimed. BackgroundTasks runs end to end; Redis fallback and fast-worker races are tested.
- General demo uploads use an edge-color isolation heuristic and generic editable copy when live providers are unavailable. Complex backgrounds may remain. Bundled sample masks were prepared with actual CPU rembg and are explicitly precomputed demo data.
- Search-snippet price relevance and generated product fidelity need merchant review. Core WooCommerce has no portable SEO-plugin schema; SEO fields are retained as metadata for later plugin mapping.
- Store creates are not blindly retried. A request timeout may have made a partial draft; receipts retain known IDs or flag uncertainty. Local approved repeats do not create duplicates.
- Local persistence is a shared filesystem for a trusted operator; a local process crash may require inspection of a stale write-lock file. The hosted demo now has scoped Redis records and private Blob media, signed anonymous browser workspaces and expiring distributed locks. Production merchant accounts still require authentication and an explicit public/signed store media-import strategy. Cloud processing is bounded to the 300-second function window and can be retried after interruption; its local price-search cache is best-effort per instance.
- Physical mobile camera capture, a complete screen-reader audit and non-Chromium device coverage were not exercised. Automated AA checks do not replace those checks.
- All 33 current backend tests pass. Browser screenshot replacement retries transient Windows thumbnail/indexer locks without rerunning app actions.
