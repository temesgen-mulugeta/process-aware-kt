# EDA Report — MathEDU / ConceptKT (process-aware KT prototype)

Generated from `data/processed/interactions.json`.

## Dataset overview

- Total interactions: **4048**, students: **6**
- Correct: **3050** (75.3%) | Wrong: **998** (24.7%)
- **Ordering field:** chronological order = position within ConceptKT.json (grouped by student). `id` is a MathQA problem id, NOT a timestamp.
- Per-student interaction counts:
    - student 1: 683
    - student 2: 685
    - student 3: 678
    - student 4: 660
    - student 5: 682
    - student 6: 660

## Deficiency labels (the prediction target)

- Records carrying gold `missing_concepts`: **463** (11.4% of all; all are wrong answers: 463 confirmed)
- These are the only records with a non-empty deficiency target — the task is **heavily imbalanced** and macro-F1 will be noisy.

## Class imbalance (coarse)

- correct: **3050** (75.3%)
- conceptual_deficiency: **722** (17.8%)
- careless_error: **276** (6.8%)
- wrong_unlabeled: **0** (0.0%)

> Missing-concept prediction is only meaningful for the **conceptual_deficiency** group; careless errors have no missing concept by design.

## Per-concept positive counts (55-concept view)

How often each concept appears as a **missing** concept (target positives). Concepts with very few positives are effectively unlearnable individually — this motivates also reporting the coarser 13-category level and using imbalance-aware loss.

| concept | category | missing+ | associated+ |
|---|---|---:|---:|
| Basic Math Operations | Basic Arithmetic | 32 | 333 |
| Expression and Operations with Symbols | Basic Arithmetic | 23 | 486 |
| Unit Conversion | Basic Arithmetic | 9 | 317 |
| Range of Values | Basic Arithmetic | 5 | 12 |
| Modular Arithmetic | Basic Arithmetic | 1 | 1 |
| Factorial | Basic Arithmetic | 1 | 6 |
| Prime | Prime Numbers | 4 | 26 |
| Composite Number | Prime Numbers | 1 | 2 |
| Prime Factorization | Prime Numbers | 8 | 38 |
| Number of Factors | Factors and Multiples | 3 | 7 |
| Greatest Common Divisor | Factors and Multiples | 7 | 28 |
| Least Common Multiple | Factors and Multiples | 10 | 32 |
| Distance-Time-Speed | Physics | 48 | 548 |
| Relative Speed | Physics | 8 | 189 |
| Workload-Time-Speed | Physics | 17 | 349 |
| Mixed Solution Concentration | Physics | 13 | 73 |
| Direct Proportion and Inverse Proportion | Ratio and Proportion | 0 | 58 |
| Ratio Calculation | Ratio and Proportion | 51 | 693 |
| Simple Interest | Finance | 15 | 126 |
| Compound Interest | Finance | 19 | 46 |
| Effective Annual Interest Rate | Finance | 2 | 2 |
| Profit | Finance | 48 | 194 |
| Loss | Finance | 11 | 64 |
| Discount Problem | Finance | 13 | 76 |
| Price Calculation | Finance | 7 | 10 |
| Arithmetic Mean | Statistics and Probability | 15 | 337 |
| Mode | Statistics and Probability | 0 | 1 |
| Median | Statistics and Probability | 1 | 8 |
| Standard Deviation | Statistics and Probability | 0 | 1 |
| Normal Distribution | Statistics and Probability | 0 | 3 |
| Probability | Statistics and Probability | 14 | 121 |
| Square of the Sum | Polynomials | 6 | 26 |
| Difference of Squares | Polynomials | 0 | 2 |
| Sum of Squares | Polynomials | 1 | 3 |
| Factorization of Polynomials | Polynomials | 0 | 6 |
| Function | Polynomials | 3 | 32 |
| Roots and Coefficients | Polynomials | 2 | 4 |
| Quadratic Equation | Polynomials | 1 | 1 |
| Absolute Value Equation | Polynomials | 1 | 4 |
| Arithmetic Sequence/Series | Sequences and Series | 7 | 64 |
| Geometric Sequence/Series | Sequences and Series | 5 | 14 |
| Perimeter Calculation | Geometry | 6 | 82 |
| Area Calculation | Geometry | 22 | 250 |
| Volume Calculation | Geometry | 8 | 80 |
| Graphs of Cartesian Coordinates and Linear Equations | Geometry | 7 | 31 |
| Pythagorean Theorem | Geometry | 1 | 16 |
| Solid Geometry | Geometry | 0 | 10 |
| Plane Geometry | Geometry | 13 | 36 |
| Inclusion-Exclusion Principle | Set Theory | 13 | 69 |
| Fundamental Counting Principles | Set Theory | 1 | 24 |
| Permutations and Combinations | Permutations and Combinations | 24 | 81 |
| Pigeonhole Principle | Permutations and Combinations | 3 | 6 |
| Exact Value | Other | 1 | 2 |
| Local Value | Other | 1 | 1 |
| Face Value | Other | 3 | 5 |

- **Concepts never missing (0 positives): 7** — Direct Proportion and Inverse Proportion, Mode, Standard Deviation, Normal Distribution, Difference of Squares, Factorization of Polynomials, Solid Geometry
- **Rare concepts (1–3 positives): 17** — Modular Arithmetic, Factorial, Composite Number, Number of Factors, Effective Annual Interest Rate, Median, Sum of Squares, Function, Roots and Coefficients, Quadratic Equation, Absolute Value Equation, Pythagorean Theorem, Fundamental Counting Principles, Pigeonhole Principle, Exact Value, Local Value, Face Value

## 13-category view of missing-concept positives

| category | missing+ |
|---|---:|
| Basic Arithmetic | 71 |
| Prime Numbers | 13 |
| Factors and Multiples | 20 |
| Physics | 86 |
| Ratio and Proportion | 51 |
| Finance | 115 |
| Statistics and Probability | 30 |
| Polynomials | 14 |
| Sequences and Series | 12 |
| Geometry | 57 |
| Set Theory | 14 |
| Permutations and Combinations | 27 |
| Other | 5 |

## Decision: evaluation granularity

We report deficiency metrics at **both** the 55-concept level (fine, sparse) and the 13-category level (coarse, less sparse), per the brief. The category level is the more stable signal given the tiny dataset and rare concepts above.
