# Symphony Land Flow

This repository treats `Merging` as a landing-only state.

## Repository Land Behavior

Run `bash scripts/land.sh [issue-branch]` from the issue workspace.

The script performs this sequence:

1. Determine the issue work branch or accept it as an argument.
2. Run `scripts/verify-strict.sh` on the work branch.
3. Fetch `origin/main`.
4. Reset local `main` to `origin/main`.
5. Squash-merge the issue branch into `main`.
6. Create one final land commit.
7. Push `main` to `origin/main`.

The default land commit message is issue-aware when the branch name contains an identifier like `TIA-16`.

## Merging Rules

- Do not expand scope during `Merging`.
- Do not switch the target branch away from `main`.
- Record validation, fetch, merge, or push blockers in the Linear workpad.
- Move the issue to `Rework` when a blocker requires more code changes.
- Mark the issue `Done` only after push succeeds.

## Failure Signals

`scripts/land.sh` prints `LAND_STATUS=success` only after `git push origin main` succeeds.

On failure it prints `LAND_STATUS=failed` and exits non-zero so Symphony can keep the issue active and preserve the blocker context in the workpad.
