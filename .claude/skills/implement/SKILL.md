---
name: implement
description: "Parallel Code + Test Implementation with integration checks."
---

# /implement — Parallel Code + Test Implementation

Trigger: User approves a plan and wants implementation to begin.

## Prerequisites (BLOCKING — do not skip, do not work around)

**ALL THREE must be satisfied before writing ANY production code.** If any prerequisite is missing, you MUST stop and fulfill it first. Do not proceed "just this once" or "to save time."

1. **Phase 0 gap list must exist**: Check `ls docs/gaps/*.md`. If missing, STOP and run `/phase-0`. Do not create a gap list retroactively from code you already wrote.
2. **A plan must have been approved**: From `/plan` or explicit user instruction. The plan must reference gap list items. If no plan exists, STOP and run `/plan`. The user saying "just build it" is NOT an approved plan.
3. **The plan should include a test strategy**: Every production file needs a corresponding test plan.

If the user asks you to skip these prerequisites, respond: "The workflow requires these steps. Let me run through them quickly." Then execute the prerequisites.

## Instructions

### Step 1: Prepare Implementation Units
Break the approved plan into implementation units (typically one per file or tightly-coupled module). For each unit, identify:
- Production file(s) to create/modify
- Corresponding test file(s)
- **Context files to read** (from the plan's "Read for context" list — see `/plan` Step 1)
- Dependencies on other units (determines ordering)

### Step 2: Implement Independent Units in Parallel

**CRITICAL — All code MUST be written by sub-agents, not inline:**
You MUST use the Agent tool to spawn Code Agents and Test Agents. Do NOT write production code or test code directly using the Write/Edit tools. The entire point of this skill is multi-agent parallel implementation with specialist agents. Writing code inline bypasses the parallel review, the test-first mindset, and the cross-cutting checks that agents provide.

For units with no dependencies on each other, spawn parallel agent pairs:

**CRITICAL — Test Agents Are Not Optional:**
Every implementation unit MUST have BOTH a Code Agent AND a Test Agent launched as parallel agents. Launching a Code Agent without its corresponding Test Agent is a workflow violation. If context limits or time pressure tempt you to skip tests, you MUST still launch the Test Agent — tests are the spec and are non-negotiable. Track the count: if you launched N code agents, you must also launch N test agents.

**Code Agent** (per unit):
- **Before writing any code, read the unit's context files** (listed in the plan). This is mandatory — never guess at contracts, response shapes, or route patterns.
  - For page components: read the router file to register the route and construct correct links
  - For API calls: read the backend route handler to verify response shape and any auto-unwrap/transform behaviour
  - For forms: read the validation schema to ensure all required fields (including system fields not in dynamic definitions) have UI inputs
- Implement the production code as specified in the plan
- Follow project conventions from CLAUDE.md
- If a reference implementation is defined in CLAUDE.md, read it (READ-ONLY) when needed for implementation details
- Ensure language/framework strict mode compliance
- Do NOT write tests

**Test Agent** (per unit — MANDATORY, not optional):
- Write tests based on the PLAN and SPEC (not from the code agent's output — tests come from the specification)
- Use the project's test framework (see CLAUDE.md)
- Cover: happy path, edge cases, error conditions, boundary values
- For API endpoints: test request validation, auth checks, response shapes
- For services: test business logic, state transitions, error handling
- Follow the project's test file naming convention (see CLAUDE.md)
- **A unit with code but no tests is incomplete and MUST NOT be committed**

**E2E Test Agent** (runs once, after all units — MANDATORY for batches with user-facing changes):

**CRITICAL — E2E means REAL servers, NO mocking:**
E2E tests MUST hit real running frontend and API servers. They MUST NOT use `page.route()`, MSW, nock, or any other mechanism to mock API responses. If you mock the API, you are writing frontend integration tests, not E2E tests. The `/e2e` skill defines this requirement in detail — read it.

**BLOCKING prerequisites — all must be satisfied:**
1. **Playwright installed**: If not, install `@playwright/test`, browsers, create config and test directory.
2. **Full-stack connectivity**: Frontend and API dev servers must BOTH be running, and the frontend must be able to reach the API (via proxy, CORS, or shared origin). If the project has separate frontend/API servers and no dev proxy is configured, **configure one** (e.g. Vite `server.proxy` in `vite.config.ts`) before writing any tests.
3. **Seed data**: A mechanism to populate known test data via the real API must exist. If it doesn't, create a seed script or global setup that calls real API endpoints to create test fixtures.
4. **Auth via real API**: Tests must authenticate by calling the real auth endpoint (not by injecting fake tokens). Create or use a test-only auth helper that obtains real session tokens from the API.

**E2E test responsibilities:**
- Review what features changed and determine which E2E tests need updating
- For new user-facing features: add E2E tests covering the happy path against real servers
- For changed behaviour: update existing E2E test assertions to match
- For changed UI: update test selectors (text content, element selectors)
- For schema changes: update seed data script to include new types/fields
- Follow the `/e2e` skill for conventions — especially the no-mocking rule

**Skip conditions (narrow):** Only skip if the batch contains ZERO user-facing changes (e.g., purely backend refactoring with no API shape changes, or tooling-only changes). If in doubt, run E2E tests.

### Step 3: Dependent Units
After independent units complete, implement dependent units in dependency order, again with parallel code+test agents.

### Step 3a: UI Review (when implementation includes UI components)

If any implementation unit includes frontend page or component files, run the UI Review Agent on the new/changed UI code:

- Checks design system compliance, visual states, responsive behaviour, dark mode, consistency, reference comparison, accessibility
- See `.claude/skills/ui-review.md` for the complete checklist
- Fix any BLOCKING issues immediately; SHOULD FIX issues before integration check

### Step 3b: Smoke Wiring Check (MANDATORY — runs before full integration)

After all code agents complete but before running the full test suite, perform a fast structural verification:

1. **Route registration**: For every new/changed page component, verify it has an entry in the router. FAIL if missing.
2. **Navigation reachability**: For every new route, grep the codebase for at least one link pointing to its pattern. FAIL if no inbound link exists.
3. **API contract spot-check**: For every new/changed API call from the frontend, read the corresponding route handler and verify the frontend type annotation matches the actual response shape (accounting for any response transformation/unwrapping the API client performs). FAIL if mismatched.
4. **Form completeness**: For every new/changed create/edit form, read the API's validation schema and verify every required field has a UI input — including system fields not in dynamic field definitions. FAIL if missing.

If any FAIL: fix immediately before proceeding. This check is cheap (file reads only) and catches the most common class of wiring bugs before the expensive test suite runs.

### Step 4: Integration Check
After all units complete, run the Integration Agent:

```
1. Install dependencies (if new ones added)
2. Type check the entire project (see CLAUDE.md for command)
3. Lint check (see CLAUDE.md for command)
4. Run all unit/integration tests (see CLAUDE.md for command)
5. Run E2E tests (MANDATORY for batches with user-facing changes). If Playwright is not installed, bootstrap it first (see E2E Test Agent prerequisites). Do NOT skip this step — "framework not installed" is not a valid reason to skip. See /e2e skill; requires dev servers running.
6. **Test file count verification (BLOCKING)**:
   - Count the number of production files created/modified in this implementation
   - Count the number of test files created/modified
   - If any implementation unit has production code but NO corresponding test file, STOP and write the missing tests before proceeding
   - Log the counts explicitly: "Production files: N, Test files: M"
7. Check for cross-file issues:
   - Missing imports
   - Type mismatches at boundaries
   - Unused exports
8. Verify API contract alignment (MANDATORY — catches a known bug pattern):
   - For every frontend API call, read the backend route handler
   - Verify the expected response type matches what the API client returns after any transforms
   - For create/edit forms, verify every required API field has a UI input (including system fields)
   - For page components, verify each is registered in the router
   - For every link in new/changed code, verify it matches a route pattern in the router
```

If E2E tests fail due to changed UI or behaviour, fix the E2E tests to match the new implementation. If E2E tests fail due to bugs in the implementation, fix the implementation.

### Step 5: Fix Failures
- If **tests fail**: fix the production code to match the test expectations (tests are the spec). Only fix the test if the test itself has a verifiable bug.
- If **type errors**: fix type issues in the relevant files.
- If **lint errors**: fix lint issues.
- Re-run until all checks pass.

### Step 6: Spec Compliance Check (MANDATORY — do not skip)

After all checks pass, run a spec compliance verification:

1. Read the gap list from `docs/gaps/`
2. For each MISSING/PARTIAL item that was in scope for this implementation:
   - Verify the code exists and matches the spec
   - Verify it's reachable from the UI (if it's a route/page, there must be a link to it)
   - **Verify tests exist** — for each production file, confirm a corresponding test file exists and contains at least one test case. A feature with code but no tests is INCOMPLETE, not DONE.
3. If any item is still MISSING or PARTIAL: flag it and list what remains
4. **Test coverage gate**: List every production file and its corresponding test file. If any production file lacks tests, mark the item as PARTIAL with gap detail "missing tests".

This check catches the specific failure mode where routes exist but are unreachable (orphaned routes), or where code exists but doesn't match the expected behaviour.

### Step 7: Update CLAUDE.md (if new project knowledge was discovered)

During implementation, new project-specific knowledge often emerges. After all checks pass, update CLAUDE.md's Project Configuration if any of the following were discovered:

- **Commands** — if the integration check used commands not yet documented (dev server start, test runner, type checker, linter)
- **Test File Conventions** — if test agents established naming patterns, environment directives, or test infrastructure helpers
- **Established Patterns** — if code agents followed patterns that should be replicated (route factory signatures, service layer conventions, DI patterns, error handling approaches)
- **Coding Conventions** — if implementation revealed conventions (import style, strict mode, file organization)
- **Design System** — if UI components used shortcuts, tokens, or component patterns not yet documented

Use the Edit tool to append to existing sections. Check what's already there to avoid duplicates. This step ensures the next implementation cycle has better context.

### Step 8: Commit & Report

**If invoked by `/build` (autonomous mode):**
- Auto-commit immediately if all checks pass (type check, tests, E2E, spec compliance)
- Use descriptive commit message summarizing what was implemented
- Log results for the final `/build` report
- Do NOT wait for user approval — proceed to next batch

**If invoked standalone:**
- Present results to user: summary, test counts, spec compliance, issues resolved, remaining gaps, CLAUDE.md updates
- Wait for user approval before committing
