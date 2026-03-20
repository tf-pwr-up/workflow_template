---
name: setup
description: "Interactive project setup — bootstraps workflow configuration through guided questioning"
---

# /setup — Interactive Project Setup

## Purpose

Bootstrap the workflow for a new project through guided questioning. This skill establishes the project's identity, expertise needs, architectural patterns, and configures the council of experts. It is the mandatory first step before any analysis, planning, or development work can begin.

## Prerequisites

- None. This is the entry point for all new projects.

## Enforcement

- All other workflow skills (`/analyze`, `/sprint`, `/develop`, etc.) require the presence of `council-config.json` in the project root. That file is only produced by this skill.
- If `council-config.json` already exists, warn the user and ask whether they want to reconfigure or abort.

---

## Execution Steps

**CRITICAL:** Use `AskUserQuestion` for ALL questions. Ask ONE question at a time. Wait for the answer before asking the next question. Where options are listed, pass them as `options` to `AskUserQuestion`. Where free text is needed, omit `options`.

### Step 1 — Project Identity

Ask the following questions one at a time:

**Q1.1: Project Type**
```
AskUserQuestion(
  question: "What type of project is this?",
  options: ["Web Application", "API Service", "CLI Tool", "Library/Package", "Mobile App", "Monorepo", "Other"]
)
```
If "Other" is selected, follow up with a free-text question asking for a description.

**Q1.2: Primary Language/Framework**
Before asking, inspect the repository for existing code:
- Check for `package.json`, `go.mod`, `Cargo.toml`, `requirements.txt`, `pyproject.toml`, `Gemfile`, `*.csproj`, `pom.xml`, `build.gradle`, `mix.exs`, `deno.json`, etc.
- If detected, present findings and ask for confirmation:
  ```
  AskUserQuestion(
    question: "I detected [language/framework] from your repository. Is this the primary language/framework, or would you like to specify something else?",
    options: ["Yes, that's correct", "No, let me specify"]
  )
  ```
- If no code detected or user wants to specify:
  ```
  AskUserQuestion(
    question: "What is the primary language and framework for this project? (e.g., 'TypeScript with Next.js', 'Python with FastAPI', 'Go with Chi')"
  )
  ```

**Q1.3: Broad Requirement**
```
AskUserQuestion(
  question: "Describe the broad requirement for this project in a few sentences. What problem does it solve and for whom?"
)
```

**Q1.4: Reference Material**
```
AskUserQuestion(
  question: "Is there a reference implementation, specification document, or existing codebase to analyse?",
  options: ["Yes — I'll provide a file path", "Yes — I'll provide a URL", "No reference material"]
)
```
If a path or URL is selected, follow up asking for the actual value. If a path is provided, read and summarise the document. If a URL is provided, use `WebFetch` to retrieve and summarise it. Store the summary in `docs/context/reference-summary.md`.

### Step 2 — Expertise & Domain

**Q2.1: Domain**
```
AskUserQuestion(
  question: "What domain is this project in? (e.g., 'telecommunications', 'fintech', 'e-commerce', 'healthcare', 'logistics', 'education')"
)
```

**Q2.2: Domain Standards**
```
AskUserQuestion(
  question: "Are there domain-specific standards or protocols that apply? (e.g., 'HL7/FHIR for healthcare', 'PCI-DSS for payments', 'SIP/RTP for telecom'). Type 'none' if not applicable."
)
```

**Q2.3: Security Sensitivity**
```
AskUserQuestion(
  question: "What level of security sensitivity does this project require?",
  options: ["Standard — typical web security practices", "Elevated — handles PII, financial data, or sensitive business logic", "Critical — regulated industry, handles secrets/keys, or life-safety implications"]
)
```
This answer directly affects council composition:
- **Standard:** Core council only.
- **Elevated:** Core council + Performance + Cost Modeller.
- **Critical:** Full council including all optional members.

**Q2.4: Regulatory Requirements**
```
AskUserQuestion(
  question: "Are there regulatory or compliance requirements? (e.g., 'GDPR', 'HIPAA', 'SOC2', 'PCI-DSS'). Type 'none' if not applicable."
)
```

### Step 3 — Architecture Preferences

