---
name: review
description: "Standalone code review — council review of uncommitted changes or specific files"
---

# Standalone Code Review

A lightweight skill for running the council review process against code outside of the normal sprint workflow. Use this for ad-hoc reviews of uncommitted changes, specific files, or work-in-progress code.

**Invocation:**
- `/review` — Review all uncommitted changes.
- `/review <file1> <file2> ...` — Review specific files.
- `/review "<description>"` — Review with a description to focus the council's attention.

---

## Process Steps

### Step 1 — Identify Scope

Determine what is being reviewed based on the invocation:

1. **No arguments** — Scope is all uncommitted changes. Run `git diff` (unstaged) and `git diff --cached` (staged) to collect the full set of changes.
2. **File arguments** — Scope is the specified files. Read each file in full. If a file is also in the git diff, include the diff context as well.
3. **Description argument** (quoted string) — Scope is uncommitted changes, but the description is passed to the council to focus their review on the described concern.

If there are no uncommitted changes and no files specified, report that there is nothing to review and exit.

### Step 2 — Gather Materials

Assemble the review package:

1. **Code changes**: The diff output or file contents from Step 1.
2. **Project context**: Read `CLAUDE.md` for project conventions and architecture patterns.
3. **Domain context**: Read files in `docs/context/` for domain-specific knowledge.
4. **Bug patterns**: Read `docs/bug-patterns.md` for known pitfalls to watch for.
5. **Related tests**: For each changed file, look for corresponding test files (e.g., `foo.ts` -> `foo.test.ts`, `foo.spec.ts`, `__tests__/foo.ts`). Include test files in the materials if they exist.

### Step 3 — Dispatch to Council

Invoke the council review process with type `code` and sprint `0` (indicating standalone review):

```bash
./scripts/council-dispatch.py code 0 "<description>"
```

Where `<description>` is:
- The user-provided description if one was given.
- A generated summary of the changes if no description was provided (e.g., "Changes to auth middleware and user model").

This triggers the full council review process as defined in the `/council-review` skill:
- All active council members receive the materials with their lens prompts.
- The arbitrator runs last with all findings.
- The consolidator produces a unified review.

### Step 4 — Present Findings

Display the consolidated review to the user:

1. **Verdict**: `APPROVED` or `CHANGES_REQUESTED`.
2. **Findings table**: The full findings table from the consolidation, including:
   - Finding number, severity, description, expert source, arbitrator assessment, status.
3. **Arbitrator summary**: The arbitrator's overall assessment and verdict recommendation.
4. **Filtered findings**: Any findings that were filtered by the consolidator, with reasons (so the user can override if desired).

Format the output clearly with section headers. Lead with the verdict.

### Step 5 — User Action

After presenting findings, the user decides on next steps. This skill does not enforce any action — it is purely advisory. Common outcomes:

- **Address findings**: The user fixes issues and optionally runs `/review` again.
- **Proceed as-is**: The user accepts the findings as known and continues.
- **Partial address**: The user fixes some findings and marks others as intentional.

If the user asks to run the review again after making changes, repeat from Step 1.

---

## Findings Tracking

Standalone reviews write their findings to `docs/findings/standalone-review-<timestamp>.md` using the standard findings tracker format:

```markdown
# Findings Tracker: Standalone Review

## Review Metadata
- **Type**: code (standalone)
- **Date**: <YYYY-MM-DD>
- **Description**: <description>
- **Verdict**: <APPROVED|CHANGES_REQUESTED>

## Findings

| # | Round | Severity | Finding | Expert | Arbitrator | Status | Resolution |
|---|-------|----------|---------|--------|------------|--------|------------|
```

Standalone reviews are single-round by default. The user may re-invoke `/review` to run another round, but there is no automatic multi-round convergence loop as in sprint reviews.

---

## Differences from Sprint Code Review

| Aspect                | Sprint Code Review         | Standalone Review          |
|-----------------------|----------------------------|----------------------------|
| Trigger               | Part of `/sprint` workflow | User invokes directly      |
| Sprint context        | Full sprint plan + gap list| None (project context only)|
| Multi-round           | Automatic convergence loop | Manual re-invocation       |
| Findings location     | `sprint-<N>-findings.md`  | `standalone-review-<timestamp>.md` |
| Blocks progress       | Yes (verdict gates sprint) | No (advisory only)         |
| Retrospective tracked | Yes                        | No                         |

---

## Error Handling

- If `council-dispatch.py` is not found or not executable, report the error and suggest running `/setup` to initialise the project.
- If no council members are configured in `council-config.json`, report the error and suggest running `/setup`.
- If the dispatch fails for all platforms, report the error with details from the dispatch script's output.
- If `CLAUDE.md` does not exist, proceed without project context but warn that review quality may be reduced.
