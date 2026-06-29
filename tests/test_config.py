"""Taxonomy / config invariants — the label space every other module trusts.

These are the cheapest, highest-leverage tests: if the 55-concept space or the
6-way error enum ever drifts, multi-hot encoding and the analyzer silently break.
"""

from __future__ import annotations

from src import config as C


def test_concept_space_is_55_unique():
    assert C.NUM_CONCEPTS == 55
    assert len(C.CONCEPTS) == 55
    assert len(set(C.CONCEPTS)) == 55, "duplicate concept string in CONCEPTS"


def test_concept_to_id_is_a_bijection_over_indices():
    assert C.CONCEPT_TO_ID == {c: i for i, c in enumerate(C.CONCEPTS)}
    for i, c in enumerate(C.CONCEPTS):
        assert C.CONCEPT_TO_ID[c] == i


def test_categories_partition_all_concepts():
    assert C.NUM_CATEGORIES == 13
    # every concept belongs to exactly one category, and categories cover all 55
    flat = [c for cat in C.CONCEPTS_BY_CATEGORY.values() for c in cat]
    assert sorted(flat) == sorted(C.CONCEPTS)
    for c in C.CONCEPTS:
        assert c in C.CONCEPT_TO_CATEGORY
        assert C.CONCEPT_TO_CATEGORY[c] in C.CATEGORIES


def test_error_types_enum_shape():
    assert C.NUM_ERROR_TYPES == 6
    assert C.ERROR_TYPES[-1] == "none", "'none' must be last so its id is highest"
    assert C.ERROR_TYPE_TO_ID == {e: i for i, e in enumerate(C.ERROR_TYPES)}


def test_error_groups_are_disjoint_and_within_enum():
    assert C.CONCEPTUAL_ERRORS.isdisjoint(C.CARELESS_ERRORS)
    known = set(C.ERROR_TYPES)
    assert C.CONCEPTUAL_ERRORS <= known
    assert C.CARELESS_ERRORS <= known
    assert "none" not in C.CONCEPTUAL_ERRORS and "none" not in C.CARELESS_ERRORS


def test_mathedu_error_map_targets_are_valid_enum_values():
    for raw, norm in C.MATHEDU_ERROR_TYPE_MAP.items():
        assert norm in C.ERROR_TYPE_TO_ID, f"{raw!r} maps to unknown enum {norm!r}"


def test_normalize_error_type_handles_known_unknown_and_none():
    assert C.normalize_error_type("Careless error") == "careless_error"
    assert C.normalize_error_type("Wrong mathematical operation/concept") == "wrong_operation_or_concept"
    assert C.normalize_error_type("  Algebraic error  ") == "calculation_error"  # trims
    assert C.normalize_error_type("not a real error string") == "none"
    assert C.normalize_error_type(None) == "none"
    assert C.normalize_error_type("") == "none"
