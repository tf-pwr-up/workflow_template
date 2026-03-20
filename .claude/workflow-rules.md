# Workflow Rules

This document is the enforcement backbone of the entire workflow. Every agent, skill, and phase is bound by these rules. Violations are treated as defects.

---

## Craftsmanship Standard

**I am not lazy. I am not in a rush. I do not take shortcuts. My job is to deliver a great output that works first time.**

This is not aspirational. It is a contract. Every agent spawned in this workflow inherits this standard. If an agent produces output that would not survive a thorough code review by a senior engineer, the output is rejected and the agent re-runs.

---

## Workflow Overview

```
/setup --> /analyze --> [/sprint <N> --> /develop <N> --> /retrospective <N>] (repeat per sprint)
                              ^
                         /review (anytime)
```

### Phase Gating

Each phase produces artefacts that gate entry to the next phase. No phase can begin until its predecessor's gate conditions are met.

| Phase | Gate Output | Required Before |
|---|---|---|
| `/setup` | Populated `CLAUDE.md` (project description, stack, architecture, commands, directory structure) | `/analyze` |
| `/analyze` | Gap analysis document with prioritised findings from actual codebase reading | `/sprint` |
| `/sprint <N>` | Sprint plan with task breakdown, acceptance criteria, and test specifications | `/develop <N>` |
| `/develop <N>` | All code written, all tests passing, E2E verified, full suite green | `/retrospective <N>` |
| `/retrospective <N>` | Retrospective complete, bug patterns logged, workflow changes synced | Next `/sprint <N+1>` |

**Gate enforcement**: At each phase boundary, the entering skill MUST verify the predecessor's artefacts exist and are valid. If they are missing or incomplete, the skill halts and reports what is missing rather than proceeding with assumptions.

**`/review` is non-blocking**: It can be invoked at any time during development. It does not gate other phases but its findings feed into the current sprint's work.

---

## Ground Rules

### 1. Use Multiple Agents

Parallel specialist agents handle coding, testing, and reviewing. A single agent must not perform all roles. Specifically:

- **Code Agent**: Writes implementation code. Spawned via `Agent` tool with coding-specific instructions.
- **Test Agent**: Writes tests from specifications (not from implementation code). Spawned independently.
- **Review Agent**: Reviews code for correctness, patterns, and standards. Spawned independently.
- **Plan Agent**: Produces sprint plans and task breakdowns. Spawned independently.

These agents run in parallel where possible. The orchestrating skill coordinates their outputs.

### 2. Steps Cannot Be Bypassed Without User Input

No agent may decide on its own to skip:
- Writing tests for new code
- Running E2E tests after integration
- Council review at sprint boundaries
- Running the full test suite before marking a sprint complete

If an agent believes a step should be skipped, it must ask the user explicitly via `AskUserQuestion` and receive approval.

### 3. Missing Frameworks/Dependencies Are Not a Reason to Bypass

If a test framework, linter, build tool, or dependency is not installed:
- Install it.
- Configure it.
- Then proceed.

"The project doesn't have Jest configured" is not a valid reason to skip tests. Configure Jest (or the appropriate framework) and write the tests.

### 4. If in Doubt, Ask the User

Use `AskUserQuestion` with:
- **Multiple-choice options** when the decision space is known (e.g., "Which testing framework should we use? A) Jest B) Vitest C) Mocha D) Other")
- **Free text** when the decision space is open (e.g., "Describe the expected behaviour of this endpoint")

Never silently assume. Never guess at business logic.

### 5. Detail-Oriented, No Shortcuts

- No `// TODO: implement later` stubs in delivered code
- No `test.skip()` or `xit()` in delivered tests
- No "this is good enough for now" compromises
- No workarounds that mask underlying issues
- No placeholder implementations that defer real work

If something cannot be completed, it is reported as incomplete rather than delivered as a stub.

### 6. Architectural Patterns Must Be Obeyed

- New architectural patterns are proposed during `/analyze` or `/sprint` planning phases
- They are reviewed and approved before coding begins
- During `/develop`, code conforms to approved patterns
- Agents do not invent new patterns during coding — if a new pattern is needed, they pause and escalate to the orchestrator

### 7. Questions Use Multiple-Choice or Free Text

Never ask yes/no questions when richer input would produce a better outcome. Examples:

- BAD: "Should I add error handling?" (yes/no)
- GOOD: "What error handling strategy should we use? A) Try-catch with custom error types B) Result/Either pattern C) Error middleware D) Something else — please describe"

- BAD: "Is this the right approach?" (yes/no)
- GOOD: "I see two viable approaches: A) [description] B) [description]. Which do you prefer, or would you like to suggest an alternative?"

### 8. Experts Can Research from the Internet

All agents have access to `WebSearch` and `WebFetch` tools. When encountering:
- An unfamiliar API or library
- A deprecation warning or breaking change
- A best-practice question for a specific framework version

Agents should research current documentation rather than relying on potentially outdated training data.

---

## Bypass Prevention

These rules exist because AI agents have a natural tendency to consolidate work inline for efficiency. This workflow explicitly forbids that tendency.

### Delegation Requirements

