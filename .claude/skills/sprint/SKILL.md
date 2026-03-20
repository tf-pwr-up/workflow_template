---
name: sprint
description: "Sprint planning — detailed analysis, planning, and council review for a specific sprint"
---

# /sprint — Sprint Development & Review (Planning Phase)

## Purpose

This skill orchestrates the PLANNING phase for a specific sprint. It produces a comprehensive, council-reviewed implementation plan ready for `/develop`. This is NOT the coding phase — no production code is written here.

## Invocation

```
/sprint <N>
```

Where `N` is the sprint number from the approved sprint breakdown.

## Prerequisites (BLOCKING)

Before ANY work begins, verify ALL of the following. If any check fails, STOP and instruct the user on how to resolve it.

1. **Approved requirements exist** at `docs/requirements/proposed-sprints.md`. If this file does not exist, tell the user to run `/analyze` first. Do NOT proceed without it.
2. **Sprint N is defined** in the sprint breakdown within `docs/requirements/proposed-sprints.md`. If sprint N is not listed, STOP and inform the user that the requested sprint number does not exist in the approved breakdown.

## Execution Phases

This skill has four sequential phases: A, B, C, D. Each phase MUST complete before the next begins. No phase may be skipped.

---

## Phase A: Detailed Analysis

### Step 1 — Load Context

Read the following files to establish full context before any analysis begins:

| File | Purpose |
|------|---------|
| `docs/requirements/proposed-sprints.md` | Sprint N requirements and acceptance criteria |
| `CLAUDE.md` | Architectural patterns, conventions, tech stack |
| `docs/plans/sprint-<M>-plan.md` (for all M < N) | Prior sprint plans — understand what was already built |
| `docs/outcomes/sprint-<M>-outcome.md` (for all M < N) | Prior sprint outcomes — understand what actually shipped and any deviations |
| `docs/bug-patterns.md` | Known bug patterns to avoid repeating |
| `docs/findings/sprint-<M>-findings.md` (for all M < N) | Prior council findings — avoid previously flagged issues |

If any prior-sprint files do not exist (e.g., this is sprint 1), note their absence and continue.

### Step 2 — Detailed Questioning

Spawn an **Analysis Agent** using the Agent tool. The agent MUST:

- Ask implementation-specific questions to the user via `AskUserQuestion`, **one question at a time**
- Focus on resolving ambiguities in the sprint requirements, specifically:
  - Ambiguous acceptance criteria (what exactly constitutes "done"?)
  - Data model details (field types, relationships, constraints, defaults)
  - API contracts (request/response shapes, status codes, error formats)
  - UI/UX expectations (layouts, responsive behaviour, accessibility requirements)
  - Integration details (third-party services, auth flows, webhook formats)
  - Edge cases not addressed in requirements (empty states, error states, concurrent access)
- Continue asking until all ambiguities for this sprint are resolved
- Record answers for use in subsequent phases

The agent should be pragmatic — do not ask questions whose answers are obvious from context or conventions in CLAUDE.md.

### Step 3 — Gap Analysis

This step requires TWO sub-agents spawned via the Agent tool. They MUST be separate agents.

**ANTI-BYPASS RULE:** The gap list MUST be produced by the Inventory Agent and Gap Agent via the Agent tool. The orchestrator (you) MUST NOT write the gap list directly using Write/Edit tools. This ensures independent analysis.

#### 3a — Inventory Agent

Spawn using Agent tool with `subagent_type: Explore`.

Instructions for the Inventory Agent:
- Read the sprint N requirements from `docs/requirements/proposed-sprints.md`
- Read the existing codebase (source files, configs, tests)
- Produce a **complete feature checklist** — every discrete piece of functionality required by sprint N
- Number each item sequentially (e.g., INV-1, INV-2, ...)
- Include: features, UI components, API endpoints, data model changes, integrations, configuration changes, test requirements

#### 3b — Gap Agent

Spawn using Agent tool with `subagent_type: Explore`. This agent runs AFTER the Inventory Agent completes.

Instructions for the Gap Agent:
- Read the inventory produced by the Inventory Agent
- Read the existing codebase
- For each inventory item, classify as:
  - **DONE** — fully implemented and working
  - **PARTIAL** — partially implemented, specify what remains
  - **MISSING** — not implemented at all
- Perform an **integration surface check**:
  - Orphaned routes (defined but not linked from navigation)
  - Unregistered components (created but not imported/used)
  - Contract mismatches (frontend expects shape X, backend returns shape Y)
  - Missing error handlers
- Write the complete gap analysis to: `docs/gaps/sprint-<N>-gaps.md`

The gap file format:

```markdown
# Sprint <N> Gap Analysis

## Summary
- Total items: <count>
- DONE: <count>
- PARTIAL: <count>
- MISSING: <count>

## Inventory & Gap Status

| # | Item | Category | Status | Details |
|---|------|----------|--------|---------|
| INV-1 | ... | Feature | MISSING | ... |
| INV-2 | ... | API | PARTIAL | ... |

## Integration Surface Issues

| # | Type | Description | Affected Files |
|---|------|-------------|----------------|
| ISS-1 | Orphaned Route | ... | ... |
```

