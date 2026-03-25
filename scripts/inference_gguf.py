# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "llama-cpp-python",
# ]
# ///

import argparse
import json
import os
import sys

from llama_cpp import Llama

SYSTEM_PROMPT = (
    "You are a log parser. Extract all key-value fields from the input log line, "
    "one per line, in the format: key value"
)


def infer(llm: Llama, user_input: str, max_tokens: int, temperature: float) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    response = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GGUF inference — batch JSONL (default) or interactive mode."
    )
    parser.add_argument("--model", "-m", required=True, help="Path to GGUF model file.")
    parser.add_argument("--input", "-i", help="Input JSONL file (required for batch mode).")
    parser.add_argument("--output", "-o", help="Output JSONL file (required for batch mode).")
    parser.add_argument("--input-key", default="input", help="JSON key to read from each line (default: input).")
    parser.add_argument("--output-key", default="predicted", help="JSON key for LLM response (default: predicted).")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive REPL mode.")
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

    if not args.interactive:
        if not args.input or not args.output:
            parser.error("--input and --output are required in batch mode (use --interactive for REPL)")

    if not os.path.isfile(args.model):
        print(f"Error: model file not found: {args.model}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading model: {args.model}")
    with open(os.devnull, "w") as devnull:
        old_stderr = sys.stderr
        sys.stderr = devnull
        try:
            llm = Llama(
                model_path=args.model,
                n_gpu_layers=-1,
                n_ctx=2048,
                verbose=False,
            )
        finally:
            sys.stderr = old_stderr

    if args.interactive:
        print("Model loaded. Type a log line (Ctrl+D to quit).\n")

        while True:
            try:
                user_input = input("> ")
            except (EOFError, KeyboardInterrupt):
                break

            if not user_input.strip():
                continue

            print(infer(llm, user_input, args.max_tokens, args.temperature))
            print()

        print("\nDone.")
    else:
        print(f"Model loaded. Processing {args.input} ...")
        with open(args.input) as fin, open(args.output, "w") as fout:
            for i, line in enumerate(fin, 1):
                record = json.loads(line)
                value = record[args.input_key]
                result = infer(llm, value, args.max_tokens, args.temperature)
                out_record = {**record, args.output_key: result}
                fout.write(json.dumps(out_record) + "\n")
                print(f"\r  Processed {i} lines", end="", flush=True)
        print(f"\nDone. Output written to {args.output}")


if __name__ == "__main__":
    main()
