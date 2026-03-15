#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import wrap
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


FRAME_SIZES = {
    "preview": (360, 640),
    "final": (720, 1280),
}

FALLBACK_COLORS = {
    "narration": (39, 64, 96),
    "dialogue": (92, 48, 108),
    "silent": (55, 55, 55),
}

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        render_video(payload)
    except Exception as error:
        sys.stderr.write(f"{error}\n")
        return 1

    return 0


def render_video(payload: dict[str, Any]) -> None:
    kind = payload["kind"]
    fps = int(payload["fps"])
    output_path = Path(payload["outputPath"])
    project_dir = Path(payload["projectDir"])
    scenes = payload["scenes"]
    project = payload["project"]

    width, height = FRAME_SIZES.get(kind, FRAME_SIZES["preview"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError("Failed to initialize MP4 encoder.")

    total_frames = 0
    try:
        for scene in scenes:
            frame = build_scene_frame(
                project_dir=project_dir,
                project=project,
                scene=scene,
                kind=kind,
                size=(width, height),
            )
            duration_frames = max(1, round((int(scene["durationMs"]) / 1000) * fps))
            for _ in range(duration_frames):
                writer.write(frame)
            total_frames += duration_frames
    finally:
        writer.release()

    if total_frames == 0 or not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Render output is empty.")


def build_scene_frame(
    *,
    project_dir: Path,
    project: dict[str, Any],
    scene: dict[str, Any],
    kind: str,
    size: tuple[int, int],
) -> np.ndarray:
    width, height = size
    image = load_scene_image(project_dir / scene["image"], size, scene.get("type", "silent"))
    draw = ImageDraw.Draw(image, "RGBA")

    overlay_top = int(height * 0.14)
    overlay_bottom = int(height * 0.30)
    draw.rectangle((0, 0, width, overlay_top), fill=(0, 0, 0, 120))
    draw.rectangle((0, height - overlay_bottom, width, height), fill=(0, 0, 0, 165))

    title_font = load_font(max(18, width // 20))
    body_font = load_font(max(22, width // 17))
    small_font = load_font(max(14, width // 30))

    draw.text(
        (24, 18),
        str(project.get("title") or project.get("id") or "Untitled project"),
        font=title_font,
        fill=(255, 255, 255, 255),
    )
    label = build_scene_label(scene)
    draw.text((24, 54), label, font=small_font, fill=(225, 225, 225, 255))

    subtitle = str(scene.get("subtitleText") or scene.get("id") or "")
    wrapped = wrap_text(draw, subtitle, body_font, width - 48)
    text_bbox = draw.multiline_textbbox((0, 0), wrapped, font=body_font, spacing=8, align="left")
    text_height = text_bbox[3] - text_bbox[1]
    text_y = height - overlay_bottom + max(24, (overlay_bottom - text_height) // 2)
    draw.multiline_text(
        (24, text_y),
        wrapped,
        font=body_font,
        fill=(255, 255, 255, 255),
        spacing=8,
        align="left",
    )

    if kind == "preview":
        watermark_bbox = draw.textbbox((0, 0), "PREVIEW", font=small_font)
        watermark_width = watermark_bbox[2] - watermark_bbox[0]
        draw.rounded_rectangle(
            (width - watermark_width - 44, 18, width - 24, 54),
            radius=10,
            fill=(255, 196, 0, 210),
        )
        draw.text(
            (width - watermark_width - 34, 24),
            "PREVIEW",
            font=small_font,
            fill=(28, 28, 28, 255),
        )

    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def load_scene_image(path: Path, size: tuple[int, int], scene_type: str) -> Image.Image:
    width, height = size
    if path.exists():
        try:
            with Image.open(path) as source:
                image = source.convert("RGB")
            return resize_cover(image, size)
        except Exception:
            pass

    base_color = FALLBACK_COLORS.get(scene_type, FALLBACK_COLORS["silent"])
    image = Image.new("RGB", size, base_color)
    draw = ImageDraw.Draw(image)
    for index in range(height):
        blend = index / max(height - 1, 1)
        color = tuple(
            min(255, int(channel + (index % 17) * 0.2 + blend * 36))
            for channel in base_color
        )
        draw.line((0, index, width, index), fill=color)
    return image


def resize_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = size
    source_width, source_height = image.size
    scale = max(width / source_width, height / source_height)
    resized = image.resize((round(source_width * scale), round(source_height * scale)))
    left = max(0, (resized.width - width) // 2)
    top = max(0, (resized.height - height) // 2)
    return resized.crop((left, top, left + width, top + height))


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> str:
    if not text:
        return ""

    words = text.split()
    if not words:
        return text

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)

    wrapped_lines: list[str] = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            wrapped_lines.append(line)
            continue
        wrapped_lines.extend(wrap(line, width=max(8, len(line) // 2)))

    return "\n".join(wrapped_lines[:4])


def build_scene_label(scene: dict[str, Any]) -> str:
    bits = [str(scene.get("type", "scene")).upper()]
    if scene.get("speaker"):
        bits.append(str(scene["speaker"]))
    return " | ".join(bits)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


if __name__ == "__main__":
    raise SystemExit(main())
