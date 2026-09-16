"""Leakage safety + sequence/target alignment — the single biggest KT risk.

`_assert_no_leakage` is the load-bearing invariant; we test that it FIRES on
injected leakage (port of the module's `_negative_test`) and that real sequences
built by `build_sequences` align targets to the *next* interaction with correct
train/val/test labelling.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from src import config as C
from src import dataset as D
from src import features as F


def _step(*, correct: bool) -> F.StepFeatures:
    return F.StepFeatures(
        id=0, student_id=0, seq_pos=0, split="train",
        correct=1.0 if correct else 0.0,
        assoc_multihot=F.multihot([C.CONCEPTS[0]]),
        llm_missing_multihot=F.multihot([]),
        llm_error_type_id=C.ERROR_TYPE_TO_ID["none"],
        summary_embed=np.zeros(C.SUMMARY_EMBED_DIM, dtype=np.float32),
        gold_missing_multihot=F.multihot([C.CONCEPTS[0]] if not correct else []),
        gold_error_type_id=C.ERROR_TYPE_TO_ID["none"],
    )


def _tiny_table_and_store():
    """One student, 4 chronological interactions: train, train, train, test."""
    corrects = [True, False, True, False]
    splits = ["train", "train", "train", "test"]
    table, store = [], {}
    for pos, (cor, sp) in enumerate(zip(corrects, splits)):
        rid = 100 + pos
        table.append({"id": rid, "student_id": 1, "seq_pos": pos, "split": sp})
        store[(1, pos)] = _step(correct=cor)
    return table, store, corrects


def test_assert_no_leakage_fires_when_target_in_history():
    """Port of dataset._negative_test: target index 0 is also an input index."""
    bad = D.Sequence(
        student_id=99,
        dense=torch.zeros(3, 2), err_id=torch.zeros(3, dtype=torch.long),
        next_correct=torch.zeros(2), next_missing=torch.zeros(2, C.NUM_CONCEPTS),
        next_assoc=torch.zeros(2, C.NUM_CONCEPTS),
        target_kind=["train", "train"],
        target_global_idx=[0, 2],        # target 0 == input 0  -> leakage
        input_global_idx=[0, 1, 2],
    )
    with pytest.raises(AssertionError):
        D._assert_no_leakage(bad)


def test_build_sequences_is_leakage_safe_and_aligned():
    table, store, corrects = _tiny_table_and_store()
    seqs = D.build_sequences(table, store, "A")   # _assert_no_leakage runs inside
    assert len(seqs) == 1
    seq = seqs[0]

    # T=4 inputs, T-1=3 targets
    assert seq.dense.shape == (4, F.dense_dim("A"))
    assert seq.err_id.shape == (4,)
    assert seq.next_correct.shape == (3,)
    assert seq.next_missing.shape == (3, C.NUM_CONCEPTS)

    # each target's correctness equals the NEXT interaction's correctness
    expected_next = torch.tensor([float(c) for c in corrects[1:]])
    torch.testing.assert_close(seq.next_correct, expected_next)

    # every target strictly follows all inputs visible to it
    for p, tgt in enumerate(seq.target_global_idx):
        assert all(v < tgt for v in seq.input_global_idx[: p + 1])


def test_target_kinds_label_next_interaction_split():
    table, store, _ = _tiny_table_and_store()
    seq = D.build_sequences(table, store, "A")[0]
    # 3 train interactions -> 1 val (last train pos); the test interaction -> test
    assert seq.target_kind == ["train", "val", "test"]


def test_assign_val_picks_last_train_tail():
    rows = [{"seq_pos": p, "split": "train"} for p in range(10)]
    rows += [{"seq_pos": 10, "split": "test"}]
    val = D._assign_val(rows)
    # 10 train rows * 0.10 -> 1 val, the last train position
    assert val == {9}


def test_assign_val_empty_when_no_train():
    assert D._assign_val([{"seq_pos": 0, "split": "test"}]) == set()
