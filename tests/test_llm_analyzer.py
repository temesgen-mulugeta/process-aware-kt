"""Offline analyzer hygiene: prompt-hash caching, output sanitation, mock safety.

No live API is touched — the single Gemini call is monkeypatched. These tests
pin three guarantees: (1) a warm cache makes zero API calls, (2) hallucinated /
out-of-taxonomy concepts are stripped and correct answers are forced clean, and
(3) mock features never leak gold missing concepts (which would make arm B == C).
"""

from __future__ import annotations

from src import config as C
from src import llm_analyzer as A


def _rec(correct=False):
    return {
        "id": 1, "student_id": 1, "correct": correct,
        "student_process": "2 + 2 = 5", "student_answer": "5",
        "associated_concepts": [C.CONCEPTS[0]],
        "error_type": "calculation_error", "error_equation": "2+2=5",
    }


def _valid_output():
    return A.AnalyzerOutput(
        associated_concepts=[C.CONCEPTS[0]],
        missing_concepts=[],
        error_type="none",
        faulty_step="",
        partial_understanding=["set up the sum"],
        process_summary="The student added two numbers.",
    )


# --- caching ----------------------------------------------------------------
def test_analyze_caches_by_prompt_hash(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "MOCK", False)
    monkeypatch.setattr(C, "LLM_FEATURES", tmp_path)

    calls = {"n": 0}

    def fake_call(prompt):
        calls["n"] += 1
        return _valid_output()

    monkeypatch.setattr(A, "_raw_gemini_call", fake_call)

    rec = _rec(correct=True)
    first = A.analyze(rec)
    second = A.analyze(rec)            # served from disk cache

    assert first.model_dump() == second.model_dump()
    assert calls["n"] == 1, "second analyze() must hit the cache, not the API"
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_cache_key_is_deterministic_and_prompt_sensitive():
    p1 = A.build_prompt(_rec(correct=False))
    p2 = A.build_prompt(_rec(correct=True))   # correctness line differs
    assert A._cache_key(p1) == A._cache_key(p1)
    assert A._cache_key(p1) != A._cache_key(p2)


def test_use_cached_reflects_disk_state(tmp_path, monkeypatch):
    monkeypatch.setattr(A, "MOCK", False)
    monkeypatch.setattr(C, "LLM_FEATURES", tmp_path)
    monkeypatch.setattr(A, "_raw_gemini_call", lambda prompt: _valid_output())
    rec = _rec(correct=True)
    assert A.use_cached(rec) is False
    A.analyze(rec)
    assert A.use_cached(rec) is True


# --- sanitation -------------------------------------------------------------
def test_sanitize_strips_invented_concepts_and_dedupes():
    raw = A.AnalyzerOutput(
        associated_concepts=[C.CONCEPTS[0], C.CONCEPTS[0], "Invented Concept"],
        missing_concepts=[C.CONCEPTS[1], "Also Fake"],
        error_type="calculation_error",
        faulty_step="x=1", partial_understanding=[], process_summary="s",
    )
    out = A._sanitize(raw, _rec(correct=False))
    assert out.associated_concepts == [C.CONCEPTS[0]]      # dedup + drop invented
    assert out.missing_concepts == [C.CONCEPTS[1]]         # drop invented
    assert out.error_type == "calculation_error"


def test_sanitize_forces_correct_answer_to_be_clean():
    raw = A.AnalyzerOutput(
        associated_concepts=[C.CONCEPTS[0]],
        missing_concepts=[C.CONCEPTS[1]],                  # should be wiped
        error_type="calculation_error",                   # should become "none"
        faulty_step="x", partial_understanding=[], process_summary="s",
    )
    out = A._sanitize(raw, _rec(correct=True))
    assert out.missing_concepts == []
    assert out.error_type == "none"


# --- mock safety ------------------------------------------------------------
def test_mock_analyze_never_emits_gold_missing():
    """Mock arm B must not trivially equal arm C: missing_concepts stays empty."""
    rec = _rec(correct=False)
    rec["missing_concepts"] = [C.CONCEPTS[2]]              # gold present in the row
    out = A._mock_analyze(rec)
    assert out.missing_concepts == []
    assert out.associated_concepts == [C.CONCEPTS[0]]      # known-at-prediction-time, OK


def test_build_prompt_contains_concept_list_and_correctness():
    prompt = A.build_prompt(_rec(correct=False))
    assert C.CONCEPTS[0] in prompt
    assert "incorrect" in prompt
    assert "correct" in A.build_prompt(_rec(correct=True))
