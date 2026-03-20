# Bug Pattern Registry

Updated by `/retrospective` skill. Each sprint retrospective reviews bugs encountered during the sprint and records recurring patterns here. These patterns are used by agents during `/develop` to proactively avoid known issues.

## Format

| Date | Pattern | Sprint | Summary | Root Cause | Prevention Rule | Skill Updated |
|------|---------|--------|---------|------------|-----------------|---------------|

## Column Definitions

- **Date**: When the pattern was identified (YYYY-MM-DD)
- **Pattern**: Short identifier for the pattern (e.g., `IMPORT_PATH_MISMATCH`, `MISSING_NULL_CHECK`)
- **Sprint**: Sprint number where the bug was encountered
- **Summary**: One-line description of the bug
- **Root Cause**: Why the bug occurred (e.g., "Agent relied on memory instead of reading file")
- **Prevention Rule**: Specific rule agents must follow to prevent recurrence (e.g., "Always read target file before writing imports")
- **Skill Updated**: Which skill was updated to enforce the prevention rule, or "N/A" if manual enforcement

## Registry

| Date | Pattern | Sprint | Summary | Root Cause | Prevention Rule | Skill Updated |
|------|---------|--------|---------|------------|-----------------|---------------|