---

## Phase B: Planning

### Step 4 — Plan Generation

Spawn a **Plan Agent** using the Agent tool with `subagent_type: Plan`.

**ANTI-BYPASS RULE:** The plan MUST be produced by the Plan Agent via the Agent tool. The orchestrator (you) MUST NOT write the plan directly using Write/Edit tools.

Instructions for the Plan Agent:

Read the following before generating the plan:
- Sprint N requirements from `docs/requirements/proposed-sprints.md`
- Gap analysis from `docs/gaps/sprint-<N>-gaps.md`
- `CLAUDE.md` for architectural patterns and conventions
- Answers from Phase A questioning
- Prior sprint plans and outcomes (if they exist)

Produce `docs/plans/sprint-<N>-plan.md` containing ALL of the following sections:

#### 4.1 — Implementation Units

Break the work into discrete implementation units. For each unit:

```markdown
### Unit <X>: <Name>

**Gap references:** INV-3, INV-7 (from gap list)
**Dependencies:** Unit 2 must complete first
**Estimated complexity:** Low / Medium / High

**Files to create:**
- `src/components/FeatureX.tsx` — Description of what this file does

**Files to modify:**
- `src/routes/index.ts` — Add route for FeatureX
- `src/api/client.ts` — Add FeatureX API methods

**Context files (MUST read before implementing):**
- `src/components/ExistingSimilar.tsx` — Follow this pattern
- `src/types/shared.ts` — Use existing type definitions
- `CLAUDE.md` — Section on component patterns
```

#### 4.2 — Shared Interfaces & API Contracts

Define all shared types, API request/response shapes, and contracts between units. Be specific — include TypeScript types, endpoint paths, HTTP methods, status codes.

#### 4.3 — Data Model Changes

Specify schema changes, migrations, seed data updates. Include exact field names, types, constraints, defaults, and relationships.

#### 4.4 — Test Strategy

For EACH requirement in the sprint:

```markdown
#### Requirement: "<requirement text>"

**Unit tests:**
- Test that <specific behaviour> when <condition>
- Test that <error case> returns <expected result>

**Integration tests:**
- Test that <component A> correctly communicates with <component B>

**E2E tests:**
- Test user journey: <step 1> -> <step 2> -> <verify result>
```

The plan MUST propose specific tests for each requirement. Generic statements like "write tests" are NOT acceptable.

#### 4.5 — Dependency Order

A clear ordering of implementation units showing which can run in parallel and which are sequential:

```markdown
## Dependency Order

1. Unit 1 (no dependencies — can start immediately)
2. Unit 2 (no dependencies — can start immediately, parallel with Unit 1)
3. Unit 3 (depends on Unit 1)
4. Unit 4 (depends on Unit 2 and Unit 3)
```

#### 4.6 — Architectural Patterns

List specific patterns from CLAUDE.md that apply to this sprint. Quote the relevant sections. If the sprint requires a pattern not yet in CLAUDE.md, propose it here for council review.

**Validation:** The plan MUST reference gap list items by their inventory numbers (INV-1, INV-2, etc.). Every PARTIAL and MISSING item from the gap list must be addressed in at least one implementation unit. The Spec Compliance council member will verify this.

---

## Phase C: Council Review

### Step 5 — Council Review

Invoke the council review by running the following command:

```bash
./scripts/council-dispatch.py plan <N> "<sprint-title>"
```

Where `<sprint-title>` is the title/name of the sprint from the requirements.

#### Council Members (Active for Plan Review)

| Member | Focus Area |
|--------|------------|
| **Security** | Auth gaps, injection risks, data exposure, CORS, CSRF, input validation |
| **Architecture** | Pattern consistency, separation of concerns, scalability, coupling |
| **Spec Compliance** | Every requirement has a plan item, every gap item is addressed, acceptance criteria are testable |
| **Testing** | Test strategy completeness, coverage gaps, test quality, E2E feasibility |
| **Domain Expert** | Business logic correctness, domain model accuracy, workflow completeness |
| **Arbitrator** | Runs LAST — see mandate below |

#### Arbitrator Mandate

The Arbitrator reviews ALL findings from other council members and for each finding determines:

- **Scope creep detection** — Is this finding asking for work outside sprint N scope?
- **Complexity assessment** — Does the suggested change significantly increase complexity?
- **Nitpick identification** — Is this a stylistic preference rather than a substantive issue?
- **Security sanity check** — Is a security finding actually exploitable in this context?
- **Priority override** — Assign final priority: CRITICAL / HIGH / MEDIUM / LOW / DISMISS
- **Verdict recommendation** — APPROVE, APPROVE WITH CONDITIONS, or REQUEST CHANGES

