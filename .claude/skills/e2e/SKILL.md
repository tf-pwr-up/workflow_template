---
name: e2e
description: "Run real End-to-End tests against live servers — no mocking."
---

**I am not lazy. I am not in a rush. I do not take shortcuts. My job is to deliver a great output that works first time.**

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

## Test Quality Standard (NON-NEGOTIABLE)

E2E tests must be **USER JOURNEY tests**, not "page loads" tests. A test that merely confirms a page renders is worthless — it tells you nothing about whether the application actually works.

### Requirements

- **Navigate via UI clicks, not direct URLs.** After the initial page load, all navigation must happen through clicking links, buttons, and menu items — the same way a real user would. Direct `page.goto()` calls mid-test bypass the very navigation logic you should be testing.
- **Complete full workflows.** Every test must exercise a meaningful sequence: login → create → verify → edit → verify → delete → verify. Partial workflows hide bugs.
- **Assert on data correctness, not just element visibility.** Checking that a table row exists is not enough — verify the row contains the correct values. Check counts, labels, timestamps, and computed fields.
- **Verify all visual states.** The app has loading states, empty states, error states, and success states. Test them all. A missing loading spinner or a swallowed error message is a real bug.
- **Verify form submission actually works.** Filling out a form and clicking submit is only half the test. You must verify the submitted data appears correctly on the next page or in a subsequent list view.
- **A test that checks `page.locator('#app').toBeVisible()` is NOT an E2E test** — it is a smoke test at best and provides near-zero confidence.

### Examples

**BAD — "page loads" test (provides no confidence):**
```typescript
test('dashboard page loads', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page.locator('#app')).toBeVisible();
  await expect(page.locator('h1')).toContainText('Dashboard');
});
```

**BAD — checks elements exist but not data:**
```typescript
test('entities list', async ({ page }) => {
  await page.goto('/entities');
  await expect(page.locator('table')).toBeVisible();
  await expect(page.locator('tr')).toHaveCount(3); // magic number, no data verification
});
```

**GOOD — full user journey with data verification:**
```typescript
test('create, view, edit, and delete an entity', async ({ page }) => {
  // Navigate to entities via sidebar
  await page.locator('nav a', { hasText: 'Entities' }).click();
  await expect(page).toHaveURL(/\/entities/);

  // Verify empty state or existing count
  const initialCount = await page.locator('table tbody tr').count();

  // Create a new entity via the UI
  await page.locator('button', { hasText: 'New Entity' }).click();
  await page.fill('[name="name"]', 'Test Entity Alpha');
  await page.fill('[name="description"]', 'Created by E2E test');
  await page.locator('button', { hasText: 'Save' }).click();

  // Verify creation succeeded — check the data, not just the element
  await expect(page.locator('table tbody tr')).toHaveCount(initialCount + 1);
  await expect(page.locator('td', { hasText: 'Test Entity Alpha' })).toBeVisible();

  // Navigate to detail view by clicking
  await page.locator('td', { hasText: 'Test Entity Alpha' }).click();
  await expect(page.locator('h1')).toContainText('Test Entity Alpha');
  await expect(page.locator('.description')).toContainText('Created by E2E test');

  // Edit via UI
  await page.locator('button', { hasText: 'Edit' }).click();
  await page.fill('[name="name"]', 'Test Entity Beta');
  await page.locator('button', { hasText: 'Save' }).click();

  // Verify edit persisted
  await expect(page.locator('h1')).toContainText('Test Entity Beta');

  // Delete via UI
  await page.locator('button', { hasText: 'Delete' }).click();
  await page.locator('button', { hasText: 'Confirm' }).click();

  // Verify deletion
  await expect(page.locator('td', { hasText: 'Test Entity Beta' })).not.toBeVisible();
});
```

**GOOD — verifies error and loading states:**
```typescript
test('shows loading state and handles API errors gracefully', async ({ page }) => {
  await page.locator('nav a', { hasText: 'Reports' }).click();

  // Verify loading state appears
  await expect(page.locator('[data-testid="loading"]')).toBeVisible();

  // Verify data loads and loading state disappears
  await expect(page.locator('[data-testid="loading"]')).not.toBeVisible({ timeout: 10000 });
  await expect(page.locator('table tbody tr').first()).toBeVisible();
});
```

