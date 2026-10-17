# Known issues: Snap-2-Store

Last updated: 2026-10-17

## Active issues

### I-001: Advertised live pipeline and publishing are simulations

- Status: resolved (replacement implementation)
- Impact/severity: High functional gap if this is expected to create real listings; may be intentional demo scope, which is not documented.
- First observed: 2026-10-17
- Evidence: `script.js:151-172` waits on timers; `script.js:184-199` selects fixed metadata/prices; `script.js:247-250` only shows a success alert. No backend source or network API calls are present. `index.html:29` declares the FastAPI engine active without a health check.
- Expected: UI claims and success messages should accurately reflect actual service behavior.
- Actual: No SAM/vision/search/store service runs, no listing is created, and custom photos are drawn intact on a canvas (`script.js:94-140`).
- Cause: Confirmed by source inspection; all behavior is local simulation.
- Workaround: Treat the application as a frontend demo only.
- Next action: Clarify the next milestone, then either label the simulation honestly or implement and verify the intended services.

### I-002: Reset does not cancel or recover an active pipeline

- Status: resolved (replacement implementation)
- Impact/severity: P2; reset can leave processing permanently stuck or let a cleared listing reappear.
- First observed: 2026-10-17
- Evidence: Start a sample run and reset before the first 700 ms wait finishes. `script.js:257-275` clears the image/key but leaves `isProcessing` true and the loader visible. The resumed run (`script.js:151-162`) then tries to decode a null image and never finishes. Reset after the image branch is selected instead lets the old run finish with generic metadata, the old sample image, and publishing re-enabled. Both paths were reproduced using the real script with controlled DOM/timers.
- Expected: Reset cancels pending work, restores idle state, and permits a fresh run.
- Actual: Async work continues using mutated global state, or remains unresolved; a new run may immediately return at `script.js:145`.
- Cause: Confirmed; no cancellation/run identity check, and reset does not restore processing/loader state.
- Workaround: Reload the page after resetting an active pipeline.
- Next action: Introduce run cancellation or identity checks, snapshot run inputs, and reset all pending/processing state; verify early and late reset cases.

### I-003: Editable listing fields do not update the copied/published payload

- Status: resolved (replacement implementation)
- Impact/severity: P2; users' title, category, description, and price corrections are ignored by downstream output.
- First observed: 2026-10-17
- Evidence: Complete a sample run, change the title and price fields, then inspect JSON or call publish. `script.js:208-230` writes form fields and `generatedData` once; there are no field listeners or serialization before `script.js:247-254`. A focused probe confirmed the original title and price remain in the generated object and publish alert.
- Expected: Publishing/copying reflects the listing currently shown in the editable form.
- Actual: JSON and the simulated publish action retain the original generated values.
- Cause: Confirmed; the form and generated object are separate unsynchronized state.
- Workaround: None through the current form; do not treat edited fields as saved output.
- Next action: Use a single listing state or serialize/validate form values before generating JSON and publishing.

### I-004: Changing the input photo leaves the previous listing publishable

- Status: resolved (replacement implementation)
- Impact/severity: P2; the visible new photo can be paired with the previous product's listing and price.
- First observed: 2026-10-17
- Evidence: Complete the shoe sample, then select a custom image. `script.js:66-91` updates input state and the preview but does not clear `generatedData`, metadata, JSON, processed output, or disable publishing. A focused probe confirmed the old shoe payload remains active and `publishBtn.disabled` stays false.
- Expected: Replacing the input invalidates dependent results until a matching pipeline completes.
- Actual: The page shows a new input alongside an actionable stale listing.
- Cause: Confirmed; input changes do not invalidate derived state.
- Workaround: Reset after processing has fully finished, then select the new photo and run again.
- Next action: Clear or explicitly mark old results stale on input changes and disable publishing until a matching successful run.

### I-005: Invalid or failed image decoding leaves the pipeline stuck

- Status: resolved (replacement implementation)
- Impact/severity: P2; an invalid/corrupt upload can block further processing until page reload.
- First observed: 2026-10-17
- Evidence: `handleFile` (`script.js:66-74`) accepts any dropped file with no MIME/decode validation. `generateStudioProcessedImage` (`script.js:94-140`) only resolves on `img.onload`, with no `onerror`/rejection path. The processing handler (`script.js:144-237`) has no error/finally recovery. A non-image FileReader result and failed Image decode were simulated in a focused probe; the promise remained unresolved and processing stayed true with the button disabled.
- Expected: Reject invalid input with a clear error and restore the ability to run a valid image.
- Actual: Loader and processing state remain active indefinitely.
- Cause: Confirmed missing decode failure and cleanup paths; actual browser decode UI was not tested.
- Workaround: Reload the page and choose a valid image; Reset alone does not reliably recover (I-002).
- Next action: Validate supported inputs, handle reader/decode/canvas errors, and restore processing state in a final cleanup path.

## Validation limits

- The imported repository has no automated test suite or package/build configuration.
- `node --check script.js` succeeded. Ad hoc Node VM probes exercised the actual script with minimal DOM, image, and timer substitutes; no test source was added to the repository.
- Browser access to the temporary loopback preview timed out. Rendering, responsive layout, real image decoding, remote sample image content/availability, clipboard behavior, and accessibility remain unverified.
- I-001 is an observed implementation limitation; whether a simulation is acceptable is an unresolved scope question rather than a proven violation of a separate product spec.

## Resolved issues

None; no fixes were requested or applied.

## Replacement verification (2026-10-17)

The original three-file implementation was replaced in M1–M3. Historical evidence above refers to imported commit 70eab0c.

- I-001: Resolved by real backend adapter contracts plus visible demo fallback provenance and explicit local-vs-live store results. backend/app/adapters.py, pipeline.py, frontend/components/Studio.tsx. Backend 23-test suite + core Playwright flow passed; authenticated provider availability remains unverified without keys.
- I-002: Resolved by cancellation guards and per-run UI identity/disposed-stream checks. Backend cancellation and recovery tests passed; cancelled runs cannot save a late result.
- I-003: Resolved by saved edit API, generated payload from saved listing, approval revision check. Playwright changed title and price, checked exact JSON and persisted published result.
- I-004: Resolved by isolated per-job results and explicit new-listing/reset flow. Backend test confirms distinct bottle/bag payloads; the previous job is never reused for a new photo.
- I-005: Resolved by server MIME/size/decode validation before job creation, failed-stage cleanup and retry. Invalid/corrupt input and failed-stage recovery tests passed.

## Current limitations

- DEMO_MODE uses real local image compositing, illustrative multilingual copy and clearly labeled example prices. The edge-color heuristic is less accurate than SAM/rembg; complex/white backgrounds may remain.
- Real APIs and real store writes require credentials, account access and public HTTPS media. Contract tests mock the network boundary; no external draft has been created.
- Local shared-filesystem persistence is suited to a hackathon, not a multi-tenant production deployment.
