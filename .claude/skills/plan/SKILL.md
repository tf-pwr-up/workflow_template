---
name: plan
description: "Multi-Perspective Planning with parallel review agents."
---

# /plan — Multi-Perspective Planning

Trigger: User wants to plan a new feature, change, or module.

## Prerequisites (BLOCKING — do not skip, do not work around)

Before producing any plan, verify Phase 0 has been completed. **Do NOT produce a plan from memory or general knowledge — the gap list is the input.**

1. Check for a gap list artifact: `ls docs/gaps/*.md`
2. If no gap list exists, STOP and invoke `/phase-0` first. Tell the user: "Phase 0 (Feature Inventory & Gap Analysis) is required before planning. Running it now."
3. If a gap list exists, **read it** and use it as the primary input to the plan. Do not plan from memory.
4. If the gap list is stale (the codebase has changed significantly since it was created), re-run `/phase-0` to refresh it.

The plan MUST reference specific items from the gap list. Every MISSING and PARTIAL item should map to plan steps. A plan that doesn't reference gap list items is not a valid plan.

## Instructions

When the user invokes `/plan` with a description of what they want to build:

### Step 1: Produce the Plan
Use the Agent tool (subagent_type: Plan) to analyse the task and produce a numbered implementation plan. The plan must reference the gap list from Phase 0 and include:
- Every file that needs to be created or modified
- Interfaces/types shared across files
- API contracts (request/response shapes)
- Dependencies between files
- Estimated complexity per file
- **Context files to read** (per implementation unit) — files that code agents MUST read before writing code. This prevents agents from guessing at contracts. For each unit, list:
  - Router file — if the unit includes a page component (for route registration and link construction)
  - Route handler — if the unit makes API calls (for response shape and any transform/unwrap behaviour)
  - Validation schema — if the unit includes a form (for required fields including system fields)
  - Any other file whose contract the unit depends on

### Step 2: Parallel Review
Spawn review agents IN PARALLEL using the Agent tool (add UI Review Agent if UI changes are in scope):

**Architecture Agent:**
- Does this fit the project's existing patterns and conventions (see CLAUDE.md)?
- Are the interfaces consistent with the project's data model?
- Is the data flow correct (server → store → UI or equivalent)?
- Are there unnecessary abstractions or missing ones?
- Check against the project's spec and conventions

**Security Agent:**
- Are there auth/authz gaps in any new endpoint?
- Missing input validation on any user-facing input?
- Potential for injection (SQL, command, XSS)?
- Are fields properly filtered by access level?
- Secrets or credentials exposed?
- Rate limiting needed?

**Performance Agent:**
- Any O(n²) or worse algorithms?
- Unnecessary data loading or N+1 patterns?
- Missing caching opportunities?
- Bundle size impact of new dependencies?
- Memory leak potential (unclosed connections, growing arrays)?

**Testability Agent:**
- Define test strategy: what unit tests, integration tests, and E2E tests are needed
- List edge cases and boundary conditions
- What test fixtures/mocks are required?
- Are there untestable patterns in the plan that should be restructured?
- **E2E test plan**: for each user-facing feature, specify which E2E tests need to be added or updated. Include: test name, which spec file it belongs in, what assertions to make, and whether seed data needs updating.
- Output a test plan with specific test case descriptions

**UI Review Agent** (only when plan includes UI changes):
- Does the plan specify which design system components/classes to use?
- Are all visual states accounted for? (loading, empty, error, success)
- Does the plan match the reference implementation's layout and visual hierarchy (if a reference exists)?
- Are responsive breakpoints and dark mode considered?
- See `.claude/skills/ui-review.md` for the full checklist

**Spec Compliance Agent (MANDATORY — do not omit):**
- Does the plan fully address every MISSING/PARTIAL item from the Phase 0 gap list?
- For every new route/page: is there a navigation path to reach it? (Links in header, sidebar, dashboard, etc.)
- For every UI feature: does the plan include the visual states (loading, empty, error)?
- Cite specific PASS/FAIL items against the gap list by item number
- A FAIL from this agent blocks proceeding to implementation

### Step 3: Consolidate
Merge all reviewer feedback. If any reviewer flags a BLOCKING issue (security vulnerability, architectural inconsistency, untestable pattern), revise the plan and note the revision.

### Step 3b: Update CLAUDE.md (if new patterns or decisions emerged)

If the review agents identified or confirmed architectural patterns, conventions, or decisions not yet in CLAUDE.md's Project Configuration section, update it:

- **Architecture Agent** findings → update **Established Patterns** (e.g. "service layer uses pure functions with DI")
- **Security Agent** findings → update **Established Patterns** (e.g. "auth middleware pattern", "input validation approach")
- **Testability Agent** findings → update **Test File Conventions** (e.g. "unit tests adjacent to source", "E2E test naming")
- **UI Review Agent** findings → update **Design System** (if design tokens or component patterns were confirmed)

Use the Edit tool to append to existing sections. Do not overwrite — the Project Configuration is cumulative.

### Step 4: Present
Show the user:
1. The implementation plan (with any revisions noted)
2. A summary of reviewer feedback (grouped by agent)
3. The test strategy
4. Any open questions or decisions needed

Wait for user approval before proceeding to implementation.
