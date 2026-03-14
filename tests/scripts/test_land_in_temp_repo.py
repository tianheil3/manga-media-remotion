from __future__ import annotations

import os

from tests.scripts.helpers import create_feature_branch, create_git_repo, git, run


def test_land_script_squash_merges_a_feature_branch_into_main(tmp_path) -> None:
    repo = create_git_repo(tmp_path)
    branch_name = create_feature_branch(repo)
    env = os.environ.copy()
    env["STRICT_VALIDATION_COMMANDS"] = "python -c \"print('strict-ok')\""
    env["LAND_COMMIT_MESSAGE"] = "TIA-16: land changes"

    result = run(["bash", "scripts/land.sh", branch_name], cwd=repo, env=env)

    assert result.returncode == 0, result.stderr
    assert "LAND_STATUS=success" in result.stdout
    assert "strict-ok" in result.stdout

    main_sha = git(repo, "rev-parse", "main").stdout.strip()
    origin_main_sha = git(repo, "rev-parse", "origin/main").stdout.strip()
    last_subject = git(repo, "log", "-1", "--format=%s", "main").stdout.strip()
    parent_line = git(repo, "show", "--format=%P", "-s", "main").stdout.strip()
    commit_count = git(repo, "rev-list", "--count", "main").stdout.strip()
    notes_text = (repo / "notes.txt").read_text(encoding="utf-8")

    assert main_sha == origin_main_sha
    assert last_subject == "TIA-16: land changes"
    assert len(parent_line.split()) == 1
    assert commit_count == "2"
    assert notes_text == "one\ntwo\n"
