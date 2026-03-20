---
name: analyze
description: "High-level business analysis — establishes requirements through structured questioning and council review"
---

# /analyze — High-Level Business Analysis

## Purpose

Establish what needs to be built through structured business analysis questioning. This skill can run for the whole project (initial analysis) or for a new major feature (incremental analysis). The output is a set of requirements broken into proposed sprints, reviewed and approved by the council of experts.

## Prerequisites (BLOCKING)

Before executing ANY step in this skill, verify:

1. **`council-config.json` must exist** in the project root.
   - If missing: STOP. Tell the user: "Council configuration not found. Run `/setup` first to configure the project."
   - Do NOT proceed. Do NOT offer to create it manually.

2. **`docs/requirements/` directory must exist.**
   - If missing but `council-config.json` exists: create the directory structure (setup may have been partially completed).

3. **Read `council-config.json`** and load the project context (name, type, domain, language, architecture pattern). This context informs all BA questioning.

---

## Execution Steps

### Step 1 — Scope Determination

**Q1: Analysis Scope**
```
AskUserQuestion(
  question: "Is this analysis for the whole project or for a new feature/module?",
  options: ["Whole project — initial requirements gathering", "New feature — adding to existing requirements"]
)
```

**If "New feature":**
- Check `docs/requirements/00-index.md` for existing requirement areas.
- If areas exist, present them:
  ```
  AskUserQuestion(
    question: "Which area does this feature relate to? Select an existing area or choose 'New area'.",
    options: [<existing areas from index>, "New area"]
  )
  ```
- If "New area" or no index exists:
  ```
  AskUserQuestion(
    question: "Briefly describe the area or name for this feature set (e.g., 'user-authentication', 'payment-processing', 'notification-system')."
  )
  ```

Record the scope and area for use in subsequent steps.

### Step 2 — BA Questioning

Spawn a Business Analysis agent using the system prompt below. The BA agent conducts structured questioning via `AskUserQuestion`, one question at a time, adapting based on previous answers.

#### BA Agent System Prompt

```
You are a senior Business Analyst with 15 years of experience gathering requirements for software projects. Your role is to extract complete, unambiguous, testable requirements from the project stakeholder through structured questioning.

CONTEXT:
- Project type: [FROM council-config.json project.type]
- Domain: [FROM council-config.json project.domain]
- Language/Framework: [FROM council-config.json project.language]
- Architecture: [FROM council-config.json project.architecture]
- Broad requirement: [FROM setup answers or user input]

METHODOLOGY:
You follow a systematic elicitation process. For each area, you ask targeted questions, listen carefully to answers, and probe deeper where ambiguity exists. You NEVER assume requirements — you always confirm.

QUESTIONING SEQUENCE:
1. **Actors & Personas** — Who are the users? What are their roles, permissions, and goals? Are there system actors (cron jobs, external services)?

2. **Core User Stories** — For each actor, what are the primary workflows? Use the format: "As a [role], I want to [action] so that [benefit]." Probe for the complete happy path first, then edge cases.

3. **Acceptance Criteria** — For each user story, define testable acceptance criteria. Use Given/When/Then format where appropriate. Ask: "How would you verify this works correctly?"

4. **Data Entities & Relationships** — What are the core data objects? What are their attributes? How do they relate to each other? What are the cardinality constraints? Are there lifecycle states?

5. **Integration Points** — Does this interact with external systems, APIs, or services? What are the contracts? What happens when integrations fail? Are there rate limits, authentication requirements, or data format constraints?

6. **Non-Functional Requirements** — What are the performance expectations (response times, throughput)? Availability requirements? Data retention policies? Scalability targets? Accessibility standards?

7. **Edge Cases & Error Scenarios** — What happens when things go wrong? Invalid input, network failures, partial failures, concurrent modifications, data inconsistencies? What are the recovery strategies?

8. **Dependencies & Constraints** — Are there technical constraints (must use specific database, must run on specific infrastructure)? Time constraints? Budget constraints? Regulatory constraints? Backward compatibility requirements?

9. **Out of Scope** — Explicitly confirm what is NOT included to prevent scope creep.

RULES:
- Ask ONE question at a time using AskUserQuestion.
- After each answer, acknowledge what you understood and probe if anything is unclear.
- Adapt your questions based on previous answers — skip irrelevant areas, dive deeper into complex ones.
- When you have gathered sufficient information for a complete requirements document, announce that you are moving to documentation.
- If the user says "that's all" or "move on" for a section, respect it but note any gaps.
- Track which areas have been covered and which remain.
- For each requirement, mentally assess: Is it Specific? Measurable? Achievable? Relevant? Testable?
```

**Questioning process:**
1. Begin with Actors & Personas.
2. Progress through each area in the sequence above.
3. After completing all areas (or when the user indicates sufficient information), summarise what was gathered and ask for confirmation before proceeding.
4. Track any areas the user skipped or answered minimally — these become noted gaps.

### Step 3 — Requirements Documentation

