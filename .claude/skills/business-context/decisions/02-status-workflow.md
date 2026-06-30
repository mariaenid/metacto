# 02 — Status workflow for FeatureRequest

## Context
The default ranking (`top`, see [[01-ranking-algorithm]]) filters by status. The product also needs to communicate a feature request's lifecycle back to its author, voters, and the wider community — feature voting tools live and die on the loop between "I voted for this" and "here is what happened to it."

We need a status set, transition rules, a permission model, and an audit trail that can later power notifications and timeline views.

## Decision

### Status set (seven values)

| Status | Meaning | In default `top` |
|---|---|---|
| `open` | Just submitted, no triage yet | yes |
| `under_review` | Team is evaluating | yes |
| `planned` | Accepted, in backlog | yes |
| `in_progress` | Being built | yes |
| `shipped` | Delivered in production | no |
| `closed` | Declined or not pursuing | no |
| `duplicate` | Already exists as another request | no |

### State machine
- Forward linear path: `open → under_review → planned → in_progress → shipped`.
- From any non-terminal status: `→ closed` or `→ duplicate`.
- No automatic back transitions. Reverts are explicit moderator actions, logged in audit.
- `duplicate` requires a non-null `duplicate_of_id` pointing at another `FeatureRequest`.

### Permissions
- `User.role` enum: `user` (default) | `moderator` | `admin`.
- Only `moderator` and `admin` may transition status.
- Authors may *propose* a duplicate (UX hint surfaced when posting), but the actual transition requires moderator approval.

### Audit log
Every status transition writes one `StatusChangeLog` row in the same database transaction as the status update. Schema:
- `id` (UUID)
- `feature_request_id` (UUID, FK)
- `from_status`, `to_status` (enum)
- `changed_by_user_id` (UUID, FK)
- `changed_at` (timestamp)
- `reason` (text, optional)

The log powers:
- A timeline view on the FeatureRequest detail page.
- Future notifications (in scope to leave hook points; out of scope to build).
- Compliance and debug visibility for moderators.

## Consequences
- `User` gains a `role` field; authorization checks in the API layer read it.
- `duplicate_of_id` allows cycles in theory; the application layer forbids them (no A → B where B is already a duplicate of A, directly or transitively).
- `StatusChangeLog` grows linearly with status churn — bounded by request count times average lifecycle length. Not a scale concern at MVP+; partition by year if it ever becomes one.
- The moderator panel on the detail view adds contained UI surface, hidden from `user` role.
