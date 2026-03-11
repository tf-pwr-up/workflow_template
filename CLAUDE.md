# CLAUDE.md — Project Instructions

This file combines generic workflow rules with project-specific configuration.

- **Workflow rules**: See `.claude/workflow-rules.md` (synced with upstream template — do not add project-specific content there)
- **Skills**: See `.claude/skills/*.md` (synced with upstream template)
- **Project config**: Below (project-specific, auto-populated by skills)

Read `.claude/workflow-rules.md` for the full multi-agent workflow that governs all code changes.

---

## Project Configuration

> **This section is populated automatically by workflow skills.** It starts empty for new projects and accumulates project-specific knowledge as skills run. Skills that update this section:
>
> - `/analyze` → Stack, Directory Structure, Design System, Established Patterns (from Phase 1-3)
> - `/plan` → Architecture Decisions, Established Patterns (from review agent feedback)
> - `/implement` → Commands, Test File Conventions, Coding Conventions (discovered during integration checks)
> - `/postmortem` → Bug Patterns (appended when bugs are found)
>
> **Do not delete existing entries** — only add or update. This section is cumulative project memory.

### Project Description

<!-- Updated by: /analyze Phase 7, or manually by user -->

### Reference Implementation

<!-- Updated by: /analyze Step 0, or manually by user -->
<!-- Format:
Path: `/path/to/reference` (READ-ONLY — never modify)
-->

### Stack

<!-- Updated by: /analyze Phase 1 (Discovery) -->

### Commands

<!-- Updated by: /implement Step 4 (Integration Check), /e2e -->
<!-- Format:
- **Dev servers**: `command` (ports)
- **Type check**: `command`
- **Unit tests**: `command`
- **E2E tests**: `command`
- **Lint**: `command`
- **Health checks**: URLs
-->

### Directory Structure

<!-- Updated by: /analyze Phase 1 (Discovery) -->

### Test File Conventions

<!-- Updated by: /implement Step 2 (Test Agent), /plan (Testability Agent) -->

### Established Patterns

<!-- Updated by: /analyze Phase 3 (Patterns), /plan (Architecture Agent), /implement (as patterns emerge) -->
<!-- Format:
- **Pattern name**: description with code signature
-->

### Data Model Conventions

<!-- Updated by: /analyze Phase 2 (Feature Decomposition), /plan (Architecture Agent) -->

### Design System

<!-- Updated by: /analyze Phase 3 (Design System Agent), /ui-review -->

### Coding Conventions

<!-- Updated by: /plan (Architecture Agent), /review (Architecture Agent) -->

### Bug Patterns

<!-- Updated by: /postmortem Step 6 — links to docs/bug-patterns.md for full details -->
<!-- Format:
See `docs/bug-patterns.md` for the full registry. Key patterns to watch for:
- Pattern 1: brief description
- Pattern 2: brief description
-->
