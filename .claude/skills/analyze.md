# /analyze — Deep Codebase Analysis & Documentation

Trigger: User wants to deeply analyze a codebase (reference or own) to build implementation documentation.

## Purpose

Produce a persistent documentation corpus in `docs/analysis/` that captures every feature area with enough detail to implement accurately — visual design, interactions, data flow, edge cases, and user-confirmed requirements.

This replaces shallow on-the-fly Phase 0 inventories with a one-time deep analysis whose output persists across sessions.

## Usage

```
/analyze <codebase-path> [--area <feature-area>] [--ask]
```

- `<codebase-path>` — the codebase to analyze (or omit to use the reference defined in CLAUDE.md)
- `--area <feature-area>` — optional, analyze only one area (e.g. "entity-editor", "auth", "dashboard")
- `--ask` — enable interactive Q&A mode (pause to ask user clarifying questions)

If no arguments provided and a reference implementation is defined in CLAUDE.md, analyze that.

## Instructions

### Phase 1: Discovery (Structural Map)

Launch a Discovery Agent to produce a structural map of the codebase:

1. **File tree** — list all source files by directory, noting purpose of each
2. **Route map** — every URL route and what renders at each
3. **API surface** — every endpoint, method, request/response shapes
4. **Data model** — all types, interfaces, database schemas
5. **Component tree** — all UI components and their parent-child relationships
6. **Store/state map** — all state management (signals, stores, hooks, context, reducers)
7. **External dependencies** — third-party packages and what they're used for

Output: Write `docs/analysis/00-structure.md` with the complete structural map.

### Phase 2: Feature Decomposition

From the structural map, identify distinct feature areas. Common areas include (adapt to the actual codebase):

- Authentication & sessions
- Core entity CRUD & lifecycle
- Configuration & settings
- Field types & rendering
- Workflow & state transitions
- Comments & collaboration
- File management
- Search & navigation
- Dashboard & homepage
- Admin panel
- Design system & styling
- Real-time features
- Public access & SEO
- Import/export

Launch parallel Analysis Agents (up to 5 at a time) for each area. Each agent must:

1. **Read every file** relevant to this feature area (components, routes, services, tests, styles)
2. **Document user-visible behaviour** — what does the user see and do? Step-by-step flows.
3. **Document visual design** — exact CSS classes, color tokens, spacing, responsive breakpoints, animations, hover states, dark mode treatment. Include specific class strings, not descriptions.
4. **Document data flow** — what API calls, what state updates, what renders when
5. **Document interactions** — click handlers, keyboard shortcuts, form validation, loading states, error states, empty states, optimistic updates
6. **Document edge cases** — what happens when data is missing, when the network fails, when there are 0 items vs 1000 items, permission boundaries
7. **List every prop/parameter** for key components and functions

Output: Write `docs/analysis/NN-<area-name>.md` for each area (numbered for ordering).

### Phase 3: Cross-Cutting Concerns

Launch agents for concerns that span feature areas:

1. **Design System Agent** — extract the complete design vocabulary:
   - Every CSS utility class and shortcut
   - Color palette with exact values
   - Typography scale (sizes, weights, line heights)
   - Spacing system
   - Shadow scale
   - Border radius system
   - Animation/transition library
   - Icon usage patterns
   - Dark mode strategy
   - Responsive breakpoints and mobile patterns

2. **Pattern Agent** — extract recurring implementation patterns:
   - How are forms built?
   - How is loading/error/empty state handled?
   - How are lists paginated?
   - How are modals/dialogs shown?
   - How is authentication checked?
   - What's the component composition pattern?

Output: Write `docs/analysis/90-design-system.md` and `docs/analysis/91-patterns.md`.

### Phase 4: User Q&A (if --ask or gaps detected)

After analysis, present questions to the user grouped by category:

**Requirements questions** (things code can't tell us):
- "The reference has feature X — do you want this? Is it a priority?"
- "There are two patterns for Y — which do you prefer?"
- "Feature Z uses [external service] — do you have an account / want an alternative?"

**Scope questions:**
- "The reference has N feature areas. Which are must-have vs nice-to-have?"
- "Some features require major architectural changes. Include or defer?"

**Design questions:**
- "The reference uses [specific visual pattern] for X — keep it or change?"
- "Mobile layout does [thing] — is mobile support a priority?"

Record all answers in `docs/analysis/99-decisions.md`.

### Phase 5: Implementation Checklists

From the analysis docs, generate atomic implementation checklists:

For each feature area, produce a checklist where each item is:
- A single, testable unit of work
- Tagged with: [backend], [frontend], [test], [style]
- Ordered by dependency (what must be built first)
- Estimated as: trivial / small / medium / large

Output: Write `docs/analysis/95-checklists.md`.

### Phase 6: Summary & Index

Write `docs/analysis/00-index.md` with:
- Table of contents linking to all analysis docs
- High-level feature parity scorecard (if comparing to reference)
- Key architectural decisions
- Recommended implementation order
- Total estimated scope

## Output Format

Each analysis file follows this structure:

```markdown
# Feature: <Name>

## Summary
One paragraph describing what this feature does.

## User-Visible Behaviour
Step-by-step description of what the user sees and does.

## Visual Design
Exact CSS classes, colors, spacing, animations. Include literal class strings.

## Data Flow
API calls, state management, component props.

## Interactions
Event handlers, keyboard shortcuts, validation.

## Edge Cases
Empty states, errors, loading, permission boundaries, large datasets.

## Key Files (Reference)
List of files in the analyzed codebase with line-level notes.

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

If the reference codebase changes, run `/analyze` again with `--area` to update specific sections. The skill will diff against existing analysis docs and update only what changed.
