"""CLI entry point for losie-eval."""

from __future__ import annotations

import argparse
import json
import sys

from .metrics import aggregate_metrics, compute_sample_metrics


def _load_jsonl(path: str, column: str) -> list[str]:
    records: list[str] = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if column not in obj:
                print(
                    f"Error: line {lineno} of {path} has no column '{column}'",
                    file=sys.stderr,
                )
                sys.exit(1)
            records.append(obj[column])
    return records


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate structured extraction predictions."
    )
    parser.add_argument(
        "--predictions", required=True, help="Path to predictions JSONL file."
    )
    parser.add_argument(
        "--ground-truth", required=True, help="Path to ground-truth JSONL file."
    )
    parser.add_argument(
        "--prediction-column",
        default="target",
        help="Column name in predictions file (default: target).",
    )
    parser.add_argument(
        "--ground-truth-column",
        default="target",
        help="Column name in ground-truth file (default: target).",
    )
    args = parser.parse_args(argv)

    predictions = _load_jsonl(args.predictions, args.prediction_column)
    ground_truths = _load_jsonl(args.ground_truth, args.ground_truth_column)

    if len(predictions) != len(ground_truths):
        print(
            f"Error: predictions has {len(predictions)} lines but "
            f"ground-truth has {len(ground_truths)} lines.",
            file=sys.stderr,
        )
        sys.exit(1)

    all_metrics = [
        compute_sample_metrics(pred, gold)
        for pred, gold in zip(predictions, ground_truths)
    ]

    agg = aggregate_metrics(all_metrics)

    # Print summary table
    print(f"\nEvaluation results ({len(predictions)} samples)")
    print("-" * 40)
    labels = {
        "key_precision": "Key Precision",
        "key_recall": "Key Recall",
        "key_f1": "Key F1",
        "kv_precision": "Key-Value Precision",
        "kv_recall": "Key-Value Recall",
        "kv_f1": "Key-Value F1",
    }
    for key, label in labels.items():
        print(f"{label:<25} {agg[key]:.4f}")
