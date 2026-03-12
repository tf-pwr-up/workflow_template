---
name: phase-0
description: "Feature Inventory & Gap Analysis. MANDATORY before any planning or implementation."
---

# /phase-0 — Feature Inventory & Gap Analysis

Trigger: MANDATORY before any planning or implementation. This skill MUST run before `/plan` or `/implement`.

## Purpose

Produce a persistent, structured gap list that becomes the contract for what gets built. Without this artifact, no planning or implementation may proceed.

## Instructions

### Step 1: Determine Source of Truth

Check if analysis corpus exists:
```
ls docs/analysis/[0-9]*.md
```

- **If corpus exists**: Use it as primary source. Read the relevant `docs/analysis/NN-<area>.md` files for the feature area being worked on.
- **If no corpus**: Determine the source of truth:
  - If a reference implementation is defined in CLAUDE.md, read the actual files (grep/read, never guess). Also read any spec documents referenced in CLAUDE.md.
  - If no reference exists, ask the user to describe the required functionality. Do not proceed until the user has confirmed the feature set.

### Step 2: Inventory Agent

Launch an Agent (subagent_type: Explore) to produce a **complete feature inventory** for the scope of work. The inventory MUST list:

- Every route/page
- Every UI component and its behaviour
- Every API endpoint involved
- Every user interaction (clicks, keyboard shortcuts, form submissions)
- Every visual state (loading, empty, error, success)
- Every navigation path (how does the user reach this feature?)

Output format — a numbered checklist:
```
## Feature Inventory: [Area Name]

1. [Feature] — [brief description] | Reference: [file:line]
2. [Feature] — [brief description] | Reference: [file:line]
...
```

### Step 3: Gap Agent

Launch an Agent (subagent_type: Explore) to compare the inventory against the **current codebase**. For each inventory item:

- **Read actual files** to verify status (don't trust memory or assumptions)
- Classify as: `DONE` (matches spec), `PARTIAL` (exists but incomplete — list what's missing), `MISSING` (not implemented)
- For `DONE` items: verify behaviour matches, not just that the file exists

**Integration surface check** — in addition to feature-by-feature gaps, check the structural wiring:
- Routes with no navigation link (orphaned routes)
- Page components not registered in the router (orphaned components)
- API endpoints with no frontend caller (dead endpoints)
- Frontend API calls whose type annotations don't match the backend response shape

Flag these as `PARTIAL` with gap details describing the wiring issue.

Output format:
```
## Gap Analysis: [Area Name]

| # | Feature | Status | Current File | Gap Details |
|---|---------|--------|-------------|-------------|
| 1 | [name]  | DONE   | path/to/file.tsx | Matches spec |
| 2 | [name]  | PARTIAL | path/to/file.tsx | Missing: X, Y |
| 3 | [name]  | MISSING | — | Not implemented |

## Integration Surface

| Issue | Type | Details |
|-------|------|---------|
| /path/route | Orphaned route | No inbound link |
| Component.tsx | Orphaned component | Not in router |
```

### Step 4: Persist the Gap List

Write the gap list to `docs/gaps/YYYY-MM-DD-<area>.md` so it persists across sessions and can be verified later.

Create the `docs/gaps/` directory if it doesn't exist.

### Step 5: Present to User

Show the user:
1. Total counts: X DONE, Y PARTIAL, Z MISSING
2. The full gap table
3. Recommended priority order for MISSING/PARTIAL items
4. Ask: "Approve this scope, or adjust?"

**Do NOT proceed to /plan until the user confirms the gap list.**

## Enforcement

This skill is a hard prerequisite. The workflow rules require:
- `/plan` checks for a gap list artifact before proceeding
- `/implement` checks for both gap list and approved plan
- If no gap list exists, these skills MUST invoke `/phase-0` first

### Anti-Bypass

This skill MUST be invoked via the Skill tool — not simulated by manually writing a gap list file. The value of Phase 0 comes from:
1. The **Inventory Agent** reading actual reference code/specs (not the orchestrator summarising from memory)
2. The **Gap Agent** reading actual current codebase files (not the orchestrator guessing what exists)

If you find yourself writing `docs/gaps/*.md` directly without having launched these agents, you are bypassing Phase 0.
