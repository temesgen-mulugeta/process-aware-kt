"""Metric definitions — correctness acc/AUC, concept->category collapse, aggregation."""

from __future__ import annotations

import math

import numpy as np

from src import config as C
from src import metrics as M


def test_correctness_metrics_perfect_separation():
    y_true = np.array([1, 0, 1, 0])
    y_prob = np.array([0.9, 0.1, 0.8, 0.2])
    m = M.correctness_metrics(y_true, y_prob)
    assert m["acc"] == 1.0
    assert m["auc"] == 1.0


def test_correctness_auc_is_nan_for_single_class():
    y_true = np.array([1, 1])           # only one class present
    y_prob = np.array([0.9, 0.2])
    m = M.correctness_metrics(y_true, y_prob)
    assert m["acc"] == 0.5
    assert math.isnan(m["auc"])


def test_to_category_ors_concepts_into_their_category():
    mat = np.zeros((1, C.NUM_CONCEPTS), dtype=int)
    mat[0, 0] = 1                       # first concept -> category 0
    cat = M._to_category(mat)
    assert cat.shape == (1, C.NUM_CATEGORIES)
    target_cat = C.CATEGORY_TO_ID[C.CONCEPT_TO_CATEGORY[C.CONCEPTS[0]]]
    assert cat[0, target_cat] == 1
    assert cat.sum() == 1               # exactly one category lit


def test_deficiency_metrics_empty_returns_empty():
    assert M.deficiency_metrics(np.zeros((0, C.NUM_CONCEPTS)), np.zeros((0, C.NUM_CONCEPTS))) == {}


def test_deficiency_metrics_perfect_on_active_category():
    y = np.zeros((2, C.NUM_CONCEPTS), dtype=int)
    y[:, 0] = 1                          # concept 0 positive in both targets
    dm = M.deficiency_metrics(y, y.copy())
    assert dm["n_targets"] == 2
    assert dm["n_positive_concept_labels"] == 2
    active_cat = C.CONCEPT_TO_CATEGORY[C.CONCEPTS[0]]
    assert dm["per_category_f1"][active_cat] == 1.0
    # perfect prediction beats the all-zero predictor on macro-F1
    worse = M.deficiency_metrics(y, np.zeros_like(y))
    assert dm["category13"]["macro_f1"] > worse["category13"]["macro_f1"]


def test_aggregate_mean_and_std():
    agg = M.aggregate([{"x": 1.0}, {"x": 3.0}])
    assert agg["x"]["mean"] == 2.0
    assert agg["x"]["std"] == 1.0
