# Advisor revisions plan

## Submission review completed (16 September 2026)

See `output/Submission-Review-Actions.md` for the selected findings and evidence. The mask-only and majority controls were independently reproduced; all six mask exceptions were audited and the frozen-prediction sensitivity reported. Malformed-output retry handling was fixed, with 73 tests passing. Original run provenance and all 63 saved runs remain unchanged; exact run source is preserved and verified. Corrected code/artifacts are committed at `9a16cb6`; a portable source/results archive passes verification with no raw data or cache present, explicitly skipping source-label alignment in that case. Executable training/feature/mask/loss/metric code matches the original run snapshot.

The main report is still 10 pages, with 11-point text and no em dashes. Necessary factual changes and short additions preserve the correct submitted-draft baseline. Margins are now 0.9 inches to accommodate the crucial findings. Complete diagnostics are supplied separately as Markdown. All ten rendered pages were reviewed. No remote release, live API calls or retraining were performed.


## Correct report baseline, confirmed from author screenshots

All earlier claims below that commit `39341ba` was the intended original report were wrong. That commit contains a differently worded report. The correct original is `../CLAUDE/Process-Aware-KT-Report-Short.tex`, now copied unchanged to `report/original/Process-Aware-KT-Report-Short.tex`. Normalized extracted text from its PDF and the submitted `../Draft-submission/Process-Aware-KT-Draft-Report.pdf` is identical. This is the source beginning “Most knowledge tracing (KT) systems…” and “Knowledge tracing tries to follow…”.

The main report has now been rebuilt from that correct source, with local factual corrections and the compact advisor additions. Its first two introduction paragraphs and research question are preserved verbatim. The original June date, one-inch margins and 11-point body text are retained; spacing remains compact and references use small type. The final PDF is 10 pages including references, with no em dashes. Every page was visually checked. The rewritten comparison is unchanged. The abstract and full-source comparisons now use the correct original. No experiments or code changed.

Everything below is historical workflow context; its earlier report baseline claims and page/section numbers must not guide future editing.


Baseline: `39341ba` on `codex/advisor-revisions`. Preserve the submitted results as historical artifacts. All revised results must use real cached analyzer outputs, the same official split, and explicitly recorded seeds. No live API calls during experiments.

## Current report constraint: 10 pages, original wording

The latest author request supersedes the earlier expanded-paper presentation. The main source was copied directly from commit `39341ba` and changed through local substitutions and short additions. It retains the original section order, paragraphs, seven original table/figure labels, and 11-point body text. The full paper, including references, is limited to 10 pages. Margins are 0.75 inches, paragraph/title spacing is reduced, line spacing is 0.95 of the original, and references use 10-point type. The rewritten comparison remains unchanged.

The compact main paper contains: corrected A/B/C and category results; all signal ablations; paired test p-values and A/B/C confidence intervals; expanded analyzer per-class precision/recall and concept micro scores; the exact grouped eight-to-six mapping and a masked duplicate example; masking/loss equations, validation threshold rule and A/B/C thresholds; a JSON excerpt and derived feature values; leakage pseudocode and test names; per-student/LOSO results, ECE/Brier, fixed-hyperparameter rationale, artifact pointer, threats and separate AI usage.

Full 13-category confusion counts, per-concept analyzer diagnostics, all ablation/LOSO thresholds, paired-difference intervals, reliability bins and provenance remain in `results/revisions/` and `report/generated/`, referenced by the paper instead of appended to it. The extra model/threshold diagrams were optional suggestions; the original pipeline figure, two-head equations and short threshold flow remain. Earlier section/page references below describe prior versions and are historical.

`report/ORIGINAL_REPORT_REVISION.diff` records every source change against the original, and `report/ABSTRACT_WORD_DIFF.md` records the abstract word changes. This is a report-only edit; no experiment or code results changed.


## Work packages and acceptance criteria

