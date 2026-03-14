from __future__ import annotations

import shutil
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LAND_SCRIPT = ROOT / "scripts" / "land.sh"
VERIFY_SCRIPT = ROOT / "scripts" / "verify-strict.sh"


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = run(["git", *args], cwd=repo, env=env)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


def install_scripts(repo: Path) -> None:
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    for source in (LAND_SCRIPT, VERIFY_SCRIPT):
        destination = scripts_dir / source.name
        shutil.copy2(source, destination)
        destination.chmod(destination.stat().st_mode | stat.S_IXUSR)


def create_git_repo(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"

    run(["git", "init", "--bare", str(origin)], cwd=tmp_path)
    run(["git", "clone", str(origin), str(repo)], cwd=tmp_path)
    git(repo, "config", "user.name", "Codex Test")
    git(repo, "config", "user.email", "codex@example.com")
    git(repo, "checkout", "-b", "main")

    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "chore: initial commit")
    git(repo, "push", "-u", "origin", "main")

    install_scripts(repo)
    return repo


def create_feature_branch(repo: Path, branch_name: str = "tianheilene/tia-16-auto-land") -> str:
    git(repo, "checkout", "-b", branch_name)

    notes = repo / "notes.txt"
    notes.write_text("one\n", encoding="utf-8")
    git(repo, "add", "notes.txt")
    git(repo, "commit", "-m", "feat: add notes")

    notes.write_text("one\ntwo\n", encoding="utf-8")
    git(repo, "add", "notes.txt")
    git(repo, "commit", "-m", "feat: expand notes")
    return branch_name
