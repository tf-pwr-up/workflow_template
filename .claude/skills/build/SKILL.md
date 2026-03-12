---
name: build
description: "Autonomous end-to-end pipeline: spec, plan, implement all batches, test, pre-deploy."
---

# /build — Autonomous Build Pipeline

Trigger: User wants to build a set of features from spec through to deployment-ready code with minimal interruption.

## Design Principle

**Interactive during specification. Autonomous during execution.**

The user participates in Phase A (scope and plan approval) — asking questions, adjusting priorities, making architectural decisions. Once they approve, Phase B runs fully autonomously: implementing batches, writing tests, running E2E, fixing failures, committing, and running pre-deploy checks. No interruptions until the final report.

## Instructions

### Phase 0: Bootstrap (runs once per repo, idempotent)

Before any work begins, verify the repo has the infrastructure needed for autonomous operation. Create any missing files — skip if they already exist.

#### Required files:

1. **`.claude/settings.json`** — Auto-approve all tool calls so the pipeline runs without permission prompts:
   ```json
   {
     "permissions": {
       "allow": [
         "Bash(*)", "Read(*)", "Edit(*)", "Write(*)",
         "Glob(*)", "Grep(*)", "Agent(*)", "Skill(*)", "ToolSearch(*)"
       ]
     }
   }
   ```

2. **`.claude/settings.local.json`** — Listed in `.gitignore`. Same format as above but for personal/local overrides.

3. **`CLAUDE.md`** — Project instructions file. If missing, create with the standard template from workflow-rules.md (Project Configuration section starts empty and accumulates knowledge as skills run).

4. **`.claude/workflow-rules.md`** — Workflow rules. If missing, copy from template or create with standard rules.

5. **`.claude/skills/`** — Skill definitions. If missing, the `/build` skill itself needs to exist at minimum. Pull from template via `/sync-template pull` if the template remote is configured.

6. **`.gitignore`** entries — Ensure these are present:
   - `.claude/settings.local.json`
   - `.wrangler/`
   - `node_modules/`
   - `dist/`
   - Any test artifacts (e.g., `test-results/`, `playwright-report/`, `.auth-state.json`)

7. **Git repo** — If not initialized, run `git init` and create an initial commit.

This step is idempotent — running it on an already-bootstrapped repo does nothing.

---

### Phase A: Spec & Plan (Interactive — user participates)

#### Step A1: Comprehensive Gap Analysis

Run a single `/phase-0` covering ALL remaining work (not per-batch). This produces the master gap list.

- If a recent gap list exists (`docs/gaps/`), read it and ask: "The gap list from [date] shows [X DONE, Y PARTIAL, Z MISSING]. Should I refresh it or use this?"
- If no gap list exists, run `/phase-0` from scratch
- Present the gap list to the user: counts, priorities, recommended batching

**Gate: User confirms scope.** ("Approve this scope, or adjust?")

#### Step A2: Master Plan with Batch Ordering

Run `/plan` but with a broader scope — produce a **master plan** covering all approved work, organized into ordered batches:

1. **Dependency analysis**: Identify which features depend on others (e.g., "entity CRUD pages need entity types to exist first")
2. **Batch grouping**: Group features into batches where:
   - Features within a batch are independent of each other (can be implemented in parallel)
   - Batches are ordered by dependency (batch 2 may depend on batch 1's output)
   - Each batch is a coherent, committable unit
3. **Per-batch plan**: For each batch, specify:
   - Implementation units with context files
   - Test strategy (unit + E2E)
   - Expected files created/modified
   - Dependencies on prior batches (if any)
4. **Run all review agents** (Architecture, Security, Performance, Testability, Spec Compliance, UI if applicable) against the FULL master plan — not per-batch

Present the master plan with batch ordering to the user.

**Gate: User approves the master plan.** This is the LAST manual gate. Everything after this is autonomous.

If the user has questions or wants changes, iterate on the plan. Once approved, Phase B begins with no further interruptions.

---

### Phase B: Autonomous Execution (No interruptions)

After user approval, execute all batches sequentially with no manual gates. The system handles all implementation, testing, failure fixing, and committing autonomously.

#### Step B0: Log the Approved Plan

Write the approved master plan to `docs/plans/YYYY-MM-DD-build.md` so it persists across context windows. Include batch ordering, implementation units per batch, and the test strategy.

#### Step B1: Execute Each Batch (loop)

For each batch in dependency order:

##### B1.1: Delta Check (lightweight, not a full /phase-0)

Before implementing, do a quick sanity check:
- Read the master plan for this batch's implementation units
- Verify context files exist (prior batches should have created them)
- If a context file is missing and was expected from a prior batch, check if the prior batch created it under a different name or path — adapt, don't fail
- If something is fundamentally wrong (prior batch failed silently), stop the loop and report

##### B1.2: Implement (autonomous /implement with auto-commit)

Run the `/implement` skill for this batch with these overrides:
- **Skip prerequisite checks** — the master plan IS the approved plan; the gap list exists from Step A1
- **Auto-commit on green** — do NOT wait for user approval at Step 8. If all checks pass (type check, unit tests, E2E, spec compliance), commit immediately with a descriptive message
- **Auto-fix failures** — if tests fail, fix and re-run (up to 3 attempts per failure). If still failing after 3 attempts, log the failure and continue to the next batch (don't block the pipeline)
- **E2E tests are mandatory** — for every batch with user-facing changes, the E2E Test Agent must run. New features get new E2E tests. Changed features get updated E2E tests.
- **Rebuild frontend before E2E** — if frontend files changed, run the build command before E2E tests (E2E tests run against built assets, not dev server HMR)

Commit message format:
```
Add Batch N: <brief description of what was implemented>

- Feature 1: brief detail
- Feature 2: brief detail
- Tests: X unit tests, Y E2E tests added/updated
```

##### B1.3: Post-Batch Verification

After committing:
- Run `npx turbo test` to verify all unit tests still pass (regression check)
- Run `npx turbo build` to verify types still clean
- If regression detected, fix immediately before proceeding to next batch

#### Step B2: Pre-Deploy (after all batches complete)

Run the full `/pre-deploy` check:
- Unit tests (full suite)
- Type check
- E2E tests (full suite — rebuild frontend first)
- Security scan
- Dependency check
- Spec compliance (against the master gap list)

This runs autonomously — no user gate.

#### Step B3: Final Report

Present a single comprehensive report:

```
## Build Complete

### Batches Executed: N/N
| Batch | Status | Commit | Tests Added |
|-------|--------|--------|-------------|
| 1: Description | PASS | abc1234 | 5 unit, 2 E2E |
| 2: Description | PASS | def5678 | 3 unit, 1 E2E |

### Test Summary
- Unit tests: X passed, Y failed
- E2E tests: X passed, Y failed
- Type check: PASS/FAIL

### Pre-Deploy Verdict: READY / NOT READY

### Issues Encountered
[Any failures, workarounds, or deferred items]

### Remaining Gaps (if any)
[Items from gap list not yet addressed]
```

---

## Failure Handling

The pipeline should be resilient, not brittle:

1. **Test failure in a batch**: Fix and retry (up to 3 times). If unfixable, commit what works, log the failure, continue to next batch.
2. **Type error after a batch**: Fix immediately — type errors compound across batches.
3. **E2E failure**: Distinguish between "test needs updating" (fix test) and "feature is broken" (fix code). Auto-fix both.
4. **Context window pressure**: If approaching context limits during a batch, commit current progress, log where you stopped in the plan file, and note in the final report that the batch was partially completed.
5. **Prior batch dependency missing**: Check if the file exists under a different path. If truly missing, implement the minimum needed to unblock, or skip the dependent feature and log it.

## Context Window Management

For large builds spanning many batches:
- The master plan in `docs/plans/` persists across context windows
- Each batch commit is atomic — if context resets, resume from the next uncommitted batch
- The gap list tracks what's DONE — re-read it to determine where to resume
- Prefer many small batches over few large ones (reduces context pressure per batch)

## Overrides

The `/build` skill overrides these defaults from other skills:
- `/implement` Step 8: "Wait for user approval" → **Auto-commit on green**
- `/plan` Step 4: "Wait for user approval" → **Only waits in Phase A, not during batch execution**
- `/phase-0` Step 5: "Ask user to approve" → **Only runs once in Step A1, not per-batch**
