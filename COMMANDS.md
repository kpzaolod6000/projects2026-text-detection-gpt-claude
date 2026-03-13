# 1. Set up keys
cp .env.example .env
# edit .env with your keys

# 2. Local usage (needs Python 3.12 + pip install -r
requirements.txt)
./run.sh --api both --input images/scan.png
./run.sh --api chatgpt --input images/
./run.sh --api claude --input images/doc.jpg --ground-truth
truth.txt

# 3. Docker usage
docker compose build
docker compose run --rm extractor --api both --input images/

Outputs land in output/results.json (machine-readable) and
output/report.txt (human-readable table).

  New flags

  ./run.sh --api both --input images/scan.png
          # annotates at all 3 levels (default)
  ./run.sh --api both --input images/ --annotate-level word
          # word boxes only
  ./run.sh --api both --input images/ --no-annotate
          # skip annotation