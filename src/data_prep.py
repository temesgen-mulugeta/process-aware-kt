"""
data_prep.py — build one tidy, leakage-aware interaction table from the two
public repos, with ConceptKT as the chronological "spine".

Why ConceptKT is the spine (verified empirically, see FINDINGS.md):
  * ConceptKT.json is in CHRONOLOGICAL order, grouped by student
    (student 1: 683 records, then 2: 685, ... total 4048). `id` is a MathQA
    problem id, NOT a timestamp, so we must NOT sort by id.
  * ConceptKT ships the official ~90/10 chronological split
    (ConceptKT/train.json = 3644, ConceptKT/test.json = 404). We use the
    official split membership directly rather than recomputing floor(0.9N+0.5),
    so we match the paper exactly (incl. one student whose test tail is slightly
    irregular).
  * ConceptKT carries the GOLD labels: associated_concepts (required to solve)
    and missing_concepts (concepts the student failed to apply; null when correct).

MathEDU supplies the *process* fields (student_process, student_answer,
correct_or_not, teacher_review/error_type). We attach them by (id, student_id),
which gives 100% coverage (4048/4048, verified).

Note on question text: MathEDU has NO question/problem statement — its `id`
"can be mapped to a problem in MathQA" (README). We degrade gracefully: the
analyzer works from the student's solution + answer + correctness. An optional
MathQA join hook is provided (set MATHQA_PATH to a json mapping id->question).

Run:  python -m src.data_prep
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict

from src import config as C


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def _load_json(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_mathedu() -> list[dict]:
    """Concatenate MathEDU's time_series_split train/val/test (process + teacher_review)."""
    recs: list[dict] = []
    for name in ("train.json", "val.json", "test.json"):
        recs += _load_json(C.MATHEDU_SPLITS / name)
    return recs


def _load_mathqa_questions() -> dict[int, str]:
    """Optional: map id -> question text from a MathQA dump, if MATHQA_PATH is set.

    Returns {} when unavailable (the common case) so the analyzer degrades
    gracefully to solution-only analysis.
    """
    path = os.environ.get("MATHQA_PATH")
    if not path or not os.path.exists(path):
        return {}
    raw = _load_json(path)
    out: dict[int, str] = {}
    for r in raw:
        # MathQA-style records vary; try a few common keys.
        qid = r.get("id")
        q = r.get("Problem") or r.get("question") or r.get("problem")
        if qid is not None and q:
            out[int(qid)] = q
    return out


