# Business Rules

Invariants and rules that the domain must enforce.
Populated incrementally as prompts arrive.

## Format
```
## RULE-NN — Short title
**Applies to:** entity or use case.
**Rule:** the invariant or constraint, stated unambiguously.
**Rationale:** why it exists (business reason).
**Enforcement:** which layer enforces it (domain, application, infrastructure, api).
```

---

## RULE-01 — One vote per user per feature request
**Applies to:** `Vote`.
**Rule:** A user may have at most one `Vote` on a given `FeatureRequest` at any time.
**Rationale:** Vote integrity. Popularity is only meaningful as a ranking signal if each user contributes at most one vote per request.
**Enforcement:** Domain invariant on the aggregate, enforced by a database unique constraint on `(feature_request_id, user_id)`.

## RULE-02 — Ranking reflects persistent demand by default
**Applies to:** `FeatureRequest` listing.
**Rule:** The default ordering of feature requests is **Top among active**: `vote_count DESC, created_at DESC`, filtered to `status IN ('open', 'under_review', 'planned', 'in_progress')`. Alternative sorts (`hot`, `new`) are exposed through a `sort` query parameter and surfaced in the UI as a dropdown. See [[01-ranking-algorithm]].
**Rationale:** In the feature-voting domain, popularity means persistent demand for unbuilt work, not viral momentum. Filtering by active status prevents shipped or closed items from dominating; alternative sorts keep fresh ideas discoverable.
**Enforcement:** Application/repository layer (query construction). Database indexes `(status, vote_count DESC, created_at DESC)` and `(status, hot_score DESC)` support the default and `hot` queries.

## RULE-04 — Author implicit vote
**Applies to:** `FeatureRequest` submission.
**Rule:** When a `User` submits a `FeatureRequest`, a `Vote` row by that user on the new request is created in the same transaction.
**Rationale:** The author obviously wants their own request; recording it explicitly removes the awkward "vote your own idea" interaction and matches Featurebase/Canny convention.
**Enforcement:** Application use case for `submit_feature_request`.

## RULE-05 — Vote count is denormalised and maintained transactionally; hot score is derived
**Applies to:** `FeatureRequest.vote_count`, `Vote` mutations, `hot` ranking query.
**Rule:** Whenever a `Vote` is created or removed, the affected `FeatureRequest.vote_count` is updated via atomic increment/decrement in the same database transaction as the vote mutation. `hot_score` is **not** stored; it is computed at query time as `(vote_count - 1) / POWER(age_days + 2, 1.4)` from the live `vote_count` and `created_at`.
**Rationale:** A stored hot_score must be refreshed continuously because time decays whether or not votes change. Compute-on-read removes that maintenance, eliminates write-side contention, and is fast enough for the expected active-set size. Atomic increment of `vote_count` is collision-safe under high concurrency.
**Enforcement:** Repository implementation (transactional atomic UPDATE for `vote_count`); query construction in the list use case (derived hot score in the SELECT). Supersedes the earlier denormalisation plan; see [[03-concurrency-and-collision-safety]].

## RULE-06 — Valid status transitions
**Applies to:** `FeatureRequest.status`.
**Rule:** Allowed transitions are:
- Linear forward: `open → under_review → planned → in_progress → shipped`.
- From any non-terminal status: `→ closed` or `→ duplicate`.
- No automatic back transitions. Reverts are explicit moderator actions and produce their own `StatusChangeLog` entry.
**Rationale:** The state machine reflects the real lifecycle of a feature request and is the contract users see in the timeline view.
**Enforcement:** Domain state machine in `backend/apps/feature_requests/domain/` plus optimistic locking on the SQL update (`WHERE status = expected_from`).

## RULE-07 — Only moderators and admins may transition status
**Applies to:** any change to `FeatureRequest.status`.
**Rule:** Only `User`s with `role IN ('moderator', 'admin')` may perform a status transition. Regular users may suggest a duplicate when submitting, but the transition itself requires moderator approval.
**Rationale:** Roadmap control belongs to the team that owns the product. User-initiated transitions would defeat moderation.
**Enforcement:** API permission class + application-layer authorization check.

## RULE-08 — Status change is atomic with audit log
**Applies to:** every status transition.
**Rule:** The `FeatureRequest.status` update and the corresponding `StatusChangeLog` insert occur in the same database transaction. If the optimistic lock fails (zero rows updated), the transaction rolls back and no log row is written.
**Rationale:** Audit log must never disagree with the row it audits.
**Enforcement:** Repository implementation.

## RULE-09 — Duplicate requires a target and forbids cycles
**Applies to:** transitions to `status = duplicate`.
**Rule:** A request can only enter `duplicate` if `duplicate_of_id` is set and points to another `FeatureRequest`. Cycles in the duplicate chain are forbidden: a transition to `duplicate` rejects the request if the proposed target already resolves (directly or transitively) back to the source.
**Rationale:** Cycles break navigation and reporting.
**Enforcement:** Application-layer validation inside the transition use case, with row-level locks on the source and target to prevent races (see [[03-concurrency-and-collision-safety]]).

