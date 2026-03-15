# Symphony Setup

This repository keeps the Symphony configuration in the repository root:

- `WORKFLOW.md`
- `scripts/verify-strict.sh`
- `scripts/land.sh`
- `scripts/backlog-promoter.py`
- `docs/setup/strict-validation.md`
- `docs/setup/backlog-promoter.md`
- `docs/setup/symphony-land.md`
- `docs/verification/symphony-auto-land.md`

The workflow is based on the official Symphony Elixir README:

- https://github.com/openai/symphony/blob/main/elixir/README.md

## What This Repository Adds

- Repository-specific instructions pointing Symphony agents to the existing design and implementation plan docs
- Default Linear state mapping aligned with the README example, including `Human Review`, `Merging`, and `Rework`
- A repository-defined strict validation gate in `scripts/verify-strict.sh`
- A repository-defined landing flow in `scripts/land.sh`
- A safe verification checklist in `docs/verification/symphony-auto-land.md`

## Values You Still Need To Provide

- `LINEAR_API_KEY`
- `SYMPHONY_WORKSPACE_ROOT`

Suggested values:

- `SYMPHONY_WORKSPACE_ROOT=~/code/manga-media-remotion-workspaces`

## Merging Behavior

`Merging` is a landing-only state in this repository.

Before relying on `scripts/verify-strict.sh` or `scripts/land.sh`, install the repository Node workspace dependencies:

```bash
npm install
```

1. Symphony runs `scripts/verify-strict.sh`.
2. Symphony runs `scripts/land.sh` from the issue workspace.
3. The script fetches `origin/main`, resets local `main`, squash-merges the issue branch, and pushes `main`.
4. Symphony marks the issue `Done` only after the push succeeds.

Use these docs together:

- `docs/setup/strict-validation.md`
- `docs/setup/backlog-promoter.md`
- `docs/setup/symphony-land.md`
- `docs/verification/symphony-auto-land.md`

## Notes

- The current workflow intentionally does not commit repository-local Symphony skills under `.codex/skills/`. The official README marks those skills as optional.
- If you want the full repo-local Symphony skill set later, the `.gitignore` rule for `.codex/` will need to be narrowed first.
- `tracker.project_slug` is already set in `WORKFLOW.md` for this repository.
- Add issue-specific `Validation`, `Testing`, or `Test Plan` commands through `STRICT_VALIDATION_EXTRA_COMMANDS` when you need `scripts/verify-strict.sh` to run more than the default suite.

## Running Symphony

From a local checkout of `openai/symphony/elixir`:

```bash
export LINEAR_API_KEY=...
export SYMPHONY_WORKSPACE_ROOT=~/code/manga-media-remotion-workspaces

./bin/symphony /path/to/this-repo/WORKFLOW.md
```