1. **Audit and repair data identity.** Verify raw join, duplicate occurrence handling, target masks, and causal alignment. Key features by student and chronological occurrence, not repeated problem ID. Add regression tests for repeated IDs and future-feature invariance. Preserve raw data and document a masked duplicate example.
2. **Controlled experiments.** Add all seven nonempty subsets of missing concepts (M), error type (E), summary (S) to the A baseline; full MES is B. Keep A/B/C architecture and hyperparameters otherwise fixed; use seeds 0–4 on the official split. Record thresholds, epoch count, predictions, model settings and provenance. Explain the original small-model parameter choices; no retrospective test-selected tuning.
3. **Evaluation.** Add two-sided paired seed t-tests plus exact sign-flip tests for B−A and C−B, seed-mean 95% t intervals, support per category, all 13 category TP/FP/FN/TN, per-student F1 and support, associated-entry ECE/Brier and reliability bins. Do not interpret seed intervals as population intervals. Correct for the two primary comparisons.
4. **Generalization.** Run six LOSO folds for A/B/C with seed 0 and fixed hyperparameters. Exclude the held student from training, stopping and threshold selection; evaluate that student's official test tail using only their observed past history. Report this is warm-history transfer, not cold start. Compare with matching seed-0 chronological results.
5. **Analyzer agreement.** Evaluate every wrong answer in the actual validation tails, with gold error annotations; report all-class support/P/R, confusion matrix, and micro/per-concept precision/recall for gold-positive deficiency records. Cache-only reads; keep the old 20-record check historical. Extract a real masked solution→JSON→feature example and embedding norm.
6. **Report.** Update all headline claims and tables to verified revised results. Add loss/mask/threshold equations, exact eight-to-six mapping, duplicate treatment, embedding normalization/no projection, hyperparameter rationale, separate AI-use disclosure, four contributions, threats to validity, artifact checklist with seeds/commit provenance, leakage pseudocode/tests, two-head and threshold schematic, consistent reference formatting. Include tables for ablations, significance/CIs, support, analyzer agreement, per-student/LOSO, calibration and thresholds.
7. **Verification and handoff.** Run full pytest suite, complete experiment matrix, generate tables from machine-readable results, compile LaTeX twice and inspect rendered report pages. Check every advisor item against artifacts and record limitations honestly.

## Audit findings

- Two repeated `(id, student_id)` keys have different gold concept labels. The old feature store overwrites the earlier occurrence, including one training occurrence with a later test occurrence's gold labels. This invalidates a blanket leakage guarantee and requires a full corrected rerun. Existing results will be retained as historical, not silently reused.
- Original data/cache found in the local draft submission and copied to ignored `data/`; no keys copied.
- Five seeds are only five optimizer realizations on six fixed students. Exact two-sided sign-flip p-values cannot be below 0.0625 with five nonzero pairs; significance must be stated cautiously.

## Completion tracking

All seven work packages completed. See the final audit and verification evidence below.

## Final comment-by-comment audit

All 20 advisor items are addressed. The permitted hyperparameter-rationale alternative was used; no unrecorded search is claimed.

| Advisor item | Completed work / evidence |
|---|---|
| Arm B signal ablations | All seven M/E/S subsets, five matched seeds, delta vs A and parameter counts; report Table 6; `results/revisions/summary.json`. |
| Paired seed significance | B−A and C−B paired t, exact sign-flip, Bonferroni correction and difference CIs; Table 5. Neither comparison significant. |
| Per-category supports | All 13 categories including zero-support categories; Table 7. Distinguishes 59 concept labels from category-positive interactions. |
| Loss, mask, threshold equations | Report §4.2, equations 1–5, exact threshold grid/ties/fallback, gamma=2, no extra class weights. |
| Expanded analyzer agreement | All 87 wrong annotated validation answers; six-class P/R/support and confusion; 45 gold-positive records/49 labels, all 55 concept P/R/support; §6.1, Appendix C. |
| Merge/preprocessing detail | Exact eight-to-six mapping Table 1; masked concrete duplicate positions and conflicting labels; §3.1; occurrence-key bug fixed. |
| Separate AI usage | §8 discloses Gemini analyzer and Codex/Claude code/report assistance, following the author's reply. |
| Architecture / hyperparameters | §5 documents fixed original values and practical rationale, explicitly states no search/optimality claim. |
| Analyzer JSON→feature example | §4.1 and `feature_example.json`: real solution, JSON, active index 3, error ID 0, summary norm 1.000. |
| Summary handling / ablation | L2-normalized 384-vector, no projection/activation, space encoding for blanks; ME vs MES quantifies removal (+2.59 pp). |
| Per-student / LOSO | Table 8 plus 18 LOSO fits excluding held student from train/validation/tuning; Table 9 pooled comparison to matched seed 0. |
| Confidence intervals | 95% seed-mean t intervals for A/B/C Table 4; explicit fixed-student limitation. |
| Calibration / thresholds | Associated-entry 10-bin ECE/Brier Table 10; all 45 chronological thresholds and 18 LOSO thresholds Appendix A; reliability bins in JSON. |
| 13-category error breakdown | All category TP/FP/FN/TN for A/B/C, averaged over seeds; Appendix B. |
| Artifact checklist / seeds | §9, README, provenance/environment/artifact manifest with raw repo commits, source hashes and encoder hashes. Cache availability caveat explicit. |
| Leakage check details | Four-line pseudocode, exact test names, duplicate regression and future-feature perturbation tests; §4.3. |
| Explicit contributions | Four bullets in Introduction. |
| Reference / formatting polish | Consistent linked DOI/arXiv references; checked primary records and corrected pyKT authors; all tables/figures referenced in text. |
| Threats to validity | §7.1 separates internal, construct and external threats; removed unsupported guaranteed-ceiling, deterministic-API and robust-ordering claims. |
| Model / threshold visuals | Figures 1 and 2 show two-head LSTM/mask and validation-only threshold selection. |

