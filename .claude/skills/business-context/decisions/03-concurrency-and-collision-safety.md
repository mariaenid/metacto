# 03 — Concurrency and collision safety

## Context
The application is designed for high concurrency. Any operation that mutates shared state must remain correct under simultaneous writes from many clients. This is a foundational, cross-cutting constraint: no design decision is complete until it accounts for collisions.

This ADR codifies the collision-safety strategy across the system and **supersedes** the parts of [[01-ranking-algorithm]] that called for `hot_score` denormalisation.

## Decision

### Vote mutations
- The `Vote` row's existence is the source of truth for whether a user has voted on a request. The unique constraint `(feature_request_id, user_id)` makes duplicate inserts impossible at the database layer.
- `FeatureRequest.vote_count` stays denormalised, but is maintained through atomic per-row updates in the same transaction as the `Vote` mutation:
  ```sql
  BEGIN;
  INSERT INTO votes (feature_request_id, user_id) VALUES ($1, $2);
  UPDATE feature_requests SET vote_count = vote_count + 1 WHERE id = $1;
  COMMIT;
  ```
  If the `INSERT` raises a unique-constraint violation, the whole transaction rolls back; no counter drift is possible.
- Unvote uses `DELETE ... RETURNING id` to know whether to decrement. If nothing was deleted, the request is a no-op (idempotent unvote).
- The vote endpoint accepts an optional `Idempotency-Key` header; replays return the original response without re-mutating.

### Hot score
- The `hot_score` column proposed by [[01-ranking-algorithm]] is **removed**. The score is computed at query time as a derived SQL expression:
  ```sql
  (vote_count - 1)
    / POWER(EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 + 2, 1.4)
  AS hot_score
  ```
- Rationale: a stored hot_score must be refreshed continuously because time decays whether or not votes change. Compute-on-read removes that maintenance burden, eliminates the corresponding write-side contention on hot rows, and is fast enough for the expected active-set sizes (<100k rows).
- If the active set ever grows past the point where ad-hoc sorting becomes expensive, the path is a materialised view refreshed every N minutes OR a Redis sorted set updated by a background job. Both are deferred until measured need.

### Status transitions
- Status updates use optimistic locking with the expected-from-status in the WHERE clause:
  ```sql
  UPDATE feature_requests
  SET status = $new, updated_at = NOW()
  WHERE id = $id AND status = $expected_from;
  ```
  If the affected row count is zero, another moderator already transitioned the request; the API returns `409 Conflict` and the moderator re-reads the current state.
- The `StatusChangeLog` row is written inside the same transaction.

### Duplicate cycles
- Setting `duplicate_of_id` acquires row locks on the source and the target (`SELECT ... FOR UPDATE`) and walks the duplicate chain to detect cycles before committing the transition.

### Submission idempotency
- The submit endpoint accepts an `Idempotency-Key` header. Replays within a 24-hour window return the original `FeatureRequest` without inserting a new row.
- Enforced by a unique partial index on `(author_id, idempotency_key) WHERE idempotency_key IS NOT NULL`.

### Rate limiting
- Implemented in Redis with atomic `INCR` + `EXPIRE`, keyed by `(user_id, action)`. Redis acts as the single coordinator so the limit holds across replicas.

### Background jobs
- Any background job that mutates `FeatureRequest` (archiving, reconciliation, eventual notifications) uses the same row-locking and idempotency-key patterns as the API. There is no privileged "background path" that skips collision safety.

### Optimistic UI on the client
- Vote interactions update the UI immediately, send the request in the background, and reconcile against the server response. On error the UI rolls back and surfaces the failure.
- The client must include the `Idempotency-Key` header on retries so network flakiness never produces duplicate votes.

## Consequences
- Every mutating endpoint either accepts an idempotency key or is naturally idempotent through a unique constraint.
- `vote_count` may briefly disagree with `COUNT(*)` of the `Vote` table during a transaction-in-flight; a nightly reconciliation job detects and repairs any drift caused by aborted writes.
- Hot ordering is now a query-time computation. The index `(status, vote_count DESC, created_at DESC)` covers the default `top` sort; `hot` and `new` rely on the same base index plus an in-memory sort of the active subset.
- The whole codebase commits to one discipline: **assume collisions everywhere, defer denormalisation, prefer database-enforced invariants over application-layer checks**.
