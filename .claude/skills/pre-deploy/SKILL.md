---
name: pre-deploy
description: "Pre-Deployment Gate Check (tests, types, lint, security, spec compliance)."
---

## Craftsmanship Standard

> I am not lazy. I am not in a rush. I do not take shortcuts. My job is to deliver a great output that works first time.

Pre-deploy is the last gate. If it passes, users will interact with this code. Hold it to the highest standard.

# /pre-deploy — Pre-Deployment Gate Check

Trigger: User wants to verify the project is ready for deployment or merge.

## Instructions

### Step 1: Run All Checks in Parallel

Spawn parallel agents for:

**Test Runner Agent:**
- Run the project's full test suite (see CLAUDE.md for command)
- Report pass/fail counts and any failures
- If tests fail, list each failure with file, test name, and error

**Type Check Agent:**
- Run the project's type checker (see CLAUDE.md for command)
- Report any type errors with file and line

**Lint Agent:**
- Run the project's lint command (see CLAUDE.md)
- Report any lint errors

**Security Scan Agent:**
- Grep for hardcoded secrets, API keys, passwords in source files
- Check all API routes have auth middleware
- Verify no loose types on user-facing input boundaries
- Check for missing input validation on mutation routes
- Verify error responses don't leak stack traces or internal details

**Dependency Check Agent:**
- Check for known vulnerabilities in dependencies
- Check for unused dependencies
- Verify lock file is in sync with package manifest

**E2E Test Agent (PRIMARY E2E GATE):**

The E2E agent owns the entire E2E lifecycle — infrastructure, test design, test writing, execution, and verification. It must analyze the application to understand what it does, then design and write E2E tests that thoroughly cover all key user journeys. Do NOT assume anything exists. Do NOT prescribe specific test files upfront — discover what the application does and test accordingly.

