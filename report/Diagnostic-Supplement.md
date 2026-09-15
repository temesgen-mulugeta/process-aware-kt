# Diagnostic supplement

Companion to the 10-page main report. These are existing saved diagnostics plus the explicitly identified post-review controls. No new LLM calls or model fits were used.

## Analyzer error and concept diagnostics

Error accuracy: 50.5747%; majority comparator: 54/87 = 62.1%. Six-class macro-F1 includes the zero-support none class.

| Error class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| wrong_operation_or_concept | 54 | 0.6949 | 0.7593 | 0.7257 |
| lack_of_concepts | 11 | 0.0000 | 0.0000 | 0.0000 |
| calculation_error | 8 | 0.1765 | 0.3750 | 0.2400 |
| incomplete_answer | 13 | 0.0000 | 0.0000 | 0.0000 |
| careless_error | 1 | 0.0000 | 0.0000 | 0.0000 |
| none | 0 | 0.0000 | 0.0000 | 0.0000 |

Concept precision/recall below are conditional on 45 gold-positive validation records. They do not measure false positives on gold-negative answers.

| Concept | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Basic Math Operations | 5 | 0.0000 | 0.0000 | 0.0000 |
| Expression and Operations with Symbols | 4 | 0.0000 | 0.0000 | 0.0000 |
| Unit Conversion | 2 | 0.0000 | 0.0000 | 0.0000 |
| Range of Values | 0 | 0.0000 | 0.0000 | 0.0000 |
| Modular Arithmetic | 0 | 0.0000 | 0.0000 | 0.0000 |
| Factorial | 0 | 0.0000 | 0.0000 | 0.0000 |
| Prime | 0 | 0.0000 | 0.0000 | 0.0000 |
| Composite Number | 0 | 0.0000 | 0.0000 | 0.0000 |
| Prime Factorization | 0 | 0.0000 | 0.0000 | 0.0000 |
| Number of Factors | 1 | 0.0000 | 0.0000 | 0.0000 |
| Greatest Common Divisor | 0 | 0.0000 | 0.0000 | 0.0000 |
| Least Common Multiple | 0 | 0.0000 | 0.0000 | 0.0000 |
| Distance-Time-Speed | 7 | 1.0000 | 0.4286 | 0.6000 |
| Relative Speed | 0 | 0.0000 | 0.0000 | 0.0000 |
| Workload-Time-Speed | 1 | 0.0000 | 0.0000 | 0.0000 |
| Mixed Solution Concentration | 2 | 1.0000 | 0.5000 | 0.6667 |
| Direct Proportion and Inverse Proportion | 0 | 0.0000 | 0.0000 | 0.0000 |
| Ratio Calculation | 2 | 1.0000 | 0.5000 | 0.6667 |
| Simple Interest | 0 | 0.0000 | 0.0000 | 0.0000 |
| Compound Interest | 1 | 0.0000 | 0.0000 | 0.0000 |
| Effective Annual Interest Rate | 0 | 0.0000 | 0.0000 | 0.0000 |
| Profit | 4 | 0.5000 | 0.2500 | 0.3333 |
| Loss | 1 | 0.0000 | 0.0000 | 0.0000 |
| Discount Problem | 0 | 0.0000 | 0.0000 | 0.0000 |
| Price Calculation | 0 | 0.0000 | 0.0000 | 0.0000 |
| Arithmetic Mean | 2 | 0.0000 | 0.0000 | 0.0000 |
| Mode | 0 | 0.0000 | 0.0000 | 0.0000 |
| Median | 0 | 0.0000 | 0.0000 | 0.0000 |
| Standard Deviation | 0 | 0.0000 | 0.0000 | 0.0000 |
| Normal Distribution | 0 | 0.0000 | 0.0000 | 0.0000 |
| Probability | 1 | 1.0000 | 1.0000 | 1.0000 |
| Square of the Sum | 0 | 0.0000 | 0.0000 | 0.0000 |
| Difference of Squares | 0 | 0.0000 | 0.0000 | 0.0000 |
| Sum of Squares | 0 | 0.0000 | 0.0000 | 0.0000 |
| Factorization of Polynomials | 0 | 0.0000 | 0.0000 | 0.0000 |
| Function | 0 | 0.0000 | 0.0000 | 0.0000 |
| Roots and Coefficients | 0 | 0.0000 | 0.0000 | 0.0000 |
| Quadratic Equation | 1 | 0.0000 | 0.0000 | 0.0000 |
| Absolute Value Equation | 0 | 0.0000 | 0.0000 | 0.0000 |
| Arithmetic Sequence/Series | 0 | 0.0000 | 0.0000 | 0.0000 |
| Geometric Sequence/Series | 1 | 0.0000 | 0.0000 | 0.0000 |
| Perimeter Calculation | 1 | 0.0000 | 0.0000 | 0.0000 |
| Area Calculation | 2 | 0.0000 | 0.0000 | 0.0000 |
| Volume Calculation | 1 | 1.0000 | 1.0000 | 1.0000 |
| Graphs of Cartesian Coordinates and Linear Equations | 2 | 1.0000 | 0.5000 | 0.6667 |
| Pythagorean Theorem | 0 | 0.0000 | 0.0000 | 0.0000 |
| Solid Geometry | 0 | 0.0000 | 0.0000 | 0.0000 |
| Plane Geometry | 1 | 0.0000 | 0.0000 | 0.0000 |
| Inclusion-Exclusion Principle | 3 | 0.0000 | 0.0000 | 0.0000 |
| Fundamental Counting Principles | 0 | 0.0000 | 0.0000 | 0.0000 |
| Permutations and Combinations | 3 | 1.0000 | 0.3333 | 0.5000 |
| Pigeonhole Principle | 0 | 0.0000 | 0.0000 | 0.0000 |
| Exact Value | 0 | 0.0000 | 0.0000 | 0.0000 |
| Local Value | 0 | 0.0000 | 0.0000 | 0.0000 |
| Face Value | 1 | 0.0000 | 0.0000 | 0.0000 |

