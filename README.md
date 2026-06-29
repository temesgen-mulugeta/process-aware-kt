# Process-Aware Knowledge Tracing — a minimal LLM-enhanced prototype

A small, readable prototype for **concept-level deficiency prediction** on the
MathEDU / ConceptKT data. It uses **Google Gemini offline** as a "process
analyzer" to turn each *past* interaction into structured features, then trains a
**DKT-style LSTM on past-only features** to predict a student's **future**
concept deficiencies.

This is a **learning prototype**: clarity over performance. Every module is
small and commented. See `FINDINGS.md` for the literature notes and design
rationale, and "How to extend this" there for next steps.

## Data flow (the whole pipeline in one line)

```
raw record ─► Gemini analyzer ─► cached JSON ─► feature vector ─► leakage-safe
sequence ─► DKT (LSTM) ─► correctness + masked deficiency heads ─► metrics
```

- **Analyzer** (`src/llm_analyzer.py`): one cached, temperature-0,
  JSON-schema-constrained Gemini call per interaction → `{associated_concepts,
  missing_concepts, error_type, faulty_step, partial_understanding,
  process_summary}`. It only ever sees a *past* solution, never a target.
- **Features** (`src/features.py`): concept multi-hots, a learned error-type
  embedding, a frozen sentence-transformer embedding of `process_summary`, and a
  correctness bit.
- **Sequences** (`src/dataset.py`): one chronological sequence per student;
  step *i* predicts interaction *i+1*; a runtime assertion makes label leakage
  structurally impossible (with a negative self-test).
- **Model** (`src/model.py`): an LSTM with two heads — correctness (sigmoid) and
  a 55-way deficiency head **masked** to the target question's associated
  concepts.

## Three arms

| arm | per-step input | purpose |
|-----|----------------|---------|
| **A** | associated concepts + correctness | correctness-only DKT baseline |
| **B** | A + LLM features (missing concepts, error type, summary embed) | process-aware |
| **C** | A + **gold** past missing concepts + gold error type | gold-feature upper bound (ceiling) |

## Setup

```bash
# 1. Python 3.10+; a fresh venv is recommended
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Get the data (one-time; do not edit data/raw/)
git clone https://github.com/NYCU-NLP-Lab/MathEDU   data/raw/MathEDU
git clone https://github.com/NYCU-NLP-Lab/ConceptKT data/raw/ConceptKT

# 3. Configure Gemini
cp .env.example .env          # then edit:
#   GEMINI_API_KEY=<your real key from https://aistudio.google.com/apikey>
#   GEMINI_MODEL=gemini-2.5-flash-lite   (or any current low-cost Flash model)
```

The model name is read from `GEMINI_MODEL` and never hardcoded, so you can swap
models without touching code.

## How to run

```bash
# Build the tidy interaction table (joins MathEDU + ConceptKT, leakage-aware)
python -m src.data_prep

# Exploratory stats  ->  results/eda_report.md
python -m src.eda

# Validate the analyzer vs gold on ~20 records  ->  results/analyzer_validation.md
python -m src.llm_analyzer --validate      # needs GEMINI_API_KEY

# Extract structured features for ALL interactions (~4k cached calls, < $5)
python -m src.llm_analyzer --extract       # re-running makes ZERO API calls (disk cache)

# Train arms A/B/C over 5 seeds, then render the comparison table
python -m src.train                        # ->  results/metrics.json,
                                           #     results/comparison_table.md,
                                           #     results/train_log.txt
```

Outputs land in `results/`. The disk cache in `data/llm_features/` is keyed by a
hash of (prompt + model), so the analyzer is called once per interaction ever.

### Verify the no-leakage guarantee
```bash
python -m src.dataset      # runs a negative test (assertion MUST fire) + builds real sequences
```

### Tests
A deterministic `pytest` suite (no live API needed) covers the load-bearing
logic — the 55-concept/error taxonomy, per-arm feature layout, **leakage
safety**, analyzer caching + hallucination sanitation, metrics, model
forward/mask/loss shapes, and report rendering:

```bash
pytest                     # 45 tests; uses the disk cache / mocks, never calls Gemini
```

## Results

The full real pipeline has been run with `gemini-3.1-flash-lite` (analyzer
validation 75% error-type agreement; 3882 API calls, 0 failures). Deficiency
macro-F1@13: **A 24.0% → B 28.3% → C 31.1%** — the offline LLM features beat the
correctness-only baseline by +4.3 pts and recover ~60% of the gap to the gold
ceiling. See `results/comparison_table.md` and `FINDINGS.md` §4.

### Reproducing without a key (plumbing only)
If you don't have a valid `GEMINI_API_KEY`, you can still exercise the whole
downstream pipeline with **synthetic** features:

```bash
KT_MOCK_ANALYZER=1 python -m src.train     # plumbing only — NOT real results
```

Mock runs are clearly flagged (⚠️) in `results/comparison_table.md`.

## Repo layout

```
src/
  config.py        constants: 55 concepts, 13 categories, error-type map, seeds, paths, env
  data_prep.py     join MathEDU + ConceptKT -> data/processed/interactions.json (leakage-aware)
  eda.py           exploratory stats -> results/eda_report.md
  llm_analyzer.py  Gemini analyzer + disk cache + JSON schema + 7a validation (+ mock mode)
  features.py      analyzer JSON + gold labels -> model-ready feature components
  dataset.py       chronological, leakage-safe sequence builder (+ negative test)
  model.py         DKT LSTM + correctness/deficiency heads + focal loss
  metrics.py       correctness + deficiency metrics @55 concepts and @13 categories
  train.py         train arms A/B/C over 5 seeds; logs everything
  evaluate.py      render results/comparison_table.md + error analysis
tests/             deterministic pytest suite (taxonomy, leakage, caching, model, metrics)
```

## Out of scope (by design)

No AKT/transformer/graph backbones, no hyperparameter sweeps, no second LLM, and
`data/raw/` is never edited. Because we use the official ConceptKT split, the
paper baselines in the comparison table are **context, not a head-to-head**. See
`FINDINGS.md` → "How to extend this".
