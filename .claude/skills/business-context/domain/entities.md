# Entities

Canonical list of domain entities and their attributes.
Populated incrementally as prompts arrive.

## Format
```
## <EntityName>
**Purpose:** one-line description.
**Attributes:**
- `field_name` (type) — meaning, constraints.
**Relationships:**
- Links to other entities and cardinality.
**Invariants:**
- Conditions that must always hold (see also `rules.md`).
```

---

## FeatureRequest
**Purpose:** A user-submitted proposal for a new product capability that others can discover and signal demand for.
**Attributes:**
- `id` (UUID) — stable public identifier.
- `title` (string, required) — short headline of the proposal.
- `description` (text, optional) — detailed explanation; length and format to be confirmed.
- `author_id` (UUID, FK → User) — the user who submitted the request.
- `status` (enum) — lifecycle state. One of `open` (default) | `under_review` | `planned` | `in_progress` | `shipped` | `closed` | `duplicate`. Drives the default `top` filter (see [[01-ranking-algorithm]]) and the state machine in [[02-status-workflow]].
- `duplicate_of_id` (UUID, FK → FeatureRequest, nullable) — set only when `status = duplicate`. Points to the canonical request this one duplicates. Cycles are forbidden by the application layer.
- `vote_count` (integer, denormalised) — current number of upvotes, maintained transactionally with each `Vote` mutation by atomic increment/decrement (see [[03-concurrency-and-collision-safety]]).
- `created_at` (timestamp).
- `updated_at` (timestamp).

Note: `hot_score` is **not** a stored field; it is computed at query time from `vote_count` and `created_at`. The earlier denormalisation plan in [[01-ranking-algorithm]] is superseded by [[03-concurrency-and-collision-safety]].

**Relationships:**
- One `FeatureRequest` has many `Vote`s.
- Each `FeatureRequest` belongs to exactly one `User` (author).

**Invariants:** see [[rules]] (RULE-01, RULE-02, RULE-04, RULE-05).

## Vote
**Purpose:** A user's positive signal of demand on a `FeatureRequest`.
**Attributes:**
- `id` (UUID).
- `feature_request_id` (UUID, FK → FeatureRequest).
- `user_id` (UUID, FK → User).
- `created_at` (timestamp).

**Relationships:**
- Belongs to one `FeatureRequest` and one `User`.

**Invariants:**
- A user may have at most one `Vote` per `FeatureRequest` (see [[rules]] RULE-01).

## User
**Purpose:** Authenticated identity that can submit feature requests and cast votes. Some users carry elevated roles that allow status moderation.
**Attributes:**
- `id` (UUID).
- `email` (string, unique).
- `display_name` (string).
- `password_hash` (string) — Argon2id digest. Never returned by any API.
- `role` (enum) — `user` (default) | `moderator` | `admin`. Drives authorization checks for status transitions and other moderation actions.
- `email_verified` (boolean, default `false`) — write endpoints require this to be true (see [[04-authentication]]).
- `last_login_at` (timestamp, nullable).
- `created_at` (timestamp).

**Relationships:**
- Authors many `FeatureRequest`s.
- Casts many `Vote`s.
- Records many `StatusChangeLog` entries (only `moderator` and `admin` in practice).
- Holds many `RefreshToken`, `EmailVerificationToken`, `PasswordResetToken` rows.

## RefreshToken
**Purpose:** Long-lived opaque token that exchanges for a fresh access token. Rotating: each use produces a new one and invalidates the previous.
**Attributes:**
- `id` (UUID).
- `user_id` (UUID, FK → User).
- `family_id` (UUID) — groups successive rotations from a single login session. Used to invalidate the whole family on breach detection.
- `token` (string, unique, base64url-encoded 32 bytes).
- `expires_at` (timestamp, 30 days after issuance).
- `used_at` (timestamp, nullable) — when present, the token has been rotated or revoked.
- `created_at` (timestamp).

**Relationships:**
- Belongs to one `User`. Many tokens may share a `family_id` (rotation history).

**Invariants:**
- A token presented with `used_at IS NOT NULL` triggers breach detection: every `RefreshToken` with the same `family_id` is invalidated. See [[04-authentication]].
- Rotation is atomic: mark old used + insert new + return new, all in one transaction.

## EmailVerificationToken
**Purpose:** Single-use token sent by email to confirm ownership of an address.
**Attributes:**
- `id` (UUID).
- `user_id` (UUID, FK → User).
- `token` (string, unique).
- `expires_at` (timestamp, 24h after issuance).
- `used_at` (timestamp, nullable).
- `created_at` (timestamp).

**Invariants:**
- Consumed via `UPDATE ... WHERE used_at IS NULL AND expires_at > NOW()`. Zero affected rows → return `410 Gone`.

## Comment
**Purpose:** User-authored discussion message attached to a `FeatureRequest`. Flat structure, chronological.
**Attributes:**
- `id` (UUID).
- `feature_request_id` (UUID, FK → FeatureRequest).
- `author_id` (UUID, FK → User).
- `body` (text, 1–2000 characters, limited Markdown).
- `created_at` (timestamp).
- `updated_at` (timestamp) — used for optimistic locking on edits.
- `deleted_at` (timestamp, nullable) — set on self-delete.
- `deleted_by_user_id` (UUID, FK → User, nullable) — populated on self-delete (equals `author_id`).
- `hidden_by_moderator_id` (UUID, FK → User, nullable) — populated on moderator hide.
- `hidden_reason` (text, nullable).

**Relationships:**
- Belongs to one `FeatureRequest` and one `User` (author).
- Has many `CommentModerationLog` entries (zero for un-moderated comments).

**Invariants:**
- A comment cannot be edited after 15 minutes from `created_at`; see [[05-comments]].
- A comment is never hard-deleted; tombstones preserve thread continuity.

## CommentModerationLog
**Purpose:** Audit record for moderator actions on `Comment`s.
**Attributes:**
- `id` (UUID).
- `comment_id` (UUID, FK → Comment).
- `action` (enum: `hide` | `unhide`).
- `by_user_id` (UUID, FK → User) — must have `moderator` or `admin` role.
- `at` (timestamp).
- `reason` (text, optional).

**Relationships:**
- Belongs to one `Comment` and one `User`.

**Invariants:**
- Written in the same transaction as the corresponding `Comment` mutation (see [[03-concurrency-and-collision-safety]]).

## PasswordResetToken
**Purpose:** Single-use token that authorises a password reset.
**Attributes:**
- `id` (UUID).
- `user_id` (UUID, FK → User).
- `token` (string, unique).
- `expires_at` (timestamp, 1h after issuance).
- `used_at` (timestamp, nullable).
- `created_at` (timestamp).

**Invariants:**
- Same atomic-consumption pattern as `EmailVerificationToken`.

## StatusChangeLog
**Purpose:** Audit record of every `FeatureRequest` status transition. Powers the timeline view, future notifications, and moderator visibility.
**Attributes:**
- `id` (UUID).
- `feature_request_id` (UUID, FK → FeatureRequest).
- `from_status` (enum) — status before the change.
- `to_status` (enum) — status after the change.
- `changed_by_user_id` (UUID, FK → User) — must have `moderator` or `admin` role.
- `changed_at` (timestamp).
- `reason` (text, optional) — moderator-supplied justification.

**Relationships:**
- Belongs to one `FeatureRequest` and one `User`.

**Invariants:**
- Written in the same transaction as the `FeatureRequest.status` update (see [[03-concurrency-and-collision-safety]]).
- `from_status` must equal the request's status at the moment of the transition; enforced via optimistic locking.
