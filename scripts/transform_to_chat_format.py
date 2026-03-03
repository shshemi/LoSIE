#!/usr/bin/env python3
"""Transform source/text/target JSONL into chat-format JSONL for fine-tuning."""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Convert source/text/target JSONL to chat-format JSONL."
    )
    parser.add_argument("input", help="Input JSONL file")
    parser.add_argument("output", help="Output JSONL file")
    parser.add_argument(
        "--system-prompt",
        required=True,
        help="System prompt to include in each conversation",
    )
    args = parser.parse_args()

    with open(args.input) as fin, open(args.output, "w") as fout:
        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Skipping line {line_num}: {e}", file=sys.stderr)
                continue

            messages = [
                {"role": "system", "content": args.system_prompt},
                {"role": "user", "content": entry["text"]},
                {"role": "assistant", "content": entry["target"]},
            ]
            fout.write(json.dumps({"messages": messages}) + "\n")


if __name__ == "__main__":
    main()
