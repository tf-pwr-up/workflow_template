---
name: sync
description: "Bidirectional template sync — pull workflow updates from template, push improvements back"
---

# Bidirectional Template Sync

Manages synchronisation between a project's workflow files and the shared workflow template repository. Ensures workflow improvements flow in both directions: template updates reach projects, and project-discovered improvements reach the template.

**Invocation:**
- `/sync pull` — Pull latest template updates into the current project.
- `/sync push` — Push local workflow improvements back to the template.
- `/sync status` — Check the sync state of all shared files.

---

## File Classification

### Shared Files (Synced)

These files are owned by the workflow template and kept in sync across all projects:

| File / Pattern                           | Purpose                          |
|------------------------------------------|----------------------------------|
| `.claude/workflow-rules.md`              | Core workflow rules              |
| `.claude/skills/**/*.md`                 | All skill definitions            |
| `scripts/council-dispatch.py`            | Council API dispatch script      |
| `scripts/council-check.sh`              | Council health check script      |
| `.github/workflows/workflow-gate.yml`    | CI workflow gate                 |

### Project-Specific Files (Never Synced)

These files are owned by the project and never pushed to or pulled from the template:

| File / Pattern                           | Purpose                          |
|------------------------------------------|----------------------------------|
| `CLAUDE.md`                              | Project-level context            |
| `council-config.json`                    | Project council configuration    |
| `docs/**`                                | All project documentation        |
| `.claude/settings.json`                  | Project Claude settings          |

---

## Mode: `/sync pull`

Pull workflow updates from the template repository into the current project.

### Step 1 — Verify Template Remote

Check that the template remote is configured:

```bash
git remote -v | grep workflow
```

Expected output should show a remote named `workflow` (or `workflow-template`) pointing to the template repository.

If the remote does not exist:
- Ask the user for the template repository URL.
- Add it: `git remote add workflow <url>`
- Verify: `git remote -v | grep workflow`

### Step 2 — Fetch Latest

Fetch the latest state from the template remote:

```bash
git fetch workflow
```

If fetch fails (auth error, network error, repo not found), report the specific error and exit.

### Step 3 — Compare Shared Files

For each shared file, compare the local version against the template version:

```bash
git diff HEAD workflow/main -- <file>
```

Categorise each file:
- **Up to date**: No differences.
- **Template ahead**: Template has changes not in the local project.
- **Local ahead**: Local project has changes not in the template (potential push candidate).
- **Diverged**: Both sides have changes — requires conflict resolution.

Present the comparison summary to the user.

### Step 4 — Merge Changes

For files where the template is ahead:

1. Show the diff to the user for each file.
2. Apply the template version: `git checkout workflow/main -- <file>`
3. Stage the updated file.

For diverged files:
1. Attempt a three-way merge using the common ancestor.
2. If the merge is clean, show the result to the user for confirmation.
3. If the merge has conflicts, present the conflicts to the user for manual resolution.
4. Do not auto-resolve conflicts — every conflict must be reviewed.

Skip files where the local project is ahead (these are push candidates, not pull targets).

### Step 5 — Resolve Conflicts

For any files with merge conflicts:

1. Display the conflict markers with surrounding context.
2. Ask the user to choose for each conflict:
   - **Take template**: Accept the template version.
   - **Keep local**: Keep the local version (mark as project-specific override if it is a deliberate deviation).
   - **Manual edit**: Let the user provide a custom resolution.
3. After all conflicts are resolved, stage the files.

### Step 6 — Commit Update

Create a commit with all pulled changes:

```
chore: sync workflow files from template

Pulled updates:
- <list of updated files>

Conflicts resolved:
- <list of conflict resolutions, if any>
```

---

## Mode: `/sync push`

Push local workflow improvements back to the template repository.

### Step 1 — Identify Changes

Find all shared files that have local modifications not present in the template:

```bash
git diff workflow/main -- <shared-file-list>
```

If no shared files have local changes, report "Nothing to push" and exit.

### Step 2 — Verify Changes Are Generic

For each changed shared file, review the diff to determine if the changes are generic (applicable to all projects) or project-specific. Apply these filters:

**Automatically filtered (project-specific):**
- Changes to domain expert lens prompts that reference project-specific domain terms.
- Bug patterns that reference project-specific code, file paths, or features.
- Configuration values that are project-specific (API keys, endpoints, project names).

