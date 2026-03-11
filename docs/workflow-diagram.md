# Workflow Diagram

## Complete Pipeline

```mermaid
flowchart TB
    subgraph Phase0["Phase 0: Discovery"]
        analyze["/analyze<br/>Deep Analysis"]
        phase0["/phase-0<br/>Gap Analysis"]
        analyze --> phase0
    end

    subgraph Phase1["Phase 1: Planning"]
        plan["/plan<br/>Implementation Plan"]
        subgraph ReviewAgents["Parallel Review Agents"]
            arch["Architecture<br/>Agent"]
            sec["Security<br/>Agent"]
            perf["Performance<br/>Agent"]
            test["Testability<br/>Agent"]
            ui_rev["UI Review<br/>Agent"]
            spec_rev["Spec Compliance<br/>Agent ⚠️"]
        end
        plan --> ReviewAgents
    end

    subgraph Phase2["Phase 2: Implementation"]
        subgraph CodeAgents["Parallel Per-Unit Agents"]
            code["Code Agent<br/>(reads context files)"]
            tests["Test Agent<br/>(writes from spec)"]
        end
        e2e_agent["E2E Test Agent"]
        ui_check["UI Review"]
        smoke["Smoke Wiring Check"]
        integration["Integration Check<br/>type check + tests + E2E"]
        fix["Fix Failures"]
        spec_gate["Spec Compliance<br/>Gate ⚠️"]

        CodeAgents --> e2e_agent
        e2e_agent --> ui_check
        ui_check --> smoke
        smoke --> integration
        integration --> fix
        fix -->|"still failing"| integration
        fix -->|"all green"| spec_gate
    end

    subgraph Phase3["Phase 3: Verification"]
        predeploy["/pre-deploy"]
        subgraph Gates["Parallel Gate Checks"]
            g_tests["Test Suite"]
            g_types["Type Check"]
            g_lint["Lint"]
            g_sec["Security Scan"]
            g_deps["Dependency Check"]
            g_e2e["E2E Tests"]
            g_spec["Spec Compliance ⚠️"]
        end
        predeploy --> Gates
    end

    phase0 -->|"gap list"| plan
    ReviewAgents -->|"approved plan"| CodeAgents
    spec_gate -->|"PASS"| commit["Auto-Commit"]
    commit --> predeploy
    Gates -->|"ALL PASS"| deploy["Ready to Deploy"]
    Gates -->|"ANY FAIL"| block["Blocked ✖"]

    style Phase0 fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style Phase1 fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style Phase2 fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style Phase3 fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style spec_rev fill:#d4a017,stroke:#b8860b,color:#000
    style spec_gate fill:#d4a017,stroke:#b8860b,color:#000
    style g_spec fill:#d4a017,stroke:#b8860b,color:#000
    style deploy fill:#2d6a4f,stroke:#1b4332,color:#fff
    style block fill:#9b2226,stroke:#641220,color:#fff
    style commit fill:#2d6a4f,stroke:#1b4332,color:#fff
```

## Analyze Phase Detail

```mermaid
flowchart LR
    subgraph Input["Source Material"]
        codebase["Codebase"]
        specs["Specs/Docs"]
        mixed["Mixed"]
    end

    subgraph Analysis["7 Phases"]
        p1["1. Discovery<br/>Structural Map"]
        p2["2. Feature<br/>Decomposition"]
        p3["3. Cross-Cutting<br/>Design System + Patterns"]
        p4["4. User Q&A"]
        p5["5. BA Review<br/>⟲ up to 3 rounds"]
        p6["6. Implementation<br/>Checklists"]
        p7["7. Summary<br/>& Index"]

        p1 --> p2 --> p3 --> p4 --> p5 --> p6 --> p7
    end

    subgraph Output["Persistent Corpus"]
        structure["00-structure.md"]
        features["NN-feature.md<br/>(per area)"]
        design["90-design-system.md"]
        patterns["91-patterns.md"]
        checklists["95-checklists.md"]
        ba_review["96-ba-review.md"]
        decisions["99-decisions.md"]
        index["00-index.md"]
    end

    subgraph AutoUpdate["CLAUDE.md Updated"]
        stack["Stack"]
        dirs["Directory Structure"]
        ds["Design System"]
        ep["Established Patterns"]
        dm["Data Model"]
    end

    Input --> p1
    p7 --> Output
    p1 -.->|"Phase 1"| stack
    p1 -.->|"Phase 1"| dirs
    p3 -.->|"Phase 3"| ds
    p3 -.->|"Phase 3"| ep
    p2 -.->|"Phase 2"| dm

    style p5 fill:#d4a017,stroke:#b8860b,color:#000
```

