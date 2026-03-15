# Backlog Promoter Setup

The backlog promoter is a small repository script that promotes configured Linear issues from `Backlog` to `Todo` after all configured prerequisite issues are `Done`.

## Prerequisites

- `LINEAR_API_KEY`
- access to the repository checkout
- a checked-in dependency config at `config/backlog-promoter.json`

## One-Shot Dry Run

Use this before enabling real updates:

```bash
python scripts/backlog-promoter.py --once --dry-run
```

This loads `config/backlog-promoter.json`, evaluates which issues are eligible, and reports the result without changing Linear.

## One-Shot Real Promotion

```bash
python scripts/backlog-promoter.py --once
```

## Polling Mode

Run the promoter continuously when you want unattended ticket staging:

```bash
python scripts/backlog-promoter.py --poll --interval-seconds 30
```

## Configuration

The promoter reads:

- `config/backlog-promoter.json`

The config defines:

- the Linear project slug
- the team key
- the source and target state names
- explicit `issue -> dependsOn[]` promotion rules

## Safe Rollout

1. Verify `LINEAR_API_KEY` is available in the environment.
2. Run `python scripts/backlog-promoter.py --once --dry-run`.
3. Confirm the expected backlog issues would be promoted.
4. Run `python scripts/backlog-promoter.py --once` once for a real promotion.
5. Only then switch to `--poll` mode for unattended operation.
