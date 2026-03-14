---
name: build
description: "Autonomous end-to-end pipeline: spec, plan, implement all batches, test, pre-deploy."
---

# /build — Autonomous Build Pipeline

Trigger: User wants to build a set of features from spec through to deployment-ready code with minimal interruption.

## Design Principle

**Interactive during specification. Autonomous during execution.**

The user participates in Phase A (scope and plan approval) — asking questions, adjusting priorities, making architectural decisions. Once they approve, Phase B runs fully autonomously: implementing batches, writing tests, running E2E, fixing failures, committing, and running pre-deploy checks. No interruptions until the final report.

## Craftsmanship Standard

> I am not lazy. I am not in a rush. I do not take shortcuts. My job is to deliver a great output that works first time.

This standard applies to the ENTIRE pipeline. Every agent spawned by /build — code agents, test agents, review agents, E2E agents — must deliver work that meets this bar. Speed without quality is waste. A feature that "mostly works" is a bug report waiting to happen.

**What this means for /build specifically:**
- E2E tests must verify user journeys, not just page loads
- Unit tests must verify behaviour, not just imports
- UI must be visible and usable by real humans
- Every feature must be reachable through navigation
- Forms must submit, APIs must respond, data must persist

## Build Modes

Before beginning, determine the build mode. This affects where E2E tests run:

- **Greenfield**: Building a new application from scratch across multiple batches. Frontend and backend are built in different batches, so per-batch E2E is structurally impossible (you can't E2E test a frontend against an API that doesn't exist yet). E2E tests run once at pre-deploy, after the full stack is assembled.
- **Incremental**: Adding features to an existing, deployed application. The baseline app already works, so each batch can be E2E tested against the running stack.

**How to determine:**
- If the project has no functional routes, no working API, or the gap list shows >50% MISSING → **Greenfield**
- If the project is deployed and the build adds/modifies specific features → **Incremental**
- **If unclear, ASK the user** during Phase A: "Is this a greenfield build or incremental? This determines whether E2E tests run per-batch or at pre-deploy."

The build mode is logged in `docs/plans/YYYY-MM-DD-build.md` and referenced by `/implement` and `/pre-deploy`.

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

8. **E2E test infrastructure (install framework — verification happens later)**:
   - Check if `@playwright/test` is installed: `npx playwright --version` or check `package.json`
   - If NOT installed:
     1. Install Playwright: `npm install -D @playwright/test` (in the root or the web app package, per project convention)
     2. Install browsers: `npx playwright install --with-deps chromium`
     3. Create `playwright.config.ts` at the project root (or web app root) with sensible defaults (baseURL from CLAUDE.md or `http://localhost:5173`, `testDir: './e2e'`, reporter: list, retries: 1)
     4. Create the `e2e/` directory if it doesn't exist
   - If already installed: verify `playwright.config.ts` exists and `e2e/` directory exists. Create them if missing.
   - **For greenfield builds**: Do NOT attempt to run E2E smoke tests here — the app doesn't exist yet. Playwright installation and config are sufficient. E2E tests will be written and run at pre-deploy after all batches complete.
   - **For incremental builds**: Run a smoke test (`npx playwright test`) to verify the existing app works with the E2E framework. This is BLOCKING — the pipeline MUST NOT proceed until E2E infrastructure is verified working.

9. **Local dev connectivity (verify architecture, defer full verification for greenfield)**:
   E2E tests must eventually hit REAL servers — not mocked APIs. This step ensures the infrastructure is understood and configured.
   - **Identify architecture**: Read project config to determine if frontend and API are served from the same origin or separate servers.
   - **If separate servers** (e.g. Vite frontend + Wrangler/Express API):
     1. Verify a dev proxy is configured so the frontend can reach the API. Check `vite.config.ts` for `server.proxy`, or check for `VITE_API_URL` / equivalent env var.
     2. If NO proxy exists: **configure one**. For Vite, add `server.proxy` entries in `vite.config.ts` that forward API paths (e.g. `/auth`, `/config`, `/entities`, `/health`) to the API server URL.
   - **If same origin**: note the single dev server command.
   - **For greenfield builds**: Server startup verification is deferred to pre-deploy (servers may not work until backend batches are complete). Document the expected dev commands in CLAUDE.md so pre-deploy knows how to start them.
   - **For incremental builds**: Verify both servers can start and the frontend can reach the API. This is BLOCKING.
   - **Seed data**: For greenfield, note that a seed script must be created during or after the batch that completes the API. For incremental, verify seed data mechanism exists now.