## Implementation Unit Detail

```mermaid
flowchart TB
    plan_unit["Plan Unit<br/>(files + context + deps)"]

    subgraph Parallel["Parallel Agents"]
        direction LR
        code_agent["Code Agent<br/>1. Read context files<br/>2. Read router/handlers/schemas<br/>3. Implement production code"]
        test_agent["Test Agent<br/>1. Read plan + spec<br/>2. Write tests from spec<br/>3. Cover happy + edge + error"]
    end

    plan_unit --> Parallel

    e2e["E2E Test Agent<br/>Add/update browser tests"]
    Parallel --> e2e

    subgraph Verification["Verification Sequence"]
        ui["UI Review<br/>Design system, states,<br/>responsive, dark mode,<br/>accessibility"]
        wiring["Smoke Wiring Check<br/>✓ Routes registered<br/>✓ Links valid<br/>✓ API contracts match<br/>✓ Forms complete"]
        integ["Integration Check<br/>✓ Type check<br/>✓ Unit tests<br/>✓ E2E tests<br/>✓ Cross-file issues<br/>✓ API contract alignment"]

        ui --> wiring --> integ
    end

    e2e --> ui
    integ -->|"failures"| fix["Fix Code<br/>(tests are the spec)"]
    fix --> integ
    integ -->|"all green"| spec["Spec Compliance ⚠️<br/>✓ Gap list items done<br/>✓ Features reachable<br/>✓ Tests exist"]
    spec -->|"PASS"| done["Update CLAUDE.md<br/>→ Commit"]
    spec -->|"FAIL"| fix2["Fix & Re-verify"]
    fix2 --> integ

    style wiring fill:#264653,stroke:#2a9d8f,color:#fff
    style spec fill:#d4a017,stroke:#b8860b,color:#000
```

## Review Agents Detail

```mermaid
flowchart LR
    trigger["Code Changes<br/>(uncommitted or specified)"]

    subgraph Agents["5 Parallel Review Agents"]
        direction TB
        ui_agent["UI Review Agent<br/>• Design system compliance<br/>• Visual states (load/empty/error)<br/>• Responsive behaviour<br/>• Dark mode<br/>• Consistency<br/>• Accessibility"]
        arch_agent["Architecture Agent<br/>• Project conventions<br/>• API contract alignment<br/>• Form binding patterns<br/>• Link construction<br/>• Bug pattern check"]
        sec_agent["Security Agent<br/>• Auth/authz on endpoints<br/>• Input validation<br/>• Injection vectors<br/>• URL param resolution<br/>• No leaked secrets"]
        perf_agent["Performance Agent<br/>• Algorithm complexity<br/>• Re-render prevention<br/>• Caching strategy<br/>• Memory leaks"]
        test_agent["Test Coverage Agent<br/>• Unit test coverage<br/>• Edge case coverage<br/>• E2E test updates<br/>• Meaningful assertions"]
    end

    trigger --> Agents

    subgraph Report["Consolidated Report"]
        blocking["BLOCKING<br/>Must fix before merge"]
        should["SHOULD FIX<br/>Significant issues"]
        consider["CONSIDER<br/>Suggestions"]
    end

    Agents --> Report

    update["Update CLAUDE.md<br/>Coding Conventions<br/>Established Patterns"]
    Report -.-> update

    style blocking fill:#9b2226,stroke:#641220,color:#fff
    style should fill:#d4a017,stroke:#b8860b,color:#000
    style consider fill:#264653,stroke:#2a9d8f,color:#fff
```

