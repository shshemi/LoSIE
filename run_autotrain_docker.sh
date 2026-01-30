#!/usr/bin/env bash
set -euo pipefail

docker build -f autotrain/Dockerfile -t losie-autotrain:cuda12.1 \
  --build-arg DATA_DIR=output/splits \
  .

docker run --rm --gpus all \
  -v "$(pwd)/output:/output" \
  losie-autotrain:cuda12.1
