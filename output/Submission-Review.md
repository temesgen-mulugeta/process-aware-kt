# Submission review: Process-Aware KT

Reviewed 15 September 2026. Scope: the final 10-page PDF, the submitted 9-page draft, Sebastian's pasted feedback, source code, tests, raw/processed data, analyzer cache, and saved experiment artifacts. This is a review; no implementation or report source was changed.

## Overall assessment

The revision substantially improves the scientific honesty and completeness of the draft. All seven “should fix” requests have substantive additions. However, I recommend another focused revision before submission: a simple missing baseline changes the interpretation, the central masking assumption has six counterexamples in the data, and the submission is not yet tied to a reproducible release of the corrected code.

The defensible contribution is a working, audited prototype with exploratory evidence about feature choices. Reliable improvement from the full LLM feature bundle, or generalization to new students, has not been established.

## What changed from the draft

| Measure | Draft | Revision |
|---|---:|---:|
| A macro-F1@13 | 24.04% | 24.28% |
| B macro-F1@13 | 28.31% | 27.39% |
| C macro-F1@13 | 31.10% | 32.06% |
| B minus A | +4.27 percentage points | +3.11 percentage points |
| Fraction of observed A-to-C gap | About 60% | About 40% |
| Analyzer error-type agreement | 15/20, 75% | 44/87, 50.6% |
| Statistical tests | Absent | Paired t and exact sign-flip tests |
| LOSO | Future work | Six folds, seed 0 |

The occurrence-key fix is real: distinct occurrences now use `(student_id, seq_pos)` rather than allowing repeated problem keys to overwrite labels. The revised source/data/cache fingerprints match the saved experiment provenance. The report appropriately retracts the guaranteed gold ceiling, deterministic-temperature claim, and strong significance/generalization implications of the draft.

## Findings to address before submission

### 1. High priority: add the mask-only baseline and revise the headline interpretation

**Location:** final PDF pp. 1, 7–10; Table 5 and Discussion/Conclusion.

I evaluated the fixed rule `predicted_missing = target_associated_concepts` on the same 404 saved test targets, with the existing metric implementation. It needs no training, history, analyzer, or fitted threshold.

| Predictor | Macro-F1@55 | Macro-F1@13 |
|---|---:|---:|
| Predict every associated concept as missing | **15.20%** | **27.50%** |
| A, five-seed mean | 10.12% | 24.28% |
| B, five-seed mean | 11.58% | 27.39% |
| C, five-seed mean | 13.70% | 32.06% |

This does not invalidate the measured B–A difference, and the baseline has a different precision/recall tradeoff. It does show that full B has not demonstrated an F1 advantage over this simple use of information already available to every arm. The mask-only rule exceeds all three arms at F1@55. It also exactly reproduces the 0.857 category F1 for Permutations and Combinations, illustrating that a strong category score need not reflect learned student history.

**Action:** add this baseline to the results, identify it as a diagnostic added during review, and preferably add a training-frequency baseline. Replace “a qualified/careful yes” with an explicitly exploratory conclusion. Error-type-only at 32.00% is an interesting follow-up, but it was identified after inspecting multiple ablations and is not independently validated.

Suggested wording: “The full LLM feature bundle increased mean F1@13 relative to our LSTM baseline, but the difference was statistically inconclusive, did not extend to LOSO, and did not exceed a mask-only baseline. Error-type-only features warrant further evaluation.”

### 2. High priority: the missing-subset-of-associated assumption is false in six records

**Location:** final PDF pp. 4–5; `src/model.py:75` and `src/model.py:94`; `src/data_prep.py:139`.

The report says a missing concept is always associated with the problem. Checking every processed row finds six exceptions: four optimization-training records, one validation record, and one test record. Positions below are the stored per-student `seq_pos` values.

| Student | Position | Evaluation role | Missing concept outside mask |
|---|---:|---|---|
| S3 | 7 | Training | Expression and Operations with Symbols |
| S3 | 63 | Training | Basic Math Operations |
| S3 | 65 | Training | Basic Math Operations |
| S3 | 70 | Training | Basic Math Operations |
| S3 | 575 | Validation | Basic Math Operations |
| S5 | 634 | Test | Basic Math Operations |

For the test example, the associated list contains only “Expression and Operations with Symbols.” The true missing label “Basic Math Operations” receives a masked logit of -1e9 and can never be predicted. Training loss ignores out-of-mask positives, whereas evaluation retains them. Consequently, only 58 of the 59 test concept positives are reachable; calibration over associated entries also excludes the unreachable positive.

**Action:** document the exceptions and exact treatment, add a regression/data-integrity check, and report a sensitivity analysis or justify retaining the constrained formulation. Do not enlarge prediction-time masks using missing labels: that would introduce target information. Any label correction should come from an independently justified annotation policy, with affected experiments rerun.