Write requirements to `docs/requirements/NN-<area>.md` where `NN` is a zero-padded sequence number.

**File format:**

```markdown
# <Area Name> Requirements

**ID:** REQ-<NN>
**Status:** Draft
**Created:** <date>
**Scope:** <whole-project | feature-name>

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| ... | Human/System | ... |

## User Stories

### US-<NN>.1: <Story Title>

**As a** <role>, **I want to** <action>, **so that** <benefit>.

**Acceptance Criteria:**
- [ ] **AC-<NN>.1.1:** Given <context>, when <action>, then <result>
- [ ] **AC-<NN>.1.2:** ...

**Priority:** <Must Have | Should Have | Could Have | Won't Have>
**Complexity:** <S | M | L>

### US-<NN>.2: <Story Title>
...

## Data Model

### <Entity Name>
| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| ... | ... | ... | ... |

**Relationships:**
- <Entity A> has many <Entity B>
- ...

## Integration Points

| System | Direction | Protocol | Auth | Error Handling |
|--------|-----------|----------|------|----------------|
| ... | Inbound/Outbound | REST/gRPC/Event | ... | ... |

## Non-Functional Requirements

| ID | Category | Requirement | Metric |
|----|----------|-------------|--------|
| NFR-<NN>.1 | Performance | ... | ... |
| NFR-<NN>.2 | Availability | ... | ... |

## Edge Cases & Error Scenarios

| ID | Scenario | Expected Behaviour | Recovery |
|----|----------|--------------------|----------|
| EC-<NN>.1 | ... | ... | ... |

## Constraints

- ...

## Out of Scope

- ...

## Open Questions / Gaps

- [ ] ...
```

**Update `docs/requirements/00-index.md`:**

```markdown
# Requirements Index

| ID | Area | Status | Sprints | Last Updated |
|----|------|--------|---------|--------------|
| REQ-01 | <area> | Draft | - | <date> |
| ... | ... | ... | ... | ... |
```

### Step 4 — Sprint Breakdown

Write to `docs/requirements/proposed-sprints.md`.

Analyse the requirements and break them into sprints based on:
- **Dependency ordering** — foundational work first (data models, auth, core entities)
- **Business value** — highest-value features early
- **Risk reduction** — tackle unknowns and integrations early
- **Logical grouping** — related stories together
- **Size constraints** — each sprint should be achievable in 1-2 weeks of work

**File format:**

```markdown
# Proposed Sprint Breakdown

**Project:** <project-name>
**Total Sprints:** <N>
**Status:** Pending Council Review
**Approved:** No

## Sprint 1: <Goal>

**Goal:** <one-sentence goal>
**Complexity:** <S | M | L>
**Dependencies:** None (foundation sprint)

**Deliverables:**
- [ ] <deliverable 1> (from US-<NN>.<X>)
- [ ] <deliverable 2> (from US-<NN>.<Y>)
- ...

**Exit Criteria:**
- [ ] <testable criterion 1>
- [ ] <testable criterion 2>
- ...

**Notes:** <any context about why these items are grouped or ordered this way>

---

## Sprint 2: <Goal>

**Goal:** <one-sentence goal>
**Complexity:** <S | M | L>
**Dependencies:** Sprint 1

**Deliverables:**
- [ ] ...

**Exit Criteria:**
- [ ] ...

---

... (repeat for all sprints)

## Dependency Graph

```text
Sprint 1 (Foundation)
  |
  +---> Sprint 2 (Core Feature A)
  |       |
  |       +---> Sprint 4 (Feature A Extensions)
  |
  +---> Sprint 3 (Core Feature B)
          |
          +---> Sprint 5 (Integration)
```

## Risk Assessment

| Sprint | Risk | Mitigation |
|--------|------|------------|
| ... | ... | ... |
```

### Step 5 — Council Review

This is a HIGH-LEVEL review. The council reviews requirements completeness and sprint planning quality — NOT code.

**Dispatch the council:**

```bash
./scripts/council-dispatch.py analyze 0 "<project-name>"
```

The `0` indicates this is round 0 (first review). The dispatch script reads `council-config.json` and invokes each council member for the `analyze` phase in the configured order.

**Council members active in the analyze phase:**

| Order | Member | Review Focus |
|-------|--------|-------------|
| 1 | Architecture | Sprint boundaries respect architectural layers. Dependencies are correctly ordered. No circular dependencies. Proposed architecture can support all requirements. |
| 2 | Spec Compliance | Every user story has testable acceptance criteria. No ambiguous requirements. No contradictions between requirements. All actors are covered. |
| 3 | Security | Security-sensitive requirements are identified. Auth/authz requirements are complete. Data handling requirements address sensitivity. Threat surface is understood. |
| 4 | Domain Expert | Domain terminology is used correctly. Domain-specific edge cases are captured. Standards compliance is addressed in requirements. Business rules are complete. |
| 5 | Arbitrator | Synthesises all findings. Produces final verdict: APPROVE, REVISE, or REJECT. |

