---
name: retrospective
description: "Sprint retrospective — examines process, proposes workflow improvements, syncs changes to template"
---

# Sprint Retrospective & Workflow Improvement

Invoked after a sprint is complete to examine the review process, identify improvement opportunities, update workflow artifacts, and sync generic improvements back to the template.

**Invocation:** `/retrospective <N>` where `<N>` is the completed sprint number.

---

## Prerequisites

Before running a retrospective, verify:
- Sprint N is marked as complete (all code merged, tests passing).
- Findings tracker exists at `docs/findings/sprint-<N>-findings.md`.
- Sprint plan exists at `docs/sprints/sprint-<N>-plan.md`.

If any prerequisite is missing, warn the user and ask whether to proceed with partial data.

---

## Process Steps

### Step 1 — Gather Sprint Data

Collect all artifacts from the sprint:

1. **Findings tracker**: Read `docs/findings/sprint-<N>-findings.md` — all rounds, all statuses.
2. **Individual council reviews**: Read all files in `docs/findings/council-responses/plan-sprint-<N>/` and `docs/findings/council-responses/code-sprint-<N>/`.
3. **Sprint plan and deviations**: Read `docs/sprints/sprint-<N>-plan.md`. Identify any deviations from the original plan (scope changes, re-ordered tasks, dropped items).
4. **Test results**: Read test output or CI results. Note pass/fail counts, flaky tests, and coverage changes.
5. **Bugs found**: Check for any bugs discovered during or after the sprint (issues, bug reports, hotfixes).
6. **Known debt**: Check for any `## Known Debt` sections from forced convergence in findings trackers.

### Step 2 — Process Analysis

Examine the review process itself for systemic issues:

1. **Drip-fed findings**: Did an expert raise a CRITICAL or HIGH finding in round 2+ that should have been caught in round 1? This indicates the expert is not being thorough in early rounds and is wasting review cycles. Track which experts exhibit this pattern.

2. **Repeated expert issues**: Is the same expert raising the same category of finding across multiple sprints? This may indicate:
   - A recurring codebase weakness that needs a structural fix (add to bug-patterns.md).
   - An expert lens that is too narrow or too aggressive (tune the lens prompt).

3. **Cross-boundary findings**: Did an expert raise a finding outside their domain (e.g., security expert raising an architecture concern)? This is healthy but should be noted. If it happens frequently, consider whether the architecture expert's lens is missing something.

4. **Arbitrator calibration**: Review the arbitrator's severity overrides:
   - How often did the arbitrator override? (Target: 10-30% of findings.)
   - Were overrides mostly up or down? Consistent downward overrides suggest experts are too aggressive.
   - Did the arbitrator flag scope creep? How often?

5. **False positive rate**: Count findings that ended up WONTFIX or were filtered by the consolidator. A high false positive rate (>25%) indicates lens prompts need tightening.

6. **Escaped bugs**: Were any bugs found AFTER the review process approved the sprint? These are the most important signal — the review process failed to catch them. Trace each escaped bug to understand:
   - Which expert should have caught it?
   - Was the relevant material provided to the council?
   - Was the bug in a category covered by the lens prompt?

### Step 3 — E2E Debt Check

Check for deferred end-to-end test obligations:

1. Search the codebase for TODO comments related to E2E tests (e.g., `TODO: E2E`, `TODO: e2e test`, `SKIP: e2e`).
2. Search the findings tracker for any testing findings with status WONTFIX that mention E2E deferral.
3. Search the sprint plan for any E2E tests listed as "deferred" or "future sprint."
4. Check `docs/findings/` for any known debt entries related to E2E coverage.

If ANY deferred E2E tests are found:
- List each one with its origin (which sprint, which finding).
- Flag as outstanding debt that must be scheduled.
- Add to the retrospective output as a dedicated `## Outstanding E2E Debt` section.

This debt does not block the retrospective but MUST be visible.

### Step 4 — Bug Pattern Analysis

For each bug found during or after the sprint:

1. **Classify**: Categorise the bug (security, logic error, integration, UI state, data handling, race condition, etc.).
2. **Trace escape path**: Determine how the bug escaped the review process. Was it:
   - Not in scope of any expert's lens?
   - In scope but missed?
   - In a code path not submitted for review?
   - An integration issue between reviewed components?
