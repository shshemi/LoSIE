from __future__ import annotations

import argparse
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run inference from an AutoTrain seq2seq checkpoint."
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        required=True,
        help="Path to trained model output directory.",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default="1991-02-14T03:12:09Z knotd[112:7]: debug: cache: prefetch worker started",
        help="Input text for the model.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=4096,
        help="Maximum number of new tokens to generate.",
    )
    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Optional device override (-1=CPU, 0=first GPU). Default: auto-select CUDA, then MPS, then CPU.",
    )
    return parser.parse_args()


def resolve_torch_device(device_arg: int | None) -> torch.device:
    if device_arg is None:
        if torch.cuda.is_available():
            return torch.device("cuda:0")
        mps_backend = getattr(torch.backends, "mps", None)
        if mps_backend is not None and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    if device_arg < 0:
        return torch.device("cpu")

    if not torch.cuda.is_available():
        raise ValueError("CUDA is not available. Use --device -1 or omit --device.")
    if device_arg >= torch.cuda.device_count():
        raise ValueError(
            f"Invalid CUDA device index {device_arg}. Available range: 0..{torch.cuda.device_count() - 1}"
        )
    return torch.device(f"cuda:{device_arg}")


def main() -> None:
    args = parse_args()
    model_dir = args.model_dir.expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(
            f"Model directory does not exist: {model_dir}\\n"
            "Run training first, or pass the correct output directory."
        )

    device = resolve_torch_device(args.device)
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(str(model_dir), local_files_only=True)
    model.to(device)
    model.eval()

    encoded = tokenizer(args.text, return_tensors="pt", truncation=True)
    encoded = {name: tensor.to(device) for name, tensor in encoded.items()}
    with torch.inference_mode():
        output_ids = model.generate(**encoded, max_new_tokens=args.max_new_tokens)
    output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    print(f"Model: {model_dir}")
    print(f"Device: {device}")
    print(f"Input: {args.text}")
    print(f"Output: {output_text}")


if __name__ == "__main__":
    main()
