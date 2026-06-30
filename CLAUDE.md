# CLAUDE.md — metaCTO Technical Assessment

## Project Rules

### Prompt Logging
Every time you receive a new instruction or prompt, append it to `prompts.txt` in the project root with a timestamp (ISO 8601) and a brief summary of what you did in response. Create the file if it doesn't exist. Keep this log updated throughout all sessions.

Entry format:
```
[YYYY-MM-DDTHH:MM:SSZ] <one-line summary of the prompt>
  -> <one-line summary of the response or actions taken>
```

## Purpose
This repository solves a technical assessment with a Django REST backend and a cross-platform React frontend (web and mobile). The architecture prioritises clean separation of concerns, code reuse where it makes sense, and native performance where it matters.

## Communication Conventions
- All Markdown deliverables (this file, READMEs, ADRs, prompts, skill content) are written in professional English.
- User instructions may arrive in Spanish; conversational responses may also be in Spanish, but every artifact persisted to disk is in English.
- Raw user prompts are preserved verbatim alongside their refined English versions.

## Stack
- **Backend:** Django + Django REST Framework, PostgreSQL, strict Clean Architecture (`domain` / `application` / `infrastructure` / `api`).
- **Frontend monorepo:** pnpm workspaces + Turborepo.
  - **Mobile:** Expo (iOS + Android).
  - **Web:** Next.js (App Router).
  - **Navigation:** Solito for unified routing across web and native.
  - **UI:** Tamagui (compiles to CSS on web for native-grade performance).
- **Testing:** unit, integration, and end-to-end coverage on both sides.

## Architecture

### Backend layout (per bounded context)
```
backend/apps/<context>/
├── domain/           # Pure entities, value objects, business rules (no Django)
├── application/      # Use cases orchestrating the domain
├── infrastructure/   # Django ORM models, repository implementations, adapters
└── api/              # DRF serializers, viewsets, urls
```

Dependency rules:
- `domain/` depends on nothing external. No Django, no DRF, no database.
- `application/` depends only on `domain/` and abstract ports.
- `infrastructure/` and `api/` depend on inner layers, never the reverse.

### Frontend layout
```
frontend/
├── apps/
│   ├── web/                # Next.js — web-only routes, SSR, SEO
│   └── mobile/             # Expo — native-only screens, deep linking, push
└── packages/
    ├── ui/                 # Cross-platform primitives (Tamagui)
    ├── features/           # Cross-platform feature screens and flows
    ├── api-client/         # Typed client for the DRF backend
    └── config/             # Shared tsconfig, eslint, prettier
```

Sharing rules:
- Cross-platform UI and feature logic live in `packages/`.
- Platform-specific code lives in `apps/web` or `apps/mobile`, never in `packages/`.
- When a component diverges per platform, use `Component.web.tsx` and `Component.native.tsx` alongside an `index.tsx` that exports the common API.

## Code Quality Standards

### Clean Architecture
- Inner layers never import outer layers.
- Dependencies cross boundaries through interfaces (ports) and dependency injection.
- Side effects (HTTP, database, filesystem) are confined to `infrastructure/`.

### Reuse first
- Before adding a function, search for an existing one. Extend rather than duplicate.
- Logic shared between web and mobile belongs in `packages/`, never copy-pasted between `apps/`.
- Logic shared between bounded contexts belongs in a clearly named shared module, not buried inside one context.

### Performance
- Backend: avoid N+1 queries with `select_related` and `prefetch_related`, paginate all list endpoints, and index filterable fields.
- Frontend: memoise expensive renders and prefer stable references with primitive props.
- Tamagui: author components to allow compile-time style extraction; avoid dynamic style props.
- Mobile bundle weight: use named imports only; never import entire libraries.

### Concurrency and collision safety
The application is built for high concurrency. Every design decision must assume collisions can happen.
- Prefer database-enforced invariants (unique constraints, atomic UPDATEs, row locks) over application-level checks.
- Mutating endpoints must be idempotent — naturally through unique constraints, or via an `Idempotency-Key` header persisted server-side.
- Status and other expected-state mutations use optimistic locking via the WHERE clause and return `409 Conflict` on stale state.
- Denormalised values must be maintained transactionally; values that depend on time decay are computed at read time, not stored.
- Background jobs follow the same locking patterns as the API; there is no privileged "background path".
- See `.claude/skills/business-context/decisions/03-concurrency-and-collision-safety.md` for the canonical strategy.

### Comments
- Default to no comments. Names should carry the meaning.
- When a comment is required, write **one short line** explaining the WHY of the feature — a constraint, a non-obvious decision, or a subtle invariant.
- Forbidden: explaining WHAT the code does, referencing tickets or tasks, multi-line essays, docstring filler without information.

## Testing Strategy

| Layer        | Backend (`backend/tests/`)             | Frontend                                  |
|--------------|----------------------------------------|-------------------------------------------|
| Unit         | `pytest`, domain and application only  | Vitest or Jest on pure functions and hooks|
| Integration  | `pytest` with a real test database     | RTL + MSW for components calling the API  |
| E2E          | `pytest` against a running API         | Playwright (web), Maestro (mobile)        |

Rules:
- Unit tests never hit the network or the database.
- Integration tests use a real PostgreSQL test database, not mocks.
- E2E tests run against a real backend instance.

## The `business-context` Skill

The skill at `.claude/skills/business-context/` holds the project's domain knowledge. It grows with every prompt the user provides.

Workflow each time a new prompt carries domain meaning:
1. Archive the raw prompt at `.claude/skills/business-context/prompts/NN-raw.md`.
2. Produce a refined English version at `prompts/NN-refined.md`.
3. Append new entities, rules, and vocabulary to `domain/*.md`.
4. If the prompt drives an architectural decision, record an ADR under `decisions/`.
5. Update `SKILL.md` only when invocation triggers change.

The skill loads automatically whenever work touches domain logic, naming, or business rules.

## Working With This Repo
- Use pnpm in `frontend/`. Never npm or yarn.
- Use a Python virtual environment in `backend/`. Never install globally.
- Run formatters and linters before committing.
- Prefer editing existing files over creating new ones.
- Do not scaffold code unless an active prompt requires it.
