"""
Tesseract-based text region detector.
Returns bounding boxes at word, line, and block granularity.
"""

from dataclasses import dataclass

import pytesseract
from PIL import Image


@dataclass
class TextBox:
    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float   # 0–100
    level: str          # "word" | "line" | "block"

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


def detect(image_path: str, level: str = "word") -> list[TextBox]:
    """
    Detect text regions in an image using Tesseract.

    Args:
        image_path: path to image file
        level: granularity — "word", "line", or "block"

    Returns:
        List of TextBox, sorted top-to-bottom then left-to-right.
    """
    level_map = {"word": 5, "line": 4, "block": 2}
    if level not in level_map:
        raise ValueError(f"level must be one of: {list(level_map)}")

    img = Image.open(image_path).convert("RGB")
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    boxes: list[TextBox] = []
    target_level = level_map[level]

    for i in range(len(data["level"])):
        if data["level"][i] != target_level:
            continue
        text = data["text"][i].strip()
        conf = float(data["conf"][i])

        # Skip empty or invalid entries
        if not text or conf < 0:
            continue

        boxes.append(
            TextBox(
                text=text,
                left=data["left"][i],
                top=data["top"][i],
                width=data["width"][i],
                height=data["height"][i],
                confidence=conf,
                level=level,
            )
        )

    # Sort top→bottom, then left→right
    boxes.sort(key=lambda b: (b.top, b.left))
    return boxes


def detect_all_levels(image_path: str) -> dict[str, list[TextBox]]:
    """Detect at all three levels in one pass."""
    img = Image.open(image_path).convert("RGB")
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    result: dict[str, list[TextBox]] = {"block": [], "line": [], "word": []}
    level_to_name = {2: "block", 4: "line", 5: "word"}

    for i in range(len(data["level"])):
        lvl = data["level"][i]
        if lvl not in level_to_name:
            continue
        name = level_to_name[lvl]
        text = data["text"][i].strip()
        conf = float(data["conf"][i])
        if not text or conf < 0:
            continue

        w = data["width"][i]
        h = data["height"][i]
        if w <= 0 or h <= 0:
            continue

        result[name].append(
            TextBox(
                text=text,
                left=data["left"][i],
                top=data["top"][i],
                width=w,
                height=h,
                confidence=conf,
                level=name,
            )
        )

    for name in result:
        result[name].sort(key=lambda b: (b.top, b.left))

    return result
