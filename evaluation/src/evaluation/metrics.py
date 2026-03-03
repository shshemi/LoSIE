"""Metric computation for structured extraction evaluation."""

from __future__ import annotations

from .parsing import parse_target


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_sample_metrics(prediction: str, ground_truth: str) -> dict[str, float]:
    """Compute all metrics for a single prediction/ground-truth pair."""
    pred = parse_target(prediction)
    gold = parse_target(ground_truth)

    pred_keys = set(pred)
    gold_keys = set(gold)

    # Key precision / recall / F1
    if pred_keys:
        key_precision = len(pred_keys & gold_keys) / len(pred_keys)
    else:
        key_precision = 1.0 if not gold_keys else 0.0

    if gold_keys:
        key_recall = len(pred_keys & gold_keys) / len(gold_keys)
    else:
        key_recall = 1.0 if not pred_keys else 0.0

    key_f1 = _f1(key_precision, key_recall)

    # Key-value precision / recall / F1
    pred_kv = set(pred.items())
    gold_kv = set(gold.items())

    if pred_kv:
        kv_precision = len(pred_kv & gold_kv) / len(pred_kv)
    else:
        kv_precision = 1.0 if not gold_kv else 0.0

    if gold_kv:
        kv_recall = len(pred_kv & gold_kv) / len(gold_kv)
    else:
        kv_recall = 1.0 if not pred_kv else 0.0

    kv_f1 = _f1(kv_precision, kv_recall)

    return {
        "key_precision": key_precision,
        "key_recall": key_recall,
        "key_f1": key_f1,
        "kv_precision": kv_precision,
        "kv_recall": kv_recall,
        "kv_f1": kv_f1,
    }


def aggregate_metrics(
    all_sample_metrics: list[dict[str, float]],
) -> dict[str, float]:
    """Macro-average metrics across all samples."""
    if not all_sample_metrics:
        return {}

    keys = all_sample_metrics[0].keys()
    return {
        k: sum(m[k] for m in all_sample_metrics) / len(all_sample_metrics) for k in keys
    }
