---
name: spec-compliance
description: "Verify implementation matches spec (reachability, contracts, tests)."
---

# /spec-compliance — Verify Implementation Matches Spec

Trigger: After implementation, before commit. Also invocable standalone to check current state.

## Purpose

Verify that what was built actually matches the spec. Produces a structured PASS/FAIL report. A FAIL verdict blocks commits.

## Instructions

### Step 1: Load the Gap List

Find the most recent gap list:
```
ls -t docs/gaps/*.md | head -1
```

If no gap list exists, STOP and tell the user to run `/phase-0` first.

### Step 2: Verify Each Item

Launch an Agent (subagent_type: Explore) that checks every MISSING and PARTIAL item from the gap list:

For each item:
1. **Check if code exists** — read actual files, don't assume
2. **Check if behaviour matches** — for UI features, verify the component renders the right elements, handles the right interactions, shows the right states
3. **Check if it's reachable** — for routes/pages, verify there's a navigation path (link, button, menu item) that takes the user there. An unreachable route is NOT complete.
4. **Check if unit tests exist** — verify test file covers the feature
5. **Check if E2E tests exist** — for user-facing features, verify there's at least one E2E test covering the happy path. Check that E2E test assertions match current UI text and selectors.

Classify each item:
- `PASS` — implemented, matches spec, reachable, unit tested, E2E tested (if user-facing)
- `WARN` — implemented but minor gaps (e.g., missing edge case, no E2E test for a secondary flow)
- `FAIL` — not implemented, doesn't match spec, unreachable from UI, or no tests at all

### Step 3: Cross-Check Navigation & Wiring

Separately verify that the app is fully wired together:

1. **Orphaned routes**: Read the router configuration. For each route, grep the codebase for links to it. Any route with NO inbound link = `FAIL: Orphaned route`.
2. **Orphaned components**: List all page components. For each, verify it's imported and used in a route definition. An unregistered page component = `FAIL: Orphaned component`.
3. **Broken links**: For every link `href` in frontend code, verify the target matches a defined route pattern. A link that doesn't match any route = `FAIL: Broken link`.
4. **Link construction**: Verify that links include all required URL segments. Compare link patterns against route definitions to catch missing segments.

### Step 3b: Cross-Check API Contracts

Verify that frontend API calls match backend response shapes:

1. For each API call in stores and pages, identify the expected response type.
2. Read the corresponding route handler to determine the actual response shape.
3. Account for any response transformation/unwrapping the API client performs (see CLAUDE.md for project-specific details).
4. Any mismatch = `FAIL: Broken API contract`.
5. For create/edit forms: verify that every required field in the API's validation schema has a corresponding UI input — including system fields that aren't part of dynamic field definitions.

### Step 4: Report

Output a structured report:

```
## Spec Compliance Report — [Date]

### Summary
- PASS: X items
- WARN: Y items
- FAIL: Z items

### Verdict: PASS / FAIL

### Details

#### PASS Items
| # | Feature | File | Notes |
|---|---------|------|-------|

#### WARN Items
| # | Feature | File | Gap |
|---|---------|------|-----|

#### FAIL Items
| # | Feature | Expected | Actual |
|---|---------|----------|--------|

#### Orphaned Routes
| Route | Component | Linked From |
|-------|-----------|-------------|

#### E2E Coverage Gaps
| Feature | Has E2E Test? | E2E File | Notes |
|---------|---------------|----------|-------|
```

### Step 5: Gate Decision

- **If FAIL count = 0**: Report PASS, proceed to commit
- **If FAIL count > 0**: Report FAIL, list what must be fixed. Do NOT commit until FAILs are resolved.
- **If WARN count > 0**: List warnings, ask user if they want to fix or accept

## Integration

This skill is invoked:
1. Automatically by `/pre-deploy` as one of its checks
2. Manually via `/spec-compliance` to check current state
3. Referenced by `/implement` after code+test agents complete
