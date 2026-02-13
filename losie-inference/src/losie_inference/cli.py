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
        "--min-new-tokens",
        type=int,
        default=0,
        help="Minimum number of new tokens to generate.",
    )
    parser.add_argument(
        "--ignore-eos",
        action="store_true",
        help="Do not stop on EOS token; continue until max token limit.",
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

    generation_kwargs = {
        "max_new_tokens": args.max_new_tokens,
        "min_new_tokens": args.min_new_tokens,
        "return_dict_in_generate": True,
    }
    if args.ignore_eos:
        generation_kwargs["eos_token_id"] = None

    with torch.inference_mode():
        generated = model.generate(**encoded, **generation_kwargs)

    sequence = generated.sequences[0]
    output_text = tokenizer.decode(sequence, skip_special_tokens=True)

    eos_token_id = model.generation_config.eos_token_id
    if isinstance(eos_token_id, int):
        eos_token_ids = {eos_token_id}
    elif isinstance(eos_token_id, (list, tuple, set)):
        eos_token_ids = {int(token_id) for token_id in eos_token_id}
    else:
        eos_token_ids = set()

    ended_on_eos = bool(eos_token_ids) and int(sequence[-1].item()) in eos_token_ids
    new_token_count = (
        int(sequence.shape[-1]) - 1
    )  # seq2seq generation starts from decoder start token.
    if ended_on_eos:
        stop_reason = "eos_token"
    elif new_token_count >= args.max_new_tokens:
        stop_reason = "max_new_tokens"
    else:
        stop_reason = "unknown"

    print(f"Model: {model_dir}")
    print(f"Device: {device}")
    print(f"New tokens: {new_token_count}")
    print(f"Stop reason: {stop_reason}")
    print(f"Input: {args.text}")
    print(f"Output: {output_text}")


if __name__ == "__main__":
    main()
