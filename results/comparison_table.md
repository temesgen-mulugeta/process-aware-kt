# Comparison table — process-aware KT prototype

- Analyzer model: `gemini-3.1-flash-lite` | seeds: [0, 1, 2, 3, 4] | split: official ConceptKT chronological 90/10 (3644/404).

## Our arms (mean ± std over seeds)

| arm | correctness acc | correctness AUC | deficiency F1@55 | F1@13 | precision@13 | recall@13 |
|---|---|---|---|---|---|---|
| A — correctness-only (DKT baseline) | 71.78% ± 0.00 | 0.59 ± 0.02 | 10.28% ± 1.32 | 24.04% ± 4.18 | 19.29% ± 3.02 | 39.49% ± 9.01 |
| B — process-aware (LLM features) | 71.78% ± 0.00 | 0.59 ± 0.00 | 12.24% ± 2.05 | 28.31% ± 4.73 | 25.16% ± 6.62 | 47.24% ± 10.08 |
| C — gold-feature upper bound | 71.78% ± 0.00 | 0.59 ± 0.01 | 13.36% ± 0.72 | 31.10% ± 1.46 | 28.78% ± 4.12 | 45.60% ± 8.08 |

## ConceptKT paper baselines (context only — different setup)

| method | correctness acc | deficiency macro-F1 |
|---|---|---|
| DKT | 64.80% | — |
| DKVMN | 63.10% | — |
| GKT | 63.20% | — |
| SAKT | 66.46% | — |
| OKT | 69.25% | 1.87% |
| Best LLM (DeepSeek-R1, ICL) | 71.02% | 17.40% |

> The paper's classic KT baselines predict correctness well but are near-useless at concept deficiency (OKT 1.87% macro-F1); only LLMs reach ~17% macro-F1. Concept-level deficiency prediction is the hard frontier.

## Error analysis — where the LLM process features (B) help vs the baseline (A)

Per-category deficiency F1 (mean over seeds), B minus A. Positive = process features helped that category.

| category | A F1@cat | B F1@cat | Δ (B−A) |
|---|---:|---:|---:|
| Sequences and Series | 0.114 | 0.460 | +0.346 |
| Physics | 0.114 | 0.237 | +0.123 |
| Statistics and Probability | 0.000 | 0.096 | +0.096 |
| Ratio and Proportion | 0.000 | 0.053 | +0.053 |
| Set Theory | 0.133 | 0.178 | +0.044 |
| Prime Numbers | 0.391 | 0.397 | +0.006 |
| Basic Arithmetic | 0.000 | 0.000 | +0.000 |
| Factors and Multiples | 0.000 | 0.000 | +0.000 |
| Permutations and Combinations | 0.857 | 0.857 | +0.000 |
| Other | 0.000 | 0.000 | +0.000 |
| Geometry | 0.533 | 0.515 | -0.019 |
| Finance | 0.481 | 0.454 | -0.027 |
| Polynomials | 0.500 | 0.433 | -0.067 |

- **Helped most:** Sequences and Series, Physics, Statistics and Probability
- Categories improved: 6 | unchanged: 4 | regressed: 3
- **Headroom to the gold ceiling (C):** F1@13 gap C−B = +2.79 pts — how much a perfect analyzer could still add over the current LLM features.
