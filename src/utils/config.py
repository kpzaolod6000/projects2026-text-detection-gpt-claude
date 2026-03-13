import os
from dotenv import load_dotenv

# load_dotenv() only sets vars that are NOT already in os.environ,
# so Docker-injected vars (via env_file) are never overwritten.
load_dotenv(override=False)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

EXTRACTION_PROMPT = (
    "Extract ALL text visible in this image exactly as it appears. "
    "Preserve original formatting, line breaks, and structure. "
    "Output only the extracted text with no additional commentary."
)
