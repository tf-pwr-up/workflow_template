# Claude Code Multi-Agent Workflow

A reusable set of Claude Code skills that enforce a gated, multi-agent development workflow. Copy this into any project to get structured planning, parallel implementation with tests, automated reviews, and spec compliance verification.

## What This Is

11 slash-command skills for [Claude Code](https://claude.com/claude-code) that work together as a development pipeline. Every code change goes through discovery, planning, review, implementation, and verification — with multiple specialised agents running in parallel at each phase.

The workflow is **project-agnostic**. It works with any stack, framework, or language. Project-specific details (stack, commands, patterns, design system) are discovered automatically by the skills and written to `CLAUDE.md` as they run.

## Quick Start

### Option A: Copy into your project (one-time)

```bash
git clone https://github.com/tf-pwr-up/workflow_template.git /tmp/wf-template

cp -r /tmp/wf-template/.claude your-project/.claude
cp /tmp/wf-template/CLAUDE.md your-project/CLAUDE.md
mkdir -p your-project/docs
cp /tmp/wf-template/docs/bug-patterns.md your-project/docs/bug-patterns.md

rm -rf /tmp/wf-template
```

### Option B: Fork with upstream sync (recommended)

This approach lets you pull template improvements and push back skill enhancements:

```bash
# Create your project repo
mkdir your-project && cd your-project && git init

# Add the template as upstream
git remote add template https://github.com/tf-pwr-up/workflow_template.git
git fetch template
git merge template/master --allow-unrelated-histories

# Add your own remote
git remote add origin git@github.com:your-org/your-project.git
git push -u origin master
```

Now you can sync skills bidirectionally — see [Upstream Sync](#upstream-sync) below.

### Start building

```bash
cd your-project
claude
```

```
/analyze /path/to/reference-or-specs    # Bootstrap project config
/phase-0                                 # Inventory & gap analysis
/plan                                    # Design + multi-perspective review
/implement                               # Parallel code + test agents
```

## The Pipeline

```
/analyze  →  /phase-0  →  /plan  →  /implement  →  /pre-deploy
                                         ↑
                                    /review (anytime)
                                    /ui-review (anytime)
                                    /postmortem (when bugs found)
                                    /spec-compliance (anytime)
                                    /sync-template (to sync with upstream)
```

Each phase gates the next. No planning without a gap list. No implementation without a plan. No deployment without passing all checks.

For detailed Mermaid diagrams of the complete workflow, agent interactions, and data flows, see **[docs/workflow-diagram.md](docs/workflow-diagram.md)**.

## File Architecture

```
your-project/
├── .claude/
│   ├── workflow-rules.md               # Generic workflow rules (synced with template)
│   └── skills/
│       ├── analyze.md                  # Deep analysis & documentation
│       ├── e2e.md                      # End-to-end integration tests
│       ├── implement.md               # Parallel code + test implementation
│       ├── phase-0.md                 # Feature inventory & gap analysis
│       ├── plan.md                    # Multi-perspective planning
│       ├── postmortem.md              # Bug postmortem & workflow improvement
│       ├── pre-deploy.md             # Pre-deployment gate check
│       ├── review.md                  # Multi-perspective code review
│       ├── spec-compliance.md         # Verify implementation matches spec
│       ├── sync-template.md           # Upstream template sync
│       └── ui-review.md              # UI quality review
├── docs/
│   ├── analysis/                      # Created by /analyze (persistent corpus)
│   ├── gaps/                          # Created by /phase-0 (gap lists)
│   └── bug-patterns.md               # Created by /postmortem (bug registry)
└── CLAUDE.md                          # Project-specific config (auto-populated)
```

### What's synced vs what's project-specific

| File | Synced with template | Content |
|------|---------------------|---------|
| `.claude/workflow-rules.md` | Yes | Workflow phases, gates, enforcement rules, anti-hallucination rules |
| `.claude/skills/*.md` | Yes | All 11 skill definitions |
| `CLAUDE.md` | **No** — project-specific | Project config: stack, commands, patterns, conventions |
| `docs/` | **No** — project-specific | Analysis corpus, gap lists, bug pattern registry |

## How CLAUDE.md Auto-Populates

`CLAUDE.md` starts with empty placeholder sections. Skills fill them in as they discover project-specific details:

| Skill | What it writes | When |
|-------|---------------|------|
| `/analyze` | Stack, Directory Structure, Design System, Patterns, Data Model | After discovery and cross-cutting analysis |
| `/plan` | Established Patterns, Test Conventions | After review consolidation |
| `/implement` | Commands, Test Conventions, Coding Conventions | After integration checks pass |
| `/review` | Coding Conventions, Established Patterns | After review identifies undocumented conventions |
| `/postmortem` | Bug Patterns | After bug analysis |

Each cycle adds more knowledge. The file grows into a comprehensive project reference that makes subsequent development cycles more accurate and efficient.

## Upstream Sync

The `/sync-template` skill manages bidirectional sync between your project and this template.

### Pull template updates

When the template gets new skills or improved workflow rules:

```
/sync-template pull
```

This fetches changes from the template remote and updates your shared files (`.claude/workflow-rules.md`, `.claude/skills/*.md`). Your project-specific `CLAUDE.md` and `docs/` are never touched.

### Push improvements back

When you improve a skill or add a prevention rule via `/postmortem` that would benefit all projects:

```
/sync-template push
```

This reviews your skill changes for project-specific content, genericises if needed, and creates a PR on the template repo. Only generic improvements are pushed — project-specific bug examples, paths, and patterns stay local.

### Check sync status

```
/sync-template status
```

Shows which shared files are ahead, behind, or in sync with the template.

### Setup

Your project needs the template as a git remote:

```bash
git remote add template https://github.com/tf-pwr-up/workflow_template.git
```

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

---

### `/phase-0` — Feature Inventory & Gap Analysis

**When**: Before planning any work. Mandatory prerequisite for `/plan`.

Compares what should exist (from analysis docs or reference) against what currently exists in the codebase. Produces a gap list classifying each feature as DONE, PARTIAL, or MISSING.

Also checks the **integration surface** — orphaned routes, unregistered components, dead endpoints, and mismatched API contracts.

**Output**: `docs/gaps/YYYY-MM-DD-<area>.md`

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

---

### `/implement` — Parallel Code + Test Implementation

**When**: After a plan is approved.

Breaks the plan into implementation units and runs parallel agent pairs:

- **Code Agent** — reads context files first, then implements production code
- **Test Agent** — writes tests from the spec (not from the code)
- **E2E Test Agent** — adds/updates browser tests for user-facing changes

Then runs a verification sequence:
1. **UI Review** — design system compliance, visual states, accessibility
2. **Smoke Wiring Check** — routes registered, links valid, API contracts match, forms complete
3. **Integration Check** — type check, full test suite, E2E tests, cross-file issues
4. **Fix Failures** — code is fixed to match tests (tests are the spec)
5. **Spec Compliance** — mandatory final gate verifying every gap list item

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

---

### `/ui-review` — UI Quality Review

**When**: Anytime on frontend code. Also runs automatically within `/review` and `/implement`.

| Category | What it checks |
|----------|---------------|
| Design system compliance | Uses project shortcuts/tokens, not raw utility strings |
| Visual states | Loading, empty, error, success — all present |
| Responsive | Mobile-first breakpoints, no overflow, tappable targets |
| Dark mode | All elements have dark mode variants (if supported) |
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

**Verdict**: PASS (0 FAILs) or FAIL (blocks commit).

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

Runs 7 parallel gate checks: test suite, type check, lint, security scan, dependency check, E2E tests, spec compliance.

**Verdict**: READY or NOT READY. A single failure blocks deployment.

---

### `/postmortem` — Bug Postmortem & Workflow Improvement

**When**: After any bug is found and fixed.

1. Documents and classifies the bug pattern
2. Traces which workflow phase should have caught it
3. Designs automatable prevention rules
4. Updates skill files with new checks
5. Adds to `docs/bug-patterns.md` registry

This is how the workflow improves itself over time.

---

### `/sync-template` — Upstream Template Sync

**When**: To pull template updates or push skill improvements back.

Three modes:
- `pull` — merge latest skills from template
- `push` — contribute generic skill improvements back (creates PR)
- `status` — check what's ahead/behind

See [Upstream Sync](#upstream-sync) above.

## Workflow Modes

### Full Review
For new patterns, schema changes, auth/security, or anything novel:
- 5-6 review agents evaluate the plan
- User approval required before implementation

### Standard
For features following established patterns:
- 2 review agents (Architecture+Security, Spec Compliance)
- Auto-proceeds if no FAIL items

## Key Design Principles

1. **Tests come from the spec, not the code** — prevents tests that verify broken behaviour
2. **Multiple perspectives catch different bug classes** — security, architecture, performance, UI, spec compliance
3. **Automated cross-checks** catch what humans miss — orphaned routes, broken API contracts, missing form fields
4. **Context files before code** — agents read contracts before implementing, never guess
5. **The workflow improves itself** — `/postmortem` traces escape paths and adds prevention rules
6. **No code ships without passing every gate** — gap list → plan review → tests → type check → spec compliance → E2E
7. **Project knowledge accumulates** — CLAUDE.md grows richer with each cycle, reducing errors over time

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- A git repository (the workflow uses git for commits and change tracking)
- GitHub CLI (`gh`) — for `/sync-template push` PR creation

## License

MIT
