# FINDINGS

Background notes, design decisions, and the actual data path used by this
prototype. Read this alongside `README.md` (how to run it) and `OUTPUTS.md` (the
full captured run record — every stage's output and result table in one file).

---

## 1. Literature notes

Five papers frame this prototype. Summaries below are deliberately short; the
takeaway for our design is in each "→ for us" line.

### ConceptKT — arXiv 2603.24073 (the target benchmark)
Extends KT from binary correctness to **concept-level deficiency prediction**:
given a student's history, predict *which* of 55 concepts (in 13 categories)
they are currently deficient in. Built on MathEDU: 4048 solution processes, 6
students, a **90/10 chronological split** (3644 train / 404 test). It explores
three response-selection strategies for in-context LLM prompting (All Responses,
Same-Concept Only, Conceptual Semantic Selection). Baselines (correctness acc):
DKT 64.80, DKVMN 63.10, GKT 63.20, SAKT 66.46, OKT 69.25; only OKT predicts
deficiencies at all, scoring **1.87% macro-F1**. Best LLM (DeepSeek-R1, semantic
selection) reaches **17.40% macro-F1**. Concept-deficiency prediction is *hard*.
→ for us: this defines our task, label space, split, and the numbers we cite for
context.

### MathEDU — arXiv 2505.18056 (the base dataset)
Student math solution processes paired with instructor feedback
(`teacher_review`: error type, error equation, bilingual advice). Tasks:
correctness classification, error identification, feedback generation.
Fine-tuned models help with the first two but generated feedback stays well
below teacher quality.
→ for us: source of the *process* fields (student_process, correctness,
teacher error annotations). Its `id` maps to a MathQA problem; it carries **no
question text** itself (see §3).

### StatusKT / KT-PSP — arXiv 2512.00311 (closest method)
A **teacher–student–teacher three-stage LLM pipeline** that extracts proficiency
signals from problem-solving processes and feeds them, as intermediate signals,
into existing KT backbones — improving prediction and interpretability over
correctness-only KT. Introduces the KT-PSP-25 dataset.
→ for us: the conceptual blueprint — *LLM as an offline analyzer producing
structured signals that a trained KT model consumes.*

### KCQRL — arXiv 2410.01727 (LLM concept annotation + embeddings)
LLMs annotate knowledge concepts per solution step; contrastive learning builds
concept-aligned question/step embeddings that replace random init in 15 KT
models across 2 datasets, improving them consistently.
→ for us: justification for (a) LLM-derived concept/process features and (b)
embedding the analyzer's `process_summary` with a sentence-transformer.

### LKT / "Language Model Can Do KT" — arXiv 2406.02893
Integrates pretrained LMs with KT via semantic text representations of
questions/concepts; helps the cold-start problem and interpretability, with wins
reported on **large** benchmarks.
→ for us: LM-KT context. The "classic DKT beats LM-KT on *small* data" intuition
is actually best supported by ConceptKT's own results (classic OKT ≈ LLMs on
correctness, but LLMs dominate the hard deficiency metric). With only 6 students
we therefore keep a **simple LSTM backbone** and use the LLM **offline** rather
than end-to-end.

### How our prototype differs from all of them
ConceptKT ran the LLM **end-to-end** (in-context learning over selected
responses). The trained KT baselines used **correctness only**. We sit in the
gap: run the LLM **offline once per past interaction** to produce *structured*
features (error type, faulty step, partial understanding, a plain-English
summary, concept tags), then train a **small DKT-style LSTM on past-only
features** to predict **future** concept deficiency. The hybrid keeps LLM
reasoning where it is strong (reading one solution) and a cheap sequence model
where data is tiny.

---

## 2. Which data path was used — the OFFICIAL gold path (not the fallback)

The agent brief anticipated that ConceptKT might be private and described a
fallback (derive concept labels with Gemini). **That fallback was not needed.**
Both repos are public:

- `github.com/NYCU-NLP-Lab/MathEDU` — process + teacher annotations.
- `github.com/NYCU-NLP-Lab/ConceptKT` — `ConceptKT.json` (4048 records),
  **gold** `associated_concepts` / `missing_concepts`, and the **official
  chronological split** `ConceptKT/train.json` (3644) + `test.json` (404).

So we use **gold concept labels** and the **official split** throughout. This
also made the optional **arm C (gold-feature upper bound)** feasible, which we
include. Because we use the paper's own split and labels, our correctness/F1
numbers are *closer* to comparable than a self-made split would be — but the
modeling setup still differs from the paper (we train a small DKT on past-only
features), so the paper column in `results/comparison_table.md` is **context,
not a head-to-head**.

### Verified data facts (see `src/data_prep.py`)
- 4048 interactions, 6 students (683/685/678/660/682/660).
- Correct 3050 (75.3%) / wrong 998 (24.7%).
- **463** records carry gold `missing_concepts` — the only non-empty deficiency
  targets. The task is heavily imbalanced; macro-F1 is noisy.
- **Chronological order = position within `ConceptKT.json`** (grouped by
  student). `id` is a **MathQA problem id, not a timestamp** — we must not sort
  by it. The official test set is (almost exactly) each student's last-10% tail;
  we use official membership directly, so we reproduce 3644/404 exactly,
  including the two duplicate `(id, student_id)` records and one student whose
  tail is slightly irregular.
- **Join:** ConceptKT is the spine (order + split + gold labels); MathEDU
  process fields attach by `(id, student_id)` with **100% coverage**.

