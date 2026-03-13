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

**E2E Test Agent (PRIMARY E2E GATE for greenfield builds):**

For greenfield builds, this is the FIRST and ONLY time E2E tests run. The agent owns the entire E2E lifecycle — not just running tests, but setting up the infrastructure to make them possible. Do NOT assume anything exists.

**Step E1: Infrastructure Setup (BLOCKING — do before writing any tests)**
1. **Start dev servers**: Read CLAUDE.md for dev commands. Start both frontend and API servers. Wait for health checks to pass (e.g., curl `localhost:8787/health` for API, verify frontend responds on its port). If servers fail to start, report the error — this is NOT READY.
2. **Verify connectivity**: From the frontend's origin, hit an API endpoint through the proxy. If this fails, the proxy config is broken — fix it.
3. **Create seed data script** (if it doesn't exist): Write a script that calls real API endpoints to create test fixtures (entity types, entities, organisations, users). The script must be idempotent. Store at `e2e/seed.ts` or `e2e/global-setup.ts`. Seed data must include at least:
   - One entity type with fields
   - One organisation
   - One published entity
   - A test user (or auth bypass for testing)
4. **Run seed data**: Execute the seed script against the running API.
5. **Verify Playwright**: Confirm `npx playwright test --list` works and lists available tests.

**Step E2: Write E2E Tests (MANDATORY — must meet minimum coverage)**

Assess existing E2E tests against the `/e2e` skill's Minimum Coverage Requirements. Classify each existing test as a **journey test** or **smoke test** using the verification method in the `/e2e` skill. If the suite is insufficient (fewer than 5 journey tests, or journey tests < smoke tests), write the missing tests.

**Required test files (create if missing, enhance if smoke-only):**

1. **`e2e/golden-path.spec.ts`** — Golden path CRUD journey:
   - Seed test data via real API in `beforeAll`
   - Navigate to app → authenticate → create an entity through the UI form → verify it appears in the list → click into detail view → verify field values → edit via UI form → verify changes persisted → delete → verify removal
   - This is the single most important E2E test. It proves the full stack works.

2. **`e2e/auth-journeys.spec.ts`** — Auth workflow tests:
   - Test login flow (navigate to login, submit credentials/magic link, verify redirect to authenticated page)
   - Test access control (authenticated user can access admin pages; unauthenticated user is redirected or shown access denied)
   - Test logout (click logout, verify redirect, verify protected pages no longer accessible)

3. **`e2e/navigation-journeys.spec.ts`** — Navigation through UI clicks:
   - Starting from the home page, navigate to at least 3 different sections via clicks (not page.goto)
   - Verify breadcrumbs or back navigation works
   - Verify sidebar/header navigation links lead to correct pages
   - Each navigation step must verify page content, not just URL

4. **`e2e/form-submission.spec.ts`** — Form workflows:
   - For each major create/edit form in the app: fill all fields, submit, verify data persists
   - Test validation — submit with missing required fields, verify error messages
   - Test edit flow — load existing entity, modify fields, save, verify changes

**All tests must hit REAL servers — no mocking.** See `/e2e` skill.

**Minimum coverage gate**: After writing tests, count journey tests vs smoke tests. If the suite doesn't meet the `/e2e` skill's minimum requirements, keep writing until it does. This is BLOCKING.

**Step E3: Run E2E Tests & Quality Gate (BLOCKING)**
- Rebuild frontend first (`npm run build` or equivalent)
- Run `npx playwright test`
- Report pass/fail counts and any failures with artifact paths
- A single failure = NOT READY verdict
- Verify tests actually made real API calls (not mocked)

**E2E Quality Gate (BLOCKING — do not skip):**
After tests run, classify every test as journey or smoke using the `/e2e` skill's verification method:
1. Count tests that interact with UI (fill forms, click buttons, submit data) AND verify outcomes → **journey tests**
2. Count tests that only check page loads, element visibility, or URL patterns → **smoke tests**
3. **FAIL conditions** (any one = NOT READY):
   - Fewer than 5 journey tests total
   - Journey test count < smoke test count (the suite is mostly smoke)
   - No golden path test (create → view → edit → verify cycle)
   - No form submission test that verifies data persists
   - No auth journey test that completes a login flow
4. Log the classification: "E2E Quality: X journey tests, Y smoke tests. Ratio: X:Y."
5. If FAIL: write the missing journey tests, re-run, and re-evaluate. Do NOT declare READY with a smoke-only suite.

**For incremental builds:** E2E tests should already exist from per-batch runs. Just run the full suite and report.

**Spec Compliance Agent (MANDATORY — do not omit):**
- Read the latest gap list from `docs/gaps/`
- For every MISSING/PARTIAL item: verify it's now DONE
- For every route in the router: verify there's a navigation link to reach it
- For every implemented feature: verify unit tests exist
- Output: PASS/WARN/FAIL per item
- **E2E coverage check**: For every user-facing feature (pages, forms, workflows), verify there is at least one E2E journey test that exercises the feature through UI interaction — not just a page-load smoke test. Cross-reference the E2E test files against the feature list. Features with no E2E journey coverage = WARN.
- For every form, verify an E2E test submits data through the form and verifies the result persists
- A single FAIL = NOT READY verdict
- **E2E coverage summary**: List each major feature and its corresponding E2E journey test (or "MISSING" if none). This makes gaps visible in the report.

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
