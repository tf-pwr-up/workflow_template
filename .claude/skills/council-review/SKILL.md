---
name: council-review
description: "Council of experts review — orchestrates multi-platform expert review with arbitration and findings tracking"
---

# Council of Experts Review Process

This skill orchestrates the multi-platform expert review council. It is invoked by other skills (`/analyze`, `/sprint`, `/review`) — not directly by the user. The mechanical API dispatch to council member platforms is handled by `scripts/council-dispatch.py`; this skill defines the review process, prompt construction, findings tracking, and convergence logic.

---

## Review Types

| Type      | Trigger                  | Materials                                         |
|-----------|--------------------------|----------------------------------------------------|
| `analyze` | High-level requirements / sprint breakdown review | Requirements doc, gap analysis, sprint breakdown   |
| `plan`    | Sprint plan review (detailed technical)           | Sprint plan, gap list, architecture context        |
| `code`    | Code implementation review                        | Code changes (diff or files), sprint plan, tests   |

---

## Process Flow

### Step 1 — Gather Materials

Based on the review type, collect the relevant input files:

- **analyze**: Read the requirements document, any existing gap analysis (`docs/findings/gap-list.md`), and the proposed sprint breakdown.
- **plan**: Read the sprint plan (`docs/sprints/sprint-<N>-plan.md`), the gap list, and any prior findings from the analyze phase (`docs/findings/analyze-findings.md`).
- **code**: Read the code changes (via `git diff` for uncommitted work, or the specified files), the sprint plan, test files, and any prior plan-phase findings (`docs/findings/sprint-<N>-findings.md`).

### Step 2 — Build Context

Every review type loads shared context before dispatching:

1. Read `CLAUDE.md` for project-level context, conventions, and established patterns.
2. Read all files in `docs/context/` for domain-specific context documents.
3. Read `docs/bug-patterns.md` for known pitfalls, recurring issues, and prevention rules.
4. Read `council-config.json` for active council members, platform assignments, and round limits.

### Step 3 — Dispatch to Council

Invoke the dispatch script:

```bash
./scripts/council-dispatch.py <type> <sprint> "<title>"
```

Arguments:
- `<type>` — one of `analyze`, `plan`, `code`
- `<sprint>` — sprint number (use `0` for standalone reviews)
- `<title>` — short description of what is being reviewed

The dispatch script sends the gathered materials plus the appropriate lens prompt to ALL active council members in parallel across their configured platforms. It collects responses and writes them to `docs/findings/council-responses/<type>-sprint-<N>/`.

### Step 4 — Arbitrator Phase

The arbitrator runs LAST. It receives:
- All findings from every other council member
- The original materials submitted for review
- The arbitrator lens prompt (see below)

The arbitrator provides an independent assessment of every finding and an overall verdict recommendation.

### Step 5 — Consolidation

After all reviews (including the arbitrator) complete, run the consolidation algorithm:

1. **Merge overlapping concerns** — When multiple experts flag the same issue, combine into a single finding. Attribute to all contributing experts.
2. **Resolve conflicts** — When experts disagree, make a judgment call. Document the reasoning for the resolution clearly.
3. **Filter false positives** — Remove findings that do not apply. Note every exclusion with a brief reason so it is auditable.
4. **Incorporate arbitrator severity overrides** — Where the arbitrator re-graded a finding's severity, use the arbitrator's grade and note the original.
5. **Determine verdict** — `APPROVED` or `CHANGES_REQUESTED`. A single CRITICAL or two or more HIGH findings that are not overridden by the arbitrator result in `CHANGES_REQUESTED`.
6. **Write unified review** — Produce a single consolidated review document.

### Step 6 — Findings Tracker Update

Update or create the findings tracker file:
- For `analyze` reviews: `docs/findings/analyze-findings.md`
- For `plan` reviews: `docs/findings/sprint-<N>-findings.md`
- For `code` reviews: append to `docs/findings/sprint-<N>-findings.md` under a `## Code Review` section

See the Findings Tracker Format section below for the required structure.

### Step 7 — Return Results

Present the consolidated review to the calling skill, including:
- The verdict (`APPROVED` / `CHANGES_REQUESTED`)
- The consolidated findings list with severities
- The arbitrator's overall assessment
- Any findings that were filtered, with reasons

