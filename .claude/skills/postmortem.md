# /postmortem — Bug Postmortem & Workflow Improvement

Trigger: A bug is found (by user report, E2E failure, or manual testing). This skill analyses the root cause and strengthens the workflow to prevent the same class of bug from recurring.

## Purpose

Turn every bug into a permanent improvement. When a bug is found, don't just fix it — diagnose which workflow checkpoint should have caught it, then update that checkpoint so similar bugs can't ship again.

## Instructions

### Step 1: Document the Bug

Produce a structured bug report:

```
## Bug Report

**Summary**: [one-line description]
**Severity**: CRITICAL / HIGH / MEDIUM / LOW
**Found by**: [user report / E2E failure / manual testing / code review]
**Symptoms**: [what the user experienced]
**Root cause**: [the actual code defect]
**Files affected**: [list of files with the bug]
**Fix applied**: [what was changed to fix it]
```

### Step 2: Classify the Bug Pattern

Categorise the root cause into one or more of these patterns:

| Pattern | Description | Example |
|---------|-------------|---------|
| **Orphaned component** | Code exists but isn't wired into the app (missing route, unused import, dead component) | Page component existed but wasn't registered in the router |
| **Broken contract** | Frontend expects shape A, backend sends shape B (API response mismatch, transform/unwrap assumptions) | Store expected array, API returned paginated wrapper object |
| **Missing integration** | Individual pieces work in isolation but fail when connected (form reads stale data, link targets wrong URL) | Form read from entity prop instead of parent-provided values |
| **ID/slug confusion** | Code uses ID where slug is needed or vice versa (URL params, API lookups, link construction) | Endpoint looked up by ID but URL passes slug |
| **Missing system field** | UI doesn't expose a field the API requires, or API doesn't validate a field the UI sends | Create form had no name input but API requires name |
| **Stale selector** | UI text or structure changed but E2E test selectors weren't updated | Test looked for old text but content was renamed |
| **State isolation** | Tests or features depend on shared mutable state without proper reset | Destructive operation broke shared state for subsequent tests |

If the bug doesn't fit these patterns, create a new pattern category.

### Step 3: Trace the Escape Path

For each bug, identify which existing workflow checkpoints SHOULD have caught it but didn't:

1. **Phase 0 (Gap Analysis)** — Was the feature in the gap list? Was it marked DONE when it shouldn't have been?
2. **Plan Review** — Did the Architecture or Testability agent flag the integration point?
3. **Implementation** — Did the Code Agent verify the full data flow? Did the Test Agent write an integration test for this path?
4. **Spec Compliance** — Did the reachability check verify this route/feature works end-to-end?
5. **E2E Tests** — Was there an E2E test that should have caught this? Did the test exist but use the wrong assertions?
6. **Pre-Deploy** — Did any gate check cover this scenario?

Produce a table:

```
### Escape Path Analysis

| Checkpoint | Should Have Caught? | Why It Didn't |
|------------|-------------------|---------------|
| Phase 0 | Yes/No | [explanation] |
| Plan Review | Yes/No | [explanation] |
| Implementation | Yes/No | [explanation] |
| Spec Compliance | Yes/No | [explanation] |
| E2E Tests | Yes/No | [explanation] |
| Pre-Deploy | Yes/No | [explanation] |
```

### Step 4: Design Prevention Rules

For each bug pattern identified, propose a concrete, automatable check that would catch it. Rules must be:

- **Specific** — not "be more careful", but "grep router for every component in pages/ and flag any that aren't registered"
- **Automatable** — can be done by an agent without human judgment
- **Non-redundant** — doesn't duplicate an existing check

Format:

```
### Prevention Rules

1. **Rule name**: [short name]
   - **Pattern prevented**: [which bug pattern from Step 2]
   - **Check**: [exact steps to verify]
   - **Add to skill**: [which skill should include this check]
   - **Severity if violated**: BLOCKING / WARNING
```

### Step 5: Update the Workflow

Apply the prevention rules by editing the relevant skill files. For each rule:

1. Read the target skill file
2. Add the new check at the appropriate step
3. Write the updated skill

Common targets:
- `/spec-compliance` — add new verification checks
- `/implement` — add new integration checks
- `/review` — add new review criteria for agents
- `/plan` — add new concerns for review agents
- `/e2e` — add new test patterns or maintenance rules
- `/pre-deploy` — add new gate checks

### Step 6: Add to Bug Pattern Registry

Append the bug pattern to `docs/bug-patterns.md` (create if it doesn't exist). This file serves as institutional memory — review agents should consult it when reviewing code.

Format per entry:

```markdown
### [Pattern Name] — [Date]

**Bug**: [one-line summary]
**Root cause**: [what went wrong]
**Prevention rule**: [what check was added]
**Skill updated**: [which skill was modified]
```

### Step 7: Verify the Fix

After updating skills:
1. Re-read each modified skill file to verify the changes are coherent
2. Check that the new rules don't conflict with existing rules
3. Confirm the prevention check would actually catch the original bug if it were reintroduced

### Step 8: Report

Present to the user:

```
## Postmortem Summary

### Bug
[one-line summary]

### Root Cause Pattern(s)
[list of patterns from Step 2]

### Escape Path
[which checkpoints failed and why]

### Prevention Rules Added
[list of rules with target skills]

### Skills Updated
[list of files modified]

### Confidence
[HIGH/MEDIUM/LOW that this class of bug is now preventable]
```

## When to Invoke

- After fixing any user-reported bug
- After an E2E test failure reveals a real bug (not just a stale selector)
- After discovering dead code, orphaned routes, or broken integrations
- Proactively after any large implementation to verify nothing was missed
