"""
Draw bounding boxes on images using PIL.

Box colors are based on confidence level:
  ≥ 80  → green    (high confidence)
  50–79 → orange   (medium confidence)
  < 50  → red      (low confidence)

Three output images are saved, one per detection level (word/line/block).
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.visualizer.detector import TextBox, detect_all_levels


# ── Color palette ─────────────────────────────────────────────────────────────

def _confidence_color(conf: float) -> tuple[int, int, int, int]:
    """Return RGBA fill color based on confidence score."""
    if conf >= 80:
        return (0, 200, 80, 40)       # green, semi-transparent fill
    elif conf >= 50:
        return (255, 165, 0, 40)      # orange
    else:
        return (220, 50, 50, 40)      # red


def _confidence_outline(conf: float) -> tuple[int, int, int]:
    """Return solid RGB outline color based on confidence score."""
    if conf >= 80:
        return (0, 160, 60)
    elif conf >= 50:
        return (200, 120, 0)
    else:
        return (180, 30, 30)


# ── Font helper ───────────────────────────────────────────────────────────────

def _get_font(size: int = 11):
    """Return a PIL font, falling back to the built-in if no TTF found."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", size)
        except Exception:
            return ImageFont.load_default()


# ── Core drawing ──────────────────────────────────────────────────────────────

def _draw_boxes(
    image: Image.Image,
    boxes: list[TextBox],
    show_labels: bool = True,
    outline_width: int = 2,
) -> Image.Image:
    """Return a new image with boxes drawn over it."""
    # Work on RGBA so we can use semi-transparent fills
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _get_font(max(10, base.height // 80))

    for box in boxes:
        fill = _confidence_color(box.confidence)
        outline = _confidence_outline(box.confidence)
        x0, y0, x1, y1 = box.bbox

        # Semi-transparent fill
        draw.rectangle([x0, y0, x1, y1], fill=fill)
        # Solid outline (PIL outline accepts RGB only, not RGBA)
        for w in range(outline_width):
            draw.rectangle([x0 - w, y0 - w, x1 + w, y1 + w], outline=outline)

        # Label: text + confidence
        if show_labels:
            label = f"{box.text} ({box.confidence:.0f}%)"
            # Tiny background pill behind the label for readability
            try:
                bbox_text = draw.textbbox((x0 + 2, y0 - 14), label, font=font)
                draw.rectangle(bbox_text, fill=(30, 30, 30, 160))
                draw.text((x0 + 2, y0 - 14), label, fill=(255, 255, 255, 240), font=font)
            except AttributeError:
                # PIL < 9 fallback
                draw.text((x0 + 2, y0 - 12), label, fill=(255, 255, 0, 230), font=font)

    # Flatten overlay onto base, convert back to RGB for saving
    composited = Image.alpha_composite(base, overlay).convert("RGB")
    return composited


def _draw_legend(image: Image.Image) -> Image.Image:
    """Append a small legend strip at the bottom of the image."""
    legend_h = max(30, image.height // 20)
    legend = Image.new("RGB", (image.width, legend_h), (30, 30, 30))
    draw = ImageDraw.Draw(legend)
    font = _get_font(max(10, legend_h // 3))

    items = [
        ("High conf (≥80%)", (0, 160, 60)),
        ("Medium conf (50–79%)", (200, 120, 0)),
        ("Low conf (<50%)", (180, 30, 30)),
    ]
    x = 10
    for label, color in items:
        draw.rectangle([x, 6, x + 18, legend_h - 6], fill=color)
        draw.text((x + 22, legend_h // 4), label, fill=(220, 220, 220), font=font)
        x += image.width // 3

    combined = Image.new("RGB", (image.width, image.height + legend_h))
    combined.paste(image, (0, 0))
    combined.paste(legend, (0, image.height))
    return combined


# ── Public API ────────────────────────────────────────────────────────────────

def annotate(
    image_path: str,
    output_dir: str,
    levels: list[str] | None = None,
    show_labels: bool = True,
    show_legend: bool = True,
) -> dict[str, str]:
    """
    Detect text regions and save annotated images.

    Args:
        image_path:  path to the input image
        output_dir:  directory where annotated images are written
        levels:      list of levels to annotate, e.g. ["word", "line", "block"]
                     defaults to all three
        show_labels: whether to draw text + confidence labels on each box
        show_legend: whether to append a color legend at the bottom

    Returns:
        dict mapping level name → output file path
    """
    if levels is None:
        levels = ["word", "line", "block"]

    os.makedirs(output_dir, exist_ok=True)

    all_boxes = detect_all_levels(image_path)
    stem = Path(image_path).stem
    base_image = Image.open(image_path).convert("RGB")

    saved: dict[str, str] = {}

    for level in levels:
        boxes = all_boxes.get(level, [])
        if not boxes:
            print(f"    [annotator] No {level}-level boxes found in {image_path}")
            continue

        annotated = _draw_boxes(base_image.copy(), boxes, show_labels=show_labels)

        if show_legend:
            annotated = _draw_legend(annotated)

        out_path = os.path.join(output_dir, f"{stem}_annotated_{level}.png")
        annotated.save(out_path, "PNG", optimize=True)
        saved[level] = out_path
        print(f"    [annotator] {level}: {len(boxes)} boxes → {out_path}")

    return saved
