# Backlog Promoter Design

**Date:** 2026-03-15

**Status:** Approved

## Goal

Add a repository-managed backlog promoter that automatically moves selected Linear issues from `Backlog` to `Todo` after all configured prerequisite issues are `Done`, so Symphony can continue unattended work without a human manually re-staging the next ticket.

## Product Need

The current Symphony integration only works on Linear issues that are already in an active state. `Backlog` is intentionally excluded from the active state set in `WORKFLOW.md`, which prevents Symphony from picking up downstream tickets automatically after prerequisite tickets complete.

This is correct for safety, but it leaves a gap in automation:

- a small first wave of tickets can be activated manually
- follow-up tickets can be created and prioritized in `Backlog`
- nothing promotes those follow-up tickets into `Todo` when the required prerequisites are finished

The backlog promoter closes that gap without changing Symphony itself.

## Recommended Architecture

### Component Split

Implement the promoter as a standalone repository script with a repository-managed dependency configuration.

- Config file: `config/backlog-promoter.json`
- Executable script: `scripts/backlog-promoter.py`

The promoter is intentionally external to Symphony:

- Symphony continues to own active issue execution
- the promoter only decides when a configured backlog issue is eligible to become `Todo`
- issue landing, validation, review, and merges remain unchanged

### Why This Shape

This is the smallest viable extension to the current unattended workflow.

It keeps the responsibility boundary clean:

- Symphony handles active tickets
- the promoter manages the `Backlog -> Todo` transition
- Linear remains the shared system of record

It also keeps dependency rules versioned in Git, reviewable in pull requests, and independent from fragile issue-description parsing.

## Non-Goals

The first version must not:

- create Linear issues
- update issues in any state other than the configured source state
- move issues directly to `In Progress`
- replace Symphony execution
- land branches
- infer dependencies from issue descriptions, labels, or comments
- support complex boolean dependency expressions such as `A or B`

## Configuration Model

The promoter reads a single repository configuration file.

Suggested shape:

```json
{
  "version": 1,
  "projectSlug": "manga-media-remotion-e37e12494859",
  "teamKey": "TIA",
  "sourceState": "Backlog",
  "targetState": "Todo",
  "promotions": [
    {
      "issue": "TIA-34",
      "dependsOn": ["TIA-31", "TIA-32"]
    },
    {
      "issue": "TIA-35",
      "dependsOn": ["TIA-30", "TIA-32", "TIA-34"]
    },
    {
      "issue": "TIA-36",
      "dependsOn": ["TIA-30", "TIA-31", "TIA-32", "TIA-34", "TIA-35"]
    }
  ]
}
```

### Field Rules

- `version`: config schema version
- `projectSlug`: Linear project slug used by the promoter
- `teamKey`: Linear team key for issue lookup and validation
- `sourceState`: only issues currently in this state are eligible for promotion
- `targetState`: issues are promoted to this state once eligible
- `promotions`: list of explicit promotion rules

Each promotion rule contains:

- `issue`: the issue to promote
- `dependsOn`: all prerequisite issues that must be `Done`

### Validation Rules

The promoter should reject configuration that contains:

- duplicate target issues
- duplicate prerequisites within a rule
- self-dependencies
- unknown issue identifier format
- circular dependencies across promotion rules

## Promotion Rules

The first version should apply these rules:

1. Only inspect issues listed in `promotions`
2. Only promote issues currently in `sourceState`
3. Only promote when every issue in `dependsOn` is in `Done`
4. Promote to `targetState`
5. If a target issue is already active, completed, canceled, or otherwise no longer in `sourceState`, skip it without changing anything
6. If an issue lookup fails or the state lookup fails, log the problem and continue evaluating other rules
7. Multiple independent issues may be promoted in a single run
8. The promoter must never demote or revert issue states

## Runtime Model

### Supported Modes

The script should support:

- one-shot mode for manual execution
- polling mode for unattended execution
- dry-run mode for safe evaluation without writes

Suggested commands:

```bash
python scripts/backlog-promoter.py --once
python scripts/backlog-promoter.py --poll --interval-seconds 30
python scripts/backlog-promoter.py --once --dry-run
```

### Environment

The promoter should rely on:

- `LINEAR_API_KEY`

Optional:

- `BACKLOG_PROMOTER_CONFIG` to override the default config path
- `BACKLOG_PROMOTER_INTERVAL_SECONDS` to override polling interval

### State Resolution

The script should query Linear at startup to resolve:

- the project by configured slug
- the team by configured key
- the configured source and target states by name

It should not hardcode Linear state IDs in the repository config.

## Logging and Observability

The first version should emit plain text logs that are easy to tail in `tmux`, `systemd`, or redirected files.

Each run should log:

- config file path
- dry-run or real mode
- resolved project and state names
- eligible promotions
- promotions performed
- skips and reasons
- API or config errors

Example:

```text
Loaded config: config/backlog-promoter.json
Resolved states: Backlog -> Todo
Eligible: TIA-34
Promoted TIA-34 from Backlog to Todo
Skipped TIA-35: dependency TIA-34 is not Done
```

## Failure Handling

The promoter should be conservative:

- invalid config should fail the run before any writes
- a single failed issue update should not prevent evaluating the remaining rules
- Linear API read failures should fail the current run with a non-zero exit code
- polling mode should log the error, sleep, and retry rather than exiting immediately

## Testing Strategy

The implementation should include automated coverage for:

- config parsing
- duplicate target detection
- self-dependency rejection
- cycle detection
- eligibility when all prerequisites are `Done`
- skipping when target is not in the source state
- dry-run behavior
- partial API failure handling
- multi-issue promotion in one run

The repository already uses `tests/scripts/` for Symphony automation scripts, so the promoter should follow that pattern.

## Operational Rollout

The safe rollout path is:

1. Add the promoter config and script
2. Run `--dry-run` against the existing backlog
3. Verify the expected issues would be promoted
4. Start polling mode in a long-running shell or supervisor
5. Observe the first real promotion before relying on it for larger chains

## Recommendation

Implement the standalone polling script plus repository config file now.

This is the smallest design that:

- preserves the existing Symphony workflow
- keeps dependency rules versioned in Git
- allows unattended overnight issue chaining
- avoids introducing new complexity into `WORKFLOW.md` or the Symphony process itself