3. **Design prevention rule**: Write a specific, actionable rule that would catch this class of bug in future reviews. Rules should be concrete (e.g., "When reviewing auth endpoints, verify that rate limiting is applied to login and password reset routes") not vague ("Be more careful about auth").
4. **Update bug-patterns.md**: Append the new pattern to `docs/bug-patterns.md` with:
   ```markdown
   ## <Pattern Name>
   - **Sprint**: <N>
   - **Category**: <classification>
   - **Escape Path**: <how it was missed>
   - **Prevention Rule**: <actionable rule>
   - **Example**: <brief description of the actual bug>
   ```

### Step 5 — Propose Workflow Changes

Based on the analysis, propose changes. Present each proposal to the user with a before/after comparison:

**Lens prompt updates**: If an expert consistently misses a category, propose adding specific instructions to their lens. Show the current lens excerpt and the proposed addition.

**New council members**: If a category of issue is consistently missed by all experts, propose activating an optional member or creating a new specialist lens.

**Rule changes**: If convergence guardrails were hit, propose adjusting round limits or convergence thresholds. If false positive rates are high, propose tightening lens focus.

**Bug pattern additions**: Present each new bug pattern for confirmation before writing.

**Council configuration changes**: If an expert is consistently unhelpful (high false positive rate, findings always overridden by arbitrator), propose deactivation or lens rework.

Format proposals as:

```
### Proposal: <title>
**Reason**: <what was observed>
**Before**: <current state>
**After**: <proposed change>
**Impact**: <expected improvement>
```

Wait for user approval on each proposal before applying.

### Step 6 — Apply Changes

For each approved proposal, apply the changes:

1. **council-config.json**: Update council member settings, round limits, thresholds.
2. **docs/bug-patterns.md**: Append new bug patterns.
3. **CLAUDE.md**: Update project conventions if workflow changes affect development patterns.
4. **Archive sprint plan**: Move `docs/sprints/sprint-<N>-plan.md` to `docs/sprints/archive/sprint-<N>-plan.md` (create archive directory if it does not exist).
5. **Update findings tracker**: Mark the sprint findings as archived by adding `**Status**: ARCHIVED` to the metadata section.

### Step 7 — Workflow Sync Check (BLOCKING)

This step is BLOCKING. The retrospective cannot complete until it is resolved.

1. Check if any workflow-shared files were modified during this sprint:
   - `.claude/skills/**/*.md`
   - `.claude/workflow-rules.md`
   - `scripts/council-dispatch.py`
   - `scripts/council-check.sh`
   - `.github/workflows/workflow-gate.yml`

2. If modifications are found, present them to the user with two options:
   - **Sync to template**: Run `/sync push` to push generic improvements back to the workflow template.
   - **Mark as project-specific override**: Explicitly acknowledge that these changes are intentional project-specific deviations. Add them to a `## Project-Specific Overrides` section in `CLAUDE.md`.

3. The retrospective CANNOT be marked complete until every modified workflow file is either synced or marked as a project-specific override. This ensures workflow improvements are never silently lost.

### Step 8 — Template Sync

If generic workflow improvements were identified (lens refinements, new convergence rules, improved bug pattern templates):

1. Ask the user if they want to sync these back to the template repository.
2. If yes, invoke `/sync push` with the relevant files.
3. Report the sync result (PR created, conflicts, etc.).

---

## Output Format

The retrospective produces a summary document written to `docs/retrospectives/sprint-<N>-retro.md`:

```markdown
# Sprint <N> Retrospective

## Summary
- **Date**: <YYYY-MM-DD>
- **Sprint scope**: <brief description>
- **Verdict history**: <e.g., "Plan: APPROVED round 1, Code: CHANGES_REQUESTED round 1 -> APPROVED round 2">

## Review Process Metrics
- **Total findings**: <count>
- **False positive rate**: <percentage>
- **Arbitrator override rate**: <percentage>
- **Rounds used**: plan <N>/<max>, code <N>/<max>
- **Escaped bugs**: <count>

## Drip-Feed Analysis
<findings that appeared late>

## Arbitrator Calibration
<override patterns>

## Escaped Bugs
<bug details and escape path analysis>

## Outstanding E2E Debt
<deferred E2E tests>

## Workflow Changes Applied
<list of changes made>

## Workflow Sync Status
<synced / overrides marked / pending>

## Known Debt Carried Forward
<unresolved items from forced convergence>
```

---

## Error Handling

- If sprint data is incomplete, proceed with what is available but note gaps in the retrospective output.
- If `docs/bug-patterns.md` does not exist, create it with a header before appending.
- If the archive directory does not exist, create it.
- If `/sync push` fails, do not block the retrospective — log the failure and remind the user to sync manually.
