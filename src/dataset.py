"""
dataset.py — chronological, leakage-safe sequence builder (brief Sections 1 & 6).

One sequence per student, in chronological order. At step i the model sees the
features of interaction i and predicts interaction i+1:

    input  at step i : features(interaction_i)          # PAST only
    target at step i : (correct_{i+1}, missing_{i+1})   # the NEXT interaction

The single most important invariant: when predicting interaction t, the model
must never have consumed features derived from interaction t itself. Because the
prediction for target index t is produced from the hidden state at step t-1
(which only ever consumed inputs 0..t-1), this holds by construction. We ALSO
add an explicit runtime assertion (`_assert_no_leakage`) that is exercised on
every built sequence and has a dedicated negative test (`python -m src.dataset`).

Splits:
  * A target position is a TEST target iff that interaction is in the official
    ConceptKT test split. Everything earlier in the student's timeline is history
    the model may condition on.
  * For early stopping we carve a VAL set: the last VAL_TAIL_FRAC of each
    student's TRAIN targets (still strictly before any test target).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from src import config as C
from src import features as F


@dataclass
class Sequence:
    """One student's tensorized sequence for a given arm."""
    student_id: int
    dense: torch.Tensor          # [T, dense_dim]   input features, step i
    err_id: torch.Tensor         # [T] long         error-type id, step i
    # targets aligned so that index i is the label for predicting interaction i+1
    next_correct: torch.Tensor   # [T-1]            correctness of interaction i+1
    next_missing: torch.Tensor   # [T-1, 55]        gold missing multi-hot of i+1
    next_assoc: torch.Tensor     # [T-1, 55]        assoc mask of i+1
    target_kind: list[str]       # length T-1: "train" | "val" | "test" (for i+1)
    target_global_idx: list[int] # length T-1: global interaction index of i+1 (leakage check)
    input_global_idx: list[int]  # length T:   global interaction index of step i


def _student_order(table: list[dict]) -> dict[int, list[dict]]:
    """Group rows by student, sorted by chronological seq_pos."""
    by_student: dict[int, list[dict]] = {}
    for r in table:
        by_student.setdefault(r["student_id"], []).append(r)
    for sid in by_student:
        by_student[sid].sort(key=lambda r: r["seq_pos"])
    return by_student


def _assign_val(rows: list[dict]) -> set[int]:
    """Pick val target positions: last VAL_TAIL_FRAC of TRAIN interactions.

    Returns a set of seq_pos that should count as 'val' targets (for early stop).
    """
    train_pos = [r["seq_pos"] for r in rows if r["split"] == "train"]
    if not train_pos:
        return set()
    n_val = max(1, int(round(len(train_pos) * C.VAL_TAIL_FRAC)))
    return set(train_pos[-n_val:])


def build_sequences(table: list[dict],
                    store: dict[tuple[int, int], F.StepFeatures],
                    arm: str) -> list[Sequence]:
    """Build one leakage-safe Sequence per student for the given arm."""
    by_student = _student_order(table)
    sequences: list[Sequence] = []

    for sid, rows in by_student.items():
        val_positions = _assign_val(rows)

        dense_steps, err_steps, in_gidx = [], [], []
        nxt_correct, nxt_missing, nxt_assoc, tgt_kind, tgt_gidx = [], [], [], [], []

        for i, r in enumerate(rows):
            sf = store[(r["id"], r["student_id"])]
            dense_steps.append(F.step_dense_vector(sf, arm))
            err_steps.append(F.step_error_id(sf, arm))
            in_gidx.append(r["seq_pos"])

            if i + 1 < len(rows):                     # there is a NEXT interaction to predict
                nxt = rows[i + 1]
                sf_next = store[(nxt["id"], nxt["student_id"])]
                nxt_correct.append(sf_next.correct)
                nxt_missing.append(sf_next.gold_missing_multihot)
                nxt_assoc.append(sf_next.assoc_multihot)
                # target kind comes from the NEXT interaction's split/val membership
                if nxt["split"] == "test":
                    kind = "test"
                elif nxt["seq_pos"] in val_positions:
                    kind = "val"
                else:
                    kind = "train"
                tgt_kind.append(kind)
                tgt_gidx.append(nxt["seq_pos"])

        seq = Sequence(
            student_id=sid,
            dense=torch.tensor(np.stack(dense_steps), dtype=torch.float32),
            err_id=torch.tensor(err_steps, dtype=torch.long),
            next_correct=torch.tensor(nxt_correct, dtype=torch.float32),
            next_missing=torch.tensor(np.stack(nxt_missing), dtype=torch.float32) if nxt_missing else torch.zeros(0, C.NUM_CONCEPTS),
            next_assoc=torch.tensor(np.stack(nxt_assoc), dtype=torch.float32) if nxt_assoc else torch.zeros(0, C.NUM_CONCEPTS),
            target_kind=tgt_kind,
            target_global_idx=tgt_gidx,
            input_global_idx=in_gidx,
        )
        _assert_no_leakage(seq)
        sequences.append(seq)

    return sequences


