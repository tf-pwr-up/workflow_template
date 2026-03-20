# Workflow Diagrams

Visual reference for the workflow pipeline, review process, development phase, and team sync flow.

---

## 1. Complete Pipeline Flow

The end-to-end workflow from project setup through iterative sprint delivery.

```mermaid
flowchart TD
    Start([Project Start]) --> Setup["/setup\n- Scan codebase\n- Populate CLAUDE.md\n- Configure stack"]

    Setup --> SetupGate{CLAUDE.md\npopulated?}
    SetupGate -->|No| Setup
    SetupGate -->|Yes| Analyze

    Analyze["/analyze\n- Read actual source files\n- Identify gaps\n- Prioritise findings"] --> AnalyzeGate{Gap analysis\ncomplete?}
    AnalyzeGate -->|No| Analyze
    AnalyzeGate -->|Yes| Sprint

    Sprint["/sprint N\n- Plan Agent creates breakdown\n- Define acceptance criteria\n- Define test specifications"] --> SprintGate{Sprint plan\napproved?}
    SprintGate -->|No| Sprint
    SprintGate -->|Yes| Develop

    Develop["/develop N\n- Code Agents implement\n- Test Agents write tests\n- E2E verification\n- Full suite green"] --> DevelopGate{All tests pass?\nCode reviewed?}
    DevelopGate -->|No| Develop
    DevelopGate -->|Yes| Retro

    Retro["/retrospective N\n- Log bug patterns\n- Sync workflow changes\n- Update CLAUDE.md"] --> RetroGate{Retrospective\ncomplete?}
    RetroGate -->|No| Retro
    RetroGate -->|Yes| MoreSprints

    MoreSprints{More sprints\nneeded?}
    MoreSprints -->|Yes| Sprint
    MoreSprints -->|No| Done([Project Complete])

    Review["/review\n- Council dispatch\n- Multi-platform review\n- Findings consolidated"]
    Review -.->|Can run anytime\nduring develop| Develop

    style Setup fill:#4a90d9,color:#fff
    style Analyze fill:#7b68ee,color:#fff
    style Sprint fill:#f5a623,color:#fff
    style Develop fill:#50c878,color:#fff
    style Retro fill:#e74c3c,color:#fff
    style Review fill:#95a5a6,color:#fff
```

---

## 2. Council Review Detail

The `/review` process: dispatching to review platforms, arbitrating conflicts, and consolidating findings.

```mermaid
flowchart TD
    Trigger(["/review invoked"]) --> Dispatch["scripts/council-dispatch.py\n- Prepare review context\n- Package changed files\n- Format review request"]

    Dispatch --> Platform1["Reviewer 1\n(Platform A)"]
    Dispatch --> Platform2["Reviewer 2\n(Platform B)"]
    Dispatch --> Platform3["Reviewer 3\n(Platform C)"]

    Platform1 --> Collect["Collect Reviews\nscripts/council-check.sh\n- Poll for completion\n- Gather responses"]
    Platform2 --> Collect
    Platform3 --> Collect

    Collect --> Conflicts{Conflicting\nfindings?}

    Conflicts -->|Yes| Arbitrator["Arbitrator Agent\n- Weigh reviewer arguments\n- Consider project context\n- Produce ruling with rationale"]
    Conflicts -->|No| Consolidate

    Arbitrator --> Consolidate["Consolidate Findings\n- Merge unique findings\n- Apply arbitration rulings\n- Categorise by severity"]

    Consolidate --> Tracker["Findings Tracker\n- Critical: must fix before merge\n- Major: should fix this sprint\n- Minor: can defer with justification\n- Suggestion: team discretion"]

    Tracker --> Critical{Critical\nfindings?}
    Critical -->|Yes| FixRequired["Feed back to\n/develop for fixes"]
    Critical -->|No| Approved([Review Complete])

    FixRequired --> Trigger

    style Trigger fill:#95a5a6,color:#fff
    style Dispatch fill:#4a90d9,color:#fff
    style Arbitrator fill:#e74c3c,color:#fff
    style Consolidate fill:#7b68ee,color:#fff
    style Tracker fill:#f5a623,color:#fff
```

---

## 3. Development Phase Detail

The `/develop` phase: parallel code and test agents, E2E verification, fix loops, and full suite validation.

