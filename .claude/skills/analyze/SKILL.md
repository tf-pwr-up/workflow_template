---
name: analyze
description: "Deep Analysis & Documentation of a source codebase or spec."
---

# /analyze — Deep Analysis & Documentation

Trigger: User wants to analyze a source (codebase, requirements, specs) to build implementation documentation.

## Purpose

Produce a persistent documentation corpus in `docs/analysis/` that captures every feature area with enough detail to implement accurately — visual design, interactions, data flow, edge cases, and user-confirmed requirements.

This is the **first step** in the workflow. Everything else reads from this output.

## Usage

```
/analyze [source-path] [--area <feature-area>] [--ask]
```

- `source-path` — the source to analyze (codebase directory, spec folder, or document path)
- `--area <name>` — analyze only one area (e.g. "entity-editor", "auth", "dashboard")
- `--ask` — enable interactive Q&A mode (pause to ask user clarifying questions)

If no arguments provided and a reference implementation is defined in CLAUDE.md, analyze that.

## Instructions

### Step 0: Identify Source Type

Read the source path and classify it:

- **Codebase** — contains source files (`.ts`, `.tsx`, `.py`, `.go`, etc.), `package.json`, `Cargo.toml`, etc.
- **Spec/Requirements** — contains documents (`.md`, `.docx`, `.pdf`, `.txt`), wireframes, or design files
- **Mixed** — contains both code and documentation

This classification determines how each phase operates (see per-phase instructions below).

---

### Phase 1: Discovery (Structural Map)

Launch a Discovery Agent to produce a structural map of the source material.

**If source is a codebase:**
1. File tree — list all source files by directory, noting purpose of each
2. Route map — every URL route and what renders/handles each
3. API surface — every endpoint, method, request/response shapes
4. Data model — all types, interfaces, database schemas
5. Component tree — all UI components and their parent-child relationships
6. Store/state map — all state management (stores, hooks, context, signals)
7. External dependencies — third-party packages and what they're used for

**If source is specs/requirements:**
1. Document inventory — list all documents, noting scope and purpose of each
2. Feature map — every feature, capability, or user story described
3. Data entities — any data models, schemas, or domain objects mentioned
4. User roles — every actor, persona, or role described
5. Integrations — any external systems, APIs, or services referenced
6. Constraints — performance, security, compliance, or platform constraints stated
7. Terminology — domain-specific terms and definitions

**If mixed:** Combine both approaches — use code as ground truth, specs as intent.

Output: Write `docs/analysis/00-structure.md` with the complete structural map.

**Update CLAUDE.md**: After writing the structural map, update the Project Configuration section of `CLAUDE.md`:
- **Stack** — runtime, frameworks, database, frontend, testing, build tools discovered
- **Directory Structure** — key directories and their purposes
- **Commands** — dev server, test, lint, type check commands found in package.json/Makefile/etc.
- **Reference Implementation** — if analyzing a reference, record its path

Use the Edit tool to replace the HTML comment placeholders with actual content. Preserve the section headers.

---

### Phase 2: Feature Decomposition

From the structural map, identify distinct feature areas. Launch parallel Analysis Agents (up to 5 at a time) for each area. Each agent must:

**If source is a codebase:**
1. Read every file relevant to this feature area
2. Document user-visible behaviour — step-by-step flows of what the user sees and does
3. Document visual design — exact CSS classes, color tokens, spacing, responsive breakpoints, animations, hover states, dark mode. Include literal class strings.
4. Document data flow — API calls, state management, component props, transforms
5. Document interactions — click handlers, keyboard shortcuts, form validation, loading states, error states, empty states
6. Document edge cases — missing data, network failures, 0 items vs 1000, permission boundaries, concurrent edits
7. List every prop/parameter for key components and functions

**If source is specs/requirements:**
1. Read every document relevant to this feature area
2. Document user-visible behaviour — step-by-step flows described or implied
3. Document visual design — any mockups, wireframes, or design specs referenced
4. Document data flow — data entities, transformations, and rules described
5. Document interactions — user actions, system responses, validation rules
6. Document edge cases — explicitly stated AND infer obvious ones the spec omits
7. List every acceptance criteria, business rule, or constraint

**Regardless of source type**, flag anything that is:
- **Ambiguous** — could be interpreted multiple ways
- **Incomplete** — behaviour not fully described
- **Contradictory** — conflicts with another part of the source material

Output: Write `docs/analysis/NN-<area-name>.md` for each area.

---

### Phase 3: Cross-Cutting Concerns

Launch agents for concerns that span feature areas:

1. **Design System Agent** — extract the complete design vocabulary:
   - If from code: every CSS utility/shortcut, color palette (hex, HSL, CSS vars), typography scale, spacing system, shadow/elevation scale, border radius, animation library, icon system, dark mode strategy, responsive breakpoints, component styling patterns
   - If from specs: any brand guidelines, color requirements, typography preferences, responsive requirements, accessibility standards, design tokens

2. **Pattern Agent** — extract recurring implementation patterns:
   - If from code: form patterns, loading/error/empty states, pagination, modals/dialogs, auth checks, data fetching/caching, component composition, real-time data handling
   - If from specs: common workflows, shared UI patterns, cross-feature behaviours, standard response patterns, error handling requirements

Output: Write `docs/analysis/90-design-system.md` and `docs/analysis/91-patterns.md`.

**Update CLAUDE.md**: After writing cross-cutting docs, update the Project Configuration section:
- **Design System** — CSS framework, config file, fonts, color tokens, shortcuts, icons, dark mode, responsive strategy
- **Established Patterns** — recurring code patterns discovered (route factory, service layer, DI, auth, error handling, test infrastructure, etc.)
- **Data Model Conventions** — data format, response conventions, state management approach
- **Coding Conventions** — language mode, import style, file organization preferences