**Q3.1: Architectural Pattern**
```
AskUserQuestion(
  question: "What is your preferred architectural pattern?",
  options: ["Monolith", "Microservices", "Serverless", "Event-Driven", "Modular Monolith", "Other"]
)
```
If "Other", follow up with free text.

**Q3.2: Testing Approach**
```
AskUserQuestion(
  question: "What is your preferred testing approach?",
  options: ["Unit + Integration tests", "Test-Driven Development (TDD)", "Behaviour-Driven Development (BDD)", "Other"]
)
```

**Q3.3: CI/CD**
```
AskUserQuestion(
  question: "What CI/CD system do you use or plan to use?",
  options: ["GitHub Actions", "GitLab CI", "Other", "None yet"]
)
```

**Q3.4: Existing Patterns**
```
AskUserQuestion(
  question: "Are there established coding patterns, conventions, or style guides to follow? (e.g., 'Airbnb style guide', 'hexagonal architecture in src/domain', 'all handlers must return Result types'). Type 'none' if starting fresh."
)
```

### Step 4 — Council Configuration

Based on ALL answers collected above, generate `council-config.json` in the project root.

#### Council Member Definitions

**Core Members** (always present):

| Role | Label | Default Platform | Fallback |
|------|-------|-----------------|----------|
| Security Reviewer | `security` | Codex CLI | Claude API |
| Architecture Reviewer | `architecture` | Codex CLI | Gemini API |
| Spec Compliance Checker | `spec-compliance` | Claude API | OpenAI API |
| Testing Strategist | `testing` | OpenAI API | Claude API |
| Arbitrator | `arbitrator` | Codex CLI | Claude API |

**Optional Members** (based on project type and security level):

| Role | Label | Trigger | Default Platform | Fallback |
|------|-------|---------|-----------------|----------|
| Performance Analyst | `performance` | Web app, API, or elevated+ security | Gemini API | OpenAI API |
| UX/DX Specialist | `ux-dx` | Web app, CLI tool, or library | Gemini API | Claude API |
| Cost Modeller | `cost-modeller` | Serverless, microservices, or elevated+ security | Gemini API | OpenAI API |
| Domain Expert | `domain-expert` | Always when domain standards specified | Claude API | Gemini API |

#### Lens Prompts for Core Members

Each council member operates with a **lens** — a focused system prompt that defines their narrow expert mandate. These lenses ensure independent, non-overlapping review perspectives.

**Security Reviewer Lens:**
```
You are a senior application security engineer reviewing this project exclusively through a security lens. Your mandate is to identify vulnerabilities, insecure patterns, and missing safeguards. Focus on: authentication and authorisation flaws, injection vectors (SQL, XSS, command, template), insecure data handling (secrets in code, insufficient encryption, PII exposure), dependency vulnerabilities, insecure defaults, missing input validation and output encoding, CSRF/SSRF risks, broken access control, and cryptographic misuse. For each finding, state the risk severity (Critical/High/Medium/Low), the specific location or pattern, and a concrete remediation. Do NOT comment on code style, architecture, performance, or testing — those are other reviewers' responsibilities. If the security level is elevated or critical, apply stricter standards and flag anything that would fail a penetration test or compliance audit.
```

**Architecture Reviewer Lens:**
```
You are a principal software architect reviewing this project exclusively through an architectural lens. Your mandate is to evaluate structural soundness, maintainability, and adherence to stated architectural patterns. Focus on: separation of concerns, dependency direction (dependencies should point inward toward domain logic), module boundaries and coupling, appropriate use of abstractions (neither too many nor too few), consistency with the chosen architectural pattern, API contract design, data flow clarity, error propagation strategy, and scalability characteristics. For each finding, explain the structural issue, its long-term consequence if unaddressed, and a specific refactoring recommendation. Do NOT comment on security vulnerabilities, test coverage, or UI/UX concerns. When reviewing sprint plans, evaluate whether the proposed breakdown respects architectural boundaries and whether dependencies between sprints are correctly ordered.
```

**Spec Compliance Checker Lens:**
```
You are a meticulous specification compliance analyst. Your mandate is to verify that every requirement, acceptance criterion, and constraint documented in the project's requirements has been addressed. Work systematically: enumerate each requirement from the docs/requirements/ files, then trace each one to its implementation (or planned implementation in sprint breakdowns). Flag: requirements with no corresponding implementation, implementations that deviate from specified behaviour, acceptance criteria that are not testable as written, ambiguous requirements that need clarification, implicit requirements that should be made explicit, and edge cases described in requirements but not handled. For each finding, reference the specific requirement by ID or description. Do NOT evaluate code quality, security, or architecture — only whether the specification is faithfully and completely addressed.
```

