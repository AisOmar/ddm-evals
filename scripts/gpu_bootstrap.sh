#!/usr/bin/env bash
# One-shot setup + collection + analysis for docs/OPEN_WEIGHTS_PROBE_PROTOCOL.md on a rented 80 GB GPU box.
# Run from the repo root on the box:   bash scripts/gpu_bootstrap.sh [label] [batch_size]
# Idempotent: rerun after an interruption and it resumes (collection skips runs already on disk).
set -euo pipefail
LABEL="${1:-qwen3_32b}"; BS="${2:-8}"; MODEL="${MODEL:-Qwen/Qwen3-32B}"
cd "$(dirname "$0")/.."
# on RunPod the volume disk is /workspace and survives a stop; keep the weights there, not on the container disk
if [ -d /workspace ] && [ -z "${HF_HOME:-}" ]; then export HF_HOME=/workspace/hf; fi
export HF_HUB_ENABLE_HF_TRANSFER=0
echo "== $(date) label=$LABEL model=$MODEL batch=$BS"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
if ! command -v uv >/dev/null; then curl -LsSf https://astral.sh/uv/install.sh | sh; fi
export PATH="$HOME/.local/bin:$PATH"
[ -d .venv ] || uv venv .venv
REQ=requirements.txt; [ -f requirements-probe.txt ] && REQ=requirements-probe.txt   # probe-only install on the box
uv pip install --python .venv/bin/python3 -r "$REQ"
.venv/bin/python3 -c "from huggingface_hub import snapshot_download; snapshot_download('$MODEL')"
mkdir -p "results/open_weights_probe/$LABEL"
.venv/bin/python3 scripts/112_probe_collect.py --model "$MODEL" --label "$LABEL" --batch-size "$BS" 2>&1 | tee -a "results/open_weights_probe/$LABEL.log"
.venv/bin/python3 scripts/113_probe_analyze.py --label "$LABEL" 2>&1 | tee -a "results/open_weights_probe/$LABEL.log"
echo "== $(date) done; copy back results/open_weights_probe/$LABEL/ (excluding acts/) and the .log"