## Minimum Coverage Requirements (BLOCKING — enforced at pre-deploy and per-batch)

E2E coverage is measured against the application's actual features, not a fixed checklist. The agent must discover what the application does and verify that every key user journey is tested.

### Coverage Principle

**If a feature exists and a user can interact with it, there must be an E2E test that exercises it.** The test must do what the user does — navigate to the feature, interact with it, and verify the result. A feature with no E2E test is an untested feature, and untested features ship bugs.

### Discovery-Driven Coverage

Before evaluating coverage, the agent must build a feature map by reading the application's routes, pages, forms, and API endpoints. Then verify:

1. **Every primary entity type has a full lifecycle test**: create → view detail page → edit → verify edit persisted → delete/deactivate → verify removal. If the app manages Products, Orders, and Users, there must be lifecycle tests for Products, Orders, and Users — not just one of them.

2. **Every form that submits data has a submission test**: The test must fill the form, submit it, and verify the submitted data appears correctly afterward (on the next page, in a list, or on a detail view). This applies to create forms, edit forms, settings forms, wizard steps, and any other form that writes data.

3. **Every multi-step workflow has an end-to-end test**: Approval flows, wizards, state transitions, import/export processes — any workflow that spans multiple steps or pages must be tested from start to finish.

4. **Every page that fetches data from the API is visited with real data**: Pages that load and display data are high-risk for integration bugs (response shape mismatches, infinite loops, error handling failures). These pages MUST be visited in E2E tests with real data present, and the test must verify the data renders correctly — not just that the page loads.

5. **Every role's primary workflows are tested**: If the app has different user roles (admin, member, public), the key workflows for each role must be covered.

6. **Error states are tested**: At least one test must trigger a form validation error and verify the error message. At least one test must verify unauthorized access is blocked.

### What Counts as a Journey Test

A test qualifies as a **journey test** if it does ALL of these:
1. **Interacts with UI elements** — clicks buttons, fills forms, navigates links
2. **Submits data or triggers state changes** — not just reading/viewing
3. **Verifies the outcome** — checks that data was created/updated/deleted, not just that a page loaded
4. **Spans multiple pages or states** — tests a workflow, not a single page render

### What Does NOT Count

These are smoke tests, not journey tests. They provide near-zero confidence:
- `page.goto(url)` + `expect(element).toBeVisible()` — proves the page renders, nothing more
- Checking that a heading contains text — proves the component exists, not that it works
- Checking that a table exists without verifying its data content
- Checking element counts without verifying element content

### Quality Gate

**BLOCKING conditions** (any one = INSUFFICIENT):
- Journey test count < smoke test count (the suite is mostly smoke)
- Any primary entity type has no lifecycle test (create/view/edit/delete)
- Any create or edit form has no submission test
- Any multi-step workflow has no end-to-end test
- Any data-fetching page is never visited with real data in any test
- No test covers form validation errors
- No test covers unauthorized access

The agent must log: "E2E Coverage: X/Y features covered. X journey tests, Y smoke tests. Uncovered features: [list]."

## Golden Path Test Suite

Every project MUST have a dedicated golden path test file (e.g. `golden-path.spec.ts`) that exercises the core user workflow end-to-end in a single continuous flow.

### Requirements

- **Seed data via real API calls** in `beforeAll` or global setup — not by injecting into the database directly.
- **Complete CRUD workflows** through the UI for the app's primary entities: create, read, update, delete.
- **Navigate exclusively through UI interactions** — click links, buttons, tabs, breadcrumbs. No `page.goto()` after the initial landing page.
- **Verify data round-trips** — data entered in a form must be visible on the detail page, in list views, and survive page refreshes.
- **Cover the core business workflow**, not just individual pages. If the app's purpose is "manage labels for products", the golden path test creates a product, adds labels, edits labels, filters by label, and deletes the product.
- **Run as a single ordered test file** — tests within the file depend on each other and run sequentially, simulating a real user session.

