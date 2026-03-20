# Workflow Template

A reusable workflow template for [Claude Code](https://claude.com/claude-code) that enforces a gated, multi-agent development pipeline. Every code change flows through setup, business analysis, planning with council review, implementation with parallel agents, and retrospective improvement.

The workflow distributes expert review across multiple AI platforms (Codex CLI, Google Gemini, Anthropic Claude API, OpenAI) so that no single model reviews its own output. A council of specialists -- security, architecture, testing, spec compliance, domain expertise -- reviews plans and code at every stage gate, with an arbitrator synthesising findings and filtering noise.

Clone this template into any software project to bootstrap a structured, repeatable development process from day one.

---

## Quick Start

### Option A: Clone into your project

Copy the workflow files into an existing project:

```bash
git clone https://github.com/<org>/workflow.git /tmp/wf
cp -r /tmp/wf/.claude your-project/.claude
cp -r /tmp/wf/scripts your-project/scripts
cp /tmp/wf/CLAUDE.md your-project/CLAUDE.md
mkdir -p your-project/docs
cp /tmp/wf/docs/bug-patterns.md your-project/docs/
cp -r /tmp/wf/.github your-project/.github
rm -rf /tmp/wf
```

### Option B: Git remote with sync (recommended)

Use a git remote so you can pull template updates over time:

```bash
mkdir your-project && cd your-project && git init
git remote add workflow https://github.com/<org>/workflow.git
git fetch workflow
git merge workflow/main --allow-unrelated-histories
git remote add origin git@github.com:your-org/your-project.git
git push -u origin main
```

This approach enables `/sync pull` and `/sync push` to keep your project's workflow files aligned with the template as it evolves.

### Team Onboarding

1. Clone the project repo.
2. Run `scripts/council-check.sh` to verify platform access and API connectivity.
3. Set up API keys in `~/.zprofile` (or your shell profile):
   ```bash
   export GOOGLE_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   export OPENAI_API_KEY="your-key"
   ```
4. Run `codex login` to authenticate the Codex CLI.
5. Run `/setup` for new projects, or `/sprint <N>` to join a project mid-flight.

---

## The Pipeline

```
/setup --> /analyze --> [/sprint <N> --> /develop <N> --> /retrospective <N>] (repeat)
                              ^
                         /review (anytime)
```

Each phase produces artefacts that gate entry to the next phase. No phase can begin until its predecessor's gate conditions are met.

| Phase | Gate Output | Required Before |
|-------|-------------|-----------------|
| `/setup` | Populated `CLAUDE.md` and `council-config.json` | `/analyze` |
| `/analyze` | Requirements doc with prioritised findings from actual codebase reading | `/sprint` |
| `/sprint <N>` | Sprint plan with task breakdown, acceptance criteria, and test specifications | `/develop <N>` |
| `/develop <N>` | All code written, all tests passing, E2E verified, full suite green | `/retrospective <N>` |
| `/retrospective <N>` | Retrospective complete, bug patterns logged, workflow changes synced | Next `/sprint <N+1>` |

If a gate's artefacts are missing or incomplete, the entering skill halts and reports what is missing rather than proceeding with assumptions. `/review` is the exception -- it can be invoked at any time during development without blocking other phases.

---

## Skills Reference

| Skill | Description |
|-------|-------------|
| `/setup` | Interactive project setup. Bootstraps the workflow through guided questioning -- establishes project identity, stack, architecture patterns, and configures the council of experts. Produces `CLAUDE.md` and `council-config.json`. |
| `/analyze` | High-level business analysis. Establishes what needs to be built through structured BA questioning, producing requirements broken into proposed sprints, reviewed and approved by the council. |
| `/sprint <N>` | Sprint planning and council review. Produces a comprehensive, council-reviewed implementation plan with task breakdown, acceptance criteria, gap analysis, and test specifications. No code is written in this phase. |
| `/develop <N>` | Development and testing with parallel agents. Orchestrates Code Agents (implementation), Test Agents (specs-first testing), and Fix Agents (failure resolution). Runs unit tests, E2E tests, and the full suite before completion. |
| `/retrospective <N>` | Sprint retrospective and workflow improvement. Examines the review process, logs bug patterns to `docs/bug-patterns.md`, updates `CLAUDE.md` with established patterns, and syncs workflow changes back to the template. |
| `/review` | Standalone code review. Runs the council review process against uncommitted changes, specific files, or work-in-progress code outside the normal sprint cycle. |
| `/council-review` | Council of experts review (invoked by other skills, not directly). Orchestrates multi-platform expert review with arbitration, findings tracking, and convergence logic. Delegates mechanical dispatch to `scripts/council-dispatch.py`. |
| `/sync` | Bidirectional template sync. `/sync pull` updates project workflow files from the template. `/sync push` pushes project improvements back. `/sync status` reports the current sync state. |

---

## Council of Experts

The council is a multi-platform review system that provides independent expert assessment at every stage gate. Reviews are dispatched to external AI platforms in parallel so that no single model reviews its own output.

### Council Composition

**6 core members** (always active):

| Role | Review Lens |
|------|-------------|
| Security Reviewer | Vulnerabilities, auth, data exposure, injection, secrets handling |
| Architecture Reviewer | Structural soundness, separation of concerns, scalability, patterns |
| Spec Compliance Reviewer | Adherence to requirements, acceptance criteria, completeness |
| Testing Reviewer | Test coverage, edge cases, test quality, missing scenarios |
| Domain Expert | Business logic correctness, domain invariants, terminology |
| Arbitrator | Synthesises all findings, resolves contradictions, filters scope creep and nitpicking, assigns final priority |

**3 optional members** (activated per project via `/setup`):

| Role | Review Lens |
|------|-------------|
| Performance Reviewer | Latency, throughput, resource usage, algorithmic complexity |
| UX/DX Reviewer | Developer experience, API ergonomics, user-facing quality |
| Cost Reviewer | Infrastructure cost, API call volume, resource efficiency |

### How It Works

1. Review materials are gathered and secrets are redacted.
2. All regular council members receive the materials and review in parallel, each through their specific lens.
3. The **Arbitrator** runs last, receiving all other members' findings. It synthesises a consolidated assessment, resolves contradictions, flags scope creep or nitpicking, and assigns a final verdict.
4. Results are written to a **findings tracker** (`docs/findings/`) with per-member verdicts, severity counts, and detailed findings.
5. If the verdict is `CHANGES_REQUESTED`, findings feed back into the development loop for resolution.

### Convergence Guardrails

- Maximum **5 review rounds** per review type per sprint. If round 5 still yields `CHANGES_REQUESTED`, the review escalates for manual triage.
- A **quorum of 3** successful reviews is required for a valid verdict.
- Each member has a configurable **fallback platform** in case the primary fails. The dispatch script retries twice before falling back.

### Supported Platforms

| Platform | Auth Method | Models |
|----------|-------------|--------|
| Codex CLI | `codex login` | Default (auto) |
| Google Gemini | `GOOGLE_API_KEY` | gemini-2.5-pro, gemini-2.5-flash |
| Anthropic Claude | `ANTHROPIC_API_KEY` | claude-sonnet-4, claude-haiku |
| OpenAI | `OPENAI_API_KEY` | gpt-4o, o3 |

Council composition (which members use which platform) is configured in `council-config.json`, generated by `/setup`.

---

## File Architecture

```
.claude/
  settings.json              # Claude Code permissions (auto-generated)
  workflow-rules.md          # Enforcement rules, ground rules, bypass prevention
  skills/
    setup/SKILL.md           # /setup skill definition
    analyze/SKILL.md         # /analyze skill definition
    sprint/SKILL.md          # /sprint skill definition
    develop/SKILL.md         # /develop skill definition
    retrospective/SKILL.md   # /retrospective skill definition
    review/SKILL.md          # /review skill definition
    council-review/SKILL.md  # /council-review skill definition
    sync/SKILL.md            # /sync skill definition
.github/
  workflows/
    workflow-gate.yml        # CI gate — enforces reviews, plans, tests, sync
scripts/
  council-dispatch.py        # Mechanical API dispatch for council reviews
  council-check.sh           # Prerequisite checker (keys, connectivity, config)
docs/
  bug-patterns.md            # Bug pattern registry (updated by /retrospective)
  workflow-diagram.md        # Mermaid diagrams of all workflow flows
  requirements/              # (generated) Requirements from /analyze
  plans/                     # (generated) Sprint plans from /sprint
  gaps/                      # (generated) Gap analyses from /sprint
  findings/                  # (generated) Council findings trackers
  reviews/                   # (generated) Individual reviewer outputs
CLAUDE.md                    # Living project config (auto-populated by skills)
council-config.json          # (generated) Council composition from /setup
```

Directories marked `(generated)` are created by skills during execution. The template ships with the base structure; project-specific artefacts accumulate as the workflow runs.

---

## Team Consistency

The workflow is designed for multi-developer teams where every contributor runs the same structured process.

- **Git remote + `/sync`**: The template repo is added as a git remote. `/sync pull` brings in template updates; `/sync push` contributes improvements back. This keeps all projects on the same workflow version.
- **CI gate**: The GitHub Actions workflow (`workflow-gate.yml`) enforces that every PR to `main` has council review artefacts, an approved plan, a passing test suite, and no unapproved workflow file modifications.
- **Individual API keys**: Each developer configures their own API keys in `~/.zprofile`. Keys are never committed to the repo. The `council-check.sh` script verifies each developer's setup.
- **Workflow change tracking**: Any modification to tracked workflow files (skills, rules, scripts) during a sprint is flagged in the retrospective. Changes must either sync back to the template or be explicitly marked as project-specific overrides in `CLAUDE.md`.

---

## Upstream Sync

The `/sync` skill manages bidirectional synchronisation between your project and the workflow template.

| Command | What It Does |
|---------|-------------|
| `/sync pull` | Fetches the latest workflow files from the template repo and applies them to your project, preserving any documented project-specific overrides. |
| `/sync push` | Identifies workflow files you have modified locally, filters out project-specific overrides, and creates a PR against the template repo with your improvements. Requires GitHub CLI (`gh`). |
| `/sync status` | Compares all tracked workflow files against the template and reports which are in sync, which have local changes, and which have upstream updates available. |

Tracked files: `.claude/skills/**`, `.claude/workflow-rules.md`, `scripts/council-dispatch.py`, `scripts/council-check.sh`, `.github/workflows/workflow-gate.yml`.

---

## CI Gate

The GitHub Actions workflow (`.github/workflows/workflow-gate.yml`) runs on every pull request targeting `main` and enforces five checks:

1. **Review artefacts exist** -- At least one findings tracker must be present in `docs/findings/`.
2. **Plan exists** -- A sprint plan in `docs/plans/` or requirements doc in `docs/requirements/` must be present.
3. **Approved verdict** -- The most recent findings tracker must contain a `Verdict: APPROVED` line.
4. **Tests pass** -- The project's test suite must pass. The test command is auto-detected (npm test, pytest, go test, cargo test, make test) or can be set via the `TEST_COMMAND` repository variable.
5. **No unapproved workflow edits** -- If tracked workflow files are modified, they must be listed in a "Workflow Overrides" section of `CLAUDE.md` or have a corresponding sync PR on the template repo.

All five checks must pass for a PR to merge. Test runner setup (Node.js, Python) is handled automatically.

---

## Requirements

| Requirement | Purpose |
|-------------|---------|
| [Claude Code CLI](https://claude.com/claude-code) | Runs the workflow skills and orchestrates agents |
| Git | Version control, branch management, diff generation |
| [GitHub CLI](https://cli.github.com/) (`gh`) | Required for `/sync push` (creates PRs against the template repo) |
| Python 3 | Runs `scripts/council-dispatch.py` for council review dispatch |
| API keys for at least 2 platforms | Required to meet the quorum minimum of 3 successful reviews (Codex counts as one platform) |

---

## License

MIT