def _assert_no_leakage(seq: Sequence) -> None:
    """Fail loudly if any target could have seen its own interaction as input.

    Prediction for target at decoding position p (predicting interaction i+1,
    i.e. seq index p maps to input steps 0..p) uses inputs with global indices
    input_global_idx[0..p]. The target's own global index is target_global_idx[p].
    It must be STRICTLY greater than every input index used to predict it.
    """
    for p, tgt_g in enumerate(seq.target_global_idx):
        # inputs visible when predicting target p are steps 0..p (the LSTM hidden
        # state after consuming step p predicts interaction p+1 == this target).
        visible = seq.input_global_idx[: p + 1]
        if tgt_g in visible:
            raise AssertionError(
                f"LEAKAGE: student {seq.student_id} target idx {tgt_g} "
                f"appears in its own history window {visible}"
            )
        if not all(v < tgt_g for v in visible):
            raise AssertionError(
                f"LEAKAGE: student {seq.student_id} target idx {tgt_g} not strictly "
                f"after all visible inputs {visible}"
            )


# ---------------------------------------------------------------------------
# Self-test: prove the leakage assertion actually fires when leakage is injected.
# Run:  python -m src.dataset
# ---------------------------------------------------------------------------
def _negative_test() -> None:
    """Deliberately inject a target into its own history; the assertion must raise."""
    bad = Sequence(
        student_id=99,
        dense=torch.zeros(3, 2), err_id=torch.zeros(3, dtype=torch.long),
        next_correct=torch.zeros(2), next_missing=torch.zeros(2, C.NUM_CONCEPTS),
        next_assoc=torch.zeros(2, C.NUM_CONCEPTS),
        target_kind=["train", "train"],
        target_global_idx=[0, 2],         # first target (0) is ALSO input index 0 -> leakage
        input_global_idx=[0, 1, 2],
    )
    try:
        _assert_no_leakage(bad)
    except AssertionError as e:
        print(f"[negative-test] PASS — assertion fired as expected:\n    {e}")
        return
    raise SystemExit("[negative-test] FAIL — leakage assertion did NOT fire!")


def _positive_test() -> None:
    """Build real sequences (mock features) and confirm the assertion passes."""
    import json
    import os
    os.environ.setdefault("KT_MOCK_ANALYZER", "1")    # no API needed for the structural test
    with open(C.PROCESSED_TABLE, encoding="utf-8") as f:
        table = json.load(f)
    store = F.build_feature_store(table)
    for arm in F.ARMS:
        seqs = build_sequences(table, store, arm)      # _assert_no_leakage runs inside
        n_test = sum(k == "test" for s in seqs for k in s.target_kind)
        n_val = sum(k == "val" for s in seqs for k in s.target_kind)
        n_train = sum(k == "train" for s in seqs for k in s.target_kind)
        print(f"[arm {arm}] students={len(seqs)} dense_dim={seqs[0].dense.shape[1]} "
              f"targets: train={n_train} val={n_val} test={n_test}")


if __name__ == "__main__":
    _negative_test()
    _positive_test()
    print("dataset.py self-tests passed.")
