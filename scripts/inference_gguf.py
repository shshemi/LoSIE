# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "transformers",
#     "torch",
#     "gguf",
#     "sentencepiece",
#     "accelerate",
# ]
# ///
"""Interactive GGUF inference. Each input is a fresh context, not a continuing chat."""

import argparse
import os
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

SYSTEM_PROMPT = (
    "You are a log parser. Extract all key-value fields from the input log line, "
    "one per line, in the format: key value"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive GGUF inference (new context per input)."
    )
    parser.add_argument("--model", "-m", required=True, help="Path to GGUF model file.")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Max tokens to generate (default: 1024).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature (default: 0.1).",
    )
    args = parser.parse_args()
    args.model = os.path.abspath(args.model)

    if not os.path.isfile(args.model):
        print(f"Error: model file not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    model_dir = os.path.dirname(args.model)
    gguf_filename = os.path.basename(args.model)

    print(f"Loading model: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(model_dir, gguf_file=gguf_filename)
    model = AutoModelForCausalLM.from_pretrained(model_dir, gguf_file=gguf_filename)

    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    model.to(device)

    print(f"Model loaded on {device}. Type a log line (Ctrl+D to quit).\n")

    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input.strip():
            continue

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]
        input_ids = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            output_ids = model.generate(
                input_ids,
                max_new_tokens=args.max_tokens,
                temperature=args.temperature,
                do_sample=args.temperature > 0,
            )

        new_tokens = output_ids[0, input_ids.shape[1] :]
        print(tokenizer.decode(new_tokens, skip_special_tokens=True))
        print()

    print("\nDone.")


if __name__ == "__main__":
    main()
