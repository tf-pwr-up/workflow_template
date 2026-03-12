---
name: e2e
description: "Run real End-to-End tests against live servers — no mocking."
---

# /e2e — End-to-End Tests

Trigger: After implementation to catch integration bugs that unit tests miss, or as a standalone check.

Referenced by `/implement` as a post-implementation step and `/pre-deploy` as a gate check.

## Core Principle (NON-NEGOTIABLE)

**E2E tests hit real, running servers. No mocked APIs. No intercepted network requests. No fake data layers.**

The entire point of E2E testing is to verify the full stack works together: browser → frontend → API → database/storage. If you mock the API, you are writing frontend integration tests, NOT E2E tests. The workflow already has unit tests and integration tests for isolated component testing — E2E exists specifically to catch the bugs those miss.

**What E2E tests MUST do:**
- Run against real frontend AND backend dev servers
- Make real HTTP requests from the browser to the real API
- Use real authentication flows (or API-seeded auth tokens stored in browser state)
- Read and write real data in the dev database/storage
- Verify the full request-response cycle works

**What E2E tests MUST NOT do:**
- Use `page.route()` to intercept and mock API responses
- Inject fake data that bypasses the API
- Skip the API server because "it's hard to set up"
- Use any form of network-level mocking (MSW, nock, etc.)

If the API server cannot start, that is a bug to fix — not a reason to mock.

## Prerequisites (BLOCKING — do not skip)

### 1. E2E Framework Must Be Installed (BLOCKING — bootstrap if missing)

Before anything else, verify the E2E test framework is installed and configured:

1. **Check installation**: Run `npx playwright --version`. If it fails or `@playwright/test` is not in `package.json`:
   - Install: `npm install -D @playwright/test`
   - Install browsers: `npx playwright install --with-deps chromium`
2. **Check config**: Verify `playwright.config.ts` exists (in project root or web app root). If missing, create one with:
   - `testDir: './e2e'` or `'./tests/e2e'`
   - `baseURL` from CLAUDE.md or `http://localhost:5173`
   - `reporter: 'list'`
   - `retries: 1`
   - `use: { headless: true }`
3. **Check test directory**: Verify the E2E test directory exists. If missing, create it with a smoke test.
4. **Verify**: Run `npx playwright test` to confirm the framework works.

**This check is MANDATORY and BLOCKING.** "Playwright not found" is never an acceptable reason to skip E2E tests.

### 2. Local Dev Connectivity Must Work (BLOCKING)

Before writing or running E2E tests, verify the frontend can reach the API:

1. **Identify the architecture**: Read the project's config files to understand how frontend and API connect:
   - Same-origin (API and assets served by same server)? → single dev server is sufficient
   - Separate servers (e.g. Vite + Wrangler, Next.js + Express)? → BOTH must run, with a proxy or CORS configured
2. **If separate servers**: Verify a dev proxy exists:
   - Check `vite.config.ts` for a `server.proxy` entry routing API paths to the API server
   - Check for `VITE_API_URL` or equivalent env var
   - If NO proxy and NO env var: **configure one before proceeding**. This is the #1 reason E2E tests silently fail — the frontend makes API calls to itself (same-origin) and gets HTML back instead of JSON.
3. **Start both servers**: Start frontend and API dev servers (see CLAUDE.md for commands)
4. **Verify connectivity**: From the frontend's base URL, make a request to an API endpoint (e.g. health check) and verify it returns JSON, not HTML. Use `curl` or a Playwright test.
5. **If connectivity fails**: Fix the proxy/CORS/env configuration. Do NOT proceed to writing tests. Do NOT mock the API as a workaround.

### 3. Dev Servers Must Be Running

Check that ALL of the application's dev servers are alive before running any tests. This means:
- Frontend dev server (Vite, Next.js, etc.)
- API/backend dev server (Wrangler, Express, etc.)
- Any other required services (database, queue, etc.)

Use health check endpoints or URLs defined in CLAUDE.md.

If servers are DOWN:
- Start them using the project's dev command (see CLAUDE.md)
- Wait up to 30 seconds, polling every 2 seconds, until they respond
- If servers fail to start after 30 seconds, STOP and report the startup error — do NOT mock as a workaround

### 4. Seed Data Must Exist

E2E tests need known data to test against. Before running tests:

1. Check if the project has a seed data script or fixture (see CLAUDE.md)
2. If seed data exists, run it to ensure the database/storage has known state
3. If no seed data exists, create a seed script that:
   - Creates at least one user account (with known credentials or token)
   - Creates minimal reference data the app needs to load (config, entity types, etc.)
   - Is idempotent (safe to run multiple times)