## All-category error counts

Counts are means across five seeds. Each row totals 404 test targets.

| Category | Arm | Positives | TP | FP | FN | TN |
|---|---|---:|---:|---:|---:|---:|
| Basic Arithmetic | A | 9.0 | 0.0 | 4.0 | 9.0 | 391.0 |
| Basic Arithmetic | B | 9.0 | 0.0 | 4.0 | 9.0 | 391.0 |
| Basic Arithmetic | C | 9.0 | 0.2 | 5.8 | 8.8 | 389.2 |
| Prime Numbers | A | 2.0 | 1.4 | 3.6 | 0.6 | 398.4 |
| Prime Numbers | B | 2.0 | 1.4 | 4.2 | 0.6 | 397.8 |
| Prime Numbers | C | 2.0 | 1.6 | 4.2 | 0.4 | 397.8 |
| Factors and Multiples | A | 0.0 | 0.0 | 2.0 | 0.0 | 402.0 |
| Factors and Multiples | B | 0.0 | 0.0 | 2.0 | 0.0 | 402.0 |
| Factors and Multiples | C | 0.0 | 0.0 | 2.0 | 0.0 | 402.0 |
| Physics | A | 6.0 | 1.2 | 0.8 | 4.8 | 397.2 |
| Physics | B | 6.0 | 1.0 | 0.2 | 5.0 | 397.8 |
| Physics | C | 6.0 | 2.4 | 3.4 | 3.6 | 394.6 |
| Ratio and Proportion | A | 7.0 | 0.0 | 0.0 | 7.0 | 397.0 |
| Ratio and Proportion | B | 7.0 | 0.0 | 0.0 | 7.0 | 397.0 |
| Ratio and Proportion | C | 7.0 | 0.4 | 0.6 | 6.6 | 396.4 |
| Finance | A | 8.0 | 7.8 | 19.2 | 0.2 | 376.8 |
| Finance | B | 8.0 | 7.8 | 19.8 | 0.2 | 376.2 |
| Finance | C | 8.0 | 8.0 | 21.4 | 0.0 | 374.6 |
| Statistics and Probability | A | 8.0 | 0.0 | 0.0 | 8.0 | 396.0 |
| Statistics and Probability | B | 8.0 | 0.2 | 0.0 | 7.8 | 396.0 |
| Statistics and Probability | C | 8.0 | 2.0 | 2.6 | 6.0 | 393.4 |
| Polynomials | A | 1.0 | 1.0 | 2.4 | 0.0 | 400.6 |
| Polynomials | B | 1.0 | 1.0 | 2.4 | 0.0 | 400.6 |
| Polynomials | C | 1.0 | 1.0 | 2.8 | 0.0 | 400.2 |
| Sequences and Series | A | 2.0 | 0.4 | 1.4 | 1.6 | 400.6 |
| Sequences and Series | B | 2.0 | 1.2 | 1.0 | 0.8 | 401.0 |
| Sequences and Series | C | 2.0 | 1.8 | 2.2 | 0.2 | 399.8 |
| Geometry | A | 8.0 | 4.0 | 3.0 | 4.0 | 393.0 |
| Geometry | B | 8.0 | 4.0 | 3.0 | 4.0 | 393.0 |
| Geometry | C | 8.0 | 4.2 | 5.8 | 3.8 | 390.2 |
| Set Theory | A | 1.0 | 0.6 | 7.6 | 0.4 | 395.4 |
| Set Theory | B | 1.0 | 0.4 | 6.0 | 0.6 | 397.0 |
| Set Theory | C | 1.0 | 0.4 | 6.4 | 0.6 | 396.6 |
| Permutations and Combinations | A | 6.0 | 6.0 | 2.0 | 0.0 | 396.0 |
| Permutations and Combinations | B | 6.0 | 6.0 | 2.0 | 0.0 | 396.0 |
| Permutations and Combinations | C | 6.0 | 6.0 | 2.0 | 0.0 | 396.0 |
| Other | A | 0.0 | 0.0 | 0.0 | 0.0 | 404.0 |
| Other | B | 0.0 | 0.0 | 0.0 | 0.0 | 404.0 |
| Other | C | 0.0 | 0.0 | 0.0 | 0.0 | 404.0 |