# ---------------------------------------------------------------------------
# Build the joined table
# ---------------------------------------------------------------------------
def build_table() -> list[dict]:
    spine = _load_json(C.CONCEPTKT_FULL)             # chronological, grouped by student
    test_split = _load_json(C.CONCEPTKT_TEST)
    train_split = _load_json(C.CONCEPTKT_TRAIN)
    mathedu = _load_mathedu()
    questions = _load_mathqa_questions()

    # --- structural sanity checks (fail loud) ---
    assert len(spine) == 4048, f"expected 4048 ConceptKT records, got {len(spine)}"
    students = sorted({r["student_id"] for r in spine})
    assert students == [1, 2, 3, 4, 5, 6], f"unexpected students: {students}"
    assert len(train_split) == 3644 and len(test_split) == 404, (
        f"official split changed: train={len(train_split)} test={len(test_split)}"
    )

    # MathEDU lookup by (id, student_id) — unique on MathEDU side (verified).
    me_by_key: dict[tuple[int, int], dict] = {}
    for r in mathedu:
        me_by_key[(r["id"], r["student_id"])] = r

    # Official test membership. (id, student_id) is *almost* unique on the spine,
    # but 2 keys appear twice. test.json is the chronological tail, so for a
    # duplicated key we mark the LAST k occurrences as test (k = how many times
    # the key is in test.json). This reproduces the official 3644/404 exactly.
    test_counts = Counter((r["id"], r["student_id"]) for r in test_split)
    key_positions: dict[tuple[int, int], list[int]] = defaultdict(list)
    for gi, rec in enumerate(spine):
        key_positions[(rec["id"], rec["student_id"])].append(gi)
    test_global_idx: set[int] = set()
    for key, positions in key_positions.items():
        k = test_counts.get(key, 0)
        if k:
            test_global_idx.update(positions[-k:])   # last k (the tail) are test

    table: list[dict] = []
    per_student_pos: dict[int, int] = defaultdict(int)   # running chronological index per student
    n_joined = 0

    for gi, rec in enumerate(spine):                 # iterate in chronological file order
        sid = rec["student_id"]
        key = (rec["id"], sid)
        pos = per_student_pos[sid]
        per_student_pos[sid] += 1

        me = me_by_key.get(key)
        if me is not None:
            n_joined += 1
        me = me or {}

        # --- correctness ---
        correct = (me.get("correct_or_not") == "correct")

        # --- error_type / faulty equation from teacher_review (first error) ---
        review = me.get("teacher_review") or {}
        errors = review.get("error") or []
        raw_error_type = errors[0].get("error_type") if errors else None
        error_equation = errors[0].get("error_equation") if errors else None
        teacher_advice_en = errors[0].get("teacher_advice_en") if errors else None
        if error_equation in (None, "None", ""):
            error_equation = None

        # --- gold concept labels (the prediction targets) ---
        associated = rec.get("associated_concepts") or []
        missing = rec.get("missing_concepts") or []      # null -> [] (correct answers)

        # Keep only concepts that exist in our canonical 55 (defensive; all should match).
        associated = [c for c in associated if c in C.CONCEPT_TO_ID]
        missing = [c for c in missing if c in C.CONCEPT_TO_ID]

        table.append({
            "id": rec["id"],
            "student_id": sid,
            "seq_pos": pos,                              # chronological index within student
            "split": "test" if gi in test_global_idx else "train",
            "question_text": questions.get(rec["id"]),   # None unless MathQA provided
            "student_process": me.get("student_process", ""),
            "student_answer": me.get("student_answer", ""),
            "correct": correct,
            "error_type": C.normalize_error_type(raw_error_type),
            "raw_error_type": raw_error_type,            # kept for analyzer validation (7a)
            "error_equation": error_equation,
            "teacher_advice_en": teacher_advice_en,
            "associated_concepts": associated,
            "associated_ids": sorted(C.CONCEPT_TO_ID[c] for c in associated),
            "missing_concepts": missing,
            "missing_ids": sorted(C.CONCEPT_TO_ID[c] for c in missing),
        })

    # --- join coverage + split count assertions ---
    assert n_joined == len(spine), f"MathEDU join incomplete: {n_joined}/{len(spine)}"
    n_test = sum(r["split"] == "test" for r in table)
    n_train = len(table) - n_test
    assert (n_train, n_test) == (3644, 404), f"split reconstruction off: {(n_train, n_test)}"

    return table


def summarize(table: list[dict]) -> str:
    n = len(table)
    n_correct = sum(r["correct"] for r in table)
    n_missing = sum(bool(r["missing_concepts"]) for r in table)
    per_student = Counter(r["student_id"] for r in table)
    has_q = sum(r["question_text"] is not None for r in table)
    lines = [
        f"records: {n}  | correct: {n_correct}  wrong: {n - n_correct}",
        f"records with gold missing_concepts: {n_missing}",
        f"records with question text (MathQA join): {has_q}",
        f"per-student counts: {dict(sorted(per_student.items()))}",
        f"split: train={sum(r['split']=='train' for r in table)} test={sum(r['split']=='test' for r in table)}",
    ]
    return "\n".join(lines)


def main() -> None:
    if not C.CONCEPTKT_FULL.exists() or not C.MATHEDU_SPLITS.exists():
        raise SystemExit(
            "Raw data missing. Clone first:\n"
            "  git clone https://github.com/NYCU-NLP-Lab/MathEDU data/raw/MathEDU\n"
            "  git clone https://github.com/NYCU-NLP-Lab/ConceptKT data/raw/ConceptKT"
        )
    table = build_table()
    with open(C.PROCESSED_TABLE, "w", encoding="utf-8") as f:
        json.dump(table, f, ensure_ascii=False, indent=1)
    print(summarize(table))
    print(f"\nwrote {C.PROCESSED_TABLE}")


if __name__ == "__main__":
    main()
