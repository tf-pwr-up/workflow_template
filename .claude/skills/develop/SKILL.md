---
name: develop
description: "Development & testing — implements sprint deliverables with parallel agents, comprehensive testing, and documentation"
---

# /develop — Development & Testing

## Purpose

This skill implements the approved sprint plan by orchestrating parallel development and test agents, running comprehensive test suites, fixing failures, and updating documentation. All production code and tests are written by sub-agents — the orchestrator coordinates but does NOT write code directly.

## Invocation

```
/develop <N>
```

Where `N` is the sprint number.

## Prerequisites (BLOCKING — ALL THREE REQUIRED)

Before ANY work begins, verify ALL of the following. If ANY check fails, STOP immediately.

| # | Prerequisite | File | If Missing |
|---|-------------|------|------------|
| 1 | Approved plan | `docs/plans/sprint-<N>-plan.md` | STOP. Tell user to run `/sprint <N>` first. |
| 2 | Gap list | `docs/gaps/sprint-<N>-gaps.md` | STOP. Tell user to run `/sprint <N>` first — gap analysis is missing. |
| 3 | Test strategy in plan | Section within `docs/plans/sprint-<N>-plan.md` | STOP. Tell user the plan is incomplete — test strategy section is required. |

Additionally, verify the plan is marked as **APPROVED** (check for the `Status: APPROVED` line at the top). If not approved, STOP and tell the user to complete `/sprint <N>` approval first.

## Craftsmanship Standard

Internalize this before writing any code:

> **"I am not lazy. I am not in a rush. I do not take shortcuts. My job is to deliver a great output that works first time."**

This means:
- Every state is handled (loading, empty, error, success for UI components)
- Every edge case identified in the plan is addressed
- Every function has clear, intentional error handling
- No TODO comments left in production code (except E2E deferral per policy below)
- No placeholder implementations
- No "happy path only" code

## Execution Steps

Steps A through H are sequential. Each step MUST complete before the next begins. No step may be skipped.

---

## Step A: Parallel Development & Test Writing

### A.1 — Parse Implementation Units

Read `docs/plans/sprint-<N>-plan.md` and extract:
- All implementation units
- Their dependency ordering
- Context files for each unit
- Files to create and modify for each unit

Group units into batches based on the dependency order:
- **Batch 1:** All units with no dependencies (can run in parallel)
- **Batch 2:** All units whose dependencies are satisfied by Batch 1 (can run in parallel within batch)
- **Batch 3:** And so on...

### A.2 — Spawn Agent Pairs

For EACH implementation unit, spawn exactly TWO agents via the Agent tool:

#### Code Agent

The Code Agent for each unit MUST follow these instructions in order:

1. **Read context files FIRST** — Every file listed in the unit's "Context files" section must be read before writing any code. This is mandatory, not optional.
2. **Read `CLAUDE.md`** — Follow all architectural patterns, naming conventions, and coding standards defined there.
3. **Read the plan's shared interfaces section** — Use the exact types and contracts specified.
4. **Implement the unit** following the plan precisely:
   - Create the files listed in "Files to create"
   - Modify the files listed in "Files to modify"
   - Handle ALL states: loading, empty, error, success (for UI components)
   - Follow error handling patterns from CLAUDE.md
   - Use existing shared utilities — do not reinvent
   - Match the code style of surrounding files
5. **Do NOT write tests.** Test writing is the Test Agent's responsibility.

#### Test Agent (MANDATORY)

The Test Agent for each unit MUST follow these instructions:

1. **Read the REQUIREMENTS** — Tests are written from the spec, not from the code.
2. **Read the PLAN's test strategy** for this unit's requirements.
3. **Read `CLAUDE.md`** for testing conventions and patterns.
4. **Do NOT read the Code Agent's output.** Tests must be independent of implementation details.
5. **Write tests covering:**
   - **Happy path** — The expected behaviour works correctly
   - **Edge cases** — Boundary values, empty inputs, maximum lengths, special characters
   - **Error paths** — Invalid inputs, network failures, unauthorized access, missing data
   - **Boundary values** — Off-by-one, zero, negative, overflow conditions
