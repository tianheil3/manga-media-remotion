# Symphony Auto-Land Design

**Date:** 2026-03-15

**Status:** Approved

## Goal

Make Symphony close the loop for this repository by automatically landing work to `main` when a Linear issue enters `Merging`, using strict validation and squash commits.

## Problem

Symphony currently performs implementation work inside issue-specific worktrees and branches, but it does not have a concrete repository-defined landing path. As a result, issues can remain in `Merging` for long periods even after implementation is complete.

The current `WORKFLOW.md` contains a generic rule that says to follow a `land` workflow if available, but this repository does not define one. The result is ambiguous behavior at the exact stage where deterministic behavior is most important.

## Desired Behavior

When a task enters `Merging`, Symphony should stop doing normal implementation work and execute a repository-defined land flow:

1. Identify the active work branch for the issue.
2. Run strict validation on the work branch.
3. Fetch and synchronize with `origin/main`.
4. Reset local `main` to `origin/main` inside the task workspace.
5. Squash-merge the work branch into `main`.
6. Create a single commit for the landed work.
7. Push `main` to `origin/main`.
8. Mark the Linear issue `Done` only after push succeeds.

If any step fails, Symphony must not close the issue and must record the failure in the workpad.

## Scope

### Included

- Repository-defined strict verification script.
- Repository-defined land script for squash merge to `main`.
- Explicit `Merging` instructions in `WORKFLOW.md`.
- Failure handling rules for validation, merge conflicts, fetch failures, and push failures.

### Excluded

- Pull-request-based merge flows.
- Multi-branch release workflows.
- Automatic changelog generation.
- Automatic rollback logic after a bad push.

## Merge Strategy

The approved merge strategy is:

- `Merging` means `strictly verify, squash into main, push`.
- Preserve no intermediate agent commits on `main`.
- Use one final commit per issue landing.

This keeps `main` readable and avoids long noisy commit chains from autonomous task execution.

## Validation Policy

The approved validation mode is `strict`.

Strict validation is defined as:

- A repository-owned default validation suite.
- Plus any additional `Validation`, `Testing`, or `Test Plan` commands described in the issue.
- Every required command must pass before landing is allowed.

The validation definition should live in a repository script such as `scripts/verify-strict.sh`.

## Landing Rules

`Merging` is a special workflow state with different rules from normal development.

### Allowed actions in `Merging`

- Run validation.
- Synchronize with remote main.
- Perform squash merge.
- Commit and push.
- Record merge blockers.

### Forbidden actions in `Merging`

- Implement unrelated new features.
- Expand scope beyond merge blockers.
- Change the target branch away from `main`.

If a failure exposes a real code problem, the issue should move back to `Rework` rather than silently accumulating extra implementation during `Merging`.

## Proposed Repository Additions

### `scripts/verify-strict.sh`

Responsibilities:

- Run repository default strict validation commands.
- Optionally execute issue-provided validation commands if they are made available to the script.
- Exit non-zero on any failure.

### `scripts/land.sh`

Responsibilities:

- Detect the current issue work branch.
- Run strict verification on that branch.
- Fetch `origin/main`.
- Reset local `main` to `origin/main` in the task workspace.
- Squash-merge the work branch into `main`.
- Create a final commit message.
- Push `main` to `origin/main`.

### `WORKFLOW.md`

Responsibilities:

- Explicitly define the repository landing path.
- Tell Symphony that `Merging` must use the repository land script.
- Require strict verification before landing.
- Require successful push before closing the issue.
- Define fallback behavior when network, auth, or merge conflicts block landing.

## Failure Handling

### Fetch failure

- Do not merge.
- Do not push.
- Record blocker in workpad.
- Keep the issue active.

### Strict validation failure

- Do not merge.
- Record the failed command and summary in workpad.
- Keep issue in `Merging` or move to `Rework`.

### Squash merge conflict

- Do not push.
- Record conflict details in workpad.
- Move issue to `Rework`.

### Push failure

- Do not mark `Done`.
- Record the failure in workpad.
- Keep issue in `Merging`.

## Workflow State Semantics

- `Todo`, `In Progress`, `Rework`: normal implementation states.
- `Human Review`: waiting for human review.
- `Merging`: landing-only state.
- `Done`: only after successful push to `origin/main`.

## Recommended Implementation Shape

The smallest effective implementation is:

1. Add `scripts/verify-strict.sh`.
2. Add `scripts/land.sh`.
3. Update `WORKFLOW.md` to make the repository land flow explicit.

This is preferred over relying purely on prompt text because merge behavior must be deterministic and auditable.

## Constraints

- The land workflow must be local to this repository and not depend on undefined external skills.
- The land flow must operate inside the issue workspace, not the developer's main working directory.
- The land flow must only update Linear to `Done` after push succeeds.
