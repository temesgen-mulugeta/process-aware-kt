"""
evaluate.py — render results/comparison_table.md + a short error analysis from
results/metrics.json (brief Section 11).

Our arms are shown side by side. The ConceptKT paper's baseline numbers (brief
Section 8) are included for CONTEXT only. Important caveat: our pipeline and
labels differ (we train a small DKT on past-only features; the paper ran LLMs
end-to-end), so treat the paper column as a reference point, not a head-to-head.
"""

from __future__ import annotations

import json

from src import config as C

# Paper baselines (brief Section 8). acc = correctness accuracy; F1 = deficiency macro-F1.
PAPER_BASELINES = [
    ("DKT",         64.80, None),
    ("DKVMN",       63.10, None),
    ("GKT",         63.20, None),
    ("SAKT",        66.46, None),
    ("OKT",         69.25, 1.87),
    ("Best LLM (DeepSeek-R1, ICL)", 71.02, 17.40),
]

ARM_NAMES = {
    "A": "A — correctness-only (DKT baseline)",
    "B": "B — process-aware (LLM features)",
    "C": "C — gold-feature upper bound",
}


def _fmt(stat: dict, scale: float = 1.0, pct: bool = False) -> str:
    m, s = stat["mean"] * scale, stat["std"] * scale
    suffix = "%" if pct else ""
    return f"{m:.2f}{suffix} ± {s:.2f}"


def build_table(results: dict) -> str:
    meta = results["meta"]
    arms = results["arms"]
    L = ["# Comparison table — process-aware KT prototype\n"]
    if meta.get("mock"):
        L.append("> ⚠️ **MOCK RUN**: features are synthetic placeholders "
                 "(`KT_MOCK_ANALYZER=1`), not real Gemini analyses. These numbers "
                 "verify the pipeline only — do NOT interpret them as results. "
                 "Set a valid `GEMINI_API_KEY`, run the analyzer, and re-run.\n")
    L.append(f"- Analyzer model: `{meta['model']}` | seeds: {meta['seeds']} | "
             f"split: official ConceptKT chronological 90/10 (3644/404).\n")

    # --- our arms ---
    L.append("## Our arms (mean ± std over seeds)\n")
    L.append("| arm | correctness acc | correctness AUC | deficiency F1@55 | F1@13 | precision@13 | recall@13 |")
    L.append("|---|---|---|---|---|---|---|")
    for arm in ("A", "B", "C"):
        if arm not in arms:
            continue
        a = arms[arm]["aggregate"]
        L.append(
            f"| {ARM_NAMES[arm]} "
            f"| {_fmt(a['correct_acc'], 100, pct=True)} "
            f"| {_fmt(a['correct_auc'])} "
            f"| {_fmt(a['def_f1_55'], 100, pct=True)} "
            f"| {_fmt(a['def_f1_13'], 100, pct=True)} "
            f"| {_fmt(a['def_prec_13'], 100, pct=True)} "
            f"| {_fmt(a['def_recall_13'], 100, pct=True)} |"
        )
    L.append("")

    # --- paper context ---
    L.append("## ConceptKT paper baselines (context only — different setup)\n")
    L.append("| method | correctness acc | deficiency macro-F1 |")
    L.append("|---|---|---|")
    for name, acc, f1 in PAPER_BASELINES:
        L.append(f"| {name} | {acc:.2f}% | {('%.2f%%' % f1) if f1 is not None else '—'} |")
    L.append("\n> The paper's classic KT baselines predict correctness well but are "
             "near-useless at concept deficiency (OKT 1.87% macro-F1); only LLMs reach "
             "~17% macro-F1. Concept-level deficiency prediction is the hard frontier.\n")
    return "\n".join(L)


def build_error_analysis(results: dict) -> str:
    arms = results["arms"]
    if "A" not in arms or "B" not in arms:
        return ""
    a_cat = arms["A"]["per_category_f1_mean"]
    b_cat = arms["B"]["per_category_f1_mean"]
    deltas = sorted(((cat, b_cat[cat] - a_cat[cat]) for cat in C.CATEGORIES),
                    key=lambda x: x[1], reverse=True)

    L = ["## Error analysis — where the LLM process features (B) help vs the baseline (A)\n",
         "Per-category deficiency F1 (mean over seeds), B minus A. Positive = process "
         "features helped that category.\n",
         "| category | A F1@cat | B F1@cat | Δ (B−A) |", "|---|---:|---:|---:|"]
    for cat, d in deltas:
        L.append(f"| {cat} | {a_cat[cat]:.3f} | {b_cat[cat]:.3f} | {d:+.3f} |")

    helped = [c for c, d in deltas if d > 1e-6]
    hurt = [c for c, d in deltas if d < -1e-6]
    L.append(f"\n- **Helped most:** {', '.join(c for c, _ in deltas[:3]) if deltas else '—'}")
    L.append(f"- Categories improved: {len(helped)} | unchanged: "
             f"{C.NUM_CATEGORIES - len(helped) - len(hurt)} | regressed: {len(hurt)}")
    if "C" in arms:
        b_f1 = arms["B"]["aggregate"]["def_f1_13"]["mean"]
        c_f1 = arms["C"]["aggregate"]["def_f1_13"]["mean"]
        gap = c_f1 - b_f1
        L.append(f"- **Headroom to the gold ceiling (C):** F1@13 gap C−B = {gap*100:+.2f} pts — "
                 f"how much a perfect analyzer could still add over the current LLM features.")
    L.append("")
    return "\n".join(L)


def main() -> None:
    path = C.RESULTS / "metrics.json"
    if not path.exists():
        raise SystemExit("Run `python -m src.train` first.")
    with open(path, encoding="utf-8") as f:
        results = json.load(f)

    out = build_table(results) + "\n" + build_error_analysis(results)
    dest = C.RESULTS / "comparison_table.md"
    dest.write_text(out, encoding="utf-8")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