**Automatically included (generic):**
- Improvements to core lens prompts (security, architecture, testing, spec compliance, arbitrator).
- New convergence rules or guardrails.
- Bug fixes in dispatch or check scripts.
- New or improved skill definitions.

**Requires user judgment:**
- Changes that mix generic and project-specific content.
- New bug patterns that MIGHT be generic (e.g., "always check for N+1 queries in list endpoints").
- Lens prompt refinements that reference specific technologies (generic if the technology is common, project-specific if niche).

Present uncertain changes to the user and ask for a classification.

### Step 3 — Filter and Present

Show the user the filtered set of changes that will be pushed:

```
## Changes to push to template:

### .claude/skills/council-review/SKILL.md
<diff showing only generic changes>

### scripts/council-dispatch.py
<diff showing bug fix>

## Filtered out (project-specific):
- docs/bug-patterns.md: Project-specific bug pattern for Stripe webhook handling
- Domain expert lens: References to FHIR protocol
```

Wait for user approval before proceeding.

### Step 4 — Create Branch and Push

1. Create a branch on the template remote:
   ```bash
   git push workflow HEAD:refs/heads/sync/<project-name>-<date>
   ```
   Where `<project-name>` is derived from the current repository name and `<date>` is the current date in `YYYY-MM-DD` format.

2. If the push fails due to permissions, report the error and suggest the user create a fork or request write access.

### Step 5 — Create Pull Request

Create a PR on the template repository:

```bash
gh pr create \
  --repo <template-repo> \
  --head sync/<project-name>-<date> \
  --base main \
  --title "Workflow sync from <project-name>" \
  --body "<description of changes>"
```

The PR body should include:
- List of files changed.
- Summary of each change.
- Origin context (which sprint or retrospective identified the improvement).

Report the PR URL to the user.

---

## Mode: `/sync status`

Check the sync state of all shared files without making any changes.

### Step 1 — Compare Against Template

For each shared file, determine its sync state:

```bash
git fetch workflow
git diff HEAD workflow/main -- <file>
```

### Step 2 — Report Status

Present a status table:

```markdown
## Workflow Sync Status

| File                                      | Status       | Details                    |
|-------------------------------------------|--------------|----------------------------|
| `.claude/workflow-rules.md`               | In sync      | —                          |
| `.claude/skills/council-review/SKILL.md`  | Local ahead   | Lens prompt refinement     |
| `.claude/skills/review/SKILL.md`          | In sync      | —                          |
| `scripts/council-dispatch.py`             | Template ahead| Bug fix in error handling  |
| `scripts/council-check.sh`               | Diverged     | Both sides modified        |
| `.github/workflows/workflow-gate.yml`     | In sync      | —                          |
```

For files that are "local ahead", note whether the changes look generic or project-specific.
For files that are "template ahead", note what changed in the template.
For diverged files, warn that a pull will require conflict resolution.

### Step 3 — Recommendations

Based on the status, provide recommendations:

- If template is ahead on any files: "Run `/sync pull` to get the latest workflow updates."
- If local is ahead on generic changes: "Run `/sync push` to share your improvements with the template."
- If files are diverged: "Run `/sync pull` first to resolve divergences, then `/sync push` if local improvements remain."
- If everything is in sync: "All workflow files are in sync with the template."

---

## Error Handling

- **No template remote**: Prompt the user to add one. Provide the command.
- **Fetch failures**: Report the specific git error (auth, network, not found). Suggest remediation.
- **Push permission denied**: Suggest forking the template or requesting write access.
- **gh CLI not available**: For PR creation, fall back to providing the user with a URL to create the PR manually.
- **Dirty working tree**: If there are uncommitted changes to shared files, warn the user and ask whether to stash, commit, or abort.
- **No common ancestor**: If the project was not cloned from the template (no shared git history), fall back to file-level comparison rather than git diff. Warn the user that conflict resolution will be manual.

---

## Sync Metadata

After each successful pull or push, record the sync state in `council-config.json`:

```json
{
  "last_sync": {
    "direction": "pull",
    "date": "2026-03-20",
    "template_commit": "<sha>",
    "files_updated": [".claude/skills/council-review/SKILL.md", "scripts/council-dispatch.py"]
  }
}
```

This metadata is used by `/sync status` to provide accurate reporting and by `/retrospective` to check if workflow changes have been synced.
