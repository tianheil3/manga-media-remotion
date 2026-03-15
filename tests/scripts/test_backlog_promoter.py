from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import pytest


CONFIG_PATH = Path("config/backlog-promoter.json")
SCRIPT_PATH = Path("scripts/backlog-promoter.py")


def load_module():
    spec = importlib.util.spec_from_file_location("backlog_promoter", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_checked_in_config_declares_backlog_to_todo_promotions() -> None:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert payload["version"] == 1
    assert payload["sourceState"] == "Backlog"
    assert payload["targetState"] == "Todo"
    assert payload["promotions"]
    for promotion in payload["promotions"]:
        assert promotion["issue"]
        assert promotion["dependsOn"]


def test_validate_config_rejects_duplicate_target_issues() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="Duplicate promotion target"):
        module.validate_config(
            {
                "version": 1,
                "projectSlug": "demo-project",
                "teamKey": "TIA",
                "sourceState": "Backlog",
                "targetState": "Todo",
                "promotions": [
                    {"issue": "TIA-100", "dependsOn": ["TIA-1"]},
                    {"issue": "TIA-100", "dependsOn": ["TIA-2"]},
                ],
            }
        )


def test_validate_config_rejects_self_dependencies() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="cannot depend on itself"):
        module.validate_config(
            {
                "version": 1,
                "projectSlug": "demo-project",
                "teamKey": "TIA",
                "sourceState": "Backlog",
                "targetState": "Todo",
                "promotions": [
                    {"issue": "TIA-101", "dependsOn": ["TIA-101"]},
                ],
            }
        )


def test_validate_config_rejects_duplicate_dependencies_in_one_rule() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="Duplicate dependency"):
        module.validate_config(
            {
                "version": 1,
                "projectSlug": "demo-project",
                "teamKey": "TIA",
                "sourceState": "Backlog",
                "targetState": "Todo",
                "promotions": [
                    {"issue": "TIA-102", "dependsOn": ["TIA-1", "TIA-1"]},
                ],
            }
        )


def test_validate_config_rejects_cycles() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="Cycle detected"):
        module.validate_config(
            {
                "version": 1,
                "projectSlug": "demo-project",
                "teamKey": "TIA",
                "sourceState": "Backlog",
                "targetState": "Todo",
                "promotions": [
                    {"issue": "TIA-103", "dependsOn": ["TIA-104"]},
                    {"issue": "TIA-104", "dependsOn": ["TIA-103"]},
                ],
            }
        )