This step is idempotent — running it on an already-bootstrapped repo does nothing.

---

### Phase A: Spec & Plan (Interactive — user participates)

#### Step A0: Determine Build Mode

Before gap analysis, determine and confirm the build mode with the user:

1. **Auto-detect**: Check the gap list (if it exists) or the codebase state:
   - No functional routes, no working API, or >50% MISSING items → suggest **Greenfield**
   - Deployed app with specific features being added → suggest **Incremental**
2. **Confirm with user**: "This looks like a **[greenfield/incremental]** build. Greenfield defers E2E tests to pre-deploy (the full stack doesn't exist yet). Incremental runs E2E per-batch (the baseline app already works). Confirm or override?"
3. **Log the mode**: The build mode is recorded in `docs/plans/YYYY-MM-DD-build.md` and passed to `/implement` and `/pre-deploy`.

#### Step A1: Comprehensive Gap Analysis

**INVOKE `/phase-0` using the Skill tool.** Do NOT manually write a gap list — the `/phase-0` skill launches Inventory and Gap sub-agents that read actual code/specs. You MUST use the Skill tool to trigger it, not simulate its output.

- If a recent gap list exists (`docs/gaps/`), read it and ask: "The gap list from [date] shows [X DONE, Y PARTIAL, Z MISSING]. Should I refresh it or use this?"
- If no gap list exists, invoke `/phase-0` from scratch via the Skill tool
- Present the gap list to the user: counts, priorities, recommended batching

**Gate: User confirms scope.** ("Approve this scope, or adjust?")

#### Step A2: Master Plan with Batch Ordering

**INVOKE `/plan` using the Skill tool.** Do NOT manually write a plan — the `/plan` skill launches a Plan Agent and spawns parallel Review Agents (Architecture, Security, Performance, Testability, Spec Compliance, UI). You MUST use the Skill tool to trigger it, not produce the plan yourself.

Pass the scope context (batch ordering, dependency analysis) as arguments to the `/plan` invocation. The plan skill will:

1. **Dependency analysis**: Identify which features depend on others
2. **Batch grouping**: Group features into ordered batches
3. **Per-batch plan**: Specify implementation units with context files, test strategy, expected files, dependencies
4. **Run all review agents in parallel** against the FULL master plan — not per-batch

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

**INVOKE `/implement` using the Skill tool** for this batch. Do NOT write production code directly — the `/implement` skill launches parallel Code Agent + Test Agent pairs using the Agent tool. You MUST use the Skill tool to trigger `/implement`, not write code yourself.

