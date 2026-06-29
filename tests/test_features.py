"""Feature encoding — multi-hot layout, per-arm dense vector shape & content.

The model's correctness depends on the exact byte layout produced here, so these
tests pin the concatenation order and dimensions for every arm.
"""

from __future__ import annotations

import numpy as np

from src import config as C
from src import features as F


def _step(assoc, llm_missing, gold_missing, *, correct=False,
          llm_err="none", gold_err="none") -> F.StepFeatures:
    """Build a StepFeatures without touching the sentence-transformer embedder."""
    return F.StepFeatures(
        id=1, student_id=1, seq_pos=0, split="train",
        correct=1.0 if correct else 0.0,
        assoc_multihot=F.multihot(assoc),
        llm_missing_multihot=F.multihot(llm_missing),
        llm_error_type_id=C.ERROR_TYPE_TO_ID[llm_err],
        summary_embed=np.arange(C.SUMMARY_EMBED_DIM, dtype=np.float32),
        gold_missing_multihot=F.multihot(gold_missing),
        gold_error_type_id=C.ERROR_TYPE_TO_ID[gold_err],
    )


def test_multihot_sets_only_known_concepts():
    first, last = C.CONCEPTS[0], C.CONCEPTS[-1]
    v = F.multihot([first, last, "Totally Invented Concept"])
    assert v.shape == (55,)
    assert v[C.CONCEPT_TO_ID[first]] == 1.0
    assert v[C.CONCEPT_TO_ID[last]] == 1.0
    assert v.sum() == 2.0, "invented concept must be ignored, not added"


def test_dense_dim_matches_each_arm_vector_length():
    sf = _step([C.CONCEPTS[0]], [C.CONCEPTS[1]], [C.CONCEPTS[2]])
    for arm in F.ARMS:
        assert F.step_dense_vector(sf, arm).shape[0] == F.dense_dim(arm)
    assert F.dense_dim("A") == 56
    assert F.dense_dim("B") == F.dense_dim("C") == 56 + 55 + C.SUMMARY_EMBED_DIM


def test_arm_a_is_assoc_plus_correctness_only():
    sf = _step([C.CONCEPTS[0]], [C.CONCEPTS[1]], [C.CONCEPTS[2]], correct=True)
    v = F.step_dense_vector(sf, "A")
    assert v.shape == (56,)
    np.testing.assert_array_equal(v[:55], sf.assoc_multihot)
    assert v[55] == 1.0  # correctness bit


def test_arm_b_uses_llm_missing_and_summary_embed():
    sf = _step([C.CONCEPTS[0]], [C.CONCEPTS[1]], [C.CONCEPTS[2]])
    v = F.step_dense_vector(sf, "B")
    np.testing.assert_array_equal(v[:55], sf.assoc_multihot)
    np.testing.assert_array_equal(v[56:111], sf.llm_missing_multihot)
    np.testing.assert_array_equal(v[111:], sf.summary_embed)


def test_arm_c_uses_gold_missing_and_zeroed_summary():
    sf = _step([C.CONCEPTS[0]], [C.CONCEPTS[1]], [C.CONCEPTS[2]])
    v = F.step_dense_vector(sf, "C")
    np.testing.assert_array_equal(v[56:111], sf.gold_missing_multihot)
    # arm C deliberately zeroes the LLM summary embedding
    np.testing.assert_array_equal(v[111:], np.zeros(C.SUMMARY_EMBED_DIM, dtype=np.float32))


def test_step_error_id_routes_per_arm():
    sf = _step([], [], [], llm_err="calculation_error", gold_err="lack_of_concepts")
    assert F.step_error_id(sf, "A") == C.ERROR_TYPE_TO_ID["none"]
    assert F.step_error_id(sf, "B") == C.ERROR_TYPE_TO_ID["calculation_error"]
    assert F.step_error_id(sf, "C") == C.ERROR_TYPE_TO_ID["lack_of_concepts"]


def test_unknown_arm_raises():
    sf = _step([], [], [])
    import pytest
    with pytest.raises(ValueError):
        F.step_dense_vector(sf, "Z")
