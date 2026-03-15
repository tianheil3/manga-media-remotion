from __future__ import annotations

import json
from pathlib import Path


CONFIG_PATH = Path("config/backlog-promoter.json")


def test_checked_in_config_declares_backlog_to_todo_promotions() -> None:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    assert payload["version"] == 1
    assert payload["sourceState"] == "Backlog"
    assert payload["targetState"] == "Todo"
    assert payload["promotions"]
    for promotion in payload["promotions"]:
        assert promotion["issue"]
        assert promotion["dependsOn"]