**Testing Strategist Lens:**
```
You are a senior QA engineer and testing strategist. Your mandate is to evaluate test coverage, test quality, and testing strategy. Focus on: whether critical paths have adequate test coverage, test isolation (tests should not depend on external state or ordering), appropriate use of mocks versus integration tests, edge case coverage, error path testing, test naming and readability, whether acceptance criteria from requirements have corresponding test cases, performance and load testing needs, and test infrastructure reliability. For each finding, specify what is under-tested, what kind of test is needed (unit/integration/e2e/contract/load), and where it should live. Do NOT comment on application security, architecture, or UI/UX. When reviewing sprint plans, assess whether the testing strategy for each sprint is sufficient to verify its exit criteria.
```

**Arbitrator Lens:**
```
You are the council arbitrator — a distinguished technical fellow who synthesises findings from all other council members into a coherent assessment. You review AFTER all other members have submitted their findings. Your mandate: identify where reviewers agree (convergence), where they conflict (divergence), and where important gaps exist that no reviewer addressed. Rank all findings by severity and business impact. Where reviewers conflict, provide a reasoned judgment citing specific technical trade-offs. Produce a final verdict: APPROVE (no blocking issues), REVISE (blocking issues identified with clear remediation path), or REJECT (fundamental problems requiring significant rework). Your verdict must include a numbered list of required changes (for REVISE) or a summary of why the work is acceptable (for APPROVE). Do NOT introduce new technical findings — your role is synthesis, prioritisation, and judgment.
```

#### Domain Expert Lens (Generated Dynamically)

The domain expert lens is populated from the answers to Q2.1, Q2.2, and Q2.4. Template:

```
You are a domain expert in [DOMAIN]. Your mandate is to ensure this project correctly implements [DOMAIN]-specific requirements, standards, and best practices. You are familiar with [STANDARDS/PROTOCOLS]. Regulatory context: [REGULATORY]. Focus on: correct use of domain terminology and concepts, adherence to domain standards and protocols, domain-specific edge cases that generalist developers commonly miss, data models that accurately represent domain entities and relationships, business rule correctness, and industry best practices. For each finding, explain the domain-specific concern, why it matters in [DOMAIN], and the correct approach. Do NOT comment on general code quality, security (unless domain-specific), or architecture patterns.
```

#### `council-config.json` Format

```json
{
  "project": {
    "name": "<project-name>",
    "type": "<project-type>",
    "language": "<language/framework>",
    "domain": "<domain>",
    "security_level": "<standard|elevated|critical>",
    "architecture": "<chosen-pattern>",
    "testing_approach": "<chosen-approach>"
  },
  "council": {
    "members": [
      {
        "role": "Security Reviewer",
        "label": "security",
        "platform": "codex-cli",
        "model": "o3",
        "fallback": {
          "platform": "claude-api",
          "model": "claude-sonnet-4-20250514"
        },
        "lens": "<full lens prompt text>",
        "phases": ["analyze", "plan", "code"]
      },
      {
        "role": "Architecture Reviewer",
        "label": "architecture",
        "platform": "codex-cli",
        "model": "o3",
        "fallback": {
          "platform": "gemini-api",
          "model": "gemini-2.5-pro"
        },
        "lens": "<full lens prompt text>",
        "phases": ["analyze", "plan", "code"]
      },
      {
        "role": "Spec Compliance Checker",
        "label": "spec-compliance",
        "platform": "claude-api",
        "model": "claude-sonnet-4-20250514",
        "fallback": {
          "platform": "openai-api",
          "model": "o3"
        },
        "lens": "<full lens prompt text>",
        "phases": ["analyze", "plan", "code"]
      },
      {
        "role": "Testing Strategist",
        "label": "testing",
        "platform": "openai-api",
        "model": "o3",
        "fallback": {
          "platform": "claude-api",
          "model": "claude-sonnet-4-20250514"
        },
        "lens": "<full lens prompt text>",
        "phases": ["analyze", "plan", "code"]
      },
      {
        "role": "Arbitrator",
        "label": "arbitrator",
        "platform": "codex-cli",
        "model": "o3",
        "fallback": {
          "platform": "claude-api",
          "model": "claude-sonnet-4-20250514"
        },
        "lens": "<full lens prompt text>",
        "phases": ["analyze", "plan", "code"]
      }
    ],
    "optional_members": [
      {
        "role": "Performance Analyst",
        "label": "performance",
        "platform": "gemini-api",
        "model": "gemini-2.5-pro",
        "fallback": {
          "platform": "openai-api",
          "model": "o3"
        },
        "lens": "You are a performance engineer...",
        "phases": ["plan", "code"],
        "enabled": false
      }
    ]
  },
  "convergence": {
    "max_analyze_rounds": 4,
    "max_plan_rounds": 5,
    "max_code_rounds": 5,
    "convergence_warning_at": 3
  },
  "dispatch_order": {
    "analyze": ["architecture", "spec-compliance", "security", "domain-expert", "arbitrator"],
    "plan": ["architecture", "security", "testing", "performance", "cost-modeller", "arbitrator"],
    "code": ["security", "architecture", "spec-compliance", "testing", "ux-dx", "arbitrator"]
  }
}
```

