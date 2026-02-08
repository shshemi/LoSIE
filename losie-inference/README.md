# LoSIE Inference (uv)

Small `uv` project that runs local inference against a trained AutoTrain checkpoint.

## Setup

```bash
cd losie-inference
uv sync
```

## Run

```bash
uv run losie-infer --model-dir ../output/losie "1991-02-14T03:12:09Z knotd[112:7]: debug: cache: prefetch worker started"
```

Optional flags:

```bash
uv run losie-infer --model-dir ../output/losie --device 0 --max-new-tokens 256 "your input text"
```

By default this lets `transformers` pipeline choose the device automatically. Use `--device` only to force a specific index or CPU (`--device -1`).
