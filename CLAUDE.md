# CLAUDE.md — Multi-Agent Development Workflow

This file has two sections:
1. **Workflow Rules** — generic, applies to any project using this skill set
2. **Project Configuration** — project-specific settings that skills reference at runtime

---

## Workflow Rules (MANDATORY)

Every code change MUST follow this multi-agent workflow. Skills in `.claude/skills/` implement each phase.

### Workflow Modes

Use **Full Review** for new patterns, schema changes, auth/security features, or anything novel.
Use **Standard** for features that follow established patterns.

---

### Phase 0: Feature Inventory (MANDATORY — runs before every plan)

Before planning any work, establish what needs to be built and verify completeness:

#### If an Analysis Corpus exists (`docs/analysis/`)

Use the pre-built analysis documentation as the **single source of truth**:

1. **Read the relevant analysis docs** — `docs/analysis/NN-<area>.md` for the feature area being worked on
2. **Gap Agent** — compare the analysis checklists against what currently exists in this codebase:
   - Check each checklist item: DONE, PARTIAL, or MISSING
   - Use actual file reads to verify (don't trust memory)
3. **Output** — the gap list becomes the input to the Plan Agent

#### If no Analysis Corpus exists

Run `/analyze` first to build one. If that's not feasible for the current task:

1. **Inventory Agent** — produces a checklist of every feature, page, component, and interaction required:
   - **If a reference implementation exists** (see Project Configuration): read the reference code (grep/read actual files, never guess) + any spec documents. List every feature, page, route, component, interaction, and UX behaviour.
   - **If no reference exists**: ask the user to describe the required functionality. Do not proceed until the user has confirmed the feature set.
2. **Gap Agent** — compares the inventory against the current codebase. Produces: MISSING, PARTIAL, DONE for each item.
3. **Output** — the gap list is the input to the Plan Agent.

**This phase is non-negotiable.** Invoke via `/phase-0`. The gap list persists to `docs/gaps/YYYY-MM-DD-<area>.md`.

### Analysis Skill (`/analyze`)

A one-time deep analysis that produces persistent documentation in `docs/analysis/`. See `.claude/skills/analyze.md`.

---

### Full Review Workflow

For novel or high-risk changes:

#### Phase 1: Plan & Multi-Perspective Review
1. **Plan Agent** — numbered implementation plan from the gap list.
2. **Spawn review agents** (Architecture, Security, Performance, Testability, UI (if applicable), Spec Compliance).
3. **Consolidate feedback** — revise plan if any FAIL items.
4. **Present plan to user for approval.**

#### Phase 2: Implement
1. **Parallel Code + Test agents** — code agent reads context files first, test agent writes from spec.
2. **UI Review** — if UI components were created/changed.
3. **Smoke Wiring Check** — route registration, navigation, API contracts, form completeness.
4. **Integration check** — type check + full test suite + E2E.
5. **Fix failures** — fix code to match tests (tests are the spec).
6. **Spec Compliance check** — mandatory final gate.
7. **Auto-commit if green.**

---

### Standard Workflow (Established Patterns)

For features following existing patterns:

#### Phase 1: Plan & Review
1. **Plan Agent** — implementation plan from gap list.
2. **Spawn 2 review agents:**
   - **Architecture & Security Review** — pattern compliance, auth, injection, input validation.
   - **Spec Compliance Review** — matches spec, all states covered.
3. **If no FAIL items, proceed to implementation.** No user approval needed.

#### Phase 2: Implement
Same as Full Review Phase 2 but proceeds automatically on green.

---

### Pre-Deploy Gate (Both Modes)

Before any deployment or merge:
1. Full test suite must pass
2. Type check must pass
3. No lint errors
4. E2E tests must pass
5. **Spec compliance check** — verify all planned features are implemented
6. Present summary

---

### Enforcement Rules

#### 1. Gap List is a Persistent Artifact
- Phase 0 writes to `docs/gaps/YYYY-MM-DD-<area>.md`
- `/plan` and `/implement` check for its existence and refuse to proceed without it

#### 2. Every Skill Checks Its Prerequisites
- `/plan` → requires gap list (runs `/phase-0` if missing)
- `/implement` → requires gap list + approved plan
- `/pre-deploy` → requires spec compliance check (runs `/spec-compliance`)

#### 3. Spec Compliance Checks Reachability, Not Just Existence
- For every route: is there a link that navigates to it?
- For every page: is there a menu item or link that leads to it?
- An orphaned route (exists but unreachable) = FAIL

#### 4. No "Done" Without Verification
- `/implement` Step 6 runs spec compliance after code+test agents complete
- `/pre-deploy` includes Spec Compliance as a blocking check
- Both read actual files — never rely on memory

#### 5. Spec Compliance Agent is Never Optional
- Appears in `/plan`, `/implement`, and `/pre-deploy` — all three
- MANDATORY label on each occurrence

---

## Anti-Hallucination Rules

1. **Never guess at implementation details** — always read the code or spec first
2. **Review agents must cite specific concerns** — no vague "this could be a problem"
3. **Test agents write tests from the spec** — not from the implementation
4. **If unsure, ask** — don't fabricate an answer
5. **Each agent has a narrow mandate** — architecture agent doesn't write code, test agent doesn't review security
6. **Verify before asserting** — grep the codebase before claiming something exists or doesn't exist
7. **Never mark a feature as "done" without comparing to the spec/reference** — read the actual code, verify it matches

---

## Git Workflow

- Feature branches off main
- Commits only after Phase 2 approval
- Commit messages describe the "why"
- Never commit without passing tests

---
---

## Project Configuration

> **This section is project-specific.** When using this workflow for a new project, replace the contents below with the project's actual settings. Skills read this section at runtime for project-specific details.

### Project Description

This project replicates the functionality described in `docs/FUNCTIONAL-SPEC.md` as a standalone local-first application.

### Reference Implementation

Path: `/Users/timfrench/labels/1c-portal-v2` (READ-ONLY — never modify files there)

Use it to understand:
- How specific features work
- Data models and schemas
- API contracts and response shapes
- Edge cases and validation rules
- UI components, layouts, styling, and user interactions
- Design system tokens and visual patterns

Always grep/read the actual code rather than relying on memory.

### Stack

- **Runtime**: Node.js with TypeScript (strict mode)
- **API framework**: Hono (@hono/node-server)
- **Database**: SQLite via better-sqlite3 (WAL mode, busy_timeout, synchronous=NORMAL)
- **Frontend**: Preact + Signals, UnoCSS
- **Testing**: Vitest (unit/integration), Playwright (E2E)
- **Monorepo**: npm workspaces + Turbo (packages/shared, apps/api, apps/web)

### Commands

- **Dev servers**: `npm run dev` (API on :3000, Web on :5173)
- **Type check**: `tsc --noEmit`
- **Unit tests**: `npm test` (Vitest)
- **E2E tests**: `npx playwright test --reporter=list`
- **E2E install**: `npx playwright install --with-deps chromium`
- **Lint**: `npm run lint`
- **Health checks**: `curl -sf http://localhost:3000/health`, `curl -sf http://localhost:5173/`

### Directory Structure

- `apps/api/` — backend API server
- `apps/web/` — frontend SPA
- `packages/shared/` — shared types and schemas
- `apps/web/src/pages/` — page components
- `apps/web/src/components/` — shared UI components
- `apps/web/src/app.tsx` — router (route definitions)
- `apps/api/src/routes/` — API route handlers
- `packages/shared/src/schemas/` — Zod validation schemas
- `e2e/` — Playwright E2E tests
- `e2e/seed-data.json` — E2E seed data fixture
- `docs/gaps/` — Phase 0 gap lists
- `docs/analysis/` — Analysis corpus
- `docs/bug-patterns.md` — Bug pattern registry

### Test File Conventions

- Unit/integration tests: `*.test.ts` adjacent to source file
- E2E tests: `e2e/NN-feature.spec.ts` (numeric prefix for ordering)
- Test files needing DOM: `// @vitest-environment jsdom` directive

### Established Patterns

- **Route factory**: `createXxxRoutes({ clock })` with default export for production
- **Service layer**: pure functions taking `(db, ...args, clock)`, using `db.transaction()` for multi-step mutations
- **DI for time**: all timestamps via injected `Clock.isoNow()`, never `new Date()` or SQL `datetime('now')`
- **Org isolation**: `orgGuard` middleware checks membership, sets `orgRole` on context
- **Auth**: JWT (jose, HS256 pinned), magic link login, session table
- **Error classes**: domain errors (e.g. `EntityNotFoundError`) caught in routes → HTTP status codes
- **Test infrastructure**: `createTestApp()` → in-memory DB + FakeClock + test doubles
- **Zod schemas**: validated in route handlers, ZodError → 400
- **API client auto-unwrap**: `handleResponse` in `api.ts` unwraps single-key JSON objects; multi-key objects are returned as-is
- **Frontend imports**: relative imports (NOT @/ aliases — Vitest doesn't resolve them)

### Data Model Conventions

- Flat entity format (no `data` wrapper) — system fields and custom fields at same level
- Consistent error responses with appropriate HTTP status codes
- No optimistic updates — server is authoritative
- No data transformations — store and serve data as-is

### Design System

- **CSS framework**: UnoCSS with Tailwind presets
- **Config file**: `apps/web/uno.config.ts`
- **Global styles**: `apps/web/src/styles/global.css`
- **Fonts**: Outfit (display), Inter (body), JetBrains Mono (mono)
- **Color tokens**: `--color-primary-*` (cyan), `--color-accent-*` (amber), `--color-surface-*` (neutral)
- **Shortcuts**: `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`, `.input`, `.input-error`, `.card`, `.card-hover`, `.heading-1`–`.heading-4`, `.badge`, `.badge-draft`, `.badge-published`, `.container-narrow`, `.container-default`, `.container-wide`
- **Icons**: Lucide via `i-lucide-*` class, standard size `w-4 h-4`
- **Dark mode**: supported, all components need `dark:` variants
- **Responsive**: mobile-first (`base` → `sm:` → `md:` → `lg:`)

### Coding Conventions

- TypeScript strict mode
- Keep file count small, each serving a distinct purpose
- Avoid premature abstractions
