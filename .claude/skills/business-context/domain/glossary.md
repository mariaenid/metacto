# Glossary

Canonical vocabulary for the project. Code identifiers and user-facing copy must use these terms exactly.
Populated incrementally as prompts arrive.

## Format
```
## Term
**Definition:** one or two sentences.
**Aliases avoided:** synonyms that must NOT be used in code or docs.
**Used in:** entities, rules, or modules where the term appears.
```

---

## Feature Request
**Definition:** A user-submitted proposal for a new product capability that other users can discover and signal demand for. Code identifier: `FeatureRequest` (singular, PascalCase).
**Aliases avoided:** "Ticket", "Idea", "Suggestion", "Issue".
**Used in:** all backend bounded contexts that deal with submissions, the frontend feature module that lists and details proposals.

## Upvote
**Definition:** A user's positive signal of demand on a feature request. Toggleable; one per user per request (see [[rules]] RULE-01). Code identifier: `Vote` (the entity) with action verb `upvote`.
**Aliases avoided:** "Like", "+1", "Star", "Reaction".
**Used in:** `Vote` entity, ranking computation, voting API endpoint.

## Ranking
**Definition:** The ordering of feature requests by popularity, surfaced by default on the list view.
**Aliases avoided:** "Sort", "Order", "Trending".
**Used in:** list query, sort options exposed to the UI.

## Vote Count
**Definition:** The current total number of upvotes on a feature request. Denormalised on the `FeatureRequest` row for performance and maintained transactionally with atomic increment/decrement; the source of truth remains the `Vote` table. A nightly reconciliation job repairs any drift caused by aborted writes.
**Aliases avoided:** "Score", "Tally", "Likes".
**Used in:** `FeatureRequest.vote_count`, list and detail endpoints.

## Hot Score
**Definition:** Derived ranking metric `(vote_count - 1) / POWER(age_days + 2, 1.4)` used by the `hot` sort. Computed at query time, never stored, so the value stays correct as age decays without write-side maintenance.
**Aliases avoided:** "Trending score", "popularity score".
**Used in:** the `hot` branch of the list query.

## Status
**Definition:** The lifecycle state of a feature request. One of `open`, `under_review`, `planned`, `in_progress`, `shipped`, `closed`, `duplicate`. See [[02-status-workflow]] for the state machine.
**Aliases avoided:** "State", "stage", "phase".
**Used in:** `FeatureRequest.status`, default `top` filter, moderator panel.

## StatusChangeLog
**Definition:** Append-only audit entity recording every status transition with `from_status`, `to_status`, actor, timestamp, and optional reason. Written transactionally with the status update it audits.
**Aliases avoided:** "history", "audit", "event log".
**Used in:** timeline view, future notification hooks, moderator visibility.

## Moderator
**Definition:** A `User` whose `role = 'moderator'`. May transition `FeatureRequest.status`, including marking duplicates and closing requests. Cannot manage other users' roles.
**Aliases avoided:** "Reviewer", "Staff".
**Used in:** authorization checks on status mutations.

## Admin
**Definition:** A `User` whose `role = 'admin'`. Has all moderator permissions plus the ability to manage user roles.
**Aliases avoided:** "Superuser", "Owner".
**Used in:** authorization checks; role assignment.

## Idempotency Key
**Definition:** A client-supplied string (header `Idempotency-Key`) that lets the server de-duplicate retried mutations within a 24-hour window. Persisted server-side per actor; replays return the original response without re-mutating.
**Aliases avoided:** "Request ID", "Correlation ID".
**Used in:** submit and vote endpoints, future write endpoints; see [[03-concurrency-and-collision-safety]].

## Optimistic Locking
**Definition:** Concurrency control pattern in which an UPDATE includes the expected current value in the `WHERE` clause (e.g., `WHERE status = $expected_from`); if zero rows are affected, the caller has lost a race and must re-read. Used for status transitions and any other expected-state mutation.
**Aliases avoided:** "Compare-and-swap" in user-facing copy (technical term only).
**Used in:** status transition repository, duplicate-of assignment.

## Access Token
**Definition:** Short-lived (15 min) JWT carrying `user_id`, `role`, and `email_verified`. Held in client memory, never persisted to storage. Presented as `Authorization: Bearer <token>` on protected requests.
**Aliases avoided:** "API key", "Session token".
**Used in:** all authenticated endpoints; see [[04-authentication]].

