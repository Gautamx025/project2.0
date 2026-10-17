# Current state: Snap-2-Store

Last updated: 2026-10-17

## Scope

Build [BUILD-BRIEF.md](BUILD-BRIEF.md) in six verified, committed milestones. This replaces the initial static demo at imported commit 70eab0c. See instructions.md and decisions.md.

## Checkpoint: M1 verified

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

Implement and verify M2: adapter interfaces + visible fallback, orchestrator/timing/retries, SSE, draft-only stores, queue and tests. Then M3 core UI, M4 support screens, M5 landing/architecture, M6 polish and end-to-end verification. Historical I-001–I-005 remain open until their replacement behavior is tested.
