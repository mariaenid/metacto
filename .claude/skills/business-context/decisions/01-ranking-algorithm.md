# 01 — Ranking algorithm for the feature request list

## Context
The product surfaces feature requests "based on popularity" (Prompt 01). Popularity in the feature-voting domain is not the same as in news (Hacker News) or general forums (Reddit): feature requests have lifecycles measured in months, not hours, and the meaningful signal is *persistent demand for unbuilt work*, not viral momentum.

A pure `ORDER BY vote_count DESC` over all requests has two failure modes:
1. Already-shipped or closed items dominate forever, hiding things the team can still act on.
2. New submissions need to accumulate votes before they appear, with no shortcut for genuine momentum.

The default ranking must reflect persistent demand while giving fresh ideas an entry path, without overcomplicating the user model.

## Decision
The list endpoint exposes a `sort` parameter with three options, surfaced in the UI as a single dropdown selector:

1. **`top`** (default) — Top among active.
   - Query: `vote_count DESC, created_at DESC` filtered to `status IN ('open', 'under_review', 'planned', 'in_progress')`.
   - Excludes `shipped`, `closed`, and `duplicate` from the default view (those items remain reachable through an explicit status filter or archive view).

2. **`hot`** — Recency-weighted score, HN-style, adapted for feature voting.
   - Formula: `score = (votes - 1) / (age_days + 2)^1.4`.
   - Gravity tuned to 1.4 (vs HN's 1.8) and age measured in days (vs HN's hours) because feature requests have month-long relevance, not news cycles.
   - Stored as a denormalised `hot_score` column on `FeatureRequest`, recomputed inside the same transaction that mutates a `Vote`, and refreshed on a periodic background job so idle items keep decaying.

3. **`new`** — Pure chronological.
   - Query: `created_at DESC`.

### Sub-decisions
- **Tie-breaking** for `top`: `created_at DESC` among rows with the same `vote_count`.
- **Author self-vote**: the author's own implicit vote is recorded as a `Vote` row at submission time. Aligns with Featurebase/Canny convention and removes the awkward "vote your own idea" interaction.
- **Vote count visibility**: the exact integer is shown on every list row and detail view, as the brief explicitly requires.
- **Filtered statuses**: items in `shipped`, `closed`, or `duplicate` are reachable via a dedicated status filter, but never appear in the default `top` feed.

## Consequences
- Ranking is coupled to status workflow: ADR-02 (status workflow) must land in the same scope as ranking. Accepted: both belong to the MVP+ scope.
- Two denormalised signals must be maintained per request (`vote_count` and `hot_score`). Both update inside the `Vote` mutation transaction.
- The dropdown adds minor UI complexity (~30 lines) but signals product maturity. Worth it.
- The composite indexes `(status, vote_count DESC, created_at DESC)` and `(status, hot_score DESC)` must exist for the default queries to scale.
- The gravity of 1.4 is a deliberate starting point, not a constant of nature. It will be revisited with usage data; the ADR records the rationale for the initial choice.
