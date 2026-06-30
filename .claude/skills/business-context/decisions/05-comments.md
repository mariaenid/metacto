# 05 — Comments

## Context
Comments live alongside votes as the second discussion primitive on a `FeatureRequest`. In feature-voting tools the conversation is narrative and clarifying ("I'd love a Slack integration because…", "Same here, mainly for incident channels", "Status: planned for Q3"), not deeply threaded debate. The scope must produce that experience without overbuilding, while staying collision-safe under high concurrency (see [[03-concurrency-and-collision-safety]]).

## Decision

### Structure
- **Flat**, ordered chronologically ascending (oldest first).
- No replies-to-comment nesting. A future iteration could add quoting if needed.

### Format and length
- **Limited Markdown:** bold, italic, links, inline code, code blocks, line breaks. No raw HTML; rendered through a server-side sanitiser.
- **Length:** 1–2000 characters, enforced at the application layer and the API.

### Editing
- Author may edit their own comment for **15 minutes** after posting. After that, edits are rejected.
- An `edited` indicator with the most recent `updated_at` is shown in the UI.
- Editing is collision-safe: `UPDATE comments SET body = $new, updated_at = NOW() WHERE id = $id AND updated_at = $expected AND author_id = $user AND created_at > NOW() - INTERVAL '15 minutes'`. Zero rows → `409 Conflict`.

### Deletion (soft)
- Self-delete: `deleted_at` set, body replaced by `[deleted]` tombstone, author hidden. Idempotent: second click is a no-op.
- Moderator hide: `hidden_by_moderator_id` and `hidden_reason` set; tombstone reads "Hidden by a moderator". An entry is written to `CommentModerationLog` in the same transaction.

### Moderation log
- `CommentModerationLog` mirrors `StatusChangeLog`: `id`, `comment_id`, `action` (`hide` | `unhide`), `by_user_id`, `at`, `reason`.
- Provides audit visibility and the hook point for future notifications.

### Reactions
- **Out of scope** for MVP+. Documented as future work. `Vote` already covers positive signal on the request itself; reactions on comments add UI weight without product value at this stage.

### Notifications
- Posting, editing, hiding, and deleting comments emit a domain event consumed by an in-process event bus. The event has no handler in the MVP+, but the hook exists so a future `EmailNotifier` or `PushNotifier` can subscribe without touching the comment write path.

### Anti-abuse
- Rate limit: 1 comment per user per 30 seconds (Redis `INCR` + `EXPIRE`).
- `Idempotency-Key` header required on POST; replays return the original comment without inserting.

### Timeline integration
- The `FeatureRequest` detail view renders a **single unified timeline** that interleaves `Comment`, `StatusChangeLog`, and notable events (creation, first vote, milestone vote counts) chronologically.
- The timeline is paginated cursor-based; comments and status changes share the same ordering key (`occurred_at`).

## Consequences
- Two new entities: `Comment`, `CommentModerationLog`. Indexes: `(feature_request_id, created_at)` on `Comment` for timeline queries; partial index on `deleted_at IS NULL` for live-comment counts.
- The unified timeline requires an aggregation query that UNIONs comments and status-change-log entries, both projected to `(occurred_at, kind, payload)`. Materialised view candidate if scale demands it; out of scope to build now.
- The 15-minute edit window is a domain rule, not a UI constraint; the server is the authoritative gate.
- The moderation log adds a small append-only table that grows linearly with hide actions; not a scale concern at MVP+ size.