## Postmortem & Self-Improvement Loop

```mermaid
flowchart TB
    bug["Bug Found"]
    doc["1. Document Bug<br/>Summary, severity,<br/>symptoms, root cause"]
    classify["2. Classify Pattern<br/>• Orphaned component<br/>• Broken contract<br/>• Missing integration<br/>• ID/slug confusion<br/>• Missing system field<br/>• Stale selector<br/>• State isolation"]
    escape["3. Trace Escape Path<br/>Which checkpoint<br/>should have caught it?"]
    rules["4. Design Prevention<br/>Specific, automatable<br/>checks"]

    subgraph Updates["5. Update Skills"]
        direction LR
        s1["spec-compliance.md"]
        s2["implement.md"]
        s3["review.md"]
        s4["plan.md"]
        s5["e2e.md"]
    end

    registry["6. Add to<br/>bug-patterns.md"]
    claude_md["Update CLAUDE.md<br/>Bug Patterns section"]
    verify["7. Verify fix would<br/>catch original bug"]
    sync["8. /sync-template push<br/>Share with template"]

    bug --> doc --> classify --> escape --> rules --> Updates
    Updates --> registry --> claude_md
    claude_md --> verify --> sync

    style bug fill:#9b2226,stroke:#641220,color:#fff
    style sync fill:#264653,stroke:#2a9d8f,color:#fff
```

## CLAUDE.md Auto-Population Flow

```mermaid
flowchart LR
    subgraph Skills["Skills That Write"]
        analyze["/analyze"]
        plan["/plan"]
        implement["/implement"]
        review["/review"]
        postmortem["/postmortem"]
    end

    subgraph Config["CLAUDE.md Project Configuration"]
        desc["Project Description"]
        ref["Reference Implementation"]
        stack["Stack"]
        cmds["Commands"]
        dirs["Directory Structure"]
        test_conv["Test File Conventions"]
        patterns["Established Patterns"]
        data["Data Model Conventions"]
        design["Design System"]
        coding["Coding Conventions"]
        bugs["Bug Patterns"]
    end

    analyze -->|"Phase 1"| stack
    analyze -->|"Phase 1"| dirs
    analyze -->|"Phase 3"| design
    analyze -->|"Phase 3"| patterns
    analyze -->|"Phase 2"| data

    plan -->|"Step 3b"| patterns
    plan -->|"Step 3b"| test_conv

    implement -->|"Step 7"| cmds
    implement -->|"Step 7"| test_conv
    implement -->|"Step 7"| patterns
    implement -->|"Step 7"| coding
    implement -->|"Step 7"| design

    review -->|"Step 4"| coding
    review -->|"Step 4"| patterns

    postmortem -->|"Step 6"| bugs
```

## Upstream Sync Architecture

```mermaid
flowchart TB
    subgraph Template["workflow_template (upstream)"]
        t_rules[".claude/workflow-rules.md"]
        t_skills[".claude/skills/*.md"]
        t_readme["README.md"]
        t_bugtemplate["docs/bug-patterns.md<br/>(empty template)"]
    end

    subgraph Project["your-project"]
        subgraph Synced["Synced with template"]
            p_rules[".claude/workflow-rules.md"]
            p_skills[".claude/skills/*.md"]
        end
        subgraph Local["Project-specific (never pushed)"]
            p_claude["CLAUDE.md<br/>(auto-populated config)"]
            p_analysis["docs/analysis/<br/>(corpus)"]
            p_gaps["docs/gaps/<br/>(gap lists)"]
            p_bugs["docs/bug-patterns.md<br/>(project bugs)"]
            p_code["src/<br/>(project code)"]
        end
    end

    t_rules <-->|"/sync-template<br/>pull / push"| p_rules
    t_skills <-->|"/sync-template<br/>pull / push"| p_skills

    style Synced fill:#264653,stroke:#2a9d8f,color:#fff
    style Local fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style Template fill:#264653,stroke:#2a9d8f,color:#fff
```