6. **Tests must verify BEHAVIOUR, not existence:**
   - CORRECT: Render component, interact with it, verify output/state change
   - CORRECT: Call function with input, assert output matches expected
   - WRONG: Assert component exists in DOM (no behaviour verified)
   - WRONG: Assert function is defined (no behaviour verified)
7. **Write integration tests** for cross-component interactions within this unit's scope.

### A.3 — Execution Order

- **Within a batch:** Launch all Code Agent + Test Agent pairs in parallel
- **Between batches:** Wait for all agents in Batch N to complete before starting Batch N+1
- **Within a unit:** The Code Agent and Test Agent for the same unit run in parallel (Test Agent writes from spec, not from code)

### A.4 — Agent Count Enforcement

**CRITICAL ENFORCEMENT RULE:**

After all agents complete for a batch, COUNT:
- Number of Code Agents launched: `C`
- Number of Test Agents launched: `T`

If `C != T`, this is a **workflow violation**. Every Code Agent MUST have a paired Test Agent. Fix immediately by launching the missing Test Agent(s).

Additionally, verify: every production file created or modified has a corresponding test file. A production file without a test file is INCOMPLETE. Flag and remediate.

### CRITICAL: Sub-Agent Code Writing Rule

**ALL code MUST be written by sub-agents via the Agent tool.** The orchestrator (you) MUST NOT write production code or test code directly using Write/Edit tools. This is a workflow violation.

The ONLY exception is trivial configuration changes (e.g., adding an entry to a config array) that are part of wiring up agent-produced code. Even then, prefer delegating to an agent.

---

## Step B: E2E Test Review

After all unit implementation and test writing is complete:

1. **Read existing E2E tests** — Find all E2E test files in the project (typically `e2e/`, `tests/e2e/`, `cypress/`, or `playwright/` directories).
2. **Read new/changed functionality** — Understand what user-facing behaviour changed in this sprint.
3. **Identify E2E coverage gaps:**
   - New user journeys that have no E2E test
   - Modified workflows where existing E2E tests are now stale
   - Critical paths that lack end-to-end verification
4. **Propose an E2E test plan** listing:
   - Each new E2E test with a description of the user journey it covers
   - Each existing E2E test that needs modification and what changes are needed
   - The data seeding strategy (how test data is created and cleaned up)
5. **Present the E2E test plan to the user** and ask for confirmation before proceeding.

---

## Step C: Write E2E Tests

After user confirms the E2E test plan:

### C.1 — E2E Infrastructure Check

If E2E test infrastructure does not exist in the project:
- Install Playwright (preferred) or the framework specified in CLAUDE.md
- Create configuration file
- Set up test directory structure
- Add npm scripts for running E2E tests
- This is NOT a reason to skip E2E tests. Set up the infrastructure.

### C.2 — Spawn E2E Test Agent

Spawn an **E2E Test Agent** via the Agent tool with these instructions:

1. **NO MOCKING.** E2E tests MUST hit real servers. The following are BANNED:
   - `page.route()` (Playwright request interception)
   - MSW (Mock Service Worker)
   - `nock`
   - Any HTTP mocking library
   - Any form of request stubbing or interception

2. **Write user journey tests:**
   - Navigate via UI (click links, fill forms — not direct URL navigation for workflows)
   - Complete full workflows end-to-end
   - Verify results are persisted (reload page, verify data still there)

3. **Golden path test (REQUIRED):**
   Write at least one test that covers the full CRUD lifecycle:
   ```
   Create resource -> View resource -> Edit resource -> Verify changes -> Delete resource -> Verify deletion
   ```

4. **Data seeding:**
   - Seed test data via real API calls (not database insertion)
   - Clean up test data after each test (or use unique identifiers)
   - Do not depend on pre-existing data in the database

5. **Authentication:**
   - Use real auth flow (login via UI or API-based auth token acquisition)
   - Do not hardcode tokens or bypass auth

### C.3 — E2E Deferral Policy

