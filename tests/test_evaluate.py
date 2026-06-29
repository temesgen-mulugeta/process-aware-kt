"""Report rendering — comparison table + error analysis from a metrics dict.

Pure string assembly (no torch/sklearn), so these run fast and guard the
mock-run warning banner and the per-category B-minus-A delta logic.
"""

from __future__ import annotations

from src import config as C
from src import evaluate as E


def _stat(mean, std=0.0):
    return {"mean": mean, "std": std}


def _aggregate():
    return {
        "correct_acc": _stat(0.70),
        "correct_auc": _stat(0.60),
        "def_f1_55": _stat(0.12),
        "def_f1_13": _stat(0.28),
        "def_prec_13": _stat(0.30),
        "def_recall_13": _stat(0.27),
    }


def _cat_map(value):
    return {cat: value for cat in C.CATEGORIES}


def _results(mock=False):
    a_cat = _cat_map(0.20)
    b_cat = _cat_map(0.20)
    b_cat[C.CATEGORIES[0]] = 0.40             # B beats A on the first category
    return {
        "meta": {"mock": mock, "model": "gemini-3.1-flash-lite",
                 "seeds": [0, 1], "arms": ["A", "B", "C"]},
        "arms": {
            "A": {"aggregate": _aggregate(), "per_category_f1_mean": a_cat},
            "B": {"aggregate": _aggregate(), "per_category_f1_mean": b_cat},
            "C": {"aggregate": _aggregate(), "per_category_f1_mean": _cat_map(0.20)},
        },
    }


def test_build_table_lists_all_arms_and_model():
    md = E.build_table(_results())
    assert "gemini-3.1-flash-lite" in md
    for arm in ("A", "B", "C"):
        assert E.ARM_NAMES[arm] in md
    assert "MOCK RUN" not in md


def test_build_table_warns_on_mock_run():
    assert "MOCK RUN" in E.build_table(_results(mock=True))


def test_error_analysis_reports_positive_delta_for_improved_category():
    md = E.build_error_analysis(_results())
    assert "Error analysis" in md
    assert C.CATEGORIES[0] in md
    assert "+0.200" in md                      # B(0.40) - A(0.20) on first category
