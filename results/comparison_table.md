# Corrected advisor revision results

These replace the draft results after fixing duplicate occurrence keys. Historical runs are in `results/historical/`.

| Arm | F1@13 (%) | SD (pp) | 95% seed-mean CI (%) |
|---|---:|---:|---|
| A | 24.28 | 3.92 | [18.84, 29.71] |
| B | 27.39 | 5.03 | [20.41, 34.36] |
| C | 32.06 | 1.94 | [29.38, 34.75] |
| B_M | 23.29 | 1.65 | [21.00, 25.59] |
| B_E | 32.00 | 1.73 | [29.60, 34.40] |
| B_S | 23.61 | 1.18 | [21.98, 25.24] |
| B_ME | 29.98 | 3.46 | [25.17, 34.78] |
| B_MS | 22.97 | 1.21 | [21.29, 24.64] |
| B_ES | 25.56 | 2.87 | [21.57, 29.55] |

B−A: +3.11 pp; paired t p=0.494, exact sign-flip p=0.5625. C−B: +4.68 pp; paired t p=0.185, exact p=0.2500. Neither contrast is significant. These intervals cover seed variability, not student population uncertainty.

Error-type-only is the strongest exploratory analyzer subset (32.00%); removing summary from full B yields 29.98%. Pooled LOSO at seed 0: A 25.70%, B 24.43%, C 31.08%.

See `revisions/summary.json`, all 63 saved run JSON/NPZ pairs, the report, and `ADVISOR_REVISIONS_PLAN.md` for complete evidence.