## Verification results

- Rebuilt raw joined table exactly matches the archived processed table; 4,048 records, zero missing analyzer cache entries.
- 63 real fits completed: 45 chronological (nine input variants × five seeds) and 18 LOSO (three arms × six students); zero live API calls.
- 67 offline tests pass, including actual held-student exclusion from training and threshold selection.
- `scripts/verify_revision_artifacts.py` independently checks all 63 prediction archives against occurrence-specific gold labels, association masks, thresholds, F1, supports, student identity, common test ordering and the source fingerprint.
- Report tables regenerated from `summary.json`; LaTeX compiled twice successfully, with no overfull boxes or unresolved references. All 16 rendered pages visually inspected; one benign underfull paragraph warning remains (no clipping/overlap).
- Original results preserved under `results/historical/`; current root results and README updated. Source, data/cache and frozen encoder fingerprints retained.

## Findings that change the draft's conclusion

Corrected F1@13: A 24.28%, B 27.39%, C 32.06%. B−A = +3.11 pp, paired t p=0.494, exact p=0.5625. Error-type-only is the strongest exploratory LLM subset (32.00%). Pooled LOSO reverses the A/B mean order: A 25.70%, B 24.43%. Expanded analyzer error-type agreement is 50.6%, not the historical spot-check's 75%. The report now states these limitations rather than asserting reliable generalization or a guaranteed gold ceiling.

No advisor item is left pending. Raw duplicate annotation disagreement, absent question text, small student count, lack of hyperparameter optimality evidence and nondistributed analyzer cache are documented study limitations, not omitted work.


## Report presentation correction (14 September 2026)

At the author's request, the main report was restored from baseline commit `39341ba` and edited in place. The original section sequence, related-work discussion, positioning table, corpus table, pipeline figure, feature table and contextual benchmark comparison are retained. Corrections replace affected numbers and unsupported conclusions; the requested mathematical details and experimental analyses are added within the existing structure and in appendices. The original inline bibliography is retained with metadata fixes.

The earlier full rewrite is preserved as `Process-Aware-KT-Rewritten-Comparison.tex` and its compiled PDF, with independent snapshots of the generated tables and references under `report/comparison/`. The phrase “advisor revisions” has been removed from the displayed date/title area of both versions. The earlier checklist's numerical section/table references describe that retained comparison version; the same substantive items remain present in the restored main report under their descriptive headings. This correction changes report presentation only, not code, experiments or results.

Presentation verification: the restored main report is 20 pages and the retained comparison is 16 pages. Both compile without overfull boxes or unresolved references. Rendered pages were visually checked. The original main-section order and all seven original table/figure labels were verified as retained; comparison inputs were checked against their frozen snapshots. No experimental code or numerical results changed in this presentation pass.

## Word-preserving revision pass (14 September 2026)

The author's revision standard is word-level preservation, not just retaining structure. The abstract was rebuilt directly from commit `39341ba` with local substitutions: corrected one-decimal metrics and observed gap fraction, gold-reference wording, occurrence/cache/environment qualifications, and a single significance/LOSO limitation sentence. It retains 225 of 234 original whitespace-delimited words in order (96.2%); `report/ABSTRACT_WORD_DIFF.md` marks every deletion and insertion. Original sentence wording was also restored in the introduction, analyzer bullets, arm comparison, historical validation, results interpretation, category explanation, discussion and conclusion, with local factual corrections only. The original category-table row order was restored, with the additional categories appended. Requested new analyses remain as additions. The separate rewritten comparison was not changed. The current 21-page main PDF compiles without overfull boxes or unresolved references and all pages were visually checked.


### Final wording and punctuation pass

Removed em dashes throughout the main paper and made small word substitutions while preserving its structure and results. Preserved the rewritten comparison separately. Recompiled the 21-page PDF, checked page renders, and confirmed no em dash remains in extracted PDF text. Updated the abstract word comparison. No code or experiment changes were needed.


Final verification of the 10-page edition: compiled twice; all 10 rendered pages checked; no overfull boxes, unresolved references or em dashes; original table/figure labels retained. Two benign underfull warnings in the analyzer schema paragraph. The abstract word diff retains 221/234 original whitespace words (94.4%, counting punctuation changes as edits). No code or experiments changed.
