# metaCTO — Feature Voting System

A full-stack feature voting platform. Users submit product feature requests, upvote others', and track progress through a status workflow. Built as a technical assessment demonstrating clean architecture, concurrency safety, and cross-platform UI.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5 + DRF, PostgreSQL 16, Redis 7 |
| Auth | JWT (15 min access / 30 day rotating refresh), Argon2id |
| Web | Next.js 14 (App Router), Tailwind CSS, react-native-web |
| Mobile | Expo 51 (iOS + Android), NativeWind v4 |
| Shared UI | React Native primitives + `className` (renders cross-platform) |
| Data fetching | TanStack Query v5 (optimistic updates, SWR revalidation) |
| Monorepo | pnpm workspaces + Turborepo |

---

## Running locally

### Prerequisites

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+ and pnpm 9+

### 1. Start infrastructure + backend

**Option A — fully containerised (recommended)**

```bash
# From the repo root — starts Postgres (5433), Redis (6380), and the Django dev server (8000)
docker compose up --build

# First run only — apply migrations and load demo data
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

**Option B — local Python, Docker only for infra**

```bash
# Start only Postgres and Redis
docker compose up postgres redis -d

# Activate the existing virtualenv and run Django
source backend/.venv/bin/activate
cd backend
python manage.py migrate        # first run only
python manage.py seed_demo      # optional demo data
python manage.py runserver      # http://localhost:8000
```

Demo credentials (password: `Demo1234!`): `admin@demo.com`, `moderator@demo.com`, `alice@demo.com`.

The API is available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/v1/docs/`

### 2. Web frontend

```bash
cd frontend
pnpm install
pnpm --filter web dev        # http://localhost:3000
```

### 3. Mobile app (optional)

```bash
cd frontend
pnpm --filter mobile dev     # opens Expo Dev Tools / QR code
```

Scan the QR code with Expo Go (iOS/Android) or press `i`/`a` to open a simulator.

### Environment variables

The frontend reads `NEXT_PUBLIC_API_URL` (web) or `EXPO_PUBLIC_API_URL` (mobile). Both default to `http://localhost:8000` so no `.env` file is required for local development.

---

## Running tests

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Requires Docker infrastructure running (port 5433 / 6380)
pytest
```

Tests are tagged: `unit` (no DB), `integration` (real DB), `e2e` (full API).  
Run a single layer: `pytest -m unit`.

### Frontend (unit)

```bash
cd frontend
pnpm --filter @metacto/features test
```

### Frontend (e2e — Playwright)

```bash
cd frontend/apps/web
pnpm e2e                     # starts Next.js automatically, then runs Playwright
```

---

## Architecture

### Backend — Clean Architecture per bounded context

```
backend/apps/
├── identity/           # Auth: register, verify email, login, JWT refresh, password reset
├── feature_requests/   # Core: submit, list/sort, vote toggle, status workflow, admin stats
└── comments/           # Comments + timeline (unified with status changes)
```

Each context follows the same four-layer structure — dependencies flow inward only:

```
domain/          ← pure Python, no Django; entities, value objects, rules
application/     ← use cases; depends only on domain + abstract ports (protocols)
infrastructure/  ← Django ORM models, repository implementations, Redis adapters
api/             ← DRF serializers, views, URLs; depends on application layer
```

**Key design decisions:**
- Votes and status transitions are idempotent — safe to retry without side effects.
- `vote_count` is denormalised with atomic `F()` increments; `hot_score` is computed at query time (no staleness risk).
- Status transitions use `SELECT FOR UPDATE` + optimistic locking → `409 Conflict` on stale state.
- Refresh tokens rotate on every use; reuse of a revoked token invalidates the entire family (breach detection).
- All mutating endpoints accept an `Idempotency-Key` header.

See `.claude/skills/business-context/decisions/` for individual ADRs.

### Frontend — Shared-first monorepo

```
frontend/
├── packages/
│   ├── ui/           # Design tokens (theme.ts) + primitive components (Button, Input, Card, Badge)
│   ├── features/     # Cross-platform screens + data hooks — shared between web and mobile
│   └── api-client/   # Typed HTTP client for the DRF API
└── apps/
    ├── web/          # Next.js pages — thin wrappers that render feature screens
    └── mobile/       # Expo Router screens — identical wrappers, different router API
```

**Sharing strategy:** All business logic and UI lives in `packages/`. Platform-specific code (router imports, storage) is isolated in `apps/`. Components are written with React Native primitives + `className`; NativeWind styles them on mobile and react-native-web passes `className` to the DOM on web where Tailwind picks it up.

### API overview

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/v1/auth/register` | — | Create account |
| POST | `/v1/auth/verify-email` | — | Activate account |
| POST | `/v1/auth/login` | — | Get access + refresh tokens |
| POST | `/v1/auth/refresh` | — | Rotate refresh token |
| POST | `/v1/auth/logout` | Bearer | Invalidate refresh family |
| GET | `/v1/feature-requests` | optional | List with `sort=top\|hot\|new` |
| POST | `/v1/feature-requests` | verified | Submit new request |
| GET | `/v1/feature-requests/:id` | optional | Detail |
| POST/DELETE | `/v1/feature-requests/:id/vote` | verified | Cast / retract vote |
| PATCH | `/v1/feature-requests/:id/status` | moderator | Transition status |
| GET/POST | `/v1/feature-requests/:id/comments` | GET public | List / post comments |
| PATCH/DELETE | `/v1/comments/:id` | author | Edit / soft-delete |
| POST | `/v1/comments/:id/hide` | moderator | Moderator hide |
| GET | `/v1/feature-requests/:id/timeline` | optional | Comments + status changes merged |
| GET | `/v1/admin/stats` | admin | Aggregate dashboard |
