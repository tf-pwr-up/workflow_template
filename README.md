# Claude Code Multi-Agent Workflow

A reusable set of Claude Code skills that enforce a gated, multi-agent development workflow. Copy this into any project to get structured planning, parallel implementation with tests, automated reviews, and spec compliance verification.

## What This Is

A collection of 10 slash-command skills for [Claude Code](https://claude.com/claude-code) that work together as a development pipeline. They enforce a disciplined workflow where every code change goes through discovery, planning, review, implementation, and verification — with multiple specialised agents running in parallel at each phase.

The workflow is **project-agnostic**. It works with any stack, framework, or language. Project-specific details (stack, commands, patterns, design system) are discovered automatically by the skills and written to `CLAUDE.md` as they run.

## Quick Start

### 1. Copy into your project

```bash
# Clone this repo
git clone <repo-url> workflow-template

# Copy skills and CLAUDE.md into your project
cp -r workflow-template/.claude your-project/.claude
cp workflow-template/CLAUDE.md your-project/CLAUDE.md
mkdir -p your-project/docs
cp workflow-template/docs/bug-patterns.md your-project/docs/bug-patterns.md
```

### 2. Start the workflow

Open Claude Code in your project directory:

```bash
cd your-project
claude
```

Then run the analysis skill to bootstrap your project configuration:

```
/analyze /path/to/reference-or-specs
```

This reads your source material (codebase, specs, or both), produces detailed analysis documentation in `docs/analysis/`, and automatically populates `CLAUDE.md` with your project's stack, patterns, design system, and conventions.

### 3. Build features

```
/phase-0          # Inventory what needs building, produce gap list
/plan             # Design the implementation, run multi-perspective review
/implement        # Parallel code + test agents, integration checks, spec compliance
```

### 4. Verify and deploy

```
/review           # Multi-perspective code review (architecture, security, performance, UI, tests)
/pre-deploy       # Full gate check: tests, types, lint, E2E, spec compliance
```

## The Pipeline

```
/analyze  →  /phase-0  →  /plan  →  /implement  →  /pre-deploy
                                         ↑
                                    /review (anytime)
                                    /ui-review (anytime)
                                    /postmortem (when bugs found)
                                    /spec-compliance (anytime)
```

Each phase gates the next. No planning without a gap list. No implementation without a plan. No deployment without passing all checks.

## Skills Reference

### `/analyze` — Deep Analysis & Documentation

**When**: Starting a new project, onboarding to a codebase, or when the reference has changed.

Analyses a source (codebase, spec documents, or both) and produces a persistent documentation corpus in `docs/analysis/`. Handles three source types:

- **Codebase** — reads code, extracts routes, API surface, data models, components, state management
- **Specs/Requirements** — reads documents, extracts features, user stories, constraints, terminology
- **Mixed** — uses code as ground truth, specs as intent

Runs 7 phases:
1. **Discovery** — structural map of the source
2. **Feature Decomposition** — detailed per-area documentation
3. **Cross-Cutting Concerns** — design system and recurring patterns
4. **User Q&A** — asks clarifying questions about requirements and scope
5. **BA Review** — iterative quality gate (up to 3 rounds) checking for gaps, ambiguities, and contradictions
6. **Implementation Checklists** — atomic, testable work items per feature area
7. **Summary & Index** — table of contents, recommended build order, scope estimate

**Updates CLAUDE.md**: Stack, Directory Structure, Design System, Established Patterns, Data Model Conventions.

---

### `/phase-0` — Feature Inventory & Gap Analysis

**When**: Before planning any work. Mandatory prerequisite for `/plan`.

Compares what should exist (from analysis docs or reference) against what currently exists in the codebase. Produces a gap list classifying each feature as DONE, PARTIAL, or MISSING.

Also checks the **integration surface** — orphaned routes, unregistered components, dead endpoints, and mismatched API contracts.

**Output**: `docs/gaps/YYYY-MM-DD-<area>.md` — persists across sessions as the contract for what gets built.

---

### `/plan` — Multi-Perspective Planning

**When**: After `/phase-0` produces a gap list.

Produces a numbered implementation plan, then runs it through parallel review agents:

- **Architecture Agent** — pattern consistency, data model, interfaces
- **Security Agent** — auth/authz, injection, validation, OWASP Top 10
- **Performance Agent** — algorithms, N+1 queries, memory leaks, bundle size
- **Testability Agent** — test strategy, edge cases, E2E test plan
- **UI Review Agent** — design system compliance, visual states, responsiveness (if UI changes)
- **Spec Compliance Agent** — verifies plan covers every gap list item (MANDATORY)

Each plan unit includes **context files to read** — files that code agents must read before writing code, preventing them from guessing at contracts.

**Updates CLAUDE.md**: Established Patterns, Test File Conventions, Design System.

---

### `/implement` — Parallel Code + Test Implementation

**When**: After a plan is approved.

Breaks the plan into implementation units and runs parallel agent pairs:

- **Code Agent** — reads context files first, then implements production code
- **Test Agent** — writes tests from the spec (not from the code)
- **E2E Test Agent** — adds/updates browser tests for user-facing changes

Then runs a verification sequence:
1. **UI Review** — checks design system compliance, visual states, accessibility
2. **Smoke Wiring Check** — fast structural verification (routes registered, links valid, API contracts match, forms complete)
3. **Integration Check** — type check, full test suite, E2E tests, cross-file issues
4. **Fix Failures** — code is fixed to match tests (tests are the spec)
5. **Spec Compliance** — mandatory final gate verifying every gap list item

**Updates CLAUDE.md**: Commands, Test File Conventions, Established Patterns, Coding Conventions, Design System.

---

### `/review` — Multi-Perspective Code Review

**When**: Anytime — on uncommitted changes, specific files, or by description.

Spawns 5 parallel review agents:

- **UI Review** — design system, visual states, responsive, dark mode, accessibility
- **Architecture** — conventions, API contracts, form bindings, link construction, bug patterns
- **Security** — auth, injection, input validation, URL param resolution
- **Performance** — algorithms, re-renders, caching, memory leaks
- **Test Coverage** — unit tests, edge cases, E2E coverage

Findings grouped by severity: BLOCKING → SHOULD FIX → CONSIDER.

**Updates CLAUDE.md**: Coding Conventions, Established Patterns.

---

### `/ui-review` — UI Quality Review

**When**: Anytime on frontend code. Also runs automatically within `/review` and `/implement`.

Checks 8 categories:

| Category | What it checks |
|----------|---------------|
| Design system compliance | Uses project shortcuts/tokens, not raw utility strings |
| Visual states | Loading, empty, error, success — all present |
| Responsive | Mobile-first breakpoints, no overflow, tappable targets |
| Dark mode | All elements have dark mode variants (if project supports it) |
| Consistency | Matches spacing, typography, actions of adjacent pages |
| Reference comparison | Matches reference implementation layout (if one exists) |
| Accessibility | Labels, alt text, focus styles, semantic HTML |
| Polish | Icons, transitions, loading indicators |

---

### `/spec-compliance` — Verify Implementation Matches Spec

**When**: After implementation, before commit. Also standalone to check current state.

Verifies every gap list item against the actual codebase:
- Code exists and matches spec behaviour
- UI features are reachable (no orphaned routes or components)
- Unit and E2E tests exist
- All links match router definitions
- API contracts match (frontend types vs backend response shapes)
- Create/edit forms include all required fields

**Verdict**: PASS (0 FAILs, safe to commit) or FAIL (blocks commit until resolved).

---

### `/e2e` — End-to-End Integration Tests

**When**: After implementation or as a standalone check.

Runs two test suites:
1. **Contract tests** — API response shape verification against frontend expectations
2. **Browser tests** — critical user flows in a real browser

Includes maintenance rules ensuring E2E tests stay in sync with feature changes.

---

### `/pre-deploy` — Pre-Deployment Gate Check

**When**: Before any deployment or merge.

Runs 7 parallel gate checks:
1. **Test suite** — all unit/integration tests pass
2. **Type check** — no type errors
3. **Lint** — no lint errors
4. **Security scan** — no hardcoded secrets, auth on all routes, input validation
5. **Dependency check** — no known vulnerabilities
6. **E2E tests** — all browser tests pass
7. **Spec compliance** — all gap list items verified (MANDATORY)

**Verdict**: READY or NOT READY. A single failure in any check blocks deployment.

---

### `/postmortem` — Bug Postmortem & Workflow Improvement

**When**: After any bug is found and fixed.

Turns every bug into a permanent workflow improvement:

1. Documents the bug with structured report
2. Classifies into a pattern category (orphaned component, broken contract, ID/slug confusion, missing integration, missing system field, stale selector, state isolation)
3. Traces the escape path — which workflow phase should have caught it and why it didn't
4. Designs specific, automatable prevention rules
5. Updates the relevant skill files with new checks
6. Adds to `docs/bug-patterns.md` registry

This is how the workflow improves itself over time.

**Updates CLAUDE.md**: Bug Patterns section.

## How CLAUDE.md Works

`CLAUDE.md` has two sections:

### Workflow Rules (static)
Generic rules that apply to every project — phases, gates, enforcement rules, anti-hallucination rules, git workflow. You never need to edit this section.

### Project Configuration (auto-populated)
Starts empty with placeholder templates. Skills populate it as they run:

| Skill | What it writes | When |
|-------|---------------|------|
| `/analyze` | Stack, Directory Structure, Design System, Patterns, Data Model | After discovery and cross-cutting analysis |
| `/plan` | Established Patterns, Test Conventions | After review consolidation |
| `/implement` | Commands, Test Conventions, Coding Conventions | After integration checks pass |
| `/review` | Coding Conventions, Established Patterns | After review identifies undocumented conventions |
| `/postmortem` | Bug Patterns | After bug analysis |

Each cycle adds more knowledge. The file grows into a comprehensive project reference that makes subsequent development cycles more accurate and efficient.

## Workflow Modes

### Full Review
For new patterns, schema changes, auth/security, or anything novel:
- 5-6 review agents evaluate the plan
- User approval required before implementation
- Use when the risk of getting it wrong is high

### Standard
For features following established patterns:
- 2 review agents (Architecture+Security, Spec Compliance)
- Auto-proceeds if no FAIL items
- Use when the pattern is already proven

## Key Design Principles

1. **Tests come from the spec, not the code** — prevents tests that verify broken behaviour
2. **Multiple perspectives catch different bug classes** — security, architecture, performance, UI, spec compliance
3. **Automated cross-checks** catch what humans miss — orphaned routes, broken API contracts, missing form fields
4. **Context files before code** — agents read contracts before implementing, never guess
5. **The workflow improves itself** — `/postmortem` traces escape paths and adds prevention rules
6. **No code ships without passing every gate** — gap list → plan review → tests → type check → spec compliance → E2E
7. **Project knowledge accumulates** — CLAUDE.md grows richer with each cycle, reducing errors over time

## Directory Structure

```
your-project/
├── .claude/
│   └── skills/
│       ├── analyze.md          # Deep analysis & documentation
│       ├── e2e.md              # End-to-end integration tests
│       ├── implement.md        # Parallel code + test implementation
│       ├── phase-0.md          # Feature inventory & gap analysis
│       ├── plan.md             # Multi-perspective planning
│       ├── postmortem.md       # Bug postmortem & workflow improvement
│       ├── pre-deploy.md       # Pre-deployment gate check
│       ├── review.md           # Multi-perspective code review
│       ├── spec-compliance.md  # Verify implementation matches spec
│       └── ui-review.md        # UI quality review
├── docs/
│   ├── analysis/               # Created by /analyze (persistent corpus)
│   ├── gaps/                   # Created by /phase-0 (gap lists)
│   └── bug-patterns.md         # Created by /postmortem (bug registry)
└── CLAUDE.md                   # Workflow rules + auto-populated project config
```

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- A git repository (the workflow uses git for commits and change tracking)

## License

MIT