**Each member receives:**
- The full contents of `docs/requirements/` (all requirement files)
- The `docs/requirements/proposed-sprints.md` file
- Their specific lens prompt from `council-config.json`
- The project context (type, domain, language, architecture)

**Findings are written to:** `docs/findings/analyze-findings.md`

**Findings format:**

```markdown
# Analysis Phase — Council Findings

**Round:** <N>
**Date:** <date>
**Verdict:** <APPROVE | REVISE | REJECT>

## Architecture Review
- [ARCH-1] <severity> — <finding>
- [ARCH-2] <severity> — <finding>

## Spec Compliance Review
- [SPEC-1] <severity> — <finding>
- [SPEC-2] <severity> — <finding>

## Security Review
- [SEC-1] <severity> — <finding>
- [SEC-2] <severity> — <finding>

## Domain Expert Review
- [DOM-1] <severity> — <finding>
- [DOM-2] <severity> — <finding>

## Arbitrator Assessment

### Convergence Points
- ...

### Divergence Points
- ...

### Gaps Identified
- ...

### Required Changes (for REVISE)
1. ...
2. ...

### Verdict: <APPROVE | REVISE | REJECT>
<reasoning>
```

**Present findings to the user:**
After the council completes, display:
1. The arbitrator's verdict
2. A summary of findings grouped by severity (Critical > High > Medium > Low)
3. The number of required changes (if REVISE)

### Step 6 — Iteration

If the verdict is **REVISE**:

1. Present the required changes to the user.
2. Ask the user how they want to proceed:
   ```
   AskUserQuestion(
     question: "The council recommends revisions. How would you like to proceed?",
     options: ["Address all findings — update requirements and re-submit", "Address selected findings — let me choose which ones", "Override — approve as-is with noted exceptions", "Discuss — I have questions about the findings"]
   )
   ```

3. If addressing findings:
   - Walk through each required change
   - Update the requirements documents
   - Update the sprint breakdown if needed
   - Re-submit to council: `./scripts/council-dispatch.py analyze <round> "<project-name>"`
   - Increment the round number

4. **Convergence guardrails:**
   - Track the current round number against `convergence.max_analyze_rounds` from `council-config.json`
   - At `convergence.convergence_warning_at` rounds, warn the user: "This analysis has gone through N review rounds. Consider approving with noted exceptions to avoid analysis paralysis."
   - At `convergence.max_analyze_rounds`, force a decision: approve as-is, approve with exceptions, or escalate.

5. **Findings tracker:**
   - Maintain a running tally in `docs/findings/analyze-findings.md`
   - Each round's findings are appended (not overwritten)
   - Track which findings from previous rounds have been addressed
   - Format: `[ADDRESSED]` or `[OPEN]` prefix on each finding

If the verdict is **REJECT**:
- Present the fundamental problems identified
- These typically indicate the requirements need significant rework
- Guide the user back through the BA questioning for the problematic areas
- This counts as a new round

If the verdict is **APPROVE**:
- Proceed directly to Step 7

### Step 7 — Approval Gate

Once the council approves (or the user overrides):

1. **Mark requirements as approved:**
   Update the status in each requirements file from `Draft` to `Approved`.

2. **Mark sprint breakdown as approved:**
   Update `docs/requirements/proposed-sprints.md`:
   ```markdown
   **Approved:** Yes
   **Approved Date:** <date>
   **Approval Type:** <Council Approved | User Override>
   **Council Rounds:** <N>
   **Open Exceptions:** <count or "None">
   ```

3. **Update the requirements index:**
   Update `docs/requirements/00-index.md` with current statuses and sprint assignments.

4. **Archive findings:**
   Copy the final `docs/findings/analyze-findings.md` to `docs/archive/analyze-findings-<date>.md`.

5. **Present summary to user:**
   ```
   Analysis complete.
   - Requirements: <N> areas documented
   - User stories: <N> total
   - Sprints: <N> proposed
   - Council rounds: <N>
   - Open exceptions: <N or "None">

   Next step: Run `/sprint` to begin planning Sprint 1.
   ```

---

## Maintenance

This skill may be re-invoked in two scenarios:

1. **New feature analysis** — When adding a major feature to an existing project. The new requirements are added alongside existing ones, and sprint breakdown is updated.

2. **Post-retrospective revision** — After `/retrospective` identifies requirement gaps or changes. The retrospective skill may recommend re-running `/analyze` for specific areas.

When re-invoked:
- Existing approved requirements are NOT modified unless explicitly requested
- New requirements get the next sequence number
- Sprint breakdown is updated to integrate new work with remaining sprints
- Council review covers only the new/changed requirements

---

## Enforcement

- The `/sprint` skill checks for the presence of `**Approved:** Yes` in `docs/requirements/proposed-sprints.md` before proceeding.
- If not found, it directs the user to run `/analyze` first.
- The approval marker serves as the gate between analysis and sprint planning.
