from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "verify-strict.sh"
DEFAULT_COMMANDS = [
    "python -m pytest apps/api/tests apps/cli/tests tests/bootstrap tests/docs tests/scripts -v",
    "npm test --workspace packages/schema",
    "npm test --workspace apps/web",
    "npm test --workspace apps/remotion",
]


def run_verify_strict(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_verify_strict_prints_default_commands_in_order() -> None:
    result = run_verify_strict("--print-commands")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines() == DEFAULT_COMMANDS


def test_verify_strict_stops_after_the_first_failure(tmp_path: Path) -> None:
    marker = tmp_path / "order.log"
    env = os.environ.copy()
    env["STRICT_VALIDATION_COMMANDS"] = "\n".join(
        [
            f"python -c \"from pathlib import Path; Path(r'{marker}').write_text('one\\n', encoding='utf-8')\"",
            "python -c \"raise SystemExit(7)\"",
            f"python -c \"from pathlib import Path; Path(r'{marker}').write_text(Path(r'{marker}').read_text(encoding='utf-8') + 'three\\n', encoding='utf-8')\"",
        ]
    )

    result = run_verify_strict(env=env)

    assert result.returncode == 7
    assert marker.read_text(encoding="utf-8").splitlines() == ["one"]
    assert "python -c \"raise SystemExit(7)\"" in result.stderr


def test_verify_strict_runs_workspace_commands_without_prechecking_node_modules(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    scripts_dir = repo / "scripts"
    packages_dir = repo / "packages" / "schema"
    scripts_dir.mkdir(parents=True)
    packages_dir.mkdir(parents=True)
    shutil.copy2(SCRIPT, scripts_dir / "verify-strict.sh")

    (repo / "package.json").write_text(
        '{\n  "name": "temp-repo",\n  "private": true,\n  "workspaces": ["packages/*"]\n}\n',
        encoding="utf-8",
    )
    (packages_dir / "package.json").write_text(
        (
            '{\n'
            '  "name": "@temp/schema",\n'
            '  "private": true,\n'
            '  "type": "module",\n'
            '  "scripts": {"test": "node --test tests/*.test.js"}\n'
            '}\n'
        ),
        encoding="utf-8",
    )
    tests_dir = packages_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "schema.test.js").write_text(
        'import test from "node:test";\n'
        'test("workspace test", () => {});\n',
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["STRICT_VALIDATION_COMMANDS"] = "npm test --workspace packages/schema"
    result = subprocess.run(
        ["bash", str(scripts_dir / "verify-strict.sh")],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Running strict validation: npm test --workspace packages/schema" in result.stdout
    assert "ℹ pass 1" in result.stdout
    assert "Strict validation passed" in result.stdout