---

## 3. Notable decisions & their rationale

- **No question text.** MathEDU has none (its `id` maps to MathQA). The analyzer
  therefore works from the student's **solution + final answer + correctness**,
  which is enough to characterize the *process*. `data_prep.py` has an optional
  hook: set `MATHQA_PATH` to a JSON dump and question text is joined by `id`.
  Concept identification does not depend on this because deficiency **targets**
  come from ConceptKT gold, not the analyzer.
- **Error-type mapping (8 → 6).** MathEDU uses 8 human-readable error strings;
  the brief's enum has 6. The map lives in `config.MATHEDU_ERROR_TYPE_MAP`. One
  judgment call: `"Comprehension error"` → `wrong_operation_or_concept`
  (misreading the problem ≈ applying the wrong concept). This affects only the
  error-type input feature and the analyzer-validation comparison, not targets.
- **Associated concepts are not leakage.** A question's associated concepts are
  known when it is presented, so we use them both as an input feature and as the
  **output mask** (missing ⊂ associated). Gold `missing_concepts` are the
  target; they are used as *input* only by arm C, and only for **past** steps.
- **Leakage is structural.** Predicting interaction *i+1* uses the LSTM hidden
  state after consuming steps 0..*i* only. `dataset._assert_no_leakage` runs on
  every built sequence, and `python -m src.dataset` includes a **negative test**
  that injects a target into its own history and confirms the assertion fires.
- **Imbalance handling.** The deficiency head uses **focal BCE** over the masked
  associated-concept space, and the decision **threshold is tuned on val**
  (never test) — without this the model predicts all-negative and macro-F1
  collapses to 0, hiding any real arm differences.
- **Tiny model on purpose.** 6 students → hidden size 64, dropout 0.4, early
  stopping. A bigger model memorizes.

---

## 4. Analyzer validation (7a) and the real run

`python -m src.llm_analyzer --validate` compares the analyzer's `error_type` and
`faulty_step` against gold `teacher_review` on ~20 incorrect records and writes
`results/analyzer_validation.md`.

**This was run with a real key (`gemini-3.1-flash-lite`):**
- Analyzer validation: **75% error_type agreement** (15/20), with many exact
  `faulty_step` matches. Disagreements cluster on the genuinely fuzzy
  `calculation_error` ↔ `wrong_operation_or_concept` boundary. Verdict: proceed.
- Full extraction: **3882 API calls, 0 failures** (3962 unique cache files —
  byte-identical student solutions share a cache key). Cost well under $5.

### Headline result (real features, 5 seeds, official split)
Deficiency **macro-F1@13 categories**: A (correctness-only) **24.0%** → B
(LLM process-aware) **28.3%** → C (gold ceiling) **31.1%**. So the offline
LLM-extracted features improve the baseline by **+4.3 pts** and recover roughly
**60%** of the gap to perfect gold features. At the 55-concept level: A 10.3% →
B 12.2% → C 13.4%. Correctness accuracy is flat at 71.8% across arms (the
correctness head is dominated by the base rate; deficiency is the interesting
signal). Per-category error analysis (see `results/comparison_table.md`) shows
the process features help **Sequences/Physics/Statistics** most and slightly
regress **Polynomials/Finance/Geometry**. Numbers are noisy (6 students, 404
test targets) — treat the *ordering* A < B < C as the finding, not the decimals.

### Reproducibility & verification
The headline numbers above are **deterministic and reproducible offline**. The
5 fixed seeds, the official split, and a warm analyzer cache
(`data/llm_features/`, 3962 files covering all 4048 interactions) mean
`python -m src.train` makes **zero API calls** and reproduces `metrics.json`
bit-for-bit. The full pipeline (data_prep → eda → analyzer validate/extract →
dataset leakage self-test → train → evaluate) was re-run end to end and every
stage reproduced; the captured run is recorded verbatim in `OUTPUTS.md`.

A deterministic **`pytest` suite (45 tests, no live API)** guards the
load-bearing logic — the concept/error taxonomy, per-arm feature layout,
**leakage safety** (the assertion is tested to fire), analyzer caching +
hallucination sanitation, metrics, and the model's forward/mask/loss shapes.
Run it with `pytest`. (The model and training paths were previously untested;
they are now covered.)

---

## 5. How to extend this

Obvious next steps, roughly in order of value:

1. **Stronger backbone via pyKT.** Swap `model.ProcessAwareDKT` for an AKT / SAKT
   / GKT / DKVMN model from `pykt-toolkit`, keeping the same per-step feature
   vector. (Listed in `requirements.txt`, intentionally unused here.)
2. **Gated fusion instead of concatenation.** Replace the concat of base +
   LLM-feature components with a learned gate, so the model can down-weight noisy
   analyzer features per step.
3. **Leave-one-student-out evaluation.** With only 6 students, LOSO (MathEDU even
   ships `dataset/leave_one_out/`) is a more honest generalization test than the
   chronological split alone.
4. **Prompt-sensitivity check.** Re-run the analyzer with 2–3 prompt variants
   (and/or a second temperature) and measure how much downstream F1 moves — the
   offline-LLM-feature approach is only useful if it is stable.
5. **Real question text via MathQA.** Join MathQA by `id` (the `MATHQA_PATH`
   hook) and re-extract; measure whether question context improves the analyzer.
6. **Calibrated multi-label thresholds per concept/category**, instead of a
   single global tuned threshold.
