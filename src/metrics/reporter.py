import json
import os
import tempfile
from pathlib import Path

from tabulate import tabulate

from src.extractors.base import ExtractionResult
from src.metrics.calculator import ComparisonMetrics


def _result_to_dict(r: ExtractionResult) -> dict:
    return {
        "api": r.api_name,
        "model": r.model_id,
        "image": r.image_path,
        "text": r.raw_text,
        "processing_time_ms": r.processing_time_ms,
        "tokens": {
            "prompt": r.prompt_tokens,
            "completion": r.completion_tokens,
            "total": r.total_tokens,
        },
        "error": r.error,
    }


def _metrics_to_dict(m: ComparisonMetrics) -> dict:
    return {
        "reference": m.reference_label,
        "cer": m.cer,
        "wer": m.wer,
        "cosine_similarity": m.cosine_similarity,
        "char_counts": {"a": m.char_count_a, "b": m.char_count_b},
        "word_counts": {"a": m.word_count_a, "b": m.word_count_b},
        "time_delta_ms": m.time_delta_ms,
        "tokens": {"a": m.tokens_a, "b": m.tokens_b},
    }


def _atomic_write(path: str, content: str):
    dir_ = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=dir_)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise


def write_results(
    image_entries: list[dict],
    output_dir: str,
):
    """
    image_entries: list of dicts with keys:
        - "path": image path
        - "results": list of ExtractionResult
        - "metrics": list of ComparisonMetrics (can be empty)
        - "annotated_images": dict level→path (can be empty)
    """
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "results.json")
    txt_path = os.path.join(output_dir, "report.txt")

    # --- JSON ---
    payload = {"images": []}
    for entry in image_entries:
        payload["images"].append(
            {
                "path": entry["path"],
                "results": [_result_to_dict(r) for r in entry["results"]],
                "metrics": [_metrics_to_dict(m) for m in entry.get("metrics", [])],
                "annotated_images": entry.get("annotated_images", {}),
            }
        )

    _atomic_write(json_path, json.dumps(payload, indent=2, ensure_ascii=False))

    # --- Plain-text report ---
    lines = ["=" * 72, "TEXT EXTRACTION REPORT", "=" * 72, ""]

    for entry in image_entries:
        lines.append(f"Image: {entry['path']}")
        lines.append("-" * 72)

        # Per-API results table
        rows = []
        for r in entry["results"]:
            status = "OK" if r.success else f"ERROR: {r.error}"
            preview = (r.raw_text[:80] + "…") if len(r.raw_text) > 80 else r.raw_text
            preview = preview.replace("\n", " ")
            rows.append([r.api_name, r.model_id, f"{r.processing_time_ms:.0f} ms",
                         r.total_tokens, status, preview])

        lines.append(tabulate(
            rows,
            headers=["API", "Model", "Time", "Tokens", "Status", "Text Preview"],
            tablefmt="simple",
        ))
        lines.append("")

        # Metrics table
        if entry.get("metrics"):
            metric_rows = []
            for m in entry["metrics"]:
                metric_rows.append([
                    m.reference_label,
                    f"{m.cer:.4f}" if m.cer is not None else "N/A",
                    f"{m.wer:.4f}" if m.wer is not None else "N/A",
                    f"{m.cosine_similarity:.4f}" if m.cosine_similarity is not None else "N/A",
                    f"{m.time_delta_ms:+.0f} ms" if m.time_delta_ms is not None else "N/A",
                ])
            lines.append("Metrics:")
            lines.append(tabulate(
                metric_rows,
                headers=["Comparison", "CER", "WER", "Cosine Sim", "Time Delta"],
                tablefmt="simple",
            ))
            lines.append("")

        # Full extracted texts
        for r in entry["results"]:
            lines.append(f"--- {r.api_name} extracted text ---")
            lines.append(r.raw_text if r.raw_text else "(empty)")
            lines.append("")

        # Annotated images
        annotated = entry.get("annotated_images", {})
        if annotated:
            lines.append("Annotated images:")
            for level, path in annotated.items():
                lines.append(f"  [{level}] {path}")
            lines.append("")

        lines.append("=" * 72)
        lines.append("")

    _atomic_write(txt_path, "\n".join(lines))
    return json_path, txt_path