4. E2E tests should restore seed data in `beforeAll` or global setup

## Test Infrastructure

Read CLAUDE.md for the project's E2E test framework and conventions. Common infrastructure patterns:
- **Global setup** — seeds data and authenticates via the real API before all tests
- **Seed data** — a script or fixture that populates the real database/storage with known state
- **Auth helper** — authenticates via the real API (POST /auth/login, etc.) and stores the session token for use in browser context
- **Serial execution** — tests run sequentially if they share database state
- **Ordered files** — test files run in a defined order (e.g. numeric prefixes)

### Auth in E2E Tests

Authentication MUST go through the real auth flow or a legitimate shortcut:

**Acceptable approaches:**
- Call the real login API endpoint to get a real session token, then inject that token into the browser's localStorage/cookies
- Use a test-only API endpoint that issues a real session token for a known test user
- Use the real magic-link/OAuth flow if it can be automated (e.g. intercepting the email in dev mode)

**NOT acceptable:**
- Injecting fake JWT tokens that were never issued by the API
- Mocking the auth middleware
- Bypassing auth entirely

## Instructions

### Step 1: Verify Full-Stack Connectivity

Before running any tests, verify the full stack is connected:

```bash
# 1. Verify frontend is up
curl -s http://localhost:<frontend-port>/ | head -1

# 2. Verify API is up
curl -s http://localhost:<api-port>/health

# 3. Verify frontend can reach API (through proxy or direct)
# From the frontend's base URL, hit an API path:
curl -s http://localhost:<frontend-port>/health
# This MUST return JSON, not HTML. If it returns HTML, the proxy is broken.
```

If step 3 fails, fix the proxy/connectivity before proceeding.

### Step 2: Run Contract Tests

If the project has API contract tests (tests that hit the real API and verify response shapes match frontend expectations):

- Run the contract test suite (see CLAUDE.md for command)
- These verify response status codes, JSON shapes, required fields, and error formats
- Capture: test names, pass/fail status, and duration per test

If contract tests fail, record the failures but continue to Step 3 — collect all results before reporting.

If no contract test suite exists, skip to Step 3.

### Step 3: Run E2E Tests

Execute the project's browser-based E2E tests (see CLAUDE.md for command). Typical:

```
npx playwright test --reporter=list
```

- These test critical user flows in a real browser against real servers
- For failures, the framework may generate screenshots/artifacts
- Capture: test names, pass/fail status, duration, and artifact paths for failures

If the E2E framework is not installed, STOP and run the bootstrap from the Prerequisites section above. Do NOT skip this step.

**Verification check**: After tests run, confirm that at least one test made a real API call. Check the API server logs or network traces. If zero API calls were made, the tests are mocked — rewrite them.

### Step 4: Report Results

Present a structured summary:

```
## E2E Test Results

### Full-Stack Connectivity: VERIFIED / FAILED
- Frontend: http://localhost:XXXX ✓
- API: http://localhost:XXXX ✓
- Proxy/connectivity: ✓

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

### Step 5: Cleanup

Remove test artifacts if all tests passed. If tests failed, keep artifacts for debugging.

## E2E Test Maintenance Rules

When features are added or changed, the E2E tests MUST be updated:

1. **New feature → new test**: Every user-facing feature needs at least one E2E test covering the happy path against real servers
2. **Changed behaviour → updated test**: If a feature's behaviour changes, update existing E2E tests to match
3. **Changed UI → updated selectors**: If UI text, structure, or navigation changes, update test selectors
4. **New data types → updated seed data**: If the schema changes, update the seed data script to include new types/fields
5. **New API endpoint → test coverage**: CRUD operations and workflow transitions need E2E tests that hit the real API
6. **Test isolation**: If a test modifies shared state, subsequent tests should re-seed data

### Adding New Tests

Follow established patterns in the existing E2E test files:
- Use the project's auth helper to authenticate via the real API
- Make real API calls — never mock network requests
- Use `.first()` on locators to handle multiple matches (strict mode)
- Use generous timeouts on initial page assertions to handle server response time
- Group related tests in describe blocks
- Add new test files following the project's naming convention

## Output Format

The final output must include:
1. **Full-stack connectivity status**: verified or failed
2. **Contract tests**: pass/fail count and table of results (if applicable)
3. **Browser tests**: pass/fail count and table of results
4. **Overall verdict**: PASS only if all suites pass with zero failures AND full-stack connectivity was verified
5. **Failure details**: error messages, screenshots, and suggested fixes
6. **Cleanup status**: confirmation that test artifacts were removed (or kept for debugging)