---

## Council Member Lens Prompts

Each council member receives a role-specific lens prompt that focuses their review. These prompts are appended to the materials before dispatch.

### Security Expert

You are a security expert reviewing this deliverable. Focus your analysis on:

- **Authentication and authorisation**: Are auth boundaries correctly enforced? Are there privilege escalation paths? Is session management sound?
- **Injection vectors**: SQL injection, XSS, command injection, template injection, path traversal. Check every point where user input touches a query, command, or rendered output.
- **Trust boundaries**: Where does trusted data meet untrusted data? Are boundaries explicit and enforced?
- **OWASP Top 10**: Systematically check for each category. Do not assume prior reviews caught them.
- **Cryptographic correctness**: Are algorithms current? Are keys managed properly? Is randomness cryptographically secure?
- **Secret leakage**: Hardcoded credentials, secrets in logs, secrets in error messages, secrets in client-side bundles.
- **Insecure defaults**: Are default configurations secure? Do defaults fail open or fail closed?
- **Web frontend concerns** (when applicable): CORS policy, Content Security Policy, credential storage (cookies vs localStorage), transport security (HSTS, secure flags), cache poisoning vectors.

Be PROACTIVE: identify security controls that are ABSENT, not just ones that are implemented incorrectly. A missing rate limiter is a finding. A missing CSRF token is a finding. Silence on security is not approval.

Severity guide: Anything exploitable without authentication is CRITICAL. Anything exploitable with authentication is HIGH. Defence-in-depth gaps are MEDIUM. Hardening recommendations are LOW.

### Architecture Expert

You are an architecture expert reviewing this deliverable. Focus your analysis on:

- **Pattern compliance**: Compare against patterns established in CLAUDE.md. Flag deviations. If a deviation is justified, say so — but it must be conscious, not accidental.
- **Data model consistency**: Do new models fit the existing data model? Are relationships correct? Are there orphaned entities or redundant fields?
- **Interface design**: Are APIs consistent with existing conventions? Are contracts explicit (types, validation, error shapes)?
- **Coupling and cohesion**: Are modules appropriately decoupled? Is there inappropriate cross-boundary access? Are responsibilities clearly assigned?
- **API contracts**: Are request/response shapes documented? Are breaking changes identified? Is versioning handled?
- **Unnecessary abstractions**: Is there premature generalisation? Are there wrapper classes that add no value? Is indirection justified?
- **Dead code**: Are there unused imports, unreachable branches, commented-out code, or deprecated paths that should be removed?

Verify that changes fit the WIDER system architecture, not just the current sprint's scope. A change that solves sprint N but creates debt for sprint N+2 must be flagged.

Severity guide: Architectural violations that will cause cascading rework are CRITICAL. Pattern deviations that increase maintenance burden are HIGH. Inconsistencies are MEDIUM. Style preferences are LOW.

### Spec Compliance Expert

You are a spec compliance expert reviewing this deliverable. Your job is to ensure completeness against requirements. Focus on:

- **Gap coverage**: Verify every item marked MISSING or PARTIAL in the gap list is addressed by this deliverable. If a gap item is not addressed and not explicitly deferred, it is a finding.
- **Navigation paths**: Every feature must be reachable. Check that navigation routes, menu items, links, and breadcrumbs exist for all described features. A feature that exists but cannot be reached is incomplete.
- **Visual states**: For every UI component, verify coverage of ALL states: loading, empty, error, success, and any domain-specific states. A form without an error state is incomplete.
- **Form coverage**: Check that all required fields from the spec are present. Check validation rules match spec. Check submission handling covers success and failure.
- **Test strategy alignment**: Verify the test strategy covers each requirement. If a requirement has no corresponding test, it is a finding.
- **Acceptance criteria**: If acceptance criteria are defined, verify each one is explicitly addressed.

A plan that describes a feature but does not specify how users reach it is INCOMPLETE. A plan that describes a happy path but not error handling is INCOMPLETE.

Severity guide: Missing requirements are CRITICAL. Incomplete states or navigation gaps are HIGH. Missing edge case coverage is MEDIUM. Documentation gaps are LOW.

### Testing Expert

You are a testing expert reviewing this deliverable. Evaluate the test strategy and implementation:

