# /review — Multi-Perspective Code Review

Trigger: User wants a review of existing or changed code.

## Instructions

When the user invokes `/review` (optionally with a file path or description):

### Step 1: Identify Scope
- If a file/path is specified, review that
- If no path, review all uncommitted changes (`git diff` + `git diff --staged`)
- If a description is given, find and review relevant files

### Step 2: Spawn Parallel Review Agents

**UI Review Agent** (only when changes touch frontend code):
- Run the full `/ui-review` checklist: design system compliance, visual states, responsive behaviour, dark mode, consistency, reference comparison, accessibility, polish
- See `.claude/skills/ui-review.md` for the complete review specification

**Architecture Review Agent:**
- Does the code follow project conventions (see CLAUDE.md)?
- Is the data model consistent with the project's established format?
- Are there unnecessary abstractions or missing patterns?
- Is the code consistent with adjacent files?
- Any dead code, unused imports, or redundant logic?
- **API contract alignment**: Do frontend API calls match the actual backend response shapes? Account for any response transformation/unwrapping the API client performs.
- **Form binding**: Are form components that serve both create and edit modes properly controlled? Do they accept live values from the parent, not just read from a potentially-null entity?
- **Link construction**: Do link `href` values match route patterns in the router? Are all required URL segments included?
- Consult `docs/bug-patterns.md` (if it exists) for known patterns to watch for.

**Security Review Agent:**
- Input validation on all user-facing inputs?
- Auth/authz checks on all protected endpoints?
- Field-level access control properly applied?
- No injection vectors (SQL, XSS, command)?
- No hardcoded secrets or credentials?
- Proper error responses (don't leak internals)?
- **URL param resolution**: Any endpoint accepting dynamic URL params (e.g. `:id`, `:slug`) must resolve consistently with the project's established pattern (see CLAUDE.md). Flag any direct ID-only lookup on a URL parameter that could be a slug.

**Performance Review Agent:**
- Algorithm complexity appropriate?
- No unnecessary re-renders or re-computations?
- Proper use of caching?
- No memory leaks?
- Database/storage access patterns efficient?

**Test Coverage Review Agent:**
- Are there unit tests for this code?
- Do tests cover edge cases and error paths?
- Are test assertions meaningful (not just "doesn't throw")?
- Any missing test scenarios?
- Are tests independent and deterministic?
- For user-facing changes: are E2E tests updated to match?
- Do existing E2E test selectors still match the current UI text and structure?
- If new features were added, is there at least one E2E test covering the happy path?

### Step 3: Consolidate & Report
Present findings grouped by severity:
- **BLOCKING** — must fix before merge (security vulnerabilities, data loss risks, broken contracts)
- **SHOULD FIX** — significant issues that should be addressed (performance problems, missing tests, convention violations)
- **CONSIDER** — suggestions for improvement (style, clarity, minor optimizations)

Each finding must cite the specific file and line, and explain WHY it's an issue.
