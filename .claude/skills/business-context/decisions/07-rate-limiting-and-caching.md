# 07 — Rate limiting and caching

## Context
Two cross-cutting concerns that often live together in production are limiting abusive traffic and accelerating hot reads. They have different economics and we treat them differently in MVP+.

## Decision

### Part A — Rate limiting (built in MVP+)
Implemented in Redis using atomic `INCR` + `EXPIRE` (fixed-window). Redis is the single coordinator across all backend replicas so the limit holds regardless of horizontal scale.

**Identity resolution:**
- Authenticated endpoints: `user_id`.
- Unauthenticated endpoints: client IP, resolved from `X-Forwarded-For` left-most trusted entry (configured per deployment). IPv6 addresses are bucketed by `/64` prefix to avoid attacker-controlled enumeration.

**Limits (initial values, tunable per deployment):**

| Endpoint | Limit | Identity |
|---|---|---|
| Login | 5 per 10 min | IP |
| Register | 3 per hour | IP |
| Password reset request | 3 per day | email |
| Email verification resend | 3 per day | user |
| Submit feature request | 5 per hour | user; AND 100 per hour | IP |
| Upvote | 60 per minute | user |
| Comment | 1 per 30 s | user |
| Read endpoints (anti-scraping) | 100 per minute | IP |

Auth endpoints' limits are already captured in [[04-authentication]]; this ADR consolidates them in one place.

**Response contract:**
- Every rate-limited endpoint returns `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` headers on every response (not only when limited).
- On rejection, returns `429 Too Many Requests` with `Retry-After` set to the window reset and an explanatory JSON body for the client to surface to the user.

**Algorithm choice:**
- Fixed-window for MVP+ — simple, single key per (action, identity, window). Edge bursts at the window boundary are acceptable for these traffic patterns.
- Sliding-window (via Redis sorted set) is documented as a future improvement when burst behaviour becomes a real problem.

### Part B — Caching (HTTP-level only in MVP+; Redis cache deferred)

**Built:**
- **`ETag` + `If-None-Match`** on list and detail endpoints. The ETag is the SHA-256 of the canonical JSON response; a matching request returns `304 Not Modified` with empty body.
- **`Cache-Control` headers:**
  - List endpoints: `Cache-Control: private, max-age=10, stale-while-revalidate=60`.
  - Detail endpoints: `Cache-Control: private, max-age=30, stale-while-revalidate=120`.
  - Authenticated user info: `Cache-Control: private, no-store`.
- **CDN-friendly:** public read endpoints are served with `Cache-Control: public` variants when no auth is present, enabling a CDN to serve `304`s and full responses without hitting the backend.

**Deferred:**
- A Redis cache layer for the top-list and detail-by-id responses is **not** built in MVP+. Postgres with the indexes specified in ADR-01 and ADR-03 serves these queries within budget at the expected MVP+ scale.

**Future direction (documented for when needed):**
- Cache-aside pattern with single-flight: the first miss acquires a `SETNX` lock; other concurrent requesters either await the writer or serve stale.
- Keys: `top:{sort}:{page}` and `request:{id}`.
- Invalidation by tag: vote and status mutations publish to a `cache-invalidation` channel; subscribers `DEL` the affected keys.
- TTLs: short (60s) on list, longer (5 min) on detail with explicit invalidation.
- Triggers to add the Redis cache:
  - p95 latency on the top-list endpoint exceeds 200ms sustained.
  - Database CPU exceeds 60% utilisation sustained.
  - Read volume on the top-list endpoint exceeds ~500 RPS at peak.

## Consequences
- Redis is a runtime dependency (rate limiting). Docker Compose ships a Redis container.
- Frontend respects `Cache-Control` and uses TanStack Query for client-side caching aligned with the server's hints.
- No cache-DB inconsistency surface in MVP+: the database is the only persistent state.
- When Redis cache is added later, the invalidation contract is in the same ADR; the implementation will not be invented at the moment of need.
