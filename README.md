# Process-Aware Knowledge Tracing

Offline Gemini process features feed a small, causal two-head LSTM for future correctness and concept deficiency prediction on MathEDU/ConceptKT.

## Advisor revisions

The corrected five-seed macro-F1@13 results are **A 24.28%, B 27.39%, C 32.06%**. The B−A paired difference is **not statistically significant** (t-test p=0.494; exact sign-flip p=0.5625). Error-type-only features score 32.00% in exploratory ablations. Pooled seed-0 LOSO gives A 25.70%, B 24.43%, C 31.08%. The larger analyzer validation study finds 44/87 (50.6%) error-type agreement.

Review diagnostics add a mask-only rule: **27.50% F1@13 and 15.20% F1@55**, so full B does not exceed this simple control. Six records contain gold missing concepts outside the prediction mask; loss ignores these positives, while evaluation retains them. The analyzer's majority comparator is 62.1%, above its 50.6% agreement. See `results/submission/diagnostics.json` and `report/Diagnostic-Supplement.md`.

The revision fixes a feature-store bug: repeated `(id, student_id)` keys overwrote distinct occurrence labels, including a training occurrence with a later test occurrence's gold labels. Features now use `(student_id, seq_pos)`. All results were rerun; the old results are explicitly historical.

- Main report: `Process-Aware-KT-Final-Report.tex` is a 10-page revision (including references) made directly from the submitted draft preserved in `report/original/Process-Aware-KT-Report-Short.tex`, with local corrections and short additions. Detailed diagnostic tables remain in `report/generated/` and `results/revisions/`. The complete source comparison is `report/ORIGINAL_REPORT_REVISION.diff`.
- Retained rewritten comparison: `Process-Aware-KT-Rewritten-Comparison.tex` and `output/pdf/Process-Aware-KT-Rewritten-Comparison.pdf`. Its tables/references are frozen under `report/comparison/`, so later main-report updates do not change the comparison.
- Compiled report: `output/pdf/Process-Aware-KT-Final-Report.pdf`.
- Plan and completed comment audit: `ADVISOR_REVISIONS_PLAN.md`.
- Complete results: `results/revisions/summary.json`, 63 run JSON/NPZ pairs, thresholds, support, per-student diagnostics, calibration and analyzer agreement.
- Historical baseline results: `results/historical/`; older narrative development notes in `FINDINGS.md` are superseded.

## Submission artifacts

Corrected code and numerical artifacts: commit `9a16cb632029aa691c4b4033d37174c67c7aab35`. A portable source/results archive is at `output/Process-Aware-KT-Artifacts-9a16cb6.tar.gz`. This is a local release, not a remotely published GitHub release. The main report cites this commit; its original experiment-source snapshot is included.

## Inputs and setup

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p data/raw
git clone https://github.com/NYCU-NLP-Lab/MathEDU data/raw/MathEDU
git clone https://github.com/NYCU-NLP-Lab/ConceptKT data/raw/ConceptKT
.venv/bin/python -m src.data_prep
```

Raw datasets, processed data and analyzer caches are ignored by Git. Numerical reproduction needs the original `data/llm_features/` cache (3,962 files), which is available locally but not distributed in this repository, plus the frozen `sentence-transformers/all-MiniLM-L6-v2` encoder. The report records this reproducibility limitation explicitly. Do not substitute mock features when reproducing scientific results.

To create a *new* analyzer cache, configure `GEMINI_API_KEY` and `GEMINI_MODEL` via `.env` and explicitly run `python -m src.llm_analyzer --extract`. This invokes Gemini and produces a new extraction condition. Training itself fails on a cache miss and never silently calls the API. Cache keys include prompt version/model/user prompt; bump the prompt version if changing the system instruction.

## Verify saved artifacts or run new experiments

See `report/ARTIFACTS.md` for exact source/environment/encoder identity and the distinction between saved-score verification and retraining. The original execution source is archived unchanged in `results/revisions/source_snapshot/`.

```bash
GEMINI_MODEL=gemini-3.1-flash-lite HF_HUB_OFFLINE=1 KT_RESULTS_DIR=results/new-runs \
  .venv/bin/python -m src.revisions
.venv/bin/python scripts/verify_revision_artifacts.py
.venv/bin/python scripts/submission_checks.py
.venv/bin/python scripts/render_revision_report.py
.venv/bin/python -m pytest
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=output/pdf Process-Aware-KT-Final-Report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=output/pdf Process-Aware-KT-Final-Report.tex
```

The runner executes A/B/C and six additional feature subsets on seeds 0–4 (45 fits), then A/B/C across six held-student folds at seed 0 (18 fits). LOSO excludes the held student from training, early stopping and threshold tuning, but uses their observed history for inference. It is warm-history transfer, not cold start.

Completed per-run files are reused only under matching scientific provenance; Git HEAD alone may change, and the recorded original commit is preserved. To repeat training from scratch, archive `results/revisions/` elsewhere and create a fresh directory; do not mix old and new runs. `environment.txt` records the resolved environment. Source/data/cache fingerprints and CPU deterministic settings are in `provenance.json`. Fixed seeds do not imply cross-platform bitwise identity.

`src.train` remains available for basic A/B/C experiments; use `src.revisions` for the complete advisor analyses and retained predictions. `src.llm_analyzer --validate` is the original small spot-check command; the larger validation census is generated by `src.revisions`.

## Layout

- `src/data_prep.py`: occurrence-aware split reconstruction, source join, taxonomy normalization.
- `src/features.py`, `src/dataset.py`: cached components, signal subsets, occurrence identity and causal sequences.
- `src/model.py`, `src/train.py`: LSTM, masked focal BCE, validation-only threshold selection.
- `src/revisions.py`, `src/revision_analysis.py`: resumable experiment matrix, paired statistics and diagnostics.
- `tests/`: offline regression tests, including feature isolation, repeated labels, actual future-feature invariance, LOSO isolation and statistical calculations.
- `scripts/`: regenerate report tables and verify every saved prediction against source labels.

Gemini generated analyzer features. Codex and Claude assisted with code and report structure; the report includes a separate AI-usage disclosure.