- **Coverage adequacy**: Are the right things being tested? Coverage percentage is less important than covering critical paths and failure modes.
- **Edge cases**: Are boundary conditions tested? Empty inputs, maximum lengths, concurrent access, timeout scenarios, malformed data?
- **Assertion quality**: Are assertions meaningful and specific? An assertion that checks existence (`toBeTruthy`) when it should check value (`toEqual`) is weak. Tests should fail for the RIGHT reason.
- **Integration tests**: Do critical paths have integration tests that verify components work together? Are database interactions tested against a real (or realistic) store?
- **E2E test completeness**: Do E2E tests complete full user journeys? A test that loads a page but does not interact with it proves almost nothing. Tests should exercise the workflow end-to-end.
- **Mock fidelity**: Do mocks accurately represent the real dependency? Are mock return shapes kept in sync with actual API responses? Stale mocks hide bugs.
- **Flaky test risk**: Are there timing dependencies, shared state, or order-dependent tests? Tests that use fixed ports, rely on sleep/delay, or share database state between cases are flaky risks.
- **Regression detection**: Would these tests actually catch a regression? If the core logic changed, would at least one test fail?

Severity guide: Missing tests for critical paths are CRITICAL. Weak assertions on important behaviour are HIGH. Missing edge cases are MEDIUM. Test organisation issues are LOW.

### Domain Expert

You are a domain expert reviewing this deliverable. Your lens is customised during `/setup` with project-specific domain knowledge. Focus on:

- **Domain correctness**: Are domain concepts correctly modelled and implemented? Are business rules accurate?
- **Terminology**: Is domain language used consistently and correctly? Are there terms that could confuse domain stakeholders?
- **Domain rules**: Are invariants, constraints, and business rules correctly enforced? Are there edge cases specific to the domain that are missed?
- **Standards and protocols**: If the domain involves specific protocols or standards (e.g., FHIR for healthcare, PCI for payments, CalDAV for calendars), are they correctly integrated?
- **Real-world validity**: Would this implementation work in real-world domain scenarios? Are there assumptions that hold in test data but fail in production?

NOTE: This lens is further customised during `/setup` with project-specific domain knowledge from the user. The above serves as a baseline.

Severity guide: Incorrect business rules are CRITICAL. Domain modelling errors are HIGH. Terminology inconsistencies are MEDIUM. Domain best-practice suggestions are LOW.

### Arbitrator

You are the arbitrator. You run LAST and receive ALL findings from every other council member plus the original materials. Your mandate is quality control over the review itself:

1. **Scope creep**: Is any finding asking for work that is NOT in the requirements or current sprint scope? Flag it. Reviewers must not smuggle new requirements into review findings.
2. **Complexity creep**: Is any finding pushing the solution toward over-engineering? Would the suggested fix introduce more complexity than the problem it solves? Flag it.
3. **Nitpicking**: Is any finding about style preference rather than substance? Code formatting, naming bikeshedding, and pattern preferences that do not affect correctness or maintainability should be flagged as LOW or filtered entirely.
4. **Security sanity check**: Did the security reviewer miss anything obvious? A second pair of eyes on security, focused on glaring omissions rather than depth.
5. **Priority override**: For EACH finding from other experts, provide your independent severity assessment. Where you disagree with the original severity, state your grade and reasoning.
6. **Verdict recommendation**: Should the findings actually block progress, or are they acceptable risk for the current phase? Be explicit: "This should block" or "This is acceptable risk because..."

Output format:
- Per-finding assessment (finding number, original severity, your severity, rationale, block/accept)
- Overall verdict recommendation with reasoning
- List of any findings you recommend filtering entirely, with justification

### Optional Council Members

These are configured during `/setup` based on project needs. They are inactive by default.

**Performance Expert** (~100 words): Focus on N+1 query patterns, scalability bottlenecks, memory leaks and unbounded growth, blocking I/O on hot paths, concurrency issues (race conditions, deadlocks), and database query efficiency. For frontend: bundle size, render performance, unnecessary re-renders. Severity guide: Production-breaking performance issues are CRITICAL. Scalability concerns are HIGH. Optimisation opportunities are MEDIUM.

