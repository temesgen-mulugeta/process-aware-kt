"""
eda.py — exploratory stats on the processed interaction table.

Writes results/eda_report.md answering the brief's Phase-3 questions:
  * interactions per student, totals, ordering field
  * how many incorrect records carry gold missing-concept labels
  * per-concept positive counts over the 55 concepts (flag rare concepts)
  * class imbalance: correct vs careless-error vs conceptual-deficiency
  * both 55-concept and 13-category views

Run:  python -m src.data_prep && python -m src.eda
"""

from __future__ import annotations

import json
from collections import Counter

from src import config as C


def load_table() -> list[dict]:
    if not C.PROCESSED_TABLE.exists():
        raise SystemExit("Run `python -m src.data_prep` first.")
    with open(C.PROCESSED_TABLE, encoding="utf-8") as f:
        return json.load(f)


def _class_of(rec: dict) -> str:
    """Coarse class for imbalance reporting."""
    if rec["correct"]:
        return "correct"
    if rec["error_type"] in C.CONCEPTUAL_ERRORS:
        return "conceptual_deficiency"
    if rec["error_type"] in C.CARELESS_ERRORS:
        return "careless_error"
    return "wrong_unlabeled"          # wrong but no usable error_type


def build_report(table: list[dict]) -> str:
    n = len(table)
    per_student = Counter(r["student_id"] for r in table)

    n_correct = sum(r["correct"] for r in table)
    n_wrong = n - n_correct
    n_missing = sum(bool(r["missing_concepts"]) for r in table)
    n_wrong_with_missing = sum(bool(r["missing_concepts"]) and not r["correct"] for r in table)

    # per-concept positives = how often a concept appears as a *missing* concept (the target signal)
    concept_pos = Counter()
    assoc_pos = Counter()
    for r in table:
        concept_pos.update(r["missing_concepts"])
        assoc_pos.update(r["associated_concepts"])

    cls = Counter(_class_of(r) for r in table)

    # 13-category view of missing-concept positives
    cat_pos = Counter()
    for r in table:
        for c in r["missing_concepts"]:
            cat_pos[C.CONCEPT_TO_CATEGORY[c]] += 1

    L: list[str] = []
    L.append("# EDA Report — MathEDU / ConceptKT (process-aware KT prototype)\n")
    L.append("Generated from `data/processed/interactions.json`.\n")

    L.append("## Dataset overview\n")
    L.append(f"- Total interactions: **{n}**, students: **{len(per_student)}**")
    L.append(f"- Correct: **{n_correct}** ({n_correct/n:.1%}) | Wrong: **{n_wrong}** ({n_wrong/n:.1%})")
    L.append("- **Ordering field:** chronological order = position within ConceptKT.json "
             "(grouped by student). `id` is a MathQA problem id, NOT a timestamp.")
    L.append("- Per-student interaction counts:")
    for sid, c in sorted(per_student.items()):
        L.append(f"    - student {sid}: {c}")
    L.append("")

    L.append("## Deficiency labels (the prediction target)\n")
    L.append(f"- Records carrying gold `missing_concepts`: **{n_missing}** "
             f"({n_missing/n:.1%} of all; all are wrong answers: {n_wrong_with_missing} confirmed)")
    L.append(f"- These are the only records with a non-empty deficiency target — the task is "
             f"**heavily imbalanced** and macro-F1 will be noisy.")
    L.append("")

    L.append("## Class imbalance (coarse)\n")
    for k in ("correct", "conceptual_deficiency", "careless_error", "wrong_unlabeled"):
        v = cls.get(k, 0)
        L.append(f"- {k}: **{v}** ({v/n:.1%})")
    L.append("\n> Missing-concept prediction is only meaningful for the "
             "**conceptual_deficiency** group; careless errors have no missing concept by design.")
    L.append("")

    L.append("## Per-concept positive counts (55-concept view)\n")
    L.append("How often each concept appears as a **missing** concept (target positives). "
             "Concepts with very few positives are effectively unlearnable individually — "
             "this motivates also reporting the coarser 13-category level and using "
             "imbalance-aware loss.\n")
    L.append("| concept | category | missing+ | associated+ |")
    L.append("|---|---|---:|---:|")
    for c in C.CONCEPTS:
        L.append(f"| {c} | {C.CONCEPT_TO_CATEGORY[c]} | {concept_pos.get(c, 0)} | {assoc_pos.get(c, 0)} |")
    rare = [c for c in C.CONCEPTS if 0 < concept_pos.get(c, 0) <= 3]
    zero = [c for c in C.CONCEPTS if concept_pos.get(c, 0) == 0]
    L.append(f"\n- **Concepts never missing (0 positives): {len(zero)}** — {', '.join(zero) or 'none'}")
    L.append(f"- **Rare concepts (1–3 positives): {len(rare)}** — {', '.join(rare) or 'none'}")
    L.append("")

    L.append("## 13-category view of missing-concept positives\n")
    L.append("| category | missing+ |")
    L.append("|---|---:|")
    for cat in C.CATEGORIES:
        L.append(f"| {cat} | {cat_pos.get(cat, 0)} |")
    L.append("")

    L.append("## Decision: evaluation granularity\n")
    L.append("We report deficiency metrics at **both** the 55-concept level (fine, sparse) and the "
             "13-category level (coarse, less sparse), per the brief. The category level is the more "
             "stable signal given the tiny dataset and rare concepts above.")
    L.append("")
    return "\n".join(L)


def main() -> None:
    table = load_table()
    report = build_report(table)
    out = C.RESULTS / "eda_report.md"
    out.write_text(report, encoding="utf-8")
    print(f"wrote {out}")
    # also echo the headline numbers to stdout
    n = len(table)
    print(f"records={n} "
          f"correct={sum(r['correct'] for r in table)} "
          f"missing_labeled={sum(bool(r['missing_concepts']) for r in table)}")


if __name__ == "__main__":
    main()