### Structure

```typescript
// golden-path.spec.ts
import { test, expect } from '@playwright/test';

test.describe.serial('Golden Path', () => {
  test.beforeAll(async ({ request }) => {
    // Seed data via real API
    await request.post('/api/seed', { data: { reset: true } });
  });

  test('user logs in', async ({ page }) => { /* ... */ });
  test('user creates primary entity', async ({ page }) => { /* ... */ });
  test('user views and verifies entity details', async ({ page }) => { /* ... */ });
  test('user edits entity and verifies changes', async ({ page }) => { /* ... */ });
  test('user performs core business workflow', async ({ page }) => { /* ... */ });
  test('user deletes entity and verifies removal', async ({ page }) => { /* ... */ });
});
```

## Viewport Testing

Key pages MUST be tested at multiple viewport sizes to catch responsive layout bugs.

### Required Viewports

| Name    | Width  | Height |
|---------|--------|--------|
| Mobile  | 375px  | 812px  |
| Tablet  | 768px  | 1024px |
| Desktop | 1280px | 800px  |

### What to Check at Each Viewport

- **No horizontal overflow** — the page must not scroll horizontally. Check with: `await expect(page.locator('body')).toHaveCSS('overflow-x', 'visible')` and verify `scrollWidth <= clientWidth`.
- **No unreachable buttons** — all interactive elements must be within the visible area or reachable by scrolling vertically.
- **No unreadable text** — text must not be clipped, overlapping, or smaller than 12px.
- **Navigation is accessible** — hamburger menus open, sidebar collapses work, tabs are tappable.

### Implementation

```typescript
const viewports = [
  { name: 'mobile', width: 375, height: 812 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 800 },
];

for (const vp of viewports) {
  test(`dashboard renders correctly at ${vp.name} (${vp.width}x${vp.height})`, async ({ page }) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    await page.goto('/dashboard');
    await expect(page.locator('#app')).toBeVisible();

    // No horizontal overflow
    const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
    const clientWidth = await page.evaluate(() => document.body.clientWidth);
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth);

    // Key interactive elements are visible and reachable
    const navButton = page.locator('nav').first();
    await expect(navButton).toBeVisible();
    const box = await navButton.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeGreaterThan(0);
    expect(box!.height).toBeGreaterThan(0);
  });
}
```

## Visual Accessibility Checks

After each key page loads, E2E tests MUST verify that interactive elements are actually usable — not just present in the DOM.

### Required Checks

- **Interactive elements are visible and have sufficient size.** Buttons must have a bounding box of at least 24x24 pixels (the minimum comfortable tap target). Use `boundingBox()` to verify.
- **Buttons have visible text or aria-labels.** A button with no text and no `aria-label` is inaccessible. Check with `textContent()` or `getAttribute('aria-label')`.
- **Navigation links are distinguishable from surrounding text.** Links in nav elements should have distinct styling (verified via contrast or computed style checks where feasible).
- **Form inputs have visible labels.** Every `<input>`, `<select>`, and `<textarea>` must have an associated `<label>`, `aria-label`, or `placeholder` at minimum.
- **Elements are not zero-sized or off-screen.** Use `isVisible()` combined with `boundingBox()` to confirm elements are rendered within the viewport or scrollable area.

### Implementation Pattern

```typescript
async function assertAccessibleButton(page: Page, locator: Locator) {
  await expect(locator).toBeVisible();
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.width).toBeGreaterThanOrEqual(24);
  expect(box!.height).toBeGreaterThanOrEqual(24);

  const text = await locator.textContent();
  const ariaLabel = await locator.getAttribute('aria-label');
  expect(text?.trim() || ariaLabel?.trim()).toBeTruthy();
}

async function assertFormInputsLabeled(page: Page) {
  const inputs = page.locator('input:visible, select:visible, textarea:visible');
  const count = await inputs.count();
  for (let i = 0; i < count; i++) {
    const input = inputs.nth(i);
    const id = await input.getAttribute('id');
    const ariaLabel = await input.getAttribute('aria-label');
    const placeholder = await input.getAttribute('placeholder');

    if (id) {
      const label = page.locator(`label[for="${id}"]`);
      const labelExists = await label.count() > 0;
      expect(labelExists || !!ariaLabel || !!placeholder).toBeTruthy();
    } else {
      expect(ariaLabel || placeholder).toBeTruthy();
    }
  }
}
```

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
   - Creates at least one user account (with known credentials for login)
   - Creates minimal reference data the app needs to function
   - Is idempotent (safe to run multiple times)
