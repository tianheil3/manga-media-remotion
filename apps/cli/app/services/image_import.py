import shutil
from datetime import datetime, timezone
from pathlib import Path

from apps.api.app.models.frame import Frame
from apps.api.app.services.file_store import FileStore

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def import_images(project_dir: Path, image_paths: list[Path]) -> list[Frame]:
    if not image_paths:
        raise ValueError("At least one image path is required.")

    validated_paths = [Path(image_path) for image_path in image_paths]
    for image_path in validated_paths:
        if not image_path.is_file():
            raise ValueError(f"Image not found: {image_path}")
        if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            raise ValueError(f"Unsupported image file: {image_path}")

    store = FileStore(project_dir)
    project = store.load_project()
    images_dir = project_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    frames: list[Frame] = []
    for index, image_path in enumerate(validated_paths, start=1):
        extension = image_path.suffix.lower()
        destination_name = f"{index:03d}{extension}"
        destination_path = images_dir / destination_name
        shutil.copy2(image_path, destination_path)
        frames.append(
            Frame(
                frameId=f"frame-{index:03d}",
                image=f"{project.image_dir}/{destination_name}",
                ocrFile=f"ocr/{index:03d}.json",
                bubbles=[],
                reviewedBubbles=[],
            )
        )

    store.save_frames(frames)
    project.updated_at = _utc_timestamp()
    store.save_project(project)
    return frames