If real servers genuinely do not exist yet (common in early sprints where backend isn't built):

1. Write the E2E tests anyway with the correct assertions and flow
2. Mark them with a clear TODO:
   ```typescript
   test.skip('Full item CRUD journey', async ({ page }) => {
     // TODO: Enable when API server is available (Sprint N+M)
     // Tracking: See docs/findings/sprint-<N>-findings.md F-XX
   });
   ```
3. Add a tracking entry to `docs/findings/sprint-<N>-findings.md`:
   ```
   | F-XX | <round> | MEDIUM | E2E tests deferred: <description> — servers not available | AGREE-MEDIUM: Valid deferral | DEFERRED | Enable in sprint <M> when server exists |
   ```
4. Development is NOT blocked by this deferral
5. The debt MUST be paid in a subsequent sprint — it is tracked in findings

---

## Step D: Run Unit Tests & E2E Tests

### D.1 — Run Unit and Integration Tests

Execute the project's test runner for unit and integration tests:
- Use the test command from `CLAUDE.md` or `package.json` scripts
- Run with verbose output to capture individual test results
- Capture both stdout and stderr

### D.2 — Run E2E Tests

If real dev servers are available:
- Start the dev server (or use an already running one)
- Run E2E tests against it
- Capture results including screenshots on failure (if Playwright)

If servers are not available:
- Note that E2E tests are deferred per policy
- Run only the non-skipped E2E tests (if any)

### D.3 — Collect Results

Create a summary of test results:
- Total tests: passed / failed / skipped
- List each failing test with its error message
- Identify if failures are in new tests or existing tests

---

## Step E: Fix Issues (Loop)

**Max 3 attempts per failing test.**

For each failing test:

1. **Analyse the failure** — Read the error message, stack trace, and relevant source code.
2. **Fix the CODE, not the test.** Tests are the spec. The code must conform to the tests, not the other way around. Do NOT weaken test assertions to make them pass.
3. **Spawn a Fix Agent** via the Agent tool to make the correction. The Fix Agent must:
   - Read the failing test to understand expected behaviour
   - Read the production code that is failing
   - Fix the production code to satisfy the test
   - NOT modify the test (unless the test has a genuine bug — e.g., typo in selector, wrong import path)
4. **Re-run the specific failing test** to verify the fix.
5. **Track attempts.** If a test fails 3 times:
   - STOP trying to fix it automatically
   - Flag to the user with:
     - The test name and file
     - What the test expects
     - What the code does instead
     - The 3 approaches tried and why they failed
   - Ask the user how to proceed

**IMPORTANT:** If fixing a failure requires a fundamental change in approach (not just a bug fix), flag to the user IMMEDIATELY rather than burning through all 3 attempts.

---

## Step F: Run Full Test Suite

After all Step E fixes are applied, run the COMPLETE test suite — not just the new tests:

1. **Unit tests** — ALL unit tests in the project
2. **Integration tests** — ALL integration tests
3. **E2E tests** — ALL E2E tests (including pre-existing ones)
4. **Type checking** — Run the TypeScript compiler (or equivalent) across the ENTIRE project:
   ```bash
   npx tsc --noEmit
   ```
   (or the type-check command from CLAUDE.md / package.json)
5. **Lint checking** — Run the project linter across the ENTIRE project:
   ```bash
   npx eslint .
   ```
   (or the lint command from CLAUDE.md / package.json)

Capture ALL results. The goal is to detect regressions — cases where new code broke existing functionality.

---

## Step G: Fix Regressions (Loop)

**Max 3 attempts per regression.**

If Step F reveals regressions (previously passing tests now fail, type errors in existing files, lint errors in existing files):

1. **Identify the regression** — Determine which new code caused the existing test/check to fail.
2. **Spawn a Regression Fix Agent** via the Agent tool:
   - Read the failing existing test
   - Read the new code that caused the regression
   - Fix the new code to NOT break the existing test
   - Verify the fix doesn't break the new tests either
3. **Re-run the full test suite** to verify no cascading regressions.
4. **Track attempts.** If a regression persists after 3 attempts:
   - STOP trying to fix automatically
   - Flag to the user with:
     - The regression (what broke)
     - The new code that caused it
     - The conflict between old and new behaviour
     - Suggested approaches for resolution
   - Ask the user how to proceed

**CRITICAL:** Fixing a regression MUST NOT break any new tests. If there is a genuine conflict between old and new behaviour, flag to the user for a decision.

---

## Step H: Update Documentation

After all tests pass and all checks are clean:

### H.1 — Update CLAUDE.md

If this sprint introduced:
- New architectural patterns → Add to CLAUDE.md patterns section
- New CLI commands or scripts → Add to CLAUDE.md commands section
- New conventions or coding standards → Add to CLAUDE.md conventions section
- New dependencies or tools → Add to CLAUDE.md tech stack section

### H.2 — Update Requirements Docs

If the implementation deviated from the plan (with user approval):
- Note deviations in `docs/outcomes/sprint-<N>-outcome.md`
- Update `docs/requirements/proposed-sprints.md` if requirements changed

### H.3 — Update Bug Patterns

If bugs were discovered during development:
- Add new patterns to `docs/bug-patterns.md`
- Include: what the bug was, how it manifested, how it was fixed, how to prevent it

### H.4 — Create Sprint Outcome

Create `docs/outcomes/sprint-<N>-outcome.md` with:
- What was planned vs. what was delivered
- Any deviations from the plan and why
- Deferred items (E2E tests, etc.) with tracking references
- Test coverage summary
- Issues encountered and resolutions

### H.5 — Commit All Changes

Stage and commit all changes with a descriptive commit message:
```
feat(sprint-<N>): <sprint title>

Implements: <list of key features>
Tests: <unit/integration/E2E test counts>
Plan: docs/plans/sprint-<N>-plan.md
```

---

## Enforcement Rules

These rules are NON-NEGOTIABLE. Violations constitute workflow failures.

1. **No step may be skipped.** Steps A through H are mandatory and sequential.
2. **All code written by sub-agents.** The orchestrator MUST NOT use Write/Edit tools to write production code or test code. Use the Agent tool to spawn sub-agents for ALL code writing.
3. **Every Code Agent has a paired Test Agent.** If N code agents are launched, N test agents MUST also launch. Verify the count after each batch.
4. **Every production file has a test file.** A production file without corresponding tests is INCOMPLETE.
5. **Code Agents MUST read context files before writing.** This is the first thing they do, not optional.
6. **Test Agents write from spec, NOT from code.** They read requirements and the plan, not the Code Agent's output.
7. **E2E tests hit real servers.** No mocking, stubbing, or request interception in E2E tests. The only exception is the deferral policy when servers genuinely don't exist.
8. **Tests are the spec — do NOT weaken tests.** When code fails a test, fix the code. Do not relax assertions to make tests pass.
9. **Full test suite must pass.** Development is not complete until ALL tests (not just new ones) pass, type checks are clean, and linting is clean.
10. **Missing frameworks are not an excuse.** If test frameworks, linters, or type checkers aren't installed, install them. Their absence is not a reason to skip checks.

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Plan file missing | STOP. Tell user to run `/sprint <N>`. |
| Gap file missing | STOP. Tell user to run `/sprint <N>`. |
| Plan not marked APPROVED | STOP. Tell user to complete `/sprint <N>` approval. |
| Test framework not installed | Install it. This is not a blocker. |
| Dev server not available for E2E | Apply deferral policy (Step C.3). Continue with other tests. |
| Test fails after 3 fix attempts | Flag to user with details. Wait for guidance. |
| Regression after 3 fix attempts | Flag to user with details. Wait for guidance. |
| Code Agent doesn't read context files | Workflow violation. Re-spawn the agent with explicit instructions. |
| Test Agent reads code instead of spec | Workflow violation. Re-spawn the agent with explicit instructions. |
| Agent writes code directly (not via sub-agent) | Workflow violation. Delete the code and re-do via Agent tool. |

---

## Output Artifacts

| Artifact | Path | Produced By |
|----------|------|-------------|
| Production code | Various (per plan) | Code Agents |
| Unit/integration tests | Various (per plan) | Test Agents |
| E2E tests | `e2e/` or per project convention | E2E Test Agent |
| Sprint outcome | `docs/outcomes/sprint-<N>-outcome.md` | Step H |
| Updated CLAUDE.md | `CLAUDE.md` | Step H |
| Updated bug patterns | `docs/bug-patterns.md` | Step H (if applicable) |
| Git commit | Repository | Step H |
