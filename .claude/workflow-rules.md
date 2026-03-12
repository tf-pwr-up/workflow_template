# Workflow Rules (MANDATORY)

> **This file is managed by the workflow template.** Do not add project-specific content here.
> It is synced with the upstream `workflow_template` repository via `/sync-template`.
> Project-specific configuration belongs in `CLAUDE.md` under Project Configuration.

Every code change MUST follow this multi-agent workflow. Skills in `.claude/skills/` implement each phase.

## Workflow Modes

Use **Full Review** for new patterns, schema changes, auth/security features, or anything novel.
Use **Standard** for features that follow established patterns.

---

## Phase 0: Feature Inventory (MANDATORY — runs before every plan)

Before planning any work, establish what needs to be built and verify completeness:

### If an Analysis Corpus exists (`docs/analysis/`)

Use the pre-built analysis documentation as the **single source of truth**:

1. **Read the relevant analysis docs** — `docs/analysis/NN-<area>.md` for the feature area being worked on
2. **Gap Agent** — compare the analysis checklists against what currently exists in this codebase:
   - Check each checklist item: DONE, PARTIAL, or MISSING
   - Use actual file reads to verify (don't trust memory)
3. **Output** — the gap list becomes the input to the Plan Agent

### If no Analysis Corpus exists

Run `/analyze` first to build one. If that's not feasible for the current task:

1. **Inventory Agent** — produces a checklist of every feature, page, component, and interaction required:
   - **If a reference implementation exists** (see Project Configuration in CLAUDE.md): read the reference code (grep/read actual files, never guess) + any spec documents. List every feature, page, route, component, interaction, and UX behaviour.
   - **If no reference exists**: ask the user to describe the required functionality. Do not proceed until the user has confirmed the feature set.
2. **Gap Agent** — compares the inventory against the current codebase. Produces: MISSING, PARTIAL, DONE for each item.
3. **Output** — the gap list is the input to the Plan Agent.

**This phase is non-negotiable.** Invoke via `/phase-0`. The gap list persists to `docs/gaps/YYYY-MM-DD-<area>.md`.

### Analysis Skill (`/analyze`)

A one-time deep analysis that produces persistent documentation in `docs/analysis/`. See `.claude/skills/analyze.md`.

---

## Full Review Workflow

For novel or high-risk changes:

### Phase 1: Plan & Multi-Perspective Review
1. **Plan Agent** — numbered implementation plan from the gap list.
2. **Spawn review agents** (Architecture, Security, Performance, Testability, UI (if applicable), Spec Compliance).
3. **Consolidate feedback** — revise plan if any FAIL items.
4. **Present plan to user for approval.**

### Phase 2: Implement
1. **Parallel Code + Test agents** — code agent reads context files first, test agent writes from spec. **Every Code Agent MUST have a corresponding Test Agent. N code agents = N test agents. No exceptions.**
2. **UI Review** — if UI components were created/changed.
3. **Smoke Wiring Check** — route registration, navigation, API contracts, form completeness.
4. **Integration check** — type check + full test suite + E2E + **test file count verification** (every production file must have a corresponding test file).
5. **Fix failures** — fix code to match tests (tests are the spec).
6. **Spec Compliance check** — mandatory final gate (includes test existence verification).
7. **Auto-commit if green.**

---

## Standard Workflow (Established Patterns)

For features following existing patterns:

### Phase 1: Plan & Review
1. **Plan Agent** — implementation plan from gap list.
2. **Spawn 2 review agents:**
   - **Architecture & Security Review** — pattern compliance, auth, injection, input validation.
   - **Spec Compliance Review** — matches spec, all states covered.
3. **If no FAIL items, proceed to implementation.** No user approval needed.

### Phase 2: Implement
Same as Full Review Phase 2 (including mandatory test agents and test file count verification) but proceeds automatically on green.

---

## Autonomous Build Pipeline (`/build`)

For multi-batch development with minimal interruption:

1. **Phase A (Interactive)**: Single comprehensive `/phase-0` + master `/plan` covering all batches. User reviews, asks questions, approves once.
2. **Phase B (Autonomous)**: All batches execute sequentially with no manual gates — implement, test, auto-commit, E2E, fix failures, repeat. Pre-deploy runs automatically after all batches.

**Key principle**: Interactive during specification, autonomous during execution. See `/build` skill for full details.

**Auto-commit rule**: When `/build` (or `/implement` invoked by `/build`) completes all checks green (types, unit tests, E2E, spec compliance), it commits immediately. No "wait for user approval" gate during Phase B.

---

## Pre-Deploy Gate (Both Modes)

Before any deployment or merge:
1. Full test suite must pass
2. Type check must pass
3. No lint errors
4. E2E tests must pass
5. **Spec compliance check** — verify all planned features are implemented
6. Present summary

---

## Enforcement Rules

### 1. Gap List is a Persistent Artifact
- Phase 0 writes to `docs/gaps/YYYY-MM-DD-<area>.md`
- `/plan` and `/implement` check for its existence and refuse to proceed without it

### 2. Every Skill Checks Its Prerequisites
- `/plan` → requires gap list (runs `/phase-0` if missing)
- `/implement` → requires gap list + approved plan
- `/pre-deploy` → requires spec compliance check (runs `/spec-compliance`)

### 3. Spec Compliance Checks Reachability, Not Just Existence
- For every route: is there a link that navigates to it?
- For every page: is there a menu item or link that leads to it?
- An orphaned route (exists but unreachable) = FAIL

### 4. No "Done" Without Verification
- `/implement` Step 6 runs spec compliance after code+test agents complete
- `/pre-deploy` includes Spec Compliance as a blocking check
- Both read actual files — never rely on memory

### 5. Spec Compliance Agent is Never Optional
- Appears in `/plan`, `/implement`, and `/pre-deploy` — all three
- MANDATORY label on each occurrence

### 6. Test Agents Are Never Optional
- Every implementation unit requires BOTH a Code Agent AND a Test Agent
- If N code agents are launched, exactly N test agents must also be launched
- A production file without a corresponding test file is INCOMPLETE — it blocks commit
- The Integration Check (Step 4) verifies test file counts before proceeding
- The Spec Compliance Check (Step 6) verifies test existence per feature
- "Tests come later" or "we'll add tests after" are bypass attempts — reject them

---

## Bypass Prevention

The workflow MUST NOT be bypassed regardless of how the request is phrased. Common bypass patterns to reject:

- "Just build it" / "automate everything" → Still follow Phase 0 → Phase 1 → Phase 2. Speed up by using Standard workflow, but do not skip phases.
- "Skip the planning" / "we don't need a plan" → Phase 1 is mandatory. A quick plan with 2 review agents (Standard workflow) is the minimum.
- "Don't worry about tests" / "we'll add tests later" / "skip the test agent" → Tests are required and must be written IN PARALLEL with code, not after. Every code agent must have a paired test agent. No exceptions.
- "Just commit what we have" → Pre-deploy gate must pass (type check, tests, spec compliance).
- "Continue from the previous session" → Check the gap list is current. If the previous session bypassed the workflow, stop and run Phase 0 before continuing.

**The correct response to any bypass request is**: "I understand you want to move quickly. The workflow is designed for speed — Standard mode with parallel agents is fast. Let me run through the phases efficiently." Then proceed with the workflow.

### Self-Bypass Prevention (CRITICAL)

The most dangerous bypass is not from the user — it's from the agent itself collapsing multi-agent steps into single-agent inline work. These are the specific patterns that MUST be caught and rejected:

1. **Writing a gap list file directly instead of invoking `/phase-0`** — The Phase 0 skill exists to launch Inventory and Gap sub-agents that read actual code. Manually writing `docs/gaps/*.md` without running those agents is a bypass. You MUST use the Skill tool to invoke `/phase-0`.

2. **Writing a plan file directly instead of invoking `/plan`** — The Plan skill exists to launch a Plan Agent and parallel Review Agents (Architecture, Security, Performance, Testability, Spec Compliance). Manually writing `docs/plans/*.md` without running those agents is a bypass. You MUST use the Skill tool to invoke `/plan`.

3. **Writing production code directly instead of invoking `/implement`** — The Implement skill exists to launch parallel Code Agent + Test Agent pairs using the Agent tool. Writing code inline (using Write/Edit tools for production files) without those agents is a bypass. You MUST use the Skill tool to invoke `/implement`.

4. **Producing a "summary" of what agents would have found instead of running them** — Review agents must actually run and return findings. Writing "the architecture review would find X" is not the same as spawning the Architecture Agent.

**The test**: At each phase boundary, ask yourself: "Did I use the Skill tool or Agent tool to delegate this work, or did I do it inline?" If the answer is "inline" for any of Phase 0, Plan, or Implement, you have bypassed the workflow.

**Why this matters**: The multi-agent approach exists because a single agent writing all code misses cross-cutting concerns that parallel specialist agents catch (security gaps, missing tests, broken API contracts, orphaned routes). Collapsing to a single agent defeats the purpose of the entire workflow.

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