4. E2E tests should restore seed data in `beforeAll` or global setup

## Test Infrastructure

Read CLAUDE.md for the project's E2E test framework and conventions. Common infrastructure patterns:
- **Global setup** — seeds data and authenticates via the real API before all tests
- **Seed data** — a script or fixture that populates the real database/storage with known state
- **Auth helper** — completes the full login flow through the UI, including any out-of-band steps via dev-mode mechanisms (see "Auth in E2E Tests" below)
- **Serial execution** — tests run sequentially if they share database state
- **Ordered files** — test files run in a defined order (e.g. numeric prefixes)

### Auth in E2E Tests (NON-NEGOTIABLE — simulate real user experience)

Authentication MUST go through the **exact same flow a real user follows**. The goal is to test the auth system end-to-end, not bypass it. If the auth flow is broken, E2E tests MUST fail — that's the point.

**Principle: No shortcuts. Test what the user experiences.**

E2E auth tests must:

1. **Start at the login page** — navigate to it just like a user would.
2. **Submit real credentials through the UI** — fill in the form, click submit.
3. **Complete the full auth handshake** — whatever the project's auth mechanism is (magic links, OAuth, email/password), the test must go through it end-to-end. If the auth mechanism involves an out-of-band step (e.g., clicking a link in an email, entering an OTP), the dev environment MUST provide a way for tests to observe that step (e.g., server logs, a test mailbox, a predictable OTP) — and the test must USE that mechanism rather than bypassing it.
4. **Verify the authenticated state** — after auth completes, verify the user is actually logged in (user info visible, protected pages accessible).

**The auth helper must exercise the real auth infrastructure.** Read the project's auth flow, understand how it works in dev mode, and write a helper that completes it programmatically the same way a user would — just substituting the out-of-band channel (email, SMS) with whatever dev-mode equivalent the project provides (logs, test mailbox, etc.).

**Why this matters:**
- Auth is the most common source of integration bugs: proxy misconfigurations, response shape mismatches, token handling errors, callback routing issues.
- If tests bypass auth, these bugs ship to production undetected.
- An E2E test that can't log in is surfacing a real bug — not a testing problem to work around.

**NOT acceptable — these bypass auth and hide bugs:**
- Injecting tokens directly into localStorage/cookies without going through the login flow
- Creating test-only API endpoints that issue tokens
- Mocking the auth middleware or intercepting auth requests
- Pre-creating `storageState` files with tokens obtained outside the test
- Any approach where the test would still pass if the login page or auth callback were completely broken

**Building the auth helper:**
1. Read the project's auth implementation to understand the flow
2. Identify the dev-mode mechanism for completing out-of-band steps (check server logs, test email service, etc.)
3. Write a helper that automates the full flow: login UI → credential submission → out-of-band step completion → auth callback → verified session
4. If no dev-mode mechanism exists for the out-of-band step, CREATE one (e.g., log auth tokens/links to a file in dev mode) — this is infrastructure, not a bypass
5. Document the auth helper and its prerequisites in the E2E test README or CLAUDE.md

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
7. **Changed feature → updated ASSERTIONS, not just selectors**: When a feature changes, verify the feature actually works by updating what you assert on — not just how you find elements. A test that finds the right element but checks the wrong thing is worse than no test at all.
8. **Verify the feature works, not just that the page renders**: After any feature change, the E2E test must confirm the feature's actual behaviour (data saved, state transitioned, side effects occurred) — not merely that the page loaded without crashing.

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
