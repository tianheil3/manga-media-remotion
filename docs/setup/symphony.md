# Symphony Setup

This repository now includes a root-level [WORKFLOW.md](/mydata/projects/manga-media-remotion/.worktrees/symphony-setup/WORKFLOW.md) based on the official Symphony Elixir README:

- https://github.com/openai/symphony/blob/main/elixir/README.md

## What Was Added

- `WORKFLOW.md` at the repository root
- Repository-specific instructions pointing Symphony agents to the existing design and implementation plan docs
- Default Linear state mapping aligned with the README example, including `Human Review`, `Merging`, and `Rework`

## Values You Still Need To Provide

- `LINEAR_API_KEY`
- `SYMPHONY_WORKSPACE_ROOT`
- `tracker.project_slug` in `WORKFLOW.md`

Suggested values:

- `SYMPHONY_WORKSPACE_ROOT=~/code/manga-media-remotion-workspaces`

## Notes

- The current workflow intentionally does not commit repository-local Symphony skills under `.codex/skills/`. The official README marks those skills as optional.
- If you want the full repo-local Symphony skill set later, the `.gitignore` rule for `.codex/` will need to be narrowed first.
- Symphony will not be able to operate correctly until `tracker.project_slug` is replaced with your actual Linear project slug.

## Running Symphony

From a local checkout of `openai/symphony/elixir`:

```bash
export LINEAR_API_KEY=...
export SYMPHONY_WORKSPACE_ROOT=~/code/manga-media-remotion-workspaces

./bin/symphony /path/to/this-repo/WORKFLOW.md
```
