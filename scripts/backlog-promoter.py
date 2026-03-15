#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
import time
from typing import Any
import urllib.request


LINEAR_API_URL = "https://api.linear.app/graphql"
DEFAULT_CONFIG_PATH = Path("config/backlog-promoter.json")
DEFAULT_INTERVAL_SECONDS = 30


ISSUE_IDENTIFIER_PATTERN = re.compile(r"^[A-Z]+-\d+$")


def load_config(config_path: Path) -> dict[str, object]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(payload)
    return payload


def project_matches_slug(project: dict[str, Any], configured_slug: str) -> bool:
    slug_id = project.get("slugId")
    name = project.get("name")
    if not isinstance(slug_id, str) or not isinstance(name, str):
        return False

    normalized_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return configured_slug == slug_id or configured_slug == f"{normalized_name}-{slug_id}"


def validate_config(payload: dict[str, object]) -> None:
    promotions = payload.get("promotions")
    if not isinstance(promotions, list):
        raise ValueError("Config field promotions must be a list")

    seen_targets: set[str] = set()
    dependency_graph: dict[str, set[str]] = {}

    for promotion in promotions:
        if not isinstance(promotion, dict):
            raise ValueError("Each promotion must be an object")

        issue = promotion.get("issue")
        depends_on = promotion.get("dependsOn")
        if not isinstance(issue, str) or not ISSUE_IDENTIFIER_PATTERN.fullmatch(issue):
            raise ValueError(f"Invalid issue identifier: {issue!r}")
        if issue in seen_targets:
            raise ValueError(f"Duplicate promotion target: {issue}")
        seen_targets.add(issue)

        if not isinstance(depends_on, list) or not depends_on:
            raise ValueError(f"Promotion {issue} must declare dependsOn")

        dependencies: set[str] = set()
        for dependency in depends_on:
            if not isinstance(dependency, str) or not ISSUE_IDENTIFIER_PATTERN.fullmatch(dependency):
                raise ValueError(f"Invalid dependency identifier: {dependency!r}")
            if dependency == issue:
                raise ValueError(f"Issue {issue} cannot depend on itself")
            if dependency in dependencies:
                raise ValueError(f"Duplicate dependency {dependency} in {issue}")
            dependencies.add(dependency)

        dependency_graph[issue] = dependencies

    _assert_no_cycles(dependency_graph)


def find_eligible_promotions(
    config: dict[str, object],
    issue_states: dict[str, str],
    *,
    done_state: str = "Done",
) -> list[str]:
    validate_config(config)
    source_state = config["sourceState"]
    promotions = config["promotions"]
    assert isinstance(source_state, str)
    assert isinstance(promotions, list)

    eligible: list[str] = []
    for promotion in promotions:
        assert isinstance(promotion, dict)
        issue = promotion["issue"]
        depends_on = promotion["dependsOn"]
        assert isinstance(issue, str)
        assert isinstance(depends_on, list)

        if issue_states.get(issue) != source_state:
            continue
        if all(issue_states.get(dependency) == done_state for dependency in depends_on):
            eligible.append(issue)

    return eligible


def apply_promotions(
    config: dict[str, object],
    issue_states: dict[str, str],
    *,
    promote_issue,
    dry_run: bool = False,
) -> dict[str, object]:
    target_state = config["targetState"]
    assert isinstance(target_state, str)

    promoted: list[str] = []
    errors: dict[str, str] = {}

    for issue in find_eligible_promotions(config, issue_states):
        if dry_run:
            promoted.append(issue)
            continue
        try:
            promote_issue(issue, target_state)
        except Exception as exc:  # pragma: no cover - exercised via tests
            errors[issue] = str(exc)
            continue
        promoted.append(issue)

    return {
        "promoted": promoted,
        "errors": errors,
    }


