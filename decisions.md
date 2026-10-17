# Decisions: Snap-2-Store

Last updated: 2026-10-17

## Active decisions

### D-001: Import the existing repository and limit this task to review

- Date: 2026-10-17
- Status: superseded
- Source: User request to import `Gautamx025/project2.0` and "review it for now".
- Decision: Clone the default branch directly into the empty Hackathon workspace, preserve its origin and history, and review the full initial commit without application changes.
- Reason: This makes the requested repository the actual project while preserving a clear baseline.
- Alternatives: A nested clone would add an unnecessary app root; implementation changes would exceed the current request.
- Consequences: Review findings remain open. Required context records are local additions, with no commit or push requested.

## Decision history

No superseded decisions recorded. Existing technology choices are observed implementation facts, not newly approved architecture decisions.

### D-002: Implement the complete local full-stack app

- Date: 2026-10-17
- Status: accepted
- Source: New user build brief; supersedes D-001's review-only scope.
- Decision: Use this imported repository, replace its three-file mock, implement the exact requested Next.js/FastAPI stack, and commit M1–M6 after verification. Local delivery with Docker/manual commands; no hosted Sites deployment is requested.
- Reason: User requests a working local full project and milestone commits.
- Alternatives: Keeping the old static demo cannot meet the brief.
- Consequences: Original source remains recoverable in Git at 70eab0c; context files remain canonical at root.

### D-003: Local-first, clearly labeled fallback and durable shared state

- Date: 2026-10-17
- Status: accepted
- Source: Agent defaults within the user's autonomous build scope.
- Decision: Persist jobs/listings/events as per-record JSON under ignored data/, with atomic writes and Redis queue coordination; use one stateless API process with BackgroundTasks locally, RQ workers and shared data volume in Compose. Production can replace the repository interface with a shared database/object store. Demo uses local Pillow compositing, deterministic sample copy and labeled example prices; no network required.
- Reason: Offline demos and restart-safe history without adding an unrequested database service.
- Alternatives: In-memory records lose history; SQLite adds locking concerns across worker processes.
- Consequences: Local/Compose shared filesystem is required; multi-host deployment needs shared durable storage and authentication before public exposure.

### D-004: Retired model compatibility

- Date: 2026-10-17
- Status: accepted
- Source: Official provider documentation reviewed during implementation (docs/provider-reference.md).
- Decision: Keep Gemini as primary with an explicit GEMINI_MODEL env override; use the currently documented Flash model because Gemini 1.5 Flash is retired. Keep GPT-4o selectable. Use documented fal SAM2 point prompts and FLUX Kontext editing; support Replicate via configurable model/version.
- Reason: Hard-coding a retired endpoint would make real-key mode unusable.
- Alternatives: Preserve the requested 1.5 model string and always fall back; rejected because real provider behavior matters.
- Consequences: Provider/model availability varies by account; failures are visible, timed, retried and labeled as fallback.
