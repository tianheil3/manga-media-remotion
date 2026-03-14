from collections.abc import Sequence


def sort_bubbles(bubbles: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    sorted_bubbles = sorted(
        bubbles,
        key=lambda bubble: (
            -float(_bbox_value(bubble, "x")),
            float(_bbox_value(bubble, "y")),
        ),
    )

    ordered: list[dict[str, object]] = []
    for index, bubble in enumerate(sorted_bubbles):
        ordered.append({**bubble, "order": index})

    return ordered


def _bbox_value(bubble: dict[str, object], key: str) -> float:
    bbox = bubble.get("bbox")
    if not isinstance(bbox, dict):
        raise ValueError("OCR bubble is missing bbox data")

    value = bbox.get(key)
    if value is None:
        raise ValueError(f"OCR bubble bbox is missing {key}")

    return float(value)
