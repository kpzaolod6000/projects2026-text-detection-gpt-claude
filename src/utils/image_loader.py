import base64
import os
from pathlib import Path
from PIL import Image

from src.utils.config import SUPPORTED_FORMATS


def load_image_b64(image_path: str) -> tuple[str, str]:
    """Return (base64_string, mime_type) for the given image path."""
    path = Path(image_path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{ext}'. Supported: {SUPPORTED_FORMATS}")

    # Validate it's a real image (open a separate handle; verify() invalidates the file pointer)
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as exc:
        raise ValueError(f"Invalid or corrupt image '{image_path}': {exc}") from exc

    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }

    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    return b64, mime_map[ext]


def iter_images(input_path: str):
    """Yield image file paths from a file or directory."""
    p = Path(input_path)
    if p.is_file():
        yield str(p)
    elif p.is_dir():
        for f in sorted(p.iterdir()):
            if f.suffix.lower() in SUPPORTED_FORMATS:
                yield str(f)
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")
