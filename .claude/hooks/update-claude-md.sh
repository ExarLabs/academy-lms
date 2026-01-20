#!/bin/bash
set -e

# Get staged files (excluding CLAUDE.md itself to avoid loops)
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -v "CLAUDE.md" || true)

if [ -z "$STAGED_FILES" ]; then
    echo "No relevant staged files to analyze"
    exit 0
fi

# Get the diff content for context
DIFF_CONTENT=$(git diff --cached --diff-filter=ACMR -- $STAGED_FILES)

# Invoke Claude Code to analyze and update CLAUDE.md
claude -p "You are analyzing staged git changes to determine if CLAUDE.md needs updating.

## Staged Files:
$STAGED_FILES

## Diff Content:
$DIFF_CONTENT

## Task:
1. Analyze if these changes affect project architecture, key files, APIs, or patterns documented in CLAUDE.md
2. If updates are needed, use the Edit tool to update CLAUDE.md with accurate information
3. Focus on: new files/directories, changed APIs, new integrations, architectural changes
4. Do NOT update for minor changes (bug fixes, formatting, small refactors)
5. Keep CLAUDE.md concise - only document what helps understand the codebase

If no updates needed, just say 'No CLAUDE.md updates required' and exit." \
    --allowedTools "Read,Edit" \
    --max-turns 5

# Stage CLAUDE.md if it was modified
if git diff --name-only CLAUDE.md | grep -q "CLAUDE.md"; then
    git add CLAUDE.md
    echo "CLAUDE.md was updated and staged"
fi

exit 0