| Task | Must Be Delegated To | Cannot Be Done |
|---|---|---|
| Gap analysis | Agent(s) that read actual source files | Written from memory or assumptions |
| Sprint planning | Plan Agent with gap analysis as input | Written inline by orchestrator |
| Implementation code | Code Agent sub-agents (one per task or module) | Written inline by orchestrator |
| Test code | Test Agent sub-agents working from specs | Written by Code Agent or derived from implementation |
| Council review | External reviewers via `scripts/council-dispatch.py` | Simulated by summarising what reviewers "would say" |

### Phase Boundary Self-Check

At every phase boundary, the orchestrating agent must ask itself:

> "Did I use the Agent/Skill tool to delegate this work, or did I do it inline?"

If the answer is "inline", it is a bypass. The work must be redone via proper delegation.

### Artefact Verification

- Gap lists must contain file paths that were actually read (verifiable via `Read` tool invocations in the agent's history)
- Plans must reference specific gap items by ID
- Code must be written to files (not just displayed in output)
- Tests must be runnable (not just syntactically correct-looking)
- Review findings must come from actual reviewer invocations

---

## Self-Bypass Prevention (CRITICAL)

These are the most important rules in this document. They exist because context pressure, token limits, and efficiency instincts create powerful incentives to cut corners.

### The Three Temptations

1. **Tempted to skip tests due to context pressure**: STOP. Spawn a Test Agent anyway. If context is genuinely constrained, spawn a fresh agent with only the necessary context — the spec and the file paths. Tests written by a dedicated agent from specs are better than no tests.

2. **Tempted to write code inline for speed**: STOP. Spawn a Code Agent. The 30 seconds saved by writing inline is lost tenfold when the code has no independent review or test coverage. Speed is not a value in this workflow; correctness is.

3. **Tempted to summarise what reviewers "would say"**: STOP. Actually run the council via the dispatch script. A real review catches things that a simulated review cannot, because the simulated review is limited by the same blind spots as the code author.

### The Quality Test

Before completing any phase, ask:

> "Would this produce the same quality if the agent had unlimited context and time? If not, it's a shortcut."

If the answer is "no, with more context I would have written more tests / done a deeper review / structured this differently", then the work is incomplete. Find a way to achieve the higher-quality outcome, even if it means spawning additional agents or breaking the work into smaller pieces.

---

## Anti-Hallucination Rules

AI agents can confidently assert things that are not true. These rules prevent that.

1. **Never assert a file exists without reading it.** Use `Read` or `Glob` to verify. "I believe there's a config file at..." is not acceptable — check.

2. **Never assert a test passes without running it.** Use `Bash` to execute the test suite. "This test should pass because..." is not evidence. Run it.

3. **Never claim a feature works without verifying the code path.** Trace the execution from entry point to output. Read each file in the chain. Confirm the logic is connected.

4. **Never assume an import path — check the actual file.** Read the source file to confirm the export exists and the path is correct. Import path mismatches are one of the most common AI coding errors.

5. **Read context files before writing code.** Before modifying or creating a file, read the files it depends on and the files that depend on it. Understand the context before making changes.

6. **When verifying: read the actual file, don't rely on memory of what was written.** After writing a file, if you need to verify its contents, read it again. Memory of what was written can differ from what was actually written (especially after edits, merges, or tool errors).

---

## Workflow Sync Enforcement

This workflow is maintained as a template that is shared across multiple projects. Changes made during a project must flow back to the template to benefit all projects.

### Tracked Workflow Files

- `.claude/skills/*` — All skill definitions
- `.claude/workflow-rules.md` — This file
- `scripts/council-dispatch.py` — Council review dispatch script
- `scripts/council-check.sh` — Council review status check script

### Sync Rules

1. Any modification to tracked workflow files during a sprint MUST be recorded in the retrospective.
2. The `/retrospective` skill checks for unsynchronised workflow changes by comparing tracked files against the template repo.
3. If unsynchronised changes are found, the retrospective blocks completion until one of:
   - Changes are synced back to the template via `/sync push`
   - Changes are explicitly marked as project-specific overrides with user approval
4. Project-specific overrides are documented in `CLAUDE.md` under a "Workflow Overrides" section with justification.

### Sync Commands

- `/sync pull` — Pull latest workflow files from template repo into current project
- `/sync push` — Push workflow file changes from current project back to template repo

---

## Git Workflow

### Branch Strategy

- `main` — Production-ready code. Never commit directly.
- `sprint/<N>` — Feature branch for each sprint. Created by `/sprint`, developed on by `/develop`, merged after `/retrospective`.
- Hotfix branches follow the pattern `hotfix/<description>` and bypass the sprint cycle with user approval.

### Commit Rules

1. Commits are only made after all tests pass. A failing test suite blocks commits.
2. Each commit has a descriptive message following conventional commit format.
3. Work-in-progress commits are allowed on sprint branches but must be squashed before merge.

### Pull Request Rules

1. PRs are created at the end of `/develop` for the sprint branch.
2. PRs require CI gate checks to pass before merge.
3. PR descriptions include:
   - Summary of changes
   - Link to sprint plan
   - Test coverage summary
   - Any known limitations or follow-up items
4. PRs are not merged until the `/retrospective` for that sprint is complete.