## Refresh Token
**Definition:** Long-lived (30 days) opaque random string used to obtain a new access token. Rotating: each use issues a replacement and invalidates the predecessor. Stored hardware-backed on mobile, in `httpOnly` cookie on web.
**Aliases avoided:** "Long-lived token".
**Used in:** refresh endpoint; `RefreshToken` entity.

## Token Family
**Definition:** A `family_id` shared by all `RefreshToken` rows produced through successive rotations of a single login session. Detecting reuse of any used token in the family invalidates every token in that family.
**Aliases avoided:** "Token chain", "Session".
**Used in:** `RefreshToken.family_id`; breach detection on refresh.

## Email Verification
**Definition:** Process of confirming a `User` owns the email they registered with. Required before the user may submit, vote, or comment. Driven by a single-use `EmailVerificationToken` (24h TTL).
**Aliases avoided:** "Email confirmation".
**Used in:** `User.email_verified` gate on write endpoints; [[04-authentication]].

## Argon2id
**Definition:** The memory-hard hashing algorithm used for `User.password_hash`. Parameters `m = 64MB, t = 3, p = 4`. Resists GPU brute force; verification is constant-time.
**Aliases avoided:** "Password hash" (use the algorithm name explicitly in design discussions).
**Used in:** registration, login, password reset.

## Comment
**Definition:** A user-authored discussion message attached to a `FeatureRequest`. Flat (no nesting), chronological, soft-deleted with a tombstone if removed. Code identifier: `Comment` (singular, PascalCase).
**Aliases avoided:** "Reply", "Post", "Message".
**Used in:** `Comment` entity, detail view timeline, [[05-comments]].

## Timeline
**Definition:** The unified chronological feed on the `FeatureRequest` detail view that interleaves comments, status changes, and notable lifecycle events (creation, milestone votes). One ordering key (`occurred_at`) for all kinds.
**Aliases avoided:** "Activity feed", "Discussion thread".
**Used in:** detail view UI, aggregation query that UNIONs `Comment` and `StatusChangeLog`.

## Soft Delete
**Definition:** Marking a row as deleted by setting `deleted_at` (and the actor) instead of issuing a SQL `DELETE`. Used for `Comment` to preserve thread continuity while hiding the body behind a tombstone.
**Aliases avoided:** "Trash", "Archive" (those imply restorable; soft delete here is one-way).
**Used in:** `Comment.deleted_at`, `Comment.deleted_by_user_id`; future audit-bearing entities.

## Tombstone
**Definition:** The placeholder body shown for a soft-deleted or hidden `Comment` (`[deleted]` for self-delete, `Hidden by a moderator` for moderation). Preserves the position of the comment in the timeline without exposing the original content.
**Aliases avoided:** "Deleted comment", "Removed message".
**Used in:** comment rendering on the timeline.

## Stale-While-Revalidate
**Definition:** Client-side caching strategy in which a cached response is rendered immediately while a background fetch refreshes it. Implemented via TanStack Query on web and mobile, and signalled to clients through the `Cache-Control: stale-while-revalidate` directive on list and detail endpoints.
**Aliases avoided:** "SWR" (only used in code as the library name).
**Used in:** list and detail fetchers; replaces real-time push for MVP+ (see [[06-real-time-updates]]).

## ETag
**Definition:** A SHA-256 fingerprint of the canonical JSON response returned on list and detail GET endpoints. Clients send `If-None-Match: <etag>` on subsequent reads; a match returns `304 Not Modified` with empty body, saving payload weight.
**Aliases avoided:** "Hash", "Fingerprint".
**Used in:** list and detail responses; CDN cache validation.

## Single-Flight
**Definition:** Concurrency pattern in which only one concurrent requester computes a value while others wait for or serve a stale copy. Used to prevent cache stampedes. Documented in [[07-rate-limiting-and-caching]] as the strategy for when Redis caching is added; not implemented in MVP+.
**Aliases avoided:** "Lock-and-load", "thundering herd protection" (acceptable in technical discussions, not user-facing copy).
**Used in:** future Redis cache layer.

## Fixed-Window Rate Limit
**Definition:** Rate limiting strategy where a single Redis key (`{action}:{identity}:{window_start}`) is incremented and expired at the window boundary. Simple, exact within a window, allows edge bursts at the boundary.
**Aliases avoided:** "INCR-based limiter".
**Used in:** all rate-limited endpoints in MVP+.
