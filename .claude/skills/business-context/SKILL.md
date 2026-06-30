---
name: business-context
description: Load this skill whenever work touches the project's domain entities, business rules, terminology, or whenever a new user prompt needs to be archived and distilled. Holds canonical knowledge that grows with every prompt.
---

# Business Context

Canonical knowledge about the assessment domain, refined incrementally from user prompts.

## When to load
- The user asks about a domain concept, rule, or entity.
- A code change touches `backend/apps/*/domain/` or `frontend/packages/features/`.
- A new prompt arrives that needs to be archived and distilled.
- A naming or vocabulary question needs the canonical term.

## Files
- `domain/entities.md` — entities and their attributes.
- `domain/rules.md` — invariants and business rules.
- `domain/glossary.md` — vocabulary with definitions.
- `decisions/` — one file per architectural decision (ADR-lite).
- `prompts/` — archive of raw and refined user prompts.

## How to update
Each time a new prompt arrives that carries domain meaning:
1. Save the raw prompt to `prompts/NN-raw.md` verbatim (next sequential number, zero-padded).
2. Write a refined, professional English version at `prompts/NN-refined.md`.
3. Append new entities, rules, or vocabulary to the relevant `domain/*.md` files. Never overwrite; only add or refine.
4. If the prompt drives an architectural decision, record it at `decisions/NN-<kebab-slug>.md` using the template below.
5. Keep `domain/*.md` deduplicated and consistent across files.

Always update both the chronological `prompts.txt` at the repo root (see `CLAUDE.md`) and this structured archive. They serve different purposes: `prompts.txt` is a session log; this archive feeds domain knowledge.

## ADR template
```
# NN — Title

## Context
Why this decision was needed.

## Decision
What was decided.

## Consequences
Trade-offs accepted, follow-up implications.
```
