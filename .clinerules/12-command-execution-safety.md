# Command execution safety: no inline interpreter heredocs

This module defines non-negotiable command execution constraints.

## Hard constraints
- **Must not** run inline interpreter heredocs such as `python - <<'PY' ... PY`.
- **Must not** use equivalent stdin-fed inline interpreter patterns for Python execution.
- **Must** write Python code to a temporary script file and execute that file instead.
- **Must** prefer direct, non-interactive CLI commands where possible before creating any script.
- **Must** run git commands in non-interactive mode whenever possible and avoid waiting for user input.
- **Must** disable git paging when command output could invoke a pager (for example, `git --no-pager <command>`).
- **Must not** run git commands that open interactive editors/prompts unless explicitly requested by the user.
- **Should** remove temporary script files after execution unless retention is needed for debugging.

## Required pattern
✅ **Allowed approach**
1. Create a temporary `.py` file.
2. Execute it with `python /absolute/path/to/temp_script.py`.
3. Capture output/exit code as needed.
4. Clean up the temporary file when done.

## Disallowed pattern
❌ **Forbidden approach**
- `python - <<'PY'`
- Any multiline Python passed directly via stdin to the interpreter.

## Git non-interactive pattern
✅ **Preferred approach**
- `git --no-pager diff --stat`
- `git --no-pager log --oneline -n 20`
- `git commit --no-edit` (only when this behavior is explicitly appropriate)

❌ **Avoid when not explicitly requested**
- Commands that trigger pagers or interactive editors and wait for user input.

## Enforcement
- Treat this rule as a hard constraint in reviews and operational practice.
- Any deviation must be explicitly requested and documented in handoff/PR notes.
