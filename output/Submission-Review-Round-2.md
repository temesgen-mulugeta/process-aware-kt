# Submission review — round 2

Reviewed 16 September 2026 at commit `882e04c`, including the updated 10-page PDF, maintained code, original execution-source snapshot, diagnostic supplement, and portable archive associated with `9a16cb6`.

## Verdict

**The substantive findings from the first review have been addressed. The work is close to submission-ready as an exploratory study.** I found no new issue affecting the reported numerical results in this review. I recommend a short editorial pass and ensuring that the supplement and artifact archive accompany the submission. No additional model fits are necessary solely to address the previous findings under the report's now-explicit constrained-task interpretation.

This is not evidence of reliable benefit from full Arm B: that result remains statistically inconclusive, does not extend to LOSO, and does not exceed the mask-only baseline. The report now communicates those limits prominently.

## Resolution of previous findings

| Previous finding | Assessment |
|---|---|
| Missing mask-only baseline | Resolved. Table 5 includes 27.50% F1@13 and 15.20% F1@55; the abstract, results, discussion, and conclusion acknowledge it. |
| Six out-of-mask gold-label exceptions | Resolved for the declared constrained formulation. All six are disclosed; original labels and masks remain intact. A frozen-prediction sensitivity check is reported accurately and is not presented as retraining. |
| Incorrect artifact identity | Resolved locally. The corrected code/results are committed, the exact original execution source is archived, and environment/encoder identities are documented. External access still depends on delivering the archive or publishing the commit. |
| Malformed analyzer responses escaping fallback | Resolved. Parsing/schema validation now falls within the retry boundary. Tests cover repeated malformed output, schema failure followed by recovery, and API failures without cached placeholders. |
| Missing detailed diagnostics | Resolved in the companion supplement. It includes all 55 concept rows, category confusion counts, thresholds, the full worked JSON example, and mask exceptions. Submit it with the PDF. |
| Missing analyzer majority comparison | Resolved. The report includes 62.1% majority accuracy versus 50.6% analyzer accuracy and the analyzer's 16.1% six-class macro-F1. |

The advisor's seven mandatory requests are substantively covered across the main report and supplement. The recommended additions are also substantially covered. A separate detailed two-head schematic remains optional; architecture justification is supplied through the advisor's allowed explanation alternative rather than an additional search.

## Remaining edits, in priority order

### 1. Align the abstract and contribution bullet with the qualified results

**PDF pp. 1–2.** The abstract still says “Trained KT models do this very poorly, and only large language models ... do reasonably well.” The introduction now correctly says several trained baselines have no reported deficiency score. Use that narrower description in the abstract too; the current wording generalizes beyond the reported comparator evidence.

The contribution bullet claims the comparison “separates the value of the LLM signals from everything else.” This is stronger than p. 7, which correctly acknowledges changing parameter counts. Suggested replacement: “A controlled comparison of feature sets under the same training and evaluation procedure, including a gold-feature reference.”

These are interpretation/wording issues, not evidence that the computed results are wrong.

### 2. Make the main table and analyzer paragraph unambiguous

**PDF pp. 6–7.** Replace “its six-class macro-F1 is 16.1%” with “The analyzer's six-class macro-F1 is 16.1%.” The current pronoun could refer to the immediately preceding majority predictor.

Table 5's caption still says “Deficiency is where the process signals matter.” Prefer a factual description such as “The full feature bundle improves mean deficiency scores relative to A but does not exceed the mask-only control.”

The same caption attributes flat correctness accuracy to the 75% corpus rate. The actual test majority is 71.78%, and every main-arm test prediction at the 0.5 cutoff is “correct,” as established in the first review. State that directly instead of implying that identical accuracy alone proves why the head behaves that way.

### 3. Deliver the supplementary material, not just its local path

**PDF pp. 5–6; `report/ARTIFACTS.md`.** The local archive works, and the unavailable-cache limitation is now accurately disclosed. The documentation explicitly says the release has not been published remotely. A GitHub URL and commit identifier in the PDF are not sufficient if the recipient cannot retrieve that commit.

Attach `report/Diagnostic-Supplement.md` and `output/Process-Aware-KT-Artifacts-9a16cb6.tar.gz`, or provide an accessible release containing them. If the submission system prefers PDF supplements, render the diagnostic supplement separately. This is a delivery requirement, not a request to rerun experiments or claim full retraining reproducibility.

### 4. Small copyediting and layout improvements

- Abstract and conclusion: change “is not statistically significant, does not extend to ...” to “is not statistically significant and does not extend to ...”.
- Define “full B” in the abstract or call it “the full LLM feature bundle”; arm labels are introduced later.
- The long test names on p. 5 break mid-identifier. Place them in a small list or move their full names to the supplement.
- Consider emphasizing the actual B–A estimate and its interval rather than repeatedly emphasizing “40% of the observed gap.” The ratio is descriptive, not a calibrated measure of captured knowledge.
- The PDF is readable and I observed no clipped tables or overlapping text. Tables 6–8 are separated from some of their discussion by floats, but this is a minor presentation issue.

## Verification performed

- **73 tests passed.**
- **All 63 saved runs passed the artifact verifier**, including local source-label alignment and the archived execution-source fingerprint.
- Compared maintained source with the original execution snapshot. The training, feature construction, and model computation are unchanged; the relevant behavioral changes are analyzer failure handling and run-directory/provenance management.
- Extracted the portable archive into a temporary directory and ran both documented verification commands using the existing Python environment, with no processed dataset or analyzer cache in that directory. Both succeeded; the verifier correctly reported source-label alignment as unavailable there.
- Recomputed archive diagnostics match the submitted diagnostic JSON exactly. In particular, excluding the inconsistent test target gives mean F1@13 A/B/C of **24.28/27.39/32.07%** after rounding, as reported.
- The archive's 187 regular files match their corresponding workspace files byte-for-byte.
- Read the complete updated PDF and visually inspected all ten pages.

I did not perform clean-environment dependency installation, remote-release access verification, live Gemini extraction, or retrain the 63 fits. The archive test establishes saved-score verification portability within the available environment, not end-to-end reproducibility on a new machine.

## Final recommendation

Make the small wording changes above and submit the PDF with its supplement and archive. The project can now be presented credibly as a careful exploratory study with a corrected implementation, explicit negative results, and auditable artifacts. A stronger backbone, another baseline, or more seeds would be future research, not prerequisites for addressing this review.
