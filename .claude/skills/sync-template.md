# /sync-template — Sync Workflow Skills with Upstream Template

Trigger: User wants to pull latest workflow improvements from the template, or push skill improvements back to the template.

## Purpose

Maintains a bidirectional sync between a project repository and the `workflow_template` upstream. Generic workflow files (skills, workflow-rules.md) are shared; project-specific files (CLAUDE.md Project Configuration, docs/) stay local.

## Shared Files (synced with template)

These files are generic and should be identical across all projects using the template:

```
.claude/workflow-rules.md          # Workflow phases, gates, enforcement rules
.claude/skills/analyze.md          # Deep analysis & documentation
.claude/skills/e2e.md              # End-to-end integration tests
.claude/skills/implement.md        # Parallel code + test implementation
.claude/skills/phase-0.md          # Feature inventory & gap analysis
.claude/skills/plan.md             # Multi-perspective planning
.claude/skills/postmortem.md       # Bug postmortem & workflow improvement
.claude/skills/pre-deploy.md       # Pre-deployment gate check
.claude/skills/review.md           # Multi-perspective code review
.claude/skills/spec-compliance.md  # Verify implementation matches spec
.claude/skills/sync-template.md    # This file
.claude/skills/ui-review.md        # UI quality review
```

## Project-Specific Files (never pushed to template)

These files contain project-specific content and stay in the project repo only:

```
CLAUDE.md                          # Project Configuration section
docs/                              # Analysis corpus, gap lists, bug patterns
```

## Prerequisites

The project repo must have the template configured as a remote:

```bash
git remote add template https://github.com/tf-pwr-up/workflow_template.git
```

Verify with: `git remote -v | grep template`

## Instructions

### Mode: Pull (get latest from template)

When the user runs `/sync-template pull` or wants to update their workflow skills:

1. **Fetch template changes**:
   ```bash
   git fetch template
   ```

2. **Check for differences** in shared files:
   ```bash
   git diff HEAD template/master -- .claude/workflow-rules.md .claude/skills/
   ```

3. **If no differences**: Report "Already up to date" and stop.

4. **If differences exist**: Show the user a summary of what changed (which files, brief description of changes).

5. **Apply changes** by checking out the template versions of shared files:
   ```bash
   git checkout template/master -- .claude/workflow-rules.md .claude/skills/
   ```

6. **Commit the update**:
   ```
   Update workflow skills from template

   Pulled latest skill definitions from workflow_template.
   ```

7. **Report** what was updated.

### Mode: Push (contribute improvements back to template)

When the user runs `/sync-template push` or wants to share skill improvements with the template:

1. **Identify changes** to shared files since the last sync:
   ```bash
   git fetch template
   git diff template/master -- .claude/workflow-rules.md .claude/skills/
   ```

2. **Review each changed file** to verify the change is generic (not project-specific):
   - Does it reference project-specific paths, components, or patterns? → REJECT
   - Does it add a new generic check, fix a skill bug, or improve a workflow rule? → ACCEPT
   - Does it add a prevention rule from `/postmortem` that uses generic pattern names? → ACCEPT
   - Does it add a prevention rule with project-specific examples? → NEEDS EDIT (genericise first)

3. **If changes are clean**: Present the diff to the user and ask for confirmation.

4. **If changes need genericising**: Edit the skill files to remove project-specific references before pushing. Show the user the genericised version for approval.

5. **Push to template** on a branch:
   ```bash
   # Create a temporary worktree for the template repo
   cd /tmp
   git clone https://github.com/tf-pwr-up/workflow_template.git workflow_template_sync
   cd workflow_template_sync
   git checkout -b skill-update-YYYY-MM-DD

   # Copy shared files from the project
   cp <project>/.claude/workflow-rules.md .claude/workflow-rules.md
   cp <project>/.claude/skills/*.md .claude/skills/

   # Commit and push
   git add .claude/
   git commit -m "Update skills from <project-name>"
   git push origin skill-update-YYYY-MM-DD

   # Clean up
   rm -rf /tmp/workflow_template_sync
   ```

6. **Create a PR** on the template repo:
   ```bash
   gh pr create --repo tf-pwr-up/workflow_template --title "Skill updates from <project>" --body "..."
   ```

7. **Report** the PR URL to the user.

### Mode: Status (check sync state)

When the user runs `/sync-template status`:

1. **Fetch template**:
   ```bash
   git fetch template
   ```

2. **Compare shared files**:
   ```bash
   git diff HEAD template/master -- .claude/workflow-rules.md .claude/skills/
   ```

3. **Report**:
   - Files that are newer in template (pull needed)
   - Files that are newer locally (push candidate)
   - Files that are identical (in sync)

## When to Invoke

- After pulling the template: run `/sync-template pull` to get the latest skills
- After a `/postmortem` adds a new prevention rule: run `/sync-template push` to share it
- After improving a skill during development: run `/sync-template push`
- Periodically: run `/sync-template status` to check if you're behind
