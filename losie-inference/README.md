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

By default this script auto-selects device in this order: CUDA, then MPS, then CPU. Use `--device` to force a specific CUDA index or CPU (`--device -1`).

If output appears cut off, increase `--max-new-tokens`, set `--min-new-tokens`, or test with `--ignore-eos`. The script now prints `Stop reason` (`eos_token` vs `max_new_tokens`) and generated token count.
