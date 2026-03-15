#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from pathlib import Path


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
