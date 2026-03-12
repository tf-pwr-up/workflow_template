---
name: e2e
description: "Run End-to-End Integration Tests (contract + browser)."
---

# /e2e — End-to-End Integration Tests

Trigger: After implementation to catch integration bugs that unit tests miss, or as a standalone check.

Referenced by `/implement` as a post-implementation step and `/pre-deploy` as a gate check.

## Prerequisites (BLOCKING — do not skip)

### Dev Servers Must Be Running

Check that the application's dev servers are alive before running any tests. Use the health check endpoints or URLs defined in CLAUDE.md.

If servers are DOWN:
- Start them using the project's dev command (see CLAUDE.md)
- Wait up to 15 seconds, polling every 2 seconds, until they respond
- If servers fail to start after 15 seconds, STOP and report the startup error

## Test Infrastructure

Read CLAUDE.md for the project's E2E test framework and conventions. Common infrastructure patterns:
- **Global setup** — restores seed data before all tests
- **Seed data** — a backup fixture providing known DB state
- **Helpers** — auth login, API requests, token extraction
- **Serial execution** — tests run sequentially if they share DB state
- **Ordered files** — test files run in a defined order (e.g. numeric prefixes)

## Instructions

### Step 1: Run Contract Tests

If the project has API contract tests (tests that hit the real API and verify response shapes match frontend expectations):

- Run the contract test suite (see CLAUDE.md for command)
- These verify response status codes, JSON shapes, required fields, and error formats
- Capture: test names, pass/fail status, and duration per test

If contract tests fail, record the failures but continue to Step 2 — collect all results before reporting.

If no contract test suite exists, skip to Step 2.

### Step 2: Run E2E Tests

Execute the project's browser-based E2E tests (see CLAUDE.md for command). Typical:

```
npx playwright test --reporter=list
```

- These test critical user flows in a real browser
- For failures, the framework may generate screenshots/artifacts
- Capture: test names, pass/fail status, duration, and artifact paths for failures

If the E2E framework is not installed, install it first.

### Step 3: Report Results

Present a structured summary:

```
## E2E Test Results

### Contract Tests: PASS/FAIL (X passed, Y failed)
| Test Name            | Result | Duration |
|----------------------|--------|----------|
| GET /api/orgs        | PASS   | 45ms     |
| POST /api/entities   | FAIL   | 120ms    |

### Browser Tests: PASS/FAIL (X passed, Y failed)
| Test Name              | Result | Duration |
|------------------------|--------|----------|
| Login flow             | PASS   | 2.1s     |
| Create entity          | FAIL   | 3.4s     |

### Verdict: PASS / FAIL

### Failures (if any)
[For each failure:]
- **Test**: test name
- **Error**: error message and relevant stack trace
- **Screenshot**: path to failure screenshot (if available)
- **Suggested fix**: brief analysis of what likely caused the failure
```

### Step 4: Cleanup

Remove test artifacts if all tests passed. If tests failed, keep artifacts for debugging.

## E2E Test Maintenance Rules

When features are added or changed, the E2E tests MUST be updated:

1. **New feature → new test**: Every user-facing feature needs at least one E2E test covering the happy path
2. **Changed behaviour → updated test**: If a feature's behaviour changes, update existing E2E tests to match
3. **Changed UI → updated selectors**: If UI text, structure, or navigation changes, update test selectors
4. **New data types → updated seed data**: If the schema changes, update seed data fixtures to include the new types/fields
5. **New API endpoint → test coverage**: CRUD operations and workflow transitions need E2E tests
6. **Test isolation**: If a test file modifies shared state, subsequent test files should re-restore seed data

### Adding New Tests

Follow established patterns in the existing E2E test files:
- Use the project's auth helper for login
- Use the project's API helper for direct API-only tests
- Use `.first()` on locators to handle multiple matches (strict mode)
- Use generous timeouts on initial page assertions to handle load time
- Group related tests in describe blocks
- Add new test files following the project's naming convention

## Output Format

The final output must include:
1. **Contract tests**: pass/fail count and table of results (if applicable)
2. **Browser tests**: pass/fail count and table of results
3. **Overall verdict**: PASS only if all suites pass with zero failures
4. **Failure details**: error messages, screenshots, and suggested fixes
5. **Cleanup status**: confirmation that test artifacts were removed (or kept for debugging)
