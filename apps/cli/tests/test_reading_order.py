from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apps.cli.app.services.reading_order import sort_bubbles


def test_sort_bubbles_right_to_left_then_top_to_bottom() -> None:
    sorted_bubbles = sort_bubbles(
        [
            {
                "id": "left-top",
                "text": "left",
                "bbox": {"x": 10, "y": 10, "w": 5, "h": 5},
                "confidence": 0.9,
                "language": "ja",
            },
            {
                "id": "right-bottom",
                "text": "right-bottom",
                "bbox": {"x": 50, "y": 50, "w": 5, "h": 5},
                "confidence": 0.9,
                "language": "ja",
            },
            {
                "id": "right-top",
                "text": "right-top",
                "bbox": {"x": 50, "y": 10, "w": 5, "h": 5},
                "confidence": 0.9,
                "language": "ja",
            },
        ]
    )

    assert [bubble["id"] for bubble in sorted_bubbles] == [
        "right-top",
        "right-bottom",
        "left-top",
    ]
    assert [bubble["order"] for bubble in sorted_bubbles] == [0, 1, 2]
