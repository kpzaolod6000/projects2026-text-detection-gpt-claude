# How to run the text extraction container

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- [Docker Compose](https://docs.docker.com/compose/install/) v2 (bundled with Docker Desktop)
- An **OpenAI API key** (for `--api chatgpt` or `--api both`)
- An **Anthropic API key** (for `--api claude` or `--api both`)

---

## 1. Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 2. Add images

Place your images (PNG, JPG, JPEG, WEBP, GIF) inside the `images/` folder:

```
images/
  document.png
  scan.jpg
  receipt.jpeg
```

---

## 3. Build the image

```bash
docker compose build
```

This installs Python dependencies and Tesseract OCR inside the container.
Only needed once (or after changing `Dockerfile` / `requirements.txt`).

---

## 4. Run — quick reference

```bash
# Compare both APIs on all images in images/
docker compose run --rm extractor --api both --input images/

# Use only ChatGPT (GPT-4o)
docker compose run --rm extractor --api chatgpt --input images/

# Use only Claude (claude-sonnet-4-6)
docker compose run --rm extractor --api claude --input images/

# Single image
docker compose run --rm extractor --api both --input images/document.png

# With a ground-truth reference file (enables CER/WER vs known text)
docker compose run --rm extractor --api both --input images/document.png \
  --ground-truth images/document_truth.txt

# Custom output directory
docker compose run --rm extractor --api both --input images/ \
  --output-dir output/run1

# Word-level boxes only (faster, less noise)
docker compose run --rm extractor --api both --input images/ \
  --annotate-level word

# Skip bounding-box annotation entirely
docker compose run --rm extractor --api both --input images/ \
  --no-annotate
```

---

## 5. Output files

After each run, results land in the `output/` folder on your host machine
(bind-mounted from the container):

```
output/
  results.json          ← machine-readable: all extracted texts + metrics
  report.txt            ← human-readable table with comparison and scores
  annotated/
    document_annotated_word.png    ← word-level bounding boxes
    document_annotated_line.png    ← line-level bounding boxes
    document_annotated_block.png   ← paragraph/block-level bounding boxes
```

### Bounding-box color legend

| Color  | Confidence       |
|--------|-----------------|
| Green  | ≥ 80% (high)    |
| Orange | 50–79% (medium) |
| Red    | < 50% (low)     |

### Metrics in `results.json` / `report.txt`

| Metric           | Description                                         |
|------------------|-----------------------------------------------------|
| CER              | Character Error Rate (lower = more similar)         |
| WER              | Word Error Rate (lower = more similar)              |
| Cosine Similarity| TF-IDF semantic overlap (higher = more similar)     |
| Time Delta       | Processing time difference between APIs (ms)        |
| Tokens           | Prompt + completion tokens used per API             |

---

## 6. All flags

| Flag               | Values                         | Default   | Description                             |
|--------------------|--------------------------------|-----------|-----------------------------------------|
| `--api`            | `chatgpt` \| `claude` \| `both` | required  | Which API(s) to use                     |
| `--input`          | file or directory path         | required  | Image(s) to process                     |
| `--ground-truth`   | `.txt` file path               | none      | Reference text for CER/WER              |
| `--output-dir`     | directory path                 | `./output`| Where to write results                  |
| `--annotate-level` | `word` \| `line` \| `block` \| `all` | `all` | Bounding-box granularity            |
| `--no-annotate`    | flag (no value)                | off       | Skip bounding-box annotation            |

---

## 7. Run without Docker (local Python)

```bash
# Create and activate a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract (system package — outside pip)
# Ubuntu/Debian:
sudo apt install tesseract-ocr tesseract-ocr-eng

# macOS:
brew install tesseract

# Windows: download installer from https://github.com/UB-Mannheim/tesseract/wiki

# Run
./run.sh --api both --input images/
```

---

## 8. Rebuild after code changes

If you edit Python source files (no dependency changes), the container picks them up
automatically because `src/` is copied at build time — just rebuild:

```bash
docker compose build
```

If you only change `requirements.txt` or `Dockerfile`:

```bash
docker compose build --no-cache
```

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `OPENAI_API_KEY is not set` | Missing key in `.env` | Check `.env` file exists and has the key |
| `ANTHROPIC_API_KEY is not set` | Missing key in `.env` | Check `.env` file exists and has the key |
| `No supported images found` | Wrong `--input` path | Confirm images are in `images/` and path is correct |
| `tesseract is not installed` | Running locally without Tesseract | Install Tesseract (see section 7 above) |
| `Invalid or corrupt image` | Unsupported or broken file | Use PNG/JPG/WEBP; check the file opens normally |
| Permission denied on `output/` | Docker volume ownership | Run `chmod -R 777 output/` on the host |