```mermaid
flowchart TD
    Start(["/develop N starts"]) --> ReadPlan["Read Sprint Plan\n- Load task breakdown\n- Load acceptance criteria\n- Load test specifications"]

    ReadPlan --> Parallel["Spawn Parallel Agents"]

    Parallel --> CodeAgents["Code Agent(s)\n- One per task/module\n- Read context files first\n- Write implementation\n- Follow established patterns"]

    Parallel --> TestAgents["Test Agent(s)\n- Work from specs NOT code\n- Write unit tests\n- Write integration tests\n- Define E2E scenarios"]

    CodeAgents --> Integration["Integration Point\n- Code and tests land on branch\n- Verify imports and paths\n- Check for conflicts"]
    TestAgents --> Integration

    Integration --> RunUnit["Run Unit Tests"]
    RunUnit --> UnitPass{All unit\ntests pass?}
    UnitPass -->|No| FixUnit["Fix Agent\n- Read failing test output\n- Read relevant source\n- Fix code or test\n- Never delete tests"]
    FixUnit --> RunUnit
    UnitPass -->|Yes| RunE2E

    RunE2E["Run E2E Tests"] --> E2EPass{All E2E\ntests pass?}
    E2EPass -->|No| FixE2E["Fix Agent\n- Diagnose integration issue\n- Fix code path\n- Re-verify unit tests"]
    FixE2E --> RunUnit
    E2EPass -->|Yes| FullSuite

    FullSuite["Run Full Test Suite\n- All existing tests\n- All new tests\n- Linting\n- Type checking"] --> SuitePass{Full suite\ngreen?}
    SuitePass -->|No| FixRegression["Fix Agent\n- Identify regression\n- Fix without breaking\n  new functionality\n- Log bug pattern if recurring"]
    FixRegression --> FullSuite
    SuitePass -->|Yes| Commit

    Commit["Commit & PR\n- Descriptive commit message\n- Create/update PR\n- CI gates triggered"] --> Done(["/develop N complete"])

    style Start fill:#50c878,color:#fff
    style CodeAgents fill:#4a90d9,color:#fff
    style TestAgents fill:#7b68ee,color:#fff
    style FixUnit fill:#e74c3c,color:#fff
    style FixE2E fill:#e74c3c,color:#fff
    style FixRegression fill:#e74c3c,color:#fff
    style FullSuite fill:#f5a623,color:#fff
```

---

## 4. Team Sync Flow

How the workflow template stays synchronised across project repositories.

```mermaid
flowchart TD
    Template[("Workflow Template Repo\n- Skills\n- Rules\n- Scripts\n- Diagrams")]

    Template -->|"/sync pull"| ProjectA["Project A\n.claude/skills/\n.claude/workflow-rules.md\nscripts/"]
    Template -->|"/sync pull"| ProjectB["Project B\n.claude/skills/\n.claude/workflow-rules.md\nscripts/"]
    Template -->|"/sync pull"| ProjectC["Project C\n.claude/skills/\n.claude/workflow-rules.md\nscripts/"]

    ProjectA -->|"/sync push"| Template
    ProjectB -->|"/sync push"| Template
    ProjectC -->|"/sync push"| Template

    subgraph "Sync Pull Process"
        Pull1["1. Fetch latest from template repo"]
        Pull2["2. Compare tracked files"]
        Pull3["3. Apply updates preserving\nproject-specific overrides"]
        Pull4["4. Report changes applied"]
        Pull1 --> Pull2 --> Pull3 --> Pull4
    end

    subgraph "Sync Push Process"
        Push1["1. Identify modified workflow files"]
        Push2["2. Filter out project-specific overrides"]
        Push3["3. Create PR against template repo"]
        Push4["4. Mark files as synced"]
        Push1 --> Push2 --> Push3 --> Push4
    end

    subgraph "Retrospective Sync Check"
        Check1["1. Diff tracked files against\nlast sync point"]
        Check2{"Unsynchronised\nchanges?"}
        Check3["Block retrospective\ncompletion"]
        Check4["User chooses:\nA) /sync push\nB) Mark as override"]
        Check1 --> Check2
        Check2 -->|Yes| Check3 --> Check4
        Check2 -->|No| Check5([Proceed])
    end

    style Template fill:#4a90d9,color:#fff
    style ProjectA fill:#50c878,color:#fff
    style ProjectB fill:#50c878,color:#fff
    style ProjectC fill:#50c878,color:#fff
```

---

## Legend

| Colour | Meaning |
|--------|---------|
| Blue | Setup / Infrastructure |
| Purple | Analysis / Planning |
| Orange | Validation / Gating |
| Green | Implementation / Projects |
| Red | Fixes / Critical Review |
| Grey | Optional / Async |
