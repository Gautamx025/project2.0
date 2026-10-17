# Snap-2-Store

The catalog darkroom for independent sellers. Team NeuralShift / AI for Business and Commerce.

## Stack

Next.js App Router + TypeScript + Tailwind; FastAPI + Python; adapter-based image, vision, price, and draft-store integrations; Redis/RQ with BackgroundTasks fallback; SSE progress.

## Setup (development)

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
npm install
.venv\Scripts\python -m uvicorn backend.app.main:app --reload --port 8000
# A second terminal:
npm run dev
```

Open http://localhost:3000. Start with `DEMO_MODE=true`; no paid services or credentials are needed.

## Containers

```sh
cp .env.example .env
docker compose up --build
```

## Verification

```powershell
.venv\Scripts\python -m pytest
npm run build
npm run test:e2e
```

Implementation and verification are in progress. See [BUILD-BRIEF.md](BUILD-BRIEF.md), [current-state.md](current-state.md), and [known-issues.md](known-issues.md).