Run the `/implement` skill for this batch with these overrides:
- **Skip prerequisite checks** — the master plan IS the approved plan; the gap list exists from Step A1
- **Auto-commit on green** — do NOT wait for user approval at Step 8. If all checks pass (type check, unit tests, spec compliance), commit immediately with a descriptive message
- **Auto-fix failures** — if tests fail, fix and re-run (up to 3 attempts per failure). If still failing after 3 attempts, log the failure and continue to the next batch (don't block the pipeline)
- **Build mode: greenfield** — E2E tests are DEFERRED to pre-deploy (Step B2). Per-batch checks are: type check + unit tests + spec compliance only. Do NOT spawn E2E Test Agent.
- **Build mode: incremental** — E2E tests are MANDATORY per-batch for every batch with user-facing changes. The E2E Test Agent must run. New features get new E2E tests. Changed features get updated E2E tests. Rebuild frontend before E2E (E2E tests run against built assets, not dev server HMR).

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
- **Full-stack smoke test** (at least once per build, and after any batch that changes frontend-API connectivity):
  1. Start both frontend and API dev servers
  2. Verify the frontend can reach the API (curl the API health endpoint through the frontend's proxy)
  3. Load the app in a headless browser and verify it renders (not a blank page, not an error)
  4. If this fails, the proxy or dev setup is broken — fix before proceeding
- If regression detected, fix immediately before proceeding to next batch

#### Step B2: Pre-Deploy (after all batches complete)

Run the full `/pre-deploy` check. Pass the build mode so it knows its E2E responsibility.

**For greenfield builds, pre-deploy is the SOLE owner of E2E testing.** This is where:
1. Dev servers are started for the first time as a complete stack
2. Seed data scripts are created (the API now exists)
3. E2E test suite is written (golden path journeys, role-based access, navigation)
4. All E2E tests are run against real servers
5. Any E2E failures are fixed before the build is declared READY

Pre-deploy checks:
- Unit tests (full suite)
- Type check
- **E2E tests (MANDATORY — this is the primary E2E gate for greenfield builds)**:
  - Start both dev servers and verify connectivity
  - Create seed data script if it doesn't exist
  - Write E2E tests that meet the `/e2e` skill's **Minimum Coverage Requirements**:
    - Golden path CRUD journey (create → view → edit → verify → delete)
    - Auth journeys (login flow, access control, logout)
    - Navigation journeys (reach pages via clicks, verify content at each step)
    - Form submission tests (fill forms, submit, verify data persists)
  - Rebuild frontend, then run full E2E suite
  - **E2E Quality Gate**: classify each test as journey vs smoke. FAIL if fewer than 5 journey tests, or if journey tests < smoke tests. See `/e2e` skill for classification method.
  - A single E2E failure = NOT READY
  - A smoke-only E2E suite = NOT READY (even if all tests pass)
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

## Checkpoint Enforcement (CRITICAL)

At each phase boundary, the `/build` pipeline MUST verify that the required skill was actually invoked — not simulated. The checkpoints are:

### Checkpoint 1: After Phase A1
- **Verify**: The Skill tool was used to invoke `/phase-0`
- **Verify**: A gap list file exists at `docs/gaps/*.md` that was produced by the Phase 0 agents (Inventory Agent + Gap Agent)
- **If violated**: STOP. Do not proceed to A2. Invoke `/phase-0` properly.

### Checkpoint 2: After Phase A2
- **Verify**: The Skill tool was used to invoke `/plan`
- **Verify**: Parallel review agents (Architecture, Security, Performance, Testability, Spec Compliance) were spawned and returned findings
- **Verify**: A consolidated plan exists that incorporates review feedback
- **If violated**: STOP. Do not proceed to Phase B. Invoke `/plan` properly.

### Checkpoint 3: Before each batch in Phase B
- **Verify**: The Skill tool will be used to invoke `/implement` for this batch
- **Verify**: `/implement` will spawn parallel Code Agent + Test Agent pairs (not write code inline)
- **If violated**: STOP the pipeline. The agent is bypassing the multi-agent workflow.

### What counts as "invoked properly"
- The Skill tool was called with the skill name (e.g., `skill: "phase-0"`)
- The skill's internal agents (Inventory Agent, Gap Agent, Plan Agent, Review Agents, Code Agents, Test Agents) were launched via the Agent tool
- The skill produced its expected artifacts (gap list, plan, code + tests)

### What does NOT count
- Manually writing the artifact file (e.g., writing `docs/gaps/*.md` by hand)
- Summarising what the agents "would have found" without spawning them
- Writing production code directly using Write/Edit tools instead of through Code Agents
- Producing a plan without running Review Agents against it

---

## Overrides

The `/build` skill overrides these defaults from other skills:
- `/implement` Step 8: "Wait for user approval" → **Auto-commit on green**
- `/plan` Step 4: "Wait for user approval" → **Only waits in Phase A, not during batch execution**
- `/phase-0` Step 5: "Ask user to approve" → **Only runs once in Step A1, not per-batch**