**Step E1: Infrastructure Setup (BLOCKING — do before writing any tests)**
1. **Start dev servers**: Read CLAUDE.md for dev commands. Start all required servers (frontend, API, any other services). If the auth flow has an out-of-band step (email, SMS, etc.), ensure the dev environment provides a way for tests to observe it (e.g., capture server logs to a file, configure a test mailbox). Wait for health checks to pass. If servers fail to start, report the error — this is NOT READY.
2. **Verify connectivity**: From the frontend's origin, hit an API endpoint through the proxy or direct connection. If this fails, the proxy/CORS config is broken — fix it.
3. **Create auth helper** (if it doesn't exist): Read the project's auth flow and write an E2E auth helper that completes the **full login flow as a real user would**. See the `/e2e` skill's "Auth in E2E Tests" section for requirements. The helper must exercise the real auth infrastructure — no token injection, no auth bypasses, no test-only endpoints.
4. **Create seed data script** (if it doesn't exist): Write a script that calls real API endpoints to create test fixtures. The script must be idempotent. Seed data must include at least the minimum data the app needs to function (user accounts, reference/config data, sample content for CRUD testing).
5. **Run seed data**: Execute the seed script against the running API.
6. **Verify Playwright**: Confirm `npx playwright test --list` works and lists available tests.
7. **Verify auth flow works**: Run a single test that completes the full login flow through the UI. This is BLOCKING — if the auth flow doesn't work, ALL journey tests will fail. If auth fails, diagnose and fix the root cause before proceeding.

**Step E2: Application Discovery & Test Strategy Design (MANDATORY — do not skip)**

Before writing any tests, the agent MUST analyze the application to understand what it does and design a test strategy tailored to this specific system. Do NOT use a generic checklist — discover the application's actual features and workflows.

1. **Discover the application's purpose and domain**: Read the project's README, CLAUDE.md, route definitions, and page components to understand what the application does. What are its primary entities? What workflows do users perform? What roles exist?

2. **Map all user-facing features**: Read the router configuration, page components, and API routes to build a complete feature map:
   - Every page a user can visit
   - Every form a user can submit (create forms, edit forms, settings forms, search forms)
   - Every CRUD lifecycle (which entities can be created, viewed, edited, deleted/deactivated?)
   - Every workflow or multi-step process (approval flows, wizards, state transitions)
   - Every role-specific feature (admin pages, superadmin tools, public pages)
   - Every navigation path (how does a user reach each feature?)

3. **Identify all data-dependent pages**: Find every page that fetches and displays data from the API. These are high-risk for integration bugs (response shape mismatches, loading loops, error handling failures) and MUST be exercised by E2E tests. A page that renders correctly with no data but breaks when data is fetched is a critical bug that only E2E tests catch.

4. **Design the E2E test strategy**: Based on the feature map, design test suites that cover:
   - **Every primary entity's full lifecycle**: create → view detail → edit → verify edit persisted → delete/deactivate → verify removal. If the application has 3 entity types, there should be 3 lifecycle tests.
   - **Every form submission**: Every create and edit form must be submitted with valid data, and the test must verify the data appears correctly after submission (on the redirect page, in a list view, or on a detail page).
   - **Every workflow**: Multi-step processes (wizards, approval flows, state transitions) must be tested end-to-end.
   - **Every role's key journeys**: If the app has admin, superadmin, and public roles, each role's primary workflows must be tested.
   - **Error and edge cases**: Form validation, unauthorized access, empty states.
   - **Data-fetching pages**: Every page that loads data from the API must be visited with real data present, verifying that the data renders correctly (not just that the page loads).
   - **Configurable/dynamic features at full depth**: If the application supports user-defined configuration (custom fields, dynamic forms, templates, rules, configurable workflows), the tests must exercise the full pipeline: configure → use → verify. For example, if users can define custom fields on entity types, tests must create an entity type WITH custom fields, create an entity that POPULATES those fields, and verify the values appear on the detail page. Testing only with empty/default configuration is not coverage.

5. **Output the test plan**: List every test to be written with:
   - Test name and description
   - Which feature/workflow it covers
   - What it will assert (data correctness, not just element visibility)
   - Which spec file it belongs in

The test strategy must be comprehensive enough that **if any feature is broken, at least one E2E test will fail**. If a feature exists but no E2E test exercises it, that is a coverage gap.

**Step E3: Write E2E Tests (MANDATORY — must cover the test strategy)**

Write E2E tests that implement the test strategy from Step E2. All tests must follow the `/e2e` skill's quality standards:
- Hit REAL servers — no mocking
- Navigate via UI clicks, not direct URLs (after initial page load)
- Complete full workflows, not just page loads
- Assert on data correctness, not just element visibility
- Verify form submissions actually persist data

Organize tests into logical spec files based on the application's feature areas — not a prescribed list of filenames. The agent decides the right structure based on what the application does.

**Step E4: Run E2E Tests & Quality Gate (BLOCKING)**
- Rebuild frontend first (`npm run build` or equivalent)
- Run `npx playwright test`
- Report pass/fail counts and any failures with artifact paths
- **A single failure means the application has a bug.** Investigate the failure, fix the underlying bug in the application code, and re-run. Do NOT skip failing tests or mark them as known issues. The purpose of E2E tests is to find bugs — a failing test is doing its job.
- Verify tests actually made real API calls (not mocked)

**E2E Quality Gate (BLOCKING — do not skip):**
After tests run, evaluate coverage against the test strategy from Step E2:
1. **Feature coverage**: Cross-reference the feature map against the test suite. Every user-facing feature must have at least one E2E test that exercises it through the UI. Features with no coverage = FAIL.
2. **CRUD completeness**: For every primary entity type, verify the test suite covers create, view detail, edit, and delete/deactivate. Missing any step for any entity = FAIL.
3. **Form coverage**: Every create and edit form must have a test that fills it, submits it, and verifies the data persisted. A form with no submission test = FAIL.
4. **Workflow coverage**: Every multi-step workflow (wizards, approval flows, state transitions) must have a test that completes the full workflow. Untested workflows = FAIL.
5. **Data-fetching page coverage**: Every page that loads data from the API must be visited with real data and verified to render correctly. An untested data page = FAIL.
6. **Error handling**: At least one test must trigger and verify an error state (form validation, unauthorized access). Zero error tests = FAIL.
7. **Journey vs smoke ratio**: Classify tests as journey (interacts + verifies data) vs smoke (just checks page loads). Journey tests must outnumber smoke tests.
8. Log: "E2E Coverage: X features covered, Y features uncovered. X journey tests, Y smoke tests."
9. If FAIL: write the missing tests, fix any bugs found, re-run, and re-evaluate.

**For incremental builds:** E2E tests should already exist from per-batch runs. Just run the full suite and report. If any test fails, investigate and fix the underlying bug.

**Unit Test Coverage Agent (MANDATORY — do not omit):**

Unit test coverage is a hard gate, not a nice-to-have. Every production file that contains logic must have a corresponding test file with behavioural tests.

1. **Enumerate all production source files**: List every `.ts` and `.tsx` file in the project's source directories (excluding test files, config files, type-only files, and barrel/index re-exports).
2. **For each production file, check for a corresponding test file**: Look for `*.test.ts`, `*.test.tsx`, `*.spec.ts`, or `*.spec.tsx` adjacent to the source file or in a parallel test directory.
3. **Classify coverage**:
   - `COVERED` — test file exists AND contains at least one test that exercises the module's behaviour (renders component, calls function, verifies output)
   - `SHALLOW` — test file exists but only checks imports, typeof, or toBeDefined — these prove nothing and count as UNCOVERED
   - `UNCOVERED` — no test file exists
4. **Compute coverage percentage**: `COVERED / (COVERED + SHALLOW + UNCOVERED) × 100`
5. **BLOCKING gate**:
   - Coverage below 70% = **NOT READY** — write missing tests before proceeding
   - Any page component (files in `pages/`) without tests = **NOT READY**
   - Any API route handler without tests = **NOT READY**
   - Any hook or store without tests = **NOT READY**
6. **For files missing tests**: Write the tests immediately. Do not defer. Each test must:
   - For components: render with realistic props, simulate user interaction, verify output
   - For hooks/stores: call the hook/function, verify return values and state changes
   - For API routes: make requests via the test framework, verify status codes AND response shapes
   - For utilities: call with various inputs (including edge cases), verify outputs
7. **Report format**:
   ```
   Unit Test Coverage: X% (N covered, M uncovered, P shallow)

   Uncovered files:
   - path/to/file.tsx — UNCOVERED (no test file)
   - path/to/other.tsx — SHALLOW (test only checks imports)

   Verdict: PASS (≥70%) / FAIL (<70%)
   ```

After writing missing tests, re-run the full test suite to verify they pass. Then re-compute coverage.

**Spec Compliance Agent (MANDATORY — do not omit):**
- Read the latest gap list from `docs/gaps/`
- For every MISSING/PARTIAL item: verify it's now DONE
- For every route in the router: verify there's a navigation link to reach it
- For every implemented feature: verify unit tests exist (see Unit Test Coverage Agent above — must be COVERED, not SHALLOW)
- Output: PASS/WARN/FAIL per item
- **E2E coverage check**: For every user-facing feature (pages, forms, workflows), verify there is at least one E2E journey test that exercises the feature through UI interaction — not just a page-load smoke test. Cross-reference the E2E test files against the feature list. Features with no E2E journey coverage = WARN.
- For every form, verify an E2E test submits data through the form and verifies the result persists
- A single FAIL = NOT READY verdict
- **E2E coverage summary**: List each major feature and its corresponding E2E journey test (or "MISSING" if none). This makes gaps visible in the report.

**E2E Comprehensive Coverage Agent (MANDATORY — runs after E2E Quality Gate):**

This agent verifies that the E2E suite is comprehensive enough that **any broken feature will cause at least one test to fail**. It does this by discovering the application's features and cross-referencing them against the test suite.

1. **Discover all features**: Read the application's routes, pages, forms, API endpoints, and workflows to build a complete feature map. Do not use a hardcoded checklist — discover what THIS application does.

2. **Cross-reference features against tests**: For every discovered feature, identify which E2E test exercises it. A feature is "covered" only if a test navigates to it, interacts with it, and verifies the outcome. A test that just loads the page is NOT coverage.

3. **Verify CRUD completeness per entity type**: For each primary entity type the application manages, verify the test suite covers the full lifecycle: create → view detail page (with data rendered) → edit → verify edit persisted → delete/deactivate → verify removal. Missing any step = FAIL.

4. **Verify every data-fetching page is exercised**: Identify every page that loads data from an API. Verify at least one E2E test visits that page with real data present and asserts on the rendered data (not just page structure). Data-fetching pages that are never visited in tests are high-risk for integration bugs (response shape mismatches, infinite render loops, error cascades).

5. **Verify workflow completeness**: Identify every multi-step workflow (wizards, approval flows, state transitions, import/export). Verify each has an end-to-end test. Untested workflows = FAIL.

6. **Verify error handling coverage**: At least one test must trigger a validation error and verify the message. At least one test must verify unauthorized access is blocked. Zero error tests = FAIL.

7. **Verify configurable/dynamic features are tested at depth**: Identify any feature that supports user-defined configuration (custom fields, dynamic forms, configurable schemas, templates, rules, workflows). Verify the E2E tests exercise the FULL pipeline: configure the feature through the UI → use the feature with that configuration → verify the configured behaviour works downstream. A test that uses only empty or default configuration is NOT coverage of the configuration system. Missing depth = FAIL.

8. **Report format**:
   ```
   E2E Coverage Analysis:
   - Features discovered: N
   - Features with E2E coverage: X/N
   - Uncovered features: [list each with why it matters]
   - CRUD completeness per entity: [entity: create ✓, view ✓, edit ✗, delete ✗]
   - Data-fetching pages tested: X/Y
   - Workflows tested: X/Y
   - Error handling tests: N
   - Verdict: PASS / FAIL
   ```

If FAIL: write the missing tests, fix any bugs the new tests reveal, re-run, and re-evaluate. Do NOT declare READY with uncovered features.

### Step 2: Regression Check
- Compare current test count vs last deployment (if tracked)
- Flag any removed tests
- Flag any skipped tests

### Step 3: Report

Present a deployment readiness summary:

```
## Deployment Readiness

### Unit Tests: PASS/FAIL (X passed, Y failed, Z skipped)
### E2E Tests: PASS/FAIL (X passed, Y failed)
### Types: PASS/FAIL (X errors)
### Lint: PASS/FAIL (X errors)
### Security: PASS/FAIL (X findings)
### Dependencies: PASS/FAIL (X vulnerabilities)
### Spec Compliance: PASS/FAIL

### Verdict: READY / NOT READY

### Details
[Any failures or concerns listed here]
```

If NOT READY, list what must be fixed before deploying.
