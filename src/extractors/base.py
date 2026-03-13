from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    api_name: str
    model_id: str
    image_path: str
    raw_text: str
    processing_time_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, image_path: str) -> ExtractionResult:
        """Extract text from an image and return an ExtractionResult."""
        ...
