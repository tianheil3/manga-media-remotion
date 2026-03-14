import json
from pathlib import Path


def test_js_app_workspaces_are_declared() -> None:
    root = Path(__file__).resolve().parents[2]
    root_package = json.loads((root / "package.json").read_text(encoding="utf-8"))

    assert "apps/*" in root_package["workspaces"]

    expected_packages = {
        "apps/web/package.json": "@manga/web",
        "apps/remotion/package.json": "@manga/remotion",
    }

    for relative_path, expected_name in expected_packages.items():
        package_path = root / relative_path
        assert package_path.exists(), relative_path

        package = json.loads(package_path.read_text(encoding="utf-8"))
        assert package["name"] == expected_name
        assert package["private"] is True