## Thresholds

All thresholds were selected using validation, not test labels.

| Arm | Seed | Threshold | Epochs |
|---|---:|---:|---:|
| A | 0 | 0.35 | 17 |
| A | 1 | 0.35 | 23 |
| A | 2 | 0.35 | 29 |
| A | 3 | 0.35 | 17 |
| A | 4 | 0.35 | 24 |
| B | 0 | 0.35 | 16 |
| B | 1 | 0.35 | 22 |
| B | 2 | 0.35 | 21 |
| B | 3 | 0.35 | 21 |
| B | 4 | 0.35 | 27 |
| C | 0 | 0.30 | 17 |
| C | 1 | 0.35 | 58 |
| C | 2 | 0.35 | 42 |
| C | 3 | 0.35 | 25 |
| C | 4 | 0.35 | 27 |
| B_M | 0 | 0.35 | 29 |
| B_M | 1 | 0.35 | 23 |
| B_M | 2 | 0.35 | 24 |
| B_M | 3 | 0.35 | 21 |
| B_M | 4 | 0.35 | 32 |
| B_E | 0 | 0.35 | 29 |
| B_E | 1 | 0.35 | 41 |
| B_E | 2 | 0.35 | 15 |
| B_E | 3 | 0.35 | 46 |
| B_E | 4 | 0.35 | 14 |
| B_S | 0 | 0.35 | 23 |
| B_S | 1 | 0.35 | 22 |
| B_S | 2 | 0.35 | 18 |
| B_S | 3 | 0.35 | 23 |
| B_S | 4 | 0.35 | 16 |
| B_ME | 0 | 0.35 | 14 |
| B_ME | 1 | 0.35 | 23 |
| B_ME | 2 | 0.35 | 23 |
| B_ME | 3 | 0.35 | 23 |
| B_ME | 4 | 0.35 | 27 |
| B_MS | 0 | 0.35 | 21 |
| B_MS | 1 | 0.35 | 22 |
| B_MS | 2 | 0.35 | 29 |
| B_MS | 3 | 0.35 | 23 |
| B_MS | 4 | 0.35 | 23 |
| B_ES | 0 | 0.35 | 23 |
| B_ES | 1 | 0.35 | 22 |
| B_ES | 2 | 0.35 | 15 |
| B_ES | 3 | 0.35 | 16 |
| B_ES | 4 | 0.35 | 23 |

