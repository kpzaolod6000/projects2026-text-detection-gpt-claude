import os
import time

import anthropic

from src.extractors.base import BaseExtractor, ExtractionResult
from src.utils.config import ANTHROPIC_MODEL, MAX_TOKENS, REQUEST_TIMEOUT, EXTRACTION_PROMPT
from src.utils.image_loader import load_image_b64


class ClaudeExtractor(BaseExtractor):
    def __init__(self):
        # Read key at instantiation time so Docker env vars are always current
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=api_key, timeout=float(REQUEST_TIMEOUT))
        self.model = ANTHROPIC_MODEL

    def extract(self, image_path: str) -> ExtractionResult:
        b64, mime_type = load_image_b64(image_path)
        # Anthropic only supports these media types
        allowed = {"image/png", "image/jpeg", "image/webp", "image/gif"}
        if mime_type not in allowed:
            mime_type = "image/png"

        start = time.monotonic()
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": EXTRACTION_PROMPT},
                        ],
                    }
                ],
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            text = response.content[0].text if response.content else ""
            usage = response.usage
            return ExtractionResult(
                api_name="Claude",
                model_id=self.model,
                image_path=image_path,
                raw_text=text.strip(),
                processing_time_ms=round(elapsed_ms, 2),
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
            )
        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            return ExtractionResult(
                api_name="Claude",
                model_id=self.model,
                image_path=image_path,
                raw_text="",
                processing_time_ms=round(elapsed_ms, 2),
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                error=str(exc),
            )
