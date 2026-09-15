# Crucial submission-review actions

Implemented on 16 September 2026. Code/artifact commit: `9a16cb632029aa691c4b4033d37174c67c7aab35`.

| Finding | Action and evidence |
|---|---|
| Mask-only baseline | Independently recomputed from all 404 frozen test targets: F1@55 15.20%, F1@13 27.50%, P@13 18.24%, R@13 84.62%. Added to the main table and narrowed abstract, introduction, discussion and conclusion. |
| Six mask exceptions | Added a reusable data audit and regression checks. Confirmed 4 training, 1 validation and 1 test exceptions. Retained original gold labels and constrained masks. Excluding the inconsistent test row without refitting gives F1@13 A/B/C = 24.28/27.39/32.07%. Complete results in `results/submission/`. |
| Corrected artifact identity | Committed corrected code and saved results. Archived the exact original run source, verified against immutable run provenance. Recorded environment and encoder revision/weight hashes already existed and are now explicitly documented. Packaged a local source/results archive; no remote publication. |
| Malformed analyzer responses | Moved JSON/schema validation inside the retry boundary. Two malformed responses produce a cached failure placeholder; API errors still raise without caching. Added offline failure/recovery tests. No live API calls. |
| Diagnostic supplement | Added `report/Diagnostic-Supplement.md`: all concept scores, all-category confusion counts, thresholds, full JSON example and mask exceptions. Kept this outside the 10-page main PDF. |
| Analyzer majority baseline | Added 54/87 = 62.1% versus analyzer 50.6%, plus six-class macro-F1 16.1%. |
| Small correctness edits | Clarified five seed pairs / 32 assignments and exact-test resolution; included paired-difference CI; marked units and calibration seed averaging; corrected the unsupported claim about unreported ConceptKT baselines; added revision date. |

73 offline tests pass. The independent verifier passes on all 63 saved runs and the exact archived source fingerprint. Source labels were checked locally against the processed table. No model fits were rerun: prediction behavior on the warm cache, training losses, masks and labels were not changed. The sensitivity analysis uses frozen predictions, not retrained models.

Deferred as nonessential: another training-frequency baseline, new architectures/hyperparameter searches, sample-SD convention changes, and extra diagrams. The mask-only rule establishes the critical missing comparison without selecting or tuning another model on the exposed test set.

Retraining remains dependent on the original local cache and encoder weights. The archive enables saved-score verification without them, not independent end-to-end retraining. Original run provenance was not rewritten. The report preserves the correct submitted-draft wording except for necessary corrections and additions.
