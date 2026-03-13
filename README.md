# Text Detection — GPT vs Claude

A command-line pipeline that extracts text from images using **ChatGPT (GPT-4o)** and/or **Claude (claude-sonnet-4-6)**, then evaluates and compares the results with OCR-quality metrics and Tesseract-powered bounding-box annotations.

---

## Features

- Extract text from any PNG / JPG / JPEG / WEBP / GIF image
- Run **ChatGPT**, **Claude**, or **both** APIs side-by-side
- Concurrent dual-API extraction for minimal wall-clock time
- Quality metrics: **CER**, **WER**, and **TF-IDF Cosine Similarity**
- Optional comparison against a ground-truth reference file
- Tesseract bounding-box annotation at **word**, **line**, **block**, or **all** levels, color-coded by OCR confidence
- Machine-readable JSON report + human-readable text report
- Docker-first workflow — no local Python or Tesseract required

---

## Project Structure

```
text-detection-fua-gpt-claude/
├── images/                         # Input images
│   └── FUA-YELLOW-VERTICAL.jpg
├── output/                         # Generated results (gitignored)
│   ├── results.json                # Machine-readable report
│   ├── report.txt                  # Human-readable table
│   └── annotated/
│       └── FUA-YELLOW-VERTICAL_annotated_word.png
├── src/
│   ├── extractors/
│   │   ├── base.py                 # ExtractionResult dataclass + BaseExtractor ABC
│   │   ├── chatgpt_extractor.py    # OpenAI GPT-4o extractor
│   │   └── claude_extractor.py    # Anthropic Claude extractor
│   ├── pipeline/
│   │   └── runner.py              # CLI entry point (argparse + orchestration)
│   ├── metrics/
│   │   ├── calculator.py          # CER / WER / cosine similarity
│   │   └── reporter.py            # JSON + plain-text report writer
│   ├── utils/
│   │   ├── config.py              # Environment / model config
│   │   └── image_loader.py        # Recursive image path iterator
│   └── visualizer/
│       ├── detector.py            # Tesseract word/line/block detection
│       └── annotator.py          # PIL bounding-box drawing
├── tests/
│   └── fixtures/
├── Dockerfile                      # Multi-stage: builder + runtime
├── docker-compose.yml
├── run.sh                          # CLI wrapper
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Prerequisites

### Docker (recommended)
- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/) v2

### Local Python
- Python 3.12
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) with English language data

---

## Setup

### 1. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Add images

Place images inside the `images/` folder:

```
images/
  document.png
  scan.jpg
  receipt.jpeg
```

---

## Usage

### Docker (recommended)

```bash
# Build once
docker compose build

# Compare both APIs on all images
docker compose run --rm extractor --api both --input images/

# ChatGPT only — single image
docker compose run --rm extractor --api chatgpt --input images/document.png

# Claude only
docker compose run --rm extractor --api claude --input images/

# With a ground-truth reference (enables CER/WER vs known text)
docker compose run --rm extractor --api both --input images/document.png \
  --ground-truth images/document_truth.txt

# Word-level bounding boxes only
docker compose run --rm extractor --api both --input images/ \
  --annotate-level word

# Skip bounding-box annotation
docker compose run --rm extractor --api both --input images/ \
  --no-annotate

# Custom output directory
docker compose run --rm extractor --api both --input images/ \
  --output-dir output/run1
```

### Local Python

```bash
# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract (system package)
# Ubuntu/Debian:
sudo apt install tesseract-ocr tesseract-ocr-eng
# macOS:
brew install tesseract

# Run
./run.sh --api both --input images/
```

### All flags

| Flag | Values | Default | Description |
|---|---|---|---|
| `--api` | `chatgpt` \| `claude` \| `both` | required | Which API(s) to use |
| `--input` | file or directory path | required | Image(s) to process |
| `--ground-truth` | `.txt` file path | none | Reference text for CER/WER |
| `--output-dir` | directory path | `./output` | Where to write results |
| `--annotate-level` | `word` \| `line` \| `block` \| `all` | `all` | Bounding-box granularity |
| `--no-annotate` | flag | off | Skip bounding-box annotation |

---

## Input Images

### `images/FUA-YELLOW-VERTICAL.jpg`

![FUA-YELLOW-VERTICAL](images/FUA-YELLOW-VERTICAL.jpg)

---

## Output

After each run, results land in `output/`:

```
output/
  results.json          ← machine-readable: all extracted texts + metrics
  report.txt            ← human-readable table with comparison and scores
  annotated/
    <image>_annotated_word.png    ← word-level bounding boxes
    <image>_annotated_line.png    ← line-level bounding boxes
    <image>_annotated_block.png   ← paragraph/block-level bounding boxes
