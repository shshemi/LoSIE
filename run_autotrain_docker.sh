#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-losie-autotrain:cuda12.1}"
DOCKERFILE="${DOCKERFILE:-$ROOT_DIR/autotrain/Dockerfile}"
OUTPUT_DIR="${OUTPUT_DIR:-$ROOT_DIR/output}"
CONFIG_PATH="${CONFIG_PATH:-$ROOT_DIR/autotrain/seq_2_seq_config.yaml}"

if [[ ! -f "$DOCKERFILE" ]]; then
  echo "Dockerfile not found: $DOCKERFILE" >&2
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config not found: $CONFIG_PATH" >&2
  exit 1
fi

echo "Building image $IMAGE_NAME..."
docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" "$ROOT_DIR"

mkdir -p "$OUTPUT_DIR/training" "$OUTPUT_DIR/splits"

echo "Running training container..."
docker run --rm --gpus all \
  -v "$OUTPUT_DIR:/workspace/output" \
  -v "$CONFIG_PATH:/workspace/autotrain/seq_2_seq_config.yaml:ro" \
  "$IMAGE_NAME" "$@"