class LinearClient:
    def __init__(self, api_key: str | None = None, *, url: str = LINEAR_API_URL) -> None:
        self.api_key = api_key or os.environ["LINEAR_API_KEY"]
        self.url = url

    def query(self, query: str, variables: dict[str, object] | None = None) -> dict[str, Any]:
        payload = json.dumps(
            {
                "query": query,
                "variables": variables or {},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=payload,
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("errors"):
            raise RuntimeError(data["errors"])
        return data["data"]

    def resolve_project(self, project_slug: str) -> dict[str, Any]:
        data = self.query(
            """
            query {
              projects {
                nodes {
                  id
                  slugId
                  name
                }
              }
            }
            """
        )
        for project in data["projects"]["nodes"]:
            if project_matches_slug(project, project_slug):
                return project
        raise ValueError(f"Unknown Linear project slug: {project_slug}")

    def resolve_team_states(self, team_key: str) -> dict[str, str]:
        data = self.query(
            """
            query {
              teams {
                nodes {
                  key
                  states {
                    nodes {
                      id
                      name
                    }
                  }
                }
              }
            }
            """
        )
        for team in data["teams"]["nodes"]:
            if team["key"] == team_key:
                return {state["name"]: state["id"] for state in team["states"]["nodes"]}
        raise ValueError(f"Unknown Linear team key: {team_key}")

    def list_project_issues(self, project_id: str) -> list[dict[str, Any]]:
        data = self.query(
            """
            query($projectId: String!) {
              project(id: $projectId) {
                issues {
                  nodes {
                    id
                    identifier
                    state {
                      name
                    }
                  }
                }
              }
            }
            """,
            {"projectId": project_id},
        )
        return data["project"]["issues"]["nodes"]

    def update_issue_state(self, issue_id: str, state_id: str) -> None:
        self.query(
            """
            mutation($id: String!, $stateId: String!) {
              issueUpdate(
                id: $id
                input: {
                  stateId: $stateId
                }
              ) {
                success
              }
            }
            """,
            {"id": issue_id, "stateId": state_id},
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote configured Linear backlog issues to Todo")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--once", action="store_true", help="Run one promotion pass")
    mode_group.add_argument("--poll", action="store_true", help="Run the promoter continuously")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without updating Linear")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to backlog promoter config",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Polling interval for --poll mode",
    )
    return parser.parse_args(argv)


def run_cycle(
    *,
    config_path: Path,
    dry_run: bool,
    client: LinearClient | None = None,
) -> dict[str, object]:
    config = load_config(config_path)
    linear_client = client or LinearClient()

    project_slug = config["projectSlug"]
    team_key = config["teamKey"]
    source_state = config["sourceState"]
    target_state = config["targetState"]
    assert isinstance(project_slug, str)
    assert isinstance(team_key, str)
    assert isinstance(source_state, str)
    assert isinstance(target_state, str)

    project = linear_client.resolve_project(project_slug)
    state_ids = linear_client.resolve_team_states(team_key)
    if source_state not in state_ids:
        raise ValueError(f"Unknown source state: {source_state}")
    if target_state not in state_ids:
        raise ValueError(f"Unknown target state: {target_state}")

    issues = linear_client.list_project_issues(project["id"])
    issue_states = {
        issue["identifier"]: issue["state"]["name"]
        for issue in issues
    }
    issue_ids = {
        issue["identifier"]: issue["id"]
        for issue in issues
    }

    return apply_promotions(
        config,
        issue_states,
        promote_issue=lambda issue, _state_name: linear_client.update_issue_state(
            issue_ids[issue],
            state_ids[target_state],
        ),
        dry_run=dry_run,
    )


def run_polling_loop(
    run_once,
    *,
    interval_seconds: int,
    sleep=time.sleep,
    max_iterations: int | None = None,
) -> None:
    iterations = 0
    while True:
        run_once()
        iterations += 1
        if max_iterations is not None and iterations >= max_iterations:
            return
        sleep(interval_seconds)


def _assert_no_cycles(dependency_graph: dict[str, set[str]]) -> None:
    visited: set[str] = set()
    active: set[str] = set()

    def visit(issue: str) -> None:
        if issue in active:
            raise ValueError(f"Cycle detected involving {issue}")
        if issue in visited:
            return

        active.add(issue)
        for dependency in dependency_graph.get(issue, set()):
            if dependency in dependency_graph:
                visit(dependency)
        active.remove(issue)
        visited.add(issue)

    for issue in dependency_graph:
        visit(issue)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)

    if args.once:
        run_cycle(config_path=config_path, dry_run=args.dry_run)
        return 0

    run_polling_loop(
        lambda: run_cycle(config_path=config_path, dry_run=args.dry_run),
        interval_seconds=args.interval_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
