import shutil
from pathlib import Path
import sys

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.cli.app.main import app

PROJECT_ID = "demo-001"
FIXTURE_PROJECT_DIR = ROOT / "tests" / "fixtures" / "workspace" / PROJECT_ID

runner = CliRunner()


def copy_fixture_project(workspace_root: Path) -> Path:
    shutil.copytree(FIXTURE_PROJECT_DIR, workspace_root / PROJECT_ID)
    return workspace_root / PROJECT_ID


def collect_project_files(project_dir: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(project_dir)): path.read_bytes()
        for path in sorted(project_dir.rglob("*"))
        if path.is_file()
    }


def test_export_and_import_workspace_round_trip_preserves_project_files(tmp_path: Path) -> None:
    source_workspace_root = tmp_path / "workspace-source"
    source_project_dir = copy_fixture_project(source_workspace_root)
    archive_path = tmp_path / "demo-001.tar.gz"
    destination_workspace_root = tmp_path / "workspace-destination"

    export_result = runner.invoke(
        app,
        [
            "export-workspace",
            PROJECT_ID,
            str(archive_path),
            "--workspace-root",
            str(source_workspace_root),
        ],
    )

    assert export_result.exit_code == 0, export_result.stdout
    assert archive_path.is_file()

    import_result = runner.invoke(
        app,
        [
            "import-workspace",
            str(archive_path),
            "--workspace-root",
            str(destination_workspace_root),
        ],
    )

    assert import_result.exit_code == 0, import_result.stdout

    imported_project_dir = destination_workspace_root / PROJECT_ID
    assert imported_project_dir.is_dir()
    assert collect_project_files(imported_project_dir) == collect_project_files(source_project_dir)
