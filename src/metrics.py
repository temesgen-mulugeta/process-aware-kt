"""
metrics.py — correctness + deficiency metrics at 55-concept and 13-category levels.

Kept separate from train.py so the metric definitions are easy to read and reuse.
Evaluation retains every gold label, including positives outside the prediction
mask. Only predictions are constrained to associated concepts.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

from src import config as C


def correctness_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict:
    y_pred = (y_prob >= 0.5).astype(int)
    acc = float((y_pred == y_true).mean()) if len(y_true) else 0.0
    try:
        auc = float(roc_auc_score(y_true, y_prob)) if len(set(y_true.tolist())) > 1 else float("nan")
    except ValueError:
        auc = float("nan")
    return {"acc": acc, "auc": auc}


def _to_category(matrix: np.ndarray) -> np.ndarray:
    """Collapse a [N, 55] concept indicator matrix to [N, 13] categories (OR)."""
    out = np.zeros((matrix.shape[0], C.NUM_CATEGORIES), dtype=int)
    for ci, concept in enumerate(C.CONCEPTS):
        cat = C.CATEGORY_TO_ID[C.CONCEPT_TO_CATEGORY[concept]]
        out[:, cat] |= matrix[:, ci].astype(int)
    return out


def deficiency_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Macro P/R/F1 at 55-concept and 13-category levels, plus per-category F1."""
    if y_true.shape[0] == 0:
        return {}
    yt, yp = y_true.astype(int), y_pred.astype(int)

    def macro(a, b):
        return {
            "macro_f1": float(f1_score(a, b, average="macro", zero_division=0)),
            "macro_precision": float(precision_score(a, b, average="macro", zero_division=0)),
            "macro_recall": float(recall_score(a, b, average="macro", zero_division=0)),
        }

    yt13, yp13 = _to_category(yt), _to_category(yp)
    per_cat_f1 = f1_score(yt13, yp13, average=None, zero_division=0)

    return {
        "concept55": macro(yt, yp),
        "category13": macro(yt13, yp13),
        "per_category_f1": {C.CATEGORIES[i]: float(per_cat_f1[i]) for i in range(C.NUM_CATEGORIES)},
        "n_targets": int(yt.shape[0]),
        "n_positive_concept_labels": int(yt.sum()),
    }


def aggregate(runs: list[dict]) -> dict:
    """Mean +/- std over seeds for a flat dict of scalar metrics."""
    keys = runs[0].keys()
    out = {}
    for k in keys:
        vals = np.array([r[k] for r in runs], dtype=float)
        out[k] = {"mean": float(np.nanmean(vals)), "std": float(np.nanstd(vals))}
    return out
