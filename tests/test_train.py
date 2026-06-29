"""Training helpers — target-kind masking and val-tuned decision threshold.

The threshold is tuned on val (never test); these tests pin the fallback and the
grid-search behaviour so an imbalanced-label regression can't silently change it.
"""

from __future__ import annotations

import numpy as np
import torch

from src import config as C
from src import dataset as D
from src import train as T


def _seq(target_kind):
    n = len(target_kind)
    return D.Sequence(
        student_id=1,
        dense=torch.zeros(n + 1, 2), err_id=torch.zeros(n + 1, dtype=torch.long),
        next_correct=torch.zeros(n), next_missing=torch.zeros(n, C.NUM_CONCEPTS),
        next_assoc=torch.zeros(n, C.NUM_CONCEPTS),
        target_kind=list(target_kind),
        target_global_idx=list(range(1, n + 1)),
        input_global_idx=list(range(n + 1)),
    )


def test_kind_mask_selects_matching_targets():
    seq = _seq(["train", "val", "test"])
    assert T._kind_mask(seq, "test").tolist() == [False, False, True]
    assert T._kind_mask(seq, "train").tolist() == [True, False, False]
    assert T._kind_mask(seq, "val").sum().item() == 1


def test_tune_threshold_falls_back_to_half_without_positives():
    empty = np.zeros((0, C.NUM_CONCEPTS))
    assert T._tune_threshold(empty, empty) == 0.5
    no_pos = np.zeros((3, C.NUM_CONCEPTS))
    assert T._tune_threshold(no_pos, np.full_like(no_pos, 0.9)) == 0.5


def test_tune_threshold_picks_lowest_threshold_that_captures_the_positive():
    d_true = np.zeros((1, C.NUM_CONCEPTS), dtype=int)
    d_true[0, 0] = 1
    d_prob = np.zeros((1, C.NUM_CONCEPTS))
    d_prob[0, 0] = 0.9                       # captured by every grid threshold <= 0.9
    thr = T._tune_threshold(d_true, d_prob)
    assert thr in T._THRESH_GRID
    assert thr == T._THRESH_GRID[0]          # first (lowest) maximises F1 here
