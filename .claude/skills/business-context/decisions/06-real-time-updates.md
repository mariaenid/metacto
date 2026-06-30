# 06 — Real-time updates (deferred)

## Context
The product could in theory show live vote counts and incoming comments on the `FeatureRequest` detail view. The question is whether the MVP+ should build that, or rely on optimistic UI + revalidation to deliver the same perceived experience without the infrastructure.

## Decision
**Do not build real-time push in MVP+.** The detail and list views rely on:

- **Optimistic UI** on vote interactions (already specified in [[03-concurrency-and-collision-safety]]).
- **Stale-While-Revalidate** caching at the client (TanStack Query): the first paint serves cached data instantly, then the background refetch updates the view.
- **Revalidate on focus / on visible**: when the user returns to the tab (web) or brings the screen to the foreground (mobile), an automatic refetch runs.
- **Pull-to-refresh** on mobile, manual refresh affordance on web.

Together these cover the perceived smoothness of "live" without the operational cost of long-lived connections.

## Future direction (not built; designed)
If usage patterns later justify push (live admin dashboards, paid "live mode" feature, etc.), the implementation path is:

- **Server-Sent Events** (`/v1/feature-requests/{id}/events`), not WebSocket. The data is one-way; SSE is a trivial HTTP upgrade, auto-reconnects with `Last-Event-ID`, and traverses proxies without the WebSocket handshake.
- **Backplane:** Postgres `LISTEN/NOTIFY` from the same transaction as the data mutation, bridged to a Redis channel that the SSE workers subscribe to. Tying the event to the transaction prevents emitting on a rolled-back write.
- **Eventos emitidos:** `vote_count_changed` (debounced to a few hundred ms to absorb bursts), `status_changed`, `comment_added`.
- **Auth on EventSource:** short-lived signed cookie scoped to the event endpoint (the browser `EventSource` API cannot attach `Authorization` headers). Token rotation aligns with [[04-authentication]].
- **Mobile:** `react-native-sse` polyfill, or — for background notifications — Expo push notifications, which is a different problem (OS-level delivery when the app is closed).

## Trigger to revisit
Build SSE when at least one of these is true:
- User research shows refresh-driven UX is hurting engagement.
- A specific feature (e.g., live AMA on a feature request) needs push semantics.
- p95 staleness exceeds 30s and that meaningfully affects decisions made on the page.

## Consequences
- The MVP+ does not depend on Redis pub/sub, ASGI workers tuned for long-lived connections, or polyfills for EventSource on mobile.
- The frontend caching layer (TanStack Query) is canonical for state freshness; new features should add their queries to the same store rather than improvising local state.
- The ADR remains an open invitation: when reality demands realtime, the design path is documented and can be implemented without re-architecting.
