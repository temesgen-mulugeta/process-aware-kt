"""Statistical and diagnostic summaries; every input is a saved real prediction."""
from itertools import product

import numpy as np
from scipy import stats
from sklearn.metrics import classification_report, confusion_matrix

from src import config as C, metrics as M


def mean_ci(values):
    values = np.asarray(values, dtype=float)
    n = len(values)
    mean = float(values.mean())
    margin = float(stats.t.ppf(.975, n - 1) * stats.sem(values)) if n > 1 else None
    return {"mean": mean, "std": float(values.std()),
            "ci95": [mean - margin, mean + margin] if margin is not None else None,
            "n": n}


def paired_test(a, b):
    """Two-sided paired t and exact sign flip for b-a; pairs must share seed/split."""
    d = np.asarray(b, dtype=float) - np.asarray(a, dtype=float)
    if not np.any(d):
        t_p = 1.0
    elif np.std(d) == 0:
        t_p = 0.0
    else:
        t_p = float(stats.ttest_rel(b, a).pvalue)
    perm = [abs(np.mean(d * signs)) for signs in product((-1, 1), repeat=len(d))]
    exact = float(np.mean(np.asarray(perm) >= abs(d.mean()) - 1e-12))
    return {"delta": mean_ci(d), "paired_t_p": t_p, "sign_flip_p": exact,
            "paired_t_p_bonferroni": min(1., 2 * t_p),
            "sign_flip_p_bonferroni": min(1., 2 * exact)}


def calibration(y, p, assoc, n_bins=10):
    """Equal-width ECE on associated concepts only; structural zeros excluded."""
    valid = np.asarray(assoc).astype(bool)
    y, p = np.asarray(y)[valid], np.asarray(p)[valid]
    if not len(y):
        return {"n": 0, "ece": None, "brier": None, "bins": []}
    bins, ece = [], 0.
    for i in range(n_bins):
        mask = (p >= i / n_bins) & ((p < (i + 1) / n_bins) if i < n_bins - 1 else (p <= 1))
        n = int(mask.sum())
        prob = float(p[mask].mean()) if n else None
        freq = float(y[mask].mean()) if n else None
        if n:
            ece += n / len(y) * abs(prob - freq)
        bins.append({"low": i / n_bins, "high": (i + 1) / n_bins, "n": n,
                     "mean_probability": prob, "positive_rate": freq})
    return {"n": len(y), "ece": float(ece), "brier": float(np.mean((p - y) ** 2)), "bins": bins}


def prediction_summary(path):
    with np.load(path) as d:
        y, p, threshold = d['y'], d['p'], float(d['threshold'])
        yp = p >= threshold
        yt13, yp13 = M._to_category(y), M._to_category(yp)
        categories = {}
        for i, cat in enumerate(C.CATEGORIES):
            yt, pred = yt13[:, i].astype(bool), yp13[:, i].astype(bool)
            categories[cat] = {"support": int(yt.sum()), "tp": int((yt & pred).sum()),
                               "fp": int((~yt & pred).sum()), "fn": int((yt & ~pred).sum()),
                               "tn": int((~yt & ~pred).sum())}
        students = {}
        for sid in np.unique(d['student']):
            mask = d['student'] == sid
            students[str(sid)] = M.deficiency_metrics(y[mask], yp[mask])
        return {"categories": categories, "students": students,
                "calibration": calibration(y, p, d['assoc'])}


def analyzer_agreement(table, analyses):
    """Census of annotated wrong validation answers, not selected for agreement."""
    from src import dataset as D, features as F
    eligible = set()
    for sid, rows in D._student_order(table).items():
        eligible.update((sid, p) for p in D._assign_val(rows))
    pairs = [(r, a) for r, a in zip(table, analyses)
             if (r['student_id'], r['seq_pos']) in eligible and not r['correct'] and r['raw_error_type']]
    gold, pred = [r['error_type'] for r, a in pairs], [a.error_type for r, a in pairs]
    report = classification_report(gold, pred, labels=C.ERROR_TYPES, output_dict=True, zero_division=0)
    positive = [(r, a) for r, a in pairs if r['missing_concepts']]
    y = np.stack([F.multihot(r['missing_concepts']) for r, a in positive])
    p = np.stack([F.multihot(a.missing_concepts) for r, a in positive])
    concepts = classification_report(y, p, target_names=C.CONCEPTS, output_dict=True, zero_division=0)
    return {"n_wrong_annotated_validation": len(pairs), "n_gold_deficiency_records": len(positive),
            "agreement": float(np.mean(np.array(gold) == pred)), "error_types": report,
            "error_confusion": confusion_matrix(gold, pred, labels=C.ERROR_TYPES).tolist(),
            "error_labels": C.ERROR_TYPES, "concepts": concepts,
            "per_student_n": {str(s): sum(r['student_id'] == s for r, a in pairs) for s in range(1, 7)}}