#### Findings Tracker

Council findings are written to `docs/findings/sprint-<N>-findings.md` as a persistent tracker.

Format:

```markdown
# Sprint <N> Council Findings

## Review Round 1

| # | Round | Severity | Finding | Arbitrator | Status | Resolution |
|---|-------|----------|---------|------------|--------|------------|
| F-1 | 1 | HIGH | Missing input validation on /api/items POST | AGREE-HIGH: Exploitable injection risk | OPEN | |
| F-2 | 1 | MEDIUM | Component doesn't handle loading state | DOWNGRADE-LOW: Nitpick, not in acceptance criteria | OPEN | |
| F-3 | 1 | HIGH | No test for concurrent access | DISMISS: Out of scope for sprint N | DISMISSED | |
```

The Arbitrator column MUST contain one of:
- `AGREE-<PRIORITY>: <reason>`
- `UPGRADE-<PRIORITY>: <reason>`
- `DOWNGRADE-<PRIORITY>: <reason>`
- `DISMISS: <reason>`

### Step 6 — Present to User

After council review completes:

1. **Display the findings table** with the Arbitrator's assessment for each finding
2. **Summarize** the Arbitrator's overall verdict (APPROVE / APPROVE WITH CONDITIONS / REQUEST CHANGES)
3. **Ask the user** to choose one of:
   - **Approve** — Accept the plan as-is (proceed to Phase D)
   - **Iterate** — Address findings, update the plan, and re-run council review
   - **Modify requirements** — Go back and change sprint requirements before re-planning

If the user chooses **Iterate**:
- Update the plan to address the agreed-upon findings
- Mark addressed findings as RESOLVED in the tracker with the resolution description
- Re-run council: `./scripts/council-dispatch.py plan <N> "<sprint-title>"`
- New findings from subsequent rounds use incrementing round numbers (Round 2, Round 3, ...)
- Convergence guardrails apply (the council dispatch script manages iteration limits)

If the user chooses **Modify requirements**:
- Instruct the user to update `docs/requirements/proposed-sprints.md`
- Once updated, restart from Phase A

---

## Phase D: Final Plan

### Step 7 — Approval & Lock

Once the user approves the final plan:

1. Ensure the plan at `docs/plans/sprint-<N>-plan.md` reflects all approved changes
2. Mark the plan as approved by adding to the top of the file:

```markdown
> **Status: APPROVED**
> **Approved date: <current date>**
> **Council rounds: <number of review rounds>**
> **Open findings: <count of non-dismissed, non-resolved findings>**
```

3. Inform the user they can now proceed to `/develop <N>` to begin implementation

---

## Enforcement Rules

These rules are NON-NEGOTIABLE. Violations constitute workflow failures.

1. **Phase A cannot be skipped.** The gap list (`docs/gaps/sprint-<N>-gaps.md`) MUST exist before Phase B begins.
2. **Phase C cannot be skipped.** Council review is mandatory. The plan cannot be approved without at least one round of council review.
3. **Cannot proceed to `/develop` without explicit user approval.** The user must say they approve the plan.
4. **Gap list must be agent-produced.** The Inventory Agent and Gap Agent must produce the gap analysis via the Agent tool. Writing it inline is a workflow violation.
5. **Plan must be agent-produced.** The Plan Agent must produce the plan via the Agent tool. Writing it inline is a workflow violation.
6. **Plan must reference gap items.** Every PARTIAL and MISSING inventory item must appear in at least one implementation unit. The Spec Compliance council member verifies this.
7. **Plan must propose specific tests.** Every requirement must have concrete test proposals (not generic "write tests" statements).
8. **Findings tracker is persistent.** Findings from all rounds are retained. Earlier findings are never deleted — only their Status and Resolution columns are updated.

---

## Output Artifacts

| Artifact | Path | Produced By |
|----------|------|-------------|
| Gap analysis | `docs/gaps/sprint-<N>-gaps.md` | Inventory Agent + Gap Agent |
| Implementation plan | `docs/plans/sprint-<N>-plan.md` | Plan Agent |
| Council findings | `docs/findings/sprint-<N>-findings.md` | Council dispatch script |

---

## Error Handling

| Situation | Action |
|-----------|--------|
| `proposed-sprints.md` does not exist | STOP. Tell user to run `/analyze` first. |
| Sprint N not found in breakdown | STOP. Tell user the sprint number is invalid. |
| Council dispatch script not found | STOP. Tell user to run `/setup` to initialize project tooling. |
| Council dispatch script fails | Show error output. Ask user if they want to retry or skip council (skipping requires explicit user override and is logged). |
| User wants to skip council | Warn that this violates workflow. Require explicit confirmation. Log the skip in the findings file as `COUNCIL REVIEW SKIPPED BY USER OVERRIDE`. |
| Inventory/Gap agents produce empty results | Flag as suspicious. Ask user to verify requirements are sufficiently detailed. |
