"""
Entry point: python -m src.pipeline.runner --api [chatgpt|claude|both] --input <path> [options]
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.extractors.chatgpt_extractor import ChatGPTExtractor
from src.extractors.claude_extractor import ClaudeExtractor
from src.metrics import calculator
from src.metrics.reporter import write_results
from src.utils.image_loader import iter_images
from src.visualizer.annotator import annotate


def _parse_args():
    p = argparse.ArgumentParser(
        description="Extract text from images using ChatGPT and/or Claude APIs."
    )
    p.add_argument(
        "--api",
        required=True,
        choices=["chatgpt", "claude", "both"],
        help="Which API to use.",
    )
    p.add_argument(
        "--input",
        required=True,
        metavar="PATH",
        help="Path to an image file or a directory of images.",
    )
    p.add_argument(
        "--ground-truth",
        metavar="FILE",
        default=None,
        help="Optional .txt file with reference text for CER/WER calculation.",
    )
    p.add_argument(
        "--output-dir",
        default="./output",
        metavar="DIR",
        help="Directory to write results.json and report.txt (default: ./output).",
    )
    p.add_argument(
        "--no-annotate",
        action="store_true",
        default=False,
        help="Skip bounding-box annotation (requires Tesseract by default).",
    )
    p.add_argument(
        "--annotate-level",
        choices=["word", "line", "block", "all"],
        default="all",
        help="Granularity of bounding boxes: word | line | block | all (default: all).",
    )
    return p.parse_args()


def _check_keys(api: str):
    # Read fresh from os.environ so Docker-injected vars are always picked up,
    # regardless of when config.py was imported.
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if api in ("chatgpt", "both"):
        if not openai_key:
            print("ERROR: OPENAI_API_KEY is not set. Add it to .env or export it.", file=sys.stderr)
            sys.exit(1)
        if not openai_key.startswith("sk-"):
            print(f"ERROR: OPENAI_API_KEY looks invalid (expected prefix 'sk-').", file=sys.stderr)
            sys.exit(1)

    if api in ("claude", "both"):
        if not anthropic_key:
            print("ERROR: ANTHROPIC_API_KEY is not set. Add it to .env or export it.", file=sys.stderr)
            sys.exit(1)
        if not anthropic_key.startswith("sk-ant-"):
            print(f"ERROR: ANTHROPIC_API_KEY looks invalid (expected prefix 'sk-ant-').", file=sys.stderr)
            sys.exit(1)


def _process_image(image_path: str, api: str, gpt_ext, claude_ext) -> dict:
    """Run extraction for one image, return an image_entry dict."""
    results = []

    if api == "both":
        # Run both APIs concurrently
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                pool.submit(gpt_ext.extract, image_path): "chatgpt",
                pool.submit(claude_ext.extract, image_path): "claude",
            }
            result_map = {}
            for fut in as_completed(futures):
                key = futures[fut]
                result_map[key] = fut.result()
        results = [result_map["chatgpt"], result_map["claude"]]
    elif api == "chatgpt":
        results = [gpt_ext.extract(image_path)]
    else:
        results = [claude_ext.extract(image_path)]

    return {"path": image_path, "results": results}


def main():
    args = _parse_args()
    _check_keys(args.api)

    gpt_ext = ChatGPTExtractor() if args.api in ("chatgpt", "both") else None
    claude_ext = ClaudeExtractor() if args.api in ("claude", "both") else None

    ground_truth_text = None
    if args.ground_truth:
        gt_path = Path(args.ground_truth)
        if not gt_path.is_file():
            print(f"ERROR: Ground truth file not found: {args.ground_truth}", file=sys.stderr)
            sys.exit(1)
        ground_truth_text = gt_path.read_text(encoding="utf-8")

    images = list(iter_images(args.input))
    if not images:
        print(f"ERROR: No supported images found at: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(images)} image(s) with API={args.api} ...")

    annotate_levels = (
        ["word", "line", "block"] if args.annotate_level == "all"
        else [args.annotate_level]
    )
    annotated_dir = os.path.join(args.output_dir, "annotated")

    image_entries = []
    for i, img_path in enumerate(images, 1):
        print(f"  [{i}/{len(images)}] {img_path}")
        entry = _process_image(img_path, args.api, gpt_ext, claude_ext)

        # Print any API errors immediately so users see them in the terminal
        for r in entry["results"]:
            if not r.success:
                print(f"    [ERROR] {r.api_name}: {r.error}", file=sys.stderr)

        # Compute metrics
        metrics_list = []
        if args.api == "both" and len(entry["results"]) == 2:
            r_gpt, r_claude = entry["results"]
            metrics_list.append(calculator.compare(r_gpt, r_claude))

        if ground_truth_text is not None:
            for r in entry["results"]:
                metrics_list.append(calculator.compare_with_ground_truth(r, ground_truth_text))

        entry["metrics"] = metrics_list

        # Bounding-box annotation
        entry["annotated_images"] = {}
        if not args.no_annotate:
            try:
                saved = annotate(img_path, annotated_dir, levels=annotate_levels)
                entry["annotated_images"] = saved
            except Exception as exc:
                print(f"    [annotator] WARNING: {exc}", file=sys.stderr)

        image_entries.append(entry)

    json_path, txt_path = write_results(image_entries, args.output_dir)
    print(f"\nDone.")
    print(f"  JSON report : {json_path}")
    print(f"  Text report : {txt_path}")
    if not args.no_annotate:
        print(f"  Annotated   : {annotated_dir}/")


if __name__ == "__main__":
    main()
