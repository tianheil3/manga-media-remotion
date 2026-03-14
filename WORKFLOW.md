---
tracker:
  kind: linear
  project_slug: "REPLACE_WITH_LINEAR_PROJECT_SLUG"
  active_states:
    - Todo
    - In Progress
    - Human Review
    - Merging
    - Rework
  terminal_states:
    - Closed
    - Cancelled
    - Canceled
    - Duplicate
    - Done
  polling:
    interval_ms: 5000
workspace:
  root: $SYMPHONY_WORKSPACE_ROOT
hooks:
  after_create: |
    git clone --depth 1 "https://github.com/tianheil3/manga-media-remotion.git" .
  before_remove: |
    git status --short
agent:
  max_concurrent_agents: 5
  max_turns: 20
codex:
  command: codex --config shell_environment_policy.inherit=all --config model_reasoning_effort=xhigh --model gpt-5.3-codex app-server
  approval_policy: never
  thread_sandbox: workspace-write
  turn_sandbox_policy:
    type: workspaceWrite
---

You are working on a Linear ticket `{{ issue.identifier }}` for the `manga-media-remotion` repository.

{% if attempt %}
Continuation context:
- This is retry attempt #{{ attempt }} because the ticket is still in an active state.
- Resume from the current workspace state instead of restarting from scratch.
- Do not repeat already completed investigation or validation unless new changes require it.
- Do not stop while the issue remains active unless you are blocked by missing required permissions, auth, or secrets.
{% endif %}

Issue context:

- Identifier: {{ issue.identifier }}
- Title: {{ issue.title }}
- Current status: {{ issue.state }}
- Labels: {{ issue.labels }}
- URL: {{ issue.url }}

Description:
{% if issue.description %}
{{ issue.description }}
{% else %}
No description provided.
{% endif %}

Repository context:

- This repository is building a manga commentary video workflow around a Python CLI, FastAPI API, React web review UI, and Remotion renderer.
- The current product direction and MVP scope are documented in `docs/plans/2026-03-14-manga-video-workflow-design.md`.
- The implementation breakdown is documented in `docs/plans/2026-03-14-manga-video-workflow-implementation-plan.md`.
- Favor local-first project data stored under `workspace/<project-id>/`.

Execution rules:

1. This is an unattended orchestration session. Do not ask a human to perform follow-up actions unless a real external blocker exists.
2. Work only inside the provided repository workspace.
3. Start by determining the Linear ticket state, then follow the correct workflow for that state.
4. Keep exactly one persistent `## Codex Workpad` comment on the ticket as the source of truth for progress, plan, validation, and blockers.
5. Before editing code, sync with `origin/main`, record the result in the workpad, and capture a concrete reproduction or baseline signal.
6. Treat any ticket-authored `Validation`, `Testing`, or `Test Plan` sections as required acceptance input.
7. Use small, logical commits and keep the branch current.
8. Before moving a ticket to `Human Review`, make sure validation is green, PR feedback is cleared, and the workpad reflects reality.
9. When a ticket enters `Merging`, follow the repository `land` workflow if that skill is available; otherwise stop and report the missing capability in the workpad.

Repository-specific guardrails:

- Keep OCR text, translated text, voice script text, and subtitle text as separate data layers.
- Do not push workflow logic into Remotion that belongs in the Python orchestration layer.
- Prefer file-backed project state over adding a database unless the ticket explicitly requires it.
- Keep the first implementation minimal and aligned with the approved design docs unless the ticket explicitly changes scope.

If no valid Linear integration is available, stop immediately and report the missing setup as a blocker in the workpad.