```

### Annotated Output Example

**`output/annotated/FUA-YELLOW-VERTICAL_annotated_word.png`** — Tesseract word-level detection with confidence-coded bounding boxes:

![FUA-YELLOW-VERTICAL annotated word](output/annotated/FUA-YELLOW-VERTICAL_annotated_word.png)

### Input vs Output Comparison

| Input | Annotated Output |
|:---:|:---:|
| ![Input](images/FUA-YELLOW-VERTICAL.jpg) | ![Output](output/annotated/FUA-YELLOW-VERTICAL_annotated_word.png) |
| `images/FUA-YELLOW-VERTICAL.jpg` | `output/annotated/FUA-YELLOW-VERTICAL_annotated_word.png` |

---

### Bounding-box color legend

| Color | Confidence |
|---|---|
| Green | ≥ 80% (high) |
| Orange | 50–79% (medium) |
| Red | < 50% (low) |

---

## Metrics

| Metric | Description |
|---|---|
| **CER** | Character Error Rate — edit distance at character level, normalized by reference length. Lower = more similar. |
| **WER** | Word Error Rate — edit distance at word level, normalized by reference length. Lower = more similar. |
| **Cosine Similarity** | TF-IDF vector overlap between two texts. Higher = more semantically similar (0–1). |
| **Time Delta** | Processing time difference between APIs in milliseconds. |
| **Tokens** | Prompt + completion tokens consumed per API call. |

Metrics are computed between:
- **ChatGPT vs Claude** — when `--api both` is used
- **API vs ground truth** — when `--ground-truth` is provided

---

## Output Schema (`results.json`)

```json
{
  "images": [
    {
      "path": "images/document.png",
      "results": [
        {
          "api": "chatgpt",
          "model": "gpt-4o",
          "image": "images/document.png",
          "text": "Extracted text...",
          "processing_time_ms": 1234.5,
          "tokens": { "prompt": 100, "completion": 50, "total": 150 },
          "error": null
        }
      ],
      "metrics": [
        {
          "reference": "chatgpt vs claude",
          "cer": 0.0512,
          "wer": 0.0833,
          "cosine_similarity": 0.9741,
          "char_counts": { "a": 195, "b": 198 },
          "word_counts": { "a": 36, "b": 36 },
          "time_delta_ms": -320.0,
          "tokens": { "a": 150, "b": 142 }
        }
      ],
      "annotated_images": {
        "word": "output/annotated/document_annotated_word.png",
        "line": "output/annotated/document_annotated_line.png",
        "block": "output/annotated/document_annotated_block.png"
      }
    }
  ]
}
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `openai` | ChatGPT (GPT-4o) API client |
| `anthropic` | Claude API client |
| `Pillow` | Image loading and bounding-box annotation |
| `pytesseract` | Tesseract OCR Python wrapper |
| `editdistance` | CER / WER computation |
| `scikit-learn` | TF-IDF vectorizer for cosine similarity |
| `tabulate` | Human-readable table formatting in `report.txt` |
| `python-dotenv` | Load API keys from `.env` |
| `numpy` | Numerical support for sklearn |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `OPENAI_API_KEY is not set` | Missing key in `.env` | Ensure `.env` exists with valid key |
| `ANTHROPIC_API_KEY is not set` | Missing key in `.env` | Ensure `.env` exists with valid key |
| `No supported images found` | Wrong `--input` path | Verify images are in `images/` and path is correct |
| `tesseract is not installed` | Running locally without Tesseract | Install Tesseract (see Setup section) |
| `Invalid or corrupt image` | Unsupported or broken file | Use PNG/JPG/WEBP; confirm the file opens normally |
| `Permission denied on output/` | Docker volume ownership | Run `chmod -R 777 output/` on the host |

---

## Rebuild After Changes

```bash
# Source code changed only (no dependency changes)
docker compose build

# requirements.txt or Dockerfile changed
docker compose build --no-cache
```
