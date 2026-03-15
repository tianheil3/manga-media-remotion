#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
import urllib.request


LINEAR_API_URL = "https://api.linear.app/graphql"


ISSUE_IDENTIFIER_PATTERN = re.compile(r"^[A-Z]+-\d+$")


def load_config(config_path: Path) -> dict[str, object]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    validate_config(payload)
    return payload


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
            query($projectSlug: String!) {
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
            if project["slugId"] == project_slug:
                return project
        raise ValueError(f"Unknown Linear project slug: {project_slug}")

    def resolve_team_states(self, team_key: str) -> dict[str, str]:
        data = self.query(
            """
            query($teamKey: String!) {
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


def main() -> int:
    load_config(Path("config/backlog-promoter.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