### 3. High priority: the artifact citation does not identify the corrected implementation

**Location:** final PDF p. 6; README reproduction instructions; `src/revisions.py:26`.

The cited baseline commit `39341ba` is also the current local HEAD. The corrected source files are modified or untracked, including the new revision runner and analysis modules. Thus the cited commit cannot retrieve the implementation used for these results. The report acknowledges this, but acknowledgment does not fulfill the advisor's reproducible-artifact objective.

The exact analyzer cache is local and omitted from Git. The dependency file uses ranges despite its “pinned dependencies” heading. Provenance records the sentence encoder's name, but not an immutable model revision or weights hash.

**Action:** prepare an immutable release of the corrected code and analysis artifacts, cite its commit, and provide the cache or frozen feature arrays through an appropriate artifact channel if distribution is possible. Otherwise state precisely which results an external reviewer can reproduce. Supply the resolved environment and encoder revision. Preserve the original experiment provenance; updating the release should not silently rewrite run history. Note that the current resume check compares HEAD too, so a later commit changes provenance even if the scientific source is identical.

### 4. Medium priority: malformed analyzer output bypasses the fallback

**Location:** `src/llm_analyzer.py:183`, `:228`, and `:239`; final PDF p. 4.

JSON parsing and Pydantic validation happen inside `_raw_gemini_call`. The surrounding loop catches only `genai_errors.APIError`. The later JSON/validation catch surrounds `_sanitize`, after parsing has already succeeded. A malformed JSON response therefore escapes immediately instead of following the documented retry/null-placeholder policy.

I reproduced this offline by replacing `_raw_gemini_call` with a function raising `JSONDecodeError`: one call, an uncaught exception, and no cache placeholder. Existing analyzer tests exercise valid parsed objects and do not cover this failure boundary.

**Action:** place parsing/schema failures inside the intended retry boundary, distinguish infrastructure failures from malformed model output, and add focused failure-path tests. This does not invalidate the verified warm-cache runs, but it matters for fresh extraction and the robustness claim.

### 5. Medium priority: complete the diagnostic appendix

**Location:** final PDF pp. 6–8; `report/generated/`.

The final PDF contains per-class error precision/recall, but only aggregate concept precision/recall. Full per-concept results and all-category confusion counts exist as generated tables/JSON and are not included in this PDF. The PDF gives just one category's confusion example. The end-to-end JSON example is also abbreviated, with the full output left in a local artifact.

**Action:** supply a concise appendix or a clearly identified, accessible supplement containing the concept table, all 13 category confusion breakdowns, full example, and additional thresholds. Existing generated files can supply much of this without new experiments.

### 6. Medium priority: explain the analyzer's majority baseline

**Location:** final PDF p. 6, Table 4.

The expanded census is a substantial improvement, but an always-“wrong operation/concept” classifier scores 54/87 = **62.1% accuracy**, above the analyzer's **50.6%**. The analyzer has zero recall for lack of concepts, incomplete answers, and careless errors. Its six-class macro-F1 is about **16.1%**, including the zero-support “none” class under the current convention.

**Action:** add the majority comparator and interpret agreement in light of class imbalance. Keep the clear caveat that concept agreement is conditional on gold-positive records; it does not measure false positives across all wrong answers.

## Advisor-feedback checklist

“Implemented” means the requested material is present, not that the experiment establishes a significant gain.

### Should fix before submission

| Advisor request | Assessment | Evidence / remaining work |
|---|---|---|
| All Arm B signal ablations and deltas | Implemented | Table 8, p. 8; all seven nonempty signal subsets, same split/seeds. |
| Paired significance across seeds | Implemented | p. 7; B–A p=.494, C–B p=.185; exact tests and adjustment; limitations explicit. |
| Category support counts | Implemented | Table 6, p. 7; all 13 categories, including zero-support categories. |
| Loss, masking, threshold equations | Implemented with data caveat | Equations on p. 5, threshold protocol p. 6; fix the false subset assumption above. |
| Expanded analyzer–gold agreement | Substantially implemented | 87-record census and per-error-class P/R; concept micro P/R present, per-concept table outside PDF. |
| Exact normalization and duplicate example | Implemented | Table 1 and masked occurrence example, p. 3. |
| Separate AI-usage section | Implemented | Section 9, p. 9. |

### Recommended improvements

