from dataclasses import dataclass

import editdistance
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class ComparisonMetrics:
    cer: float | None          # Character Error Rate (vs ground truth or other API)
    wer: float | None          # Word Error Rate
    cosine_similarity: float | None
    char_count_a: int
    char_count_b: int | None
    word_count_a: int
    word_count_b: int | None
    time_delta_ms: float | None   # positive = A was slower
    tokens_a: int
    tokens_b: int | None
    reference_label: str       # e.g. "vs Claude" or "vs ground_truth"


def _cer(ref: str, hyp: str) -> float:
    if not ref:
        return 0.0 if not hyp else 1.0
    return editdistance.eval(ref, hyp) / len(ref)


def _wer(ref: str, hyp: str) -> float:
    ref_words = ref.split()
    hyp_words = hyp.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    return editdistance.eval(ref_words, hyp_words) / len(ref_words)


def _cosine(text_a: str, text_b: str) -> float | None:
    if not text_a.strip() or not text_b.strip():
        return None
    try:
        vec = TfidfVectorizer().fit_transform([text_a, text_b])
        return round(float(cosine_similarity(vec[0], vec[1])[0][0]), 4)
    except Exception:
        return None


def compare(result_a, result_b) -> ComparisonMetrics:
    """Compare two ExtractionResult objects against each other.
    result_b is treated as reference; CER/WER measure how much result_a differs from it.
    """
    text_a = result_a.raw_text
    text_b = result_b.raw_text
    return ComparisonMetrics(
        cer=round(_cer(ref=text_b, hyp=text_a), 4),
        wer=round(_wer(ref=text_b, hyp=text_a), 4),
        cosine_similarity=_cosine(text_a, text_b),
        char_count_a=len(text_a),
        char_count_b=len(text_b),
        word_count_a=len(text_a.split()),
        word_count_b=len(text_b.split()),
        time_delta_ms=round(result_a.processing_time_ms - result_b.processing_time_ms, 2),
        tokens_a=result_a.total_tokens,
        tokens_b=result_b.total_tokens,
        reference_label=f"{result_a.api_name} vs {result_b.api_name}",
    )


def compare_with_ground_truth(result, ground_truth_text: str) -> ComparisonMetrics:
    """Compare a single ExtractionResult against a ground truth string."""
    ref = ground_truth_text.strip()
    hyp = result.raw_text
    return ComparisonMetrics(
        cer=round(_cer(ref, hyp), 4),
        wer=round(_wer(ref, hyp), 4),
        cosine_similarity=_cosine(ref, hyp),
        char_count_a=len(hyp),
        char_count_b=len(ref),
        word_count_a=len(hyp.split()),
        word_count_b=len(ref.split()),
        time_delta_ms=None,
        tokens_a=result.total_tokens,
        tokens_b=None,
        reference_label=f"{result.api_name} vs ground_truth",
    )
