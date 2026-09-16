# Submission review round 2: actions

Applied a small editorial pass to the existing report. No code, predictions, metrics, original report, or rewritten comparison changed.

| Finding | Action |
|---|---|
| Overgeneralized benchmark claim | Abstract now names the low reported OKT score and acknowledges unreported trained baselines. |
| Comparison supposedly isolates everything | Contribution now describes feature sets under the same training and evaluation procedure, with gold past features as a reference. |
| Ambiguous analyzer score | Explicitly identifies the analyzer as having 16.1% six-class macro-F1. |
| Strong or inaccurate Table 5 caption | States observed mean B versus A and mask-only results, and that all main arms predict correct at 0.5, yielding 71.78% accuracy. Clarifies that mask-only is fixed. |
| Grammar and undefined full B | Adds the missing conjunction in abstract/conclusion; uses “the full LLM feature bundle” in the abstract. |
| Broken long test identifiers | Moves exact test names and their source file locations to the supplement. |
| Supporting material delivery | Creates `output/Process-Aware-KT-Submission.zip`, containing the final PDF, current supplement and guide, linked diagnostic files, unchanged immutable source/results archive, reading instructions and SHA-256 checksums. Prepared locally, not externally submitted. |

The optional suggestion to reduce repeated gap percentages was left for a broader editorial pass: the report already labels them descriptive and gives the effect interval. Preserving the original wording takes priority over optional restructuring. No new architectures, experiments or remote publication were needed.

## Verification in this pass

- Compiled the PDF twice: 10 pages including references; no overfull boxes or unresolved references.
- Visually inspected all ten rendered pages; no clipped tables or overlapping text.
- Confirmed no em dashes in the paper source or extracted PDF text.
- Verified ZIP integrity, all seven content checksums, linked relative paths and byte equality with the final PDF and current supplement.
- Confirmed the original source/results archive is byte-identical to its committed version.
- Updated the word-level abstract comparison and full source diff against the preserved original report.

No code changed, so the 73-test suite and 63-run verifier were not rerun in this editorial pass. Those successful checks are recorded in the round-2 review. No retraining, live analyzer calls, clean dependency installation or external submission was performed.