## RULE-11 — Write actions require verified email
**Applies to:** submit `FeatureRequest`, cast `Vote`, post `Comment` (when implemented).
**Rule:** All write endpoints reject requests from `User`s with `email_verified = false` (`403 Forbidden` with a code the UI can interpret). Reading is unaffected.
**Rationale:** Verification is the primary anti-abuse barrier: a stolen or disposable email cannot vote or submit.
**Enforcement:** API permission class. UI may also hide actions but never as the sole barrier (see [[04-authentication]]).

## RULE-12 — Refresh token rotation and breach detection
**Applies to:** `RefreshToken`.
**Rule:** Every successful refresh rotates the token: the presented one is marked used (`used_at = NOW()`) and a new token is issued with the same `family_id`. If a token with `used_at IS NOT NULL` is presented, every `RefreshToken` sharing its `family_id` is invalidated and the request returns `401`.
**Rationale:** Limits the window of a stolen token and catches replays.
**Enforcement:** Transactional repository operation with `SELECT ... FOR UPDATE`; see [[04-authentication]].

## RULE-13 — Single-use tokens are consumed atomically
**Applies to:** `EmailVerificationToken`, `PasswordResetToken`, and any future single-use credential.
**Rule:** Consumption uses `UPDATE ... WHERE used_at IS NULL AND expires_at > NOW() RETURNING id`. If zero rows are affected, the token has been used or expired and the request returns `410 Gone`.
**Rationale:** Prevents double-spend under concurrent requests (double-click, browser back, retried link).
**Enforcement:** Repository layer.

## RULE-15 — Comment body length and format
**Applies to:** `Comment.body`.
**Rule:** The body must be 1–2000 characters and is parsed as a limited Markdown subset (bold, italic, links, inline code, code blocks, line breaks). HTML is rejected; the server sanitises output.
**Rationale:** Length cap prevents abuse; Markdown subset gives expressiveness without XSS risk.
**Enforcement:** Application layer validator + sanitiser; API rejects with `422 Unprocessable Entity`.

## RULE-16 — Comments are editable only within 15 minutes by their author
**Applies to:** `Comment` updates.
**Rule:** A comment can be updated only by `author_id` and only while `now() - created_at < 15 minutes`. Editing uses optimistic locking on `updated_at`. After the window, all edit attempts return `403 Forbidden`.
**Rationale:** Allows typo fixes without enabling silent revisionism on signal-bearing discussion.
**Enforcement:** Repository layer with `UPDATE ... WHERE id = $1 AND author_id = $2 AND updated_at = $expected AND created_at > NOW() - INTERVAL '15 minutes'`; see [[05-comments]].

## RULE-17 — Comments are soft-deleted, never removed
**Applies to:** `Comment` deletion and moderator hide.
**Rule:** Deletion sets `deleted_at` and `deleted_by_user_id`; moderator hide sets `hidden_by_moderator_id` and `hidden_reason` and writes a `CommentModerationLog` entry in the same transaction. The row is never DELETE-d. Both operations are idempotent via `UPDATE ... WHERE deleted_at IS NULL` / `WHERE hidden_by_moderator_id IS NULL`.
**Rationale:** Tombstones preserve thread continuity; audit trail requires the row to remain.
**Enforcement:** Repository layer; partial index `WHERE deleted_at IS NULL AND hidden_by_moderator_id IS NULL` powers the live-comment query.

## RULE-14 — Passwords hashed with Argon2id
**Applies to:** `User.password_hash`.
**Rule:** Passwords are hashed with Argon2id (`m = 64MB, t = 3, p = 4`) before storage. Raw passwords never appear in logs, request bodies persisted to disk, or error messages. Verification is a constant-time comparison.
**Rationale:** Memory-hard hash resists GPU brute force; constant-time compare resists timing attacks.
**Enforcement:** Auth service; lint rule forbids `password` substring in log statements.

## RULE-10 — Mutating endpoints are idempotent
**Applies to:** every API endpoint that mutates state.
**Rule:** Every mutating endpoint is idempotent: either naturally (through unique constraints, e.g. the vote uniqueness on `(feature_request_id, user_id)`) or through an `Idempotency-Key` header that the server persists and de-duplicates against for at least 24 hours.
**Rationale:** Network retries from clients are normal under high concurrency. Without idempotency, retries produce duplicate effects.
**Enforcement:** API middleware + unique partial indexes on `(actor_id, idempotency_key)` where applicable. See [[03-concurrency-and-collision-safety]].

## RULE-03 — Authentication required for write actions
**Applies to:** Submission of `FeatureRequest`, casting of `Vote`.
**Rule:** Submitting a feature request or casting a vote requires an authenticated `User`. Reading the list and detail of feature requests does not.
**Rationale:** Required to enforce RULE-01 and to attribute submissions; keeps discovery friction low.
**Enforcement:** API layer (permission classes).
