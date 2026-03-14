from pathlib import Path


def test_bootstrap_layout_exists() -> None:
    root = Path(__file__).resolve().parents[2]

    expected_paths = [
        root / "apps" / "cli",
        root / "apps" / "api",
        root / "apps" / "web",
        root / "apps" / "remotion",
        root / "packages" / "schema",
        root / "packages" / "shared",
        root / "workspace" / ".gitkeep",
        root / "README.md",
    ]

    missing = [path.relative_to(root).as_posix() for path in expected_paths if not path.exists()]

    assert missing == []
