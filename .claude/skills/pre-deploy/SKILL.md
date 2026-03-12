---
name: pre-deploy
description: "Pre-Deployment Gate Check (tests, types, lint, security, spec compliance)."
---

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

**E2E Test Agent:**
- Verify dev servers are running (see CLAUDE.md for URLs/ports)
- Run the project's E2E test command
- Report pass/fail counts and any failures with artifact paths
- A single failure = NOT READY verdict
- See `/e2e` skill for full details

**Spec Compliance Agent (MANDATORY — do not omit):**
- Read the latest gap list from `docs/gaps/`
- For every MISSING/PARTIAL item: verify it's now DONE
- For every route in the router: verify there's a navigation link to reach it
- For every implemented feature: verify tests exist
- Output: PASS/WARN/FAIL per item
- A single FAIL = NOT READY verdict

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