| Advisor request | Assessment | Evidence / remaining work |
|---|---|---|
| Architecture justification/search | Implemented via allowed alternative | p. 6 explains fixed defaults; explicitly says no search established optimality. |
| Solution → JSON → features example | Mostly implemented | p. 4 gives snippet, partial JSON, indices, error ID, norm; full JSON should be in supplement. |
| Summary normalization/projection/ablation | Implemented | L2-normalized 384-D, direct concatenation, no projection; removal ablation included. |
| Per-student and LOSO | Implemented | Table 9 and p. 8; seed-0 LOSO, held student excluded from fitting/tuning, observed history allowed. |
| 95% CIs | Implemented | p. 7; seed-mean intervals, correctly distinguished from student uncertainty. |
| Thresholds and calibration | Implemented | Main-arm seed thresholds p. 6; ECE/Brier p. 8; additional thresholds in artifacts. ECE meets the requested plot-or-ECE option. |
| All 13-category confusion/error breakdowns | Partial in submitted PDF | One explicit confusion example; complete diagnostic counts exist outside the PDF. |
| Repository, commit, seeds, checklist | Partial | Link/seeds included; cited commit predates fixes and essential cache is unavailable externally. |
| Leakage snippet and named tests | Implemented | p. 5; actual causal invariance tests present and passing. |
| Contribution bullets | Implemented | Introduction, p. 2. |
| Reference consistency and formatting | Mostly implemented | References improved; dense layout and small consistency issues remain below. |
| Threats to validity | Implemented | Section 8.1, p. 9; internal, construct, external categories. |
| Two-head schematic and threshold flow | Partial / optional | Existing Figure 1 remains; threshold flow is textual; no detailed two-head/mask schematic. |

## Code and numerical verification

- **67 tests passed.**
- The repository's artifact verifier passed for **63 runs** (45 chronological fits and 18 LOSO fits).
- I independently recomputed saved per-run correctness metrics, deficiency P/R/F1 at both levels, category confusion counts, student diagnostics, and calibration; these match their run JSON files.
- Chronological summary run copies match the individual run files.
- Rebuilding preprocessing in memory exactly reproduces the stored table. Train/test occurrence-and-label multisets match the official files, beyond merely matching the counts.
- Source, processed-table, and analyzer-cache fingerprints match the recorded experiment provenance.
- Recomputing the analyzer census from the cached outputs exactly reproduces the saved agreement artifact.
- All 15 main-arm correctness runs predict “correct” for every test target at 0.5. The 71.78% accuracy is exactly majority-class performance, though the nonconstant scores retain AUC information.
- The causal LSTM slicing, occurrence keys, validation-only threshold selection, LOSO held-student exclusion, and ablation feature selection are consistent with the described implementation.

I did not rerun the 63 model fits, make live Gemini calls, or reproduce training in a clean external environment. Verification of saved artifacts is not equivalent to independent retraining. Tests passing does not negate the uncovered data-invariant and malformed-output gaps.

## Writing and presentation

The final PDF is readable, and the equations and main tables render correctly. The added material is compressed: long test names crowd the bottom of p. 5, Table 5 mixes percentage metrics with an AUC proportion without a clear unit note, and the discussion begins on p. 8 then resumes below Table 9 on p. 9. A short supplement would improve readability.

Use “five seed pairs, with 32 sign assignments,” rather than “2^5 seed pairs” (p. 7). The paired B–A 95% interval, already stored, is **[-8.38, +14.61] percentage points**; including it would make the uncertainty in the actual contrast clearer. With five pairs, the minimum two-sided exact sign-flip p-value is 2/32=.0625; explain that resolution limit.

State that ECE/Brier are means over five seeds. Add explicit mean/SD units in tables, and consider using sample SD consistently with the confidence intervals instead of retaining population SD for historical continuity. Explain that the 3,644 official training interactions are further divided for validation.

References were spot-checked against primary sources. The reported ConceptKT comparator numbers match its published table, but calling all trained baselines “almost useless” overgeneralizes: deficiency results are only supplied for OKT; several other rows are unreported. The caveat that the external benchmark is not directly comparable should remain. [ConceptKT source](https://arxiv.org/html/2603.24073v1)

The updated StatusKT ACL citation and pyKT author list are supported by their primary records. The cover still says June 2026 although this revision cites the July 2026 StatusKT publication; add an explicit revision date if June is the original project date. [StatusKT](https://aclanthology.org/2026.findings-acl.961/), [pyKT](https://arxiv.org/abs/2206.11460)

## Recommended submission order

1. Add the mask-only baseline, disclose the six mask exceptions, and narrow the conclusions.
2. Fix analyzer error handling and add targeted regression checks.
3. Package the corrected source and required artifacts under an immutable release identifier.
4. Attach the existing detailed diagnostics as a supplement and polish the PDF.

These are focused revisions. They do not require replacing the LSTM or expanding to a large hyperparameter search before presenting the work as a careful exploratory study.
