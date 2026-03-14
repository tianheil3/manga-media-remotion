import os
from pathlib import Path

from tests.scripts.helpers import create_feature_branch, create_git_repo, git, run


def test_land_script_rejects_running_without_a_work_branch(tmp_path: Path) -> None:
    repo = create_git_repo(tmp_path)

    result = run(["bash", "scripts/land.sh"], cwd=repo)

    assert result.returncode == 1
    assert "non-main work branch" in result.stderr


def test_land_script_runs_verification_before_push_and_never_reports_success_on_push_failure(
    tmp_path: Path,
) -> None:
    repo = create_git_repo(tmp_path)
    branch_name = create_feature_branch(repo)
    verification_log = tmp_path / "verify.log"
    missing_push_remote = tmp_path / "missing-origin.git"

    git(repo, "remote", "set-url", "--push", "origin", str(missing_push_remote))
    env = os.environ.copy()
    env["STRICT_VALIDATION_COMMANDS"] = (
        "python -c \"from pathlib import Path; Path(r'%s').write_text('verified\\n', encoding='utf-8')\""
        % verification_log
    )
    env["LAND_COMMIT_MESSAGE"] = "TIA-16: land changes"

    result = run(["bash", "scripts/land.sh", branch_name], cwd=repo, env=env)

    assert result.returncode != 0
    assert verification_log.read_text(encoding="utf-8").splitlines() == ["verified"]
    assert "LAND_STATUS=success" not in result.stdout
    assert "push" in result.stderr.lower()
