#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run.sh — Text extraction CLI wrapper
#
# Usage:
#   ./run.sh --api <chatgpt|claude|both> --input <image_or_dir> [options]
#
# Options:
#   --api              chatgpt | claude | both              (required)
#   --input            path to image file or directory      (required)
#   --ground-truth     path to reference .txt file          (optional)
#   --output-dir       output directory (default: ./output)
#   --no-annotate      skip bounding-box annotation
#   --annotate-level   word | line | block | all (default: all)
#   --help             show this help
#
# Examples:
#   ./run.sh --api both --input images/scan.png
#   ./run.sh --api chatgpt --input images/ --output-dir results/
#   ./run.sh --api claude --input images/doc.jpg --ground-truth truth.txt
#   ./run.sh --api both --input images/ --annotate-level word
#   ./run.sh --api both --input images/ --no-annotate
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Locate script directory so it works from anywhere ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Load .env if present ---
if [[ -f ".env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# --- Defaults ---
API=""
INPUT=""
GROUND_TRUTH=""
OUTPUT_DIR="./output"
NO_ANNOTATE=""
ANNOTATE_LEVEL=""

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --api)
            API="$2"; shift 2 ;;
        --input)
            INPUT="$2"; shift 2 ;;
        --ground-truth)
            GROUND_TRUTH="$2"; shift 2 ;;
        --output-dir)
            OUTPUT_DIR="$2"; shift 2 ;;
        --no-annotate)
            NO_ANNOTATE="1"; shift ;;
        --annotate-level)
            ANNOTATE_LEVEL="$2"; shift 2 ;;
        --help|-h)
            head -25 "$0" | grep "^#" | sed 's/^# \{0,2\}//'
            exit 0 ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Run ./run.sh --help for usage." >&2
            exit 1 ;;
    esac
done

# --- Validate required args ---
if [[ -z "$API" ]]; then
    echo "ERROR: --api is required (chatgpt | claude | both)" >&2
    exit 1
fi

if [[ -z "$INPUT" ]]; then
    echo "ERROR: --input is required" >&2
    exit 1
fi

if [[ "$API" != "chatgpt" && "$API" != "claude" && "$API" != "both" ]]; then
    echo "ERROR: --api must be one of: chatgpt, claude, both" >&2
    exit 1
fi

# --- Check API keys ---
if [[ "$API" == "chatgpt" || "$API" == "both" ]]; then
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        echo "ERROR: OPENAI_API_KEY is not set. Add it to .env or export it." >&2
        exit 1
    fi
fi

if [[ "$API" == "claude" || "$API" == "both" ]]; then
    if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
        echo "ERROR: ANTHROPIC_API_KEY is not set. Add it to .env or export it." >&2
        exit 1
    fi
fi

# --- Build Python command ---
CMD=(python -m src.pipeline.runner --api "$API" --input "$INPUT" --output-dir "$OUTPUT_DIR")

[[ -n "$GROUND_TRUTH" ]]   && CMD+=(--ground-truth "$GROUND_TRUTH")
[[ -n "$NO_ANNOTATE" ]]    && CMD+=(--no-annotate)
[[ -n "$ANNOTATE_LEVEL" ]] && CMD+=(--annotate-level "$ANNOTATE_LEVEL")

# --- Run ---
echo "API flag        : $API"
echo "Input           : $INPUT"
echo "Output dir      : $OUTPUT_DIR"
[[ -n "$GROUND_TRUTH" ]]   && echo "Ground truth    : $GROUND_TRUTH"
[[ -n "$NO_ANNOTATE" ]]    && echo "Annotation      : disabled"
[[ -z "$NO_ANNOTATE" ]]    && echo "Annotation level: ${ANNOTATE_LEVEL:-all}"
echo ""

"${CMD[@]}"
