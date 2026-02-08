from __future__ import annotations

import argparse
from pathlib import Path

from transformers import pipeline


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
        help="Optional device override passed to transformers (-1=CPU, 0=first GPU). Default: let transformers choose.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = args.model_dir.expanduser().resolve()
    if not model_dir.exists():
        raise FileNotFoundError(
            f"Model directory does not exist: {model_dir}\\n"
            "Run training first, or pass the correct output directory."
        )

    generator = pipeline(
        task="text2text-generation",
        model=str(model_dir),
        tokenizer=str(model_dir),
        device=args.device,
    )

    result = generator(args.text, max_new_tokens=args.max_new_tokens)
    first = result[0] if isinstance(result, list) and result else result

    output_text = None
    if isinstance(first, dict):
        output_text = first.get("generated_text") or first.get("translation_text")
    if output_text is None:
        output_text = str(first)

    print(f"Model: {model_dir}")
    print(f"Device: {generator.device}")
    print(f"Input: {args.text}")
    print(f"Output: {output_text}")


if __name__ == "__main__":
    main()