Use the Edit tool to replace or append to existing content. Do not overwrite previously populated sections — merge new information.

---

### Phase 4: User Q&A (if --ask flag or gaps detected)

After analysis, present questions to the user grouped by category:

**Requirements questions** (things the source can't tell us):
- "The source describes feature X — do you want this? Priority?"
- "There are two approaches for Y — which do you prefer?"
- "Feature Z requires [external service] — do you have access / want alternative?"

**Architecture questions:**
- "The source uses/implies [framework/library] — keep it or consider alternatives?"
- "What database/storage approach do you want?"
- "What are your deployment constraints?"

**Scope questions:**
- "Which feature areas are must-have vs nice-to-have vs out-of-scope?"
- "Some features require major effort (e.g. offline-first). Include or defer?"

**Design questions:**
- "The source uses/specifies [visual pattern] — keep it or change?"
- "Mobile support — what level of priority?"

Record all answers in `docs/analysis/99-decisions.md`.

---

### Phase 5: Business Analysis Review (ITERATIVE)

This phase is **critical** and runs iteratively until the corpus reaches sufficient quality.

Launch a **BA Review Agent** that acts as a senior product/business analyst. This agent:

1. **Reads the entire `docs/analysis/` corpus** produced so far
2. **Evaluates completeness** against a checklist:
   - Are all user roles and their permissions clearly defined?
   - Is every user journey documented end-to-end (not just the happy path)?
   - Are all state transitions explicit (e.g. draft → pending → published)?
   - Are validation rules concrete (not vague "must be valid")?
   - Are error scenarios documented with expected system behaviour?
   - Are data relationships and cardinality specified?
   - Are non-functional requirements stated (performance, scale, accessibility)?
   - Are integration points fully described (auth flows, API contracts, webhooks)?
   - Are there any features referenced but never fully described?
   - Are edge cases covered for every feature (empty, overflow, concurrent, offline)?
3. **Cross-references** feature docs against each other — does feature A's description of a shared entity match feature B's description?
4. **Identifies gaps** and produces a structured report:

```
## BA Review — Round N

### GAPS (must resolve before proceeding)
- [AREA: entity-editor] No description of what happens when a required field is left empty
- [AREA: auth] Token expiry time not specified

### AMBIGUITIES (need clarification)
- [AREA: workflow] "Approval" mentioned but approver role not defined
- [AREA: types] Can field order be changed after entities exist?

### CONTRADICTIONS
- [AREA: permissions] 00-structure says 3 roles, 04-permissions says 4

### SUGGESTIONS (would improve the spec)
- [AREA: search] Consider documenting search ranking/relevance logic
```

5. **Resolution loop:**
   - If gaps can be resolved from the source material: re-read the source, update the relevant analysis doc, and note what was added
   - If gaps require user input: present questions to the user (same format as Phase 4), record answers in `99-decisions.md`, and update relevant analysis docs
   - If gaps are inferred from domain knowledge: document the assumption explicitly and mark it `[ASSUMED]` so the user can confirm or override

6. **Repeat** phases 5.1–5.5 until:
   - No GAPS or CONTRADICTIONS remain
   - All AMBIGUITIES are either resolved or explicitly marked as deferred
   - The BA Review Agent signs off: `"Corpus is implementation-ready"`
   - Maximum 3 review rounds (to avoid infinite loops — escalate remaining items to user)

Output: Append review log to `docs/analysis/96-ba-review.md` (one section per round).

---

### Phase 6: Implementation Checklists

From the analysis docs (now BA-reviewed), generate atomic implementation checklists:

For each feature area, produce a checklist where each item is:
- A single, testable unit of work
- Tagged with: [backend], [frontend], [test], [style], [infra]
- Ordered by dependency (what must be built first)
- Estimated as: trivial / small / medium / large
- Grouped into implementation phases

Output: Write `docs/analysis/95-checklists.md`.

---

### Phase 7: Summary & Index

Write `docs/analysis/00-index.md` with:
- Table of contents linking to all analysis docs
- High-level feature summary
- Key architectural observations (what the source does well, what's complex)
- Recommended implementation order with rationale
- Total estimated scope by phase
- BA review status and any deferred items

---

## Output Format

Each analysis file follows this structure:

```markdown
# Feature: <Name>

## Summary
One paragraph describing what this feature does.

## User-Visible Behaviour
Step-by-step description of what the user sees and does.

## Visual Design
Exact CSS classes, colors, spacing, animations (if from code).
Design requirements and constraints (if from specs).
Include literal values wherever possible.

## Data Flow
API calls → state management → component rendering.
Include request/response shapes and data models.

## Interactions
Event handlers, keyboard shortcuts, validation rules.
Include specific values, timings, constraints.

## Edge Cases
Empty states, errors, loading, permission boundaries, large datasets.

## Key Files (Reference)
List of files in the source material with brief purpose notes.

## Open Questions [ASSUMED]
Any assumptions made during analysis, pending user confirmation.

## Implementation Checklist
- [ ] Item 1 [backend] (small)
- [ ] Item 2 [frontend] (medium)
- [ ] Item 3 [test] (small)
```

## Integration with Workflow

After `/analyze` completes, the workflow changes:

1. **Phase 0** becomes: "Read `docs/analysis/` + check current implementation against checklists"
2. **Plan Agent** receives concrete checklists instead of vague feature names
3. **Spec Compliance Agent** checks against analysis docs instead of re-reading reference code
4. **No more on-the-fly reference reading** during implementation — everything needed is in the analysis corpus

## Updating the Corpus

Run `/analyze --area <name>` to update a specific section. The skill will read the existing analysis doc and update it based on current state of the source material.

The BA Review (Phase 5) runs again on updated sections to verify completeness.