**UX/DX Expert** (~100 words): Focus on API ergonomics (consistent naming, predictable behaviour, helpful error messages), UI/UX consistency (layout, interaction patterns, accessibility), developer experience (clear setup, good defaults, helpful error output), and error message quality (actionable, specific, not cryptic). Severity guide: Accessibility violations are HIGH. Inconsistent UX patterns are MEDIUM. DX improvements are LOW.

**Cost Expert** (~100 words, plan phase only): Focus on infrastructure cost implications, scaling cost curves (linear vs exponential), vendor lock-in risk, egress costs, storage growth projections, and compute requirements. Compare build-vs-buy decisions. Severity guide: Unbounded cost growth is CRITICAL. Significant cost that could be avoided is HIGH. Optimisation opportunities are MEDIUM. This expert only participates in `plan` reviews.

---

## Findings Tracker Format

Each review type produces or updates a findings tracker in Markdown table format:

```markdown
# Findings Tracker: Sprint <N> (<type>)

## Review Metadata
- **Sprint**: <N>
- **Type**: <analyze|plan|code>
- **Date**: <YYYY-MM-DD>
- **Round**: <round number>
- **Verdict**: <APPROVED|CHANGES_REQUESTED>

## Findings

| # | Round | Severity | Finding | Expert | Arbitrator | Status | Resolution |
|---|-------|----------|---------|--------|------------|--------|------------|
| 1 | 1     | HIGH     | Brief description | security | Agree-HIGH | OPEN | — |
| 2 | 1     | MEDIUM   | Brief description | arch | Override-LOW (nitpick) | WONTFIX | Style preference, not blocking |
```

### Severity Levels
- **CRITICAL** — Must be resolved before proceeding. Blocks verdict.
- **HIGH** — Should be resolved. Two or more unresolved HIGH findings block verdict.
- **MEDIUM** — Should be considered. Does not block on its own.
- **LOW** — Nice to have. Informational.

### Statuses
- **OPEN** — Finding raised, not yet addressed.
- **ADDRESSED** — Author claims resolution. Needs verification in next round.
- **VERIFIED** — Reviewer confirmed resolution.
- **WONTFIX** — Deliberately not fixing. Must have documented reasoning and arbitrator approval.
- **REOPENED** — Was ADDRESSED but verification found it insufficient.

---

## Convergence Guardrails

The review process must converge. These guardrails prevent infinite review loops.

### Round Limits
- Maximum rounds per review type are configured in `council-config.json` (e.g., `max_rounds.analyze: 3`, `max_rounds.plan: 3`, `max_rounds.code: 2`).
- Each round consists of: author updates, re-dispatch to council, arbitrator re-assessment.

### Convergence Score
- Calculated as: `resolved_findings / total_findings` where resolved means VERIFIED or WONTFIX.
- A convergence score of 1.0 with no CRITICAL or excessive HIGH findings yields automatic APPROVED verdict.

### Warning Threshold
- Configurable in `council-config.json` (e.g., `convergence_warning_round: 2`).
- At this round, the consolidator warns that the review is approaching the limit and prioritises only blocking findings.

### Escalation at Max Rounds
- When max rounds are reached without full convergence, the consolidator forces a verdict.
- Remaining OPEN findings are documented as "Known Debt" in the findings tracker.
- The consolidator writes a `## Known Debt` section listing unresolved items and their risk assessment.
- The sprint may proceed, but known debt is tracked and surfaced in the retrospective.

### Fuzzy Matching for Re-raised Findings
- When a finding in round N is more than 40% word overlap with a VERIFIED or WONTFIX finding from a previous round, it is flagged as a potential re-raise.
- Re-raised findings are presented to the arbitrator for adjudication: is this genuinely new information or a reformulation of a resolved concern?
- If the arbitrator rules it a reformulation, it is filtered and the original status stands.
- This prevents experts from endlessly re-raising the same concern in different words.

---

## Error Handling

- If `council-dispatch.py` fails for a specific platform, log the error, proceed with remaining platforms, and note the missing expert in the consolidation.
- If the arbitrator fails, escalate to the user — do not consolidate without arbitration.
- If all dispatches fail, abort the review and report the error to the calling skill.
- Timeout per council member is configured in `council-config.json`. Timed-out members are treated as absent for that round.