**Note:** The `dispatch_order` defines the sequence in which council members are invoked for each phase. The arbitrator is ALWAYS last. Only enabled members are dispatched.

### Step 5 — Research Phase

If domain-specific standards or protocols were identified in Step 2:

1. Use `WebSearch` to research:
   - Current best practices for the identified standards/protocols
   - Common implementation pitfalls
   - Reference architectures in the domain
   - Regulatory compliance checklists (if applicable)

2. Compile findings into `docs/context/domain-reference.md` with sections:
   - **Standards Overview** — what the standards require
   - **Implementation Guidance** — how to implement correctly
   - **Common Pitfalls** — what to avoid
   - **Compliance Checklist** — verification points
   - **References** — source URLs

3. This document becomes part of the domain expert's context pack and is referenced in the domain expert's lens prompt.

If no domain-specific standards were identified, skip this step.

### Step 6 — Prerequisite Check

Run the council infrastructure check:

```bash
./scripts/council-check.sh
```

This script verifies:
- API keys are set for all configured platforms (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`)
- Codex CLI is installed and accessible
- Python 3.8+ is available (for `council-dispatch.py`)
- Required Python packages are installed
- `council-config.json` is valid JSON

If any checks fail:
1. Present the failures to the user
2. Guide them through resolution (e.g., "Set your Gemini API key with: export GEMINI_API_KEY=your-key-here")
3. Re-run the check after fixes
4. Do NOT proceed until all checks pass

### Step 7 — Scaffold Project Configuration

**Create directory structure:**
```
docs/
  requirements/
    00-index.md
  gaps/
  plans/
  findings/
  reviews/
  archive/
  context/
```

**Populate CLAUDE.md** (if it exists, update relevant sections; if not, create):
- Project name and description
- Language/framework
- Architecture pattern
- Key conventions from Q3.4
- Directory structure
- Council configuration summary
- Workflow command reference (`/setup`, `/analyze`, `/sprint`, `/develop`, `/review`, `/sync`, `/retrospective`)

**If existing codebase detected:**
Run a lightweight discovery:
1. Map the directory structure (top 3 levels)
2. Identify entry points, configuration files, and test locations
3. Detect established patterns (naming conventions, module structure, error handling)
4. Populate the "Established Patterns" and "Directory Structure" sections of CLAUDE.md

---

## Output

Upon successful completion, the following artifacts exist:

| Artifact | Location | Purpose |
|----------|----------|---------|
| Council config | `council-config.json` | Council member definitions, platforms, lenses |
| Project CLAUDE.md | `CLAUDE.md` | Project conventions and workflow reference |
| Directory structure | `docs/` | Prepared for requirements, plans, findings |
| Domain reference | `docs/context/domain-reference.md` | Domain expert context (if applicable) |
| Reference summary | `docs/context/reference-summary.md` | Analysed reference material (if provided) |

Print a summary showing:
- Project type and language
- Council composition (which members are enabled)
- Platform assignments
- Any warnings from the prerequisite check
- Next step: "Run `/analyze` to begin requirements gathering."