| Arm | Held student | Threshold |
|---|---:|---:|
| A | 1 | 0.35 |
| A | 2 | 0.35 |
| A | 3 | 0.35 |
| A | 4 | 0.10 |
| A | 5 | 0.30 |
| A | 6 | 0.25 |
| B | 1 | 0.40 |
| B | 2 | 0.35 |
| B | 3 | 0.30 |
| B | 4 | 0.10 |
| B | 5 | 0.35 |
| B | 6 | 0.25 |
| C | 1 | 0.35 |
| C | 2 | 0.35 |
| C | 3 | 0.25 |
| C | 4 | 0.35 |
| C | 5 | 0.30 |
| C | 6 | 0.25 |

## Full worked example

The JSON includes the original solution, analyzer output and derived feature indices. Identifiers are masked.

```json
{
  "student": "S*",
  "problem": "Q*",
  "solution": "\\begin{aligned} 9 & <a \\leq 21 \\\\ 19 & <b<31 \\\\ \\frac{21}{19} \\leq \\frac{a}{b} & <\\frac{31}{9} \\end{aligned}",
  "answer": "\\frac{21}{19} \\leq \\frac{a}{b} & <\\frac{31}{9}",
  "correct": false,
  "analyzer": {
    "associated_concepts": [
      "Range of Values"
    ],
    "missing_concepts": [
      "Range of Values"
    ],
    "error_type": "wrong_operation_or_concept",
    "faulty_step": "\\frac{21}{19} \\leq \\frac{a}{b} <\\frac{31}{9}",
    "partial_understanding": [
      "The student understands that the bounds of a quotient can be determined by the bounds of the numerator and denominator."
    ],
    "process_summary": "The student incorrectly combined the bounds of two variables to determine the range of their quotient, failing to account for the correct extreme values of the fraction."
  },
  "associated_indices": [
    3
  ],
  "llm_missing_indices": [
    3
  ],
  "error_id": 0,
  "summary_norm": 1.0
}
```

## Mask exceptions

Main metrics retain these original labels. Prediction masks are never widened using target missing labels.

```json
[
  {
    "student_id": 3,
    "seq_pos": 7,
    "role": "training",
    "outside_mask": [
      "Expression and Operations with Symbols"
    ]
  },
  {
    "student_id": 3,
    "seq_pos": 63,
    "role": "training",
    "outside_mask": [
      "Basic Math Operations"
    ]
  },
  {
    "student_id": 3,
    "seq_pos": 65,
    "role": "training",
    "outside_mask": [
      "Basic Math Operations"
    ]
  },
  {
    "student_id": 3,
    "seq_pos": 70,
    "role": "training",
    "outside_mask": [
      "Basic Math Operations"
    ]
  },
  {
    "student_id": 3,
    "seq_pos": 575,
    "role": "validation",
    "outside_mask": [
      "Basic Math Operations"
    ]
  },
  {
    "student_id": 5,
    "seq_pos": 634,
    "role": "test",
    "outside_mask": [
      "Basic Math Operations"
    ]
  }
]
```

## Post-review controls and sensitivity

See [diagnostics.json](../results/submission/diagnostics.json) for mask-only F1/P/R, the majority comparator, and scores after excluding the one inconsistent test target. This exclusion is a diagnostic on frozen predictions, not a corrected-label training experiment.

## Reproduction

See [ARTIFACTS.md](ARTIFACTS.md).
