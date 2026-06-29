"""
config.py — single source of truth for paths, constants, the 55-concept space,
the error-type taxonomy, and reproducibility seeds.

Everything that another module needs to agree on lives here so the pipeline has
exactly one definition of "the 55 concepts", "the 6 error types", etc.

Design note: we keep this file *data-driven and explicit* (plain lists/dicts)
rather than clever. A human reading it should be able to see the whole label
space at a glance.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]          # process-aware-kt/
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
LLM_FEATURES = DATA / "llm_features"                 # one cached JSON per analyzer call
RESULTS = ROOT / "results"

MATHEDU_DIR = RAW / "MathEDU"
CONCEPTKT_DIR = RAW / "ConceptKT"

# Canonical inputs (verified present after cloning, see data_prep.py):
CONCEPTKT_FULL = CONCEPTKT_DIR / "ConceptKT.json"            # 4048 records, chronological file order
CONCEPTKT_TRAIN = CONCEPTKT_DIR / "ConceptKT" / "train.json"  # official split (3644)
CONCEPTKT_TEST = CONCEPTKT_DIR / "ConceptKT" / "test.json"    # official split (404)
MATHEDU_SPLITS = MATHEDU_DIR / "dataset" / "time_series_split"  # train/val/test.json (process + teacher_review)

PROCESSED_TABLE = PROCESSED / "interactions.json"    # tidy joined table produced by data_prep.py

for _d in (PROCESSED, LLM_FEATURES, RESULTS):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Environment / Gemini
# ---------------------------------------------------------------------------
load_dotenv(ROOT / ".env")                           # populates os.environ from .env

# Model name is read from the environment, never hardcoded, so swapping models
# (e.g. gemini-2.5-flash-lite -> gemini-3.1-flash-lite) needs no code change.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")


def have_gemini_key() -> bool:
    """True iff a non-empty GEMINI_API_KEY is available (genai.Client() reads it)."""
    return bool(os.environ.get("GEMINI_API_KEY", "").strip())


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEEDS = [0, 1, 2, 3, 4]          # 5 seeds; report mean +/- std over these


def set_seed(seed: int) -> None:
    """Seed python, numpy and torch (CPU + CUDA) for reproducible runs."""
    import random

    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    except ImportError:          # torch optional for the non-training scripts
        pass


# ---------------------------------------------------------------------------
# The 55 concepts, grouped into 13 categories (brief Section 8).
# These exact strings match ConceptKT.json verbatim, so multi-hot encoding and
# the LLM analyzer can compare by exact string. Index in CONCEPTS == concept ID.
# ---------------------------------------------------------------------------
CONCEPTS_BY_CATEGORY: dict[str, list[str]] = {
    "Basic Arithmetic": [
        "Basic Math Operations", "Expression and Operations with Symbols",
        "Unit Conversion", "Range of Values", "Modular Arithmetic", "Factorial",
    ],
    "Prime Numbers": [
        "Prime", "Composite Number", "Prime Factorization",
    ],
    "Factors and Multiples": [
        "Number of Factors", "Greatest Common Divisor", "Least Common Multiple",
    ],
    "Physics": [
        "Distance-Time-Speed", "Relative Speed", "Workload-Time-Speed",
        "Mixed Solution Concentration",
    ],
    "Ratio and Proportion": [
        "Direct Proportion and Inverse Proportion", "Ratio Calculation",
    ],
    "Finance": [
        "Simple Interest", "Compound Interest", "Effective Annual Interest Rate",
        "Profit", "Loss", "Discount Problem", "Price Calculation",
    ],
    "Statistics and Probability": [
        "Arithmetic Mean", "Mode", "Median", "Standard Deviation",
        "Normal Distribution", "Probability",
    ],
    "Polynomials": [
        "Square of the Sum", "Difference of Squares", "Sum of Squares",
        "Factorization of Polynomials", "Function", "Roots and Coefficients",
        "Quadratic Equation", "Absolute Value Equation",
    ],
    "Sequences and Series": [
        "Arithmetic Sequence/Series", "Geometric Sequence/Series",
    ],
    "Geometry": [
        "Perimeter Calculation", "Area Calculation", "Volume Calculation",
        "Graphs of Cartesian Coordinates and Linear Equations",
        "Pythagorean Theorem", "Solid Geometry", "Plane Geometry",
    ],
    "Set Theory": [
        "Inclusion-Exclusion Principle", "Fundamental Counting Principles",
    ],
    "Permutations and Combinations": [
        "Permutations and Combinations", "Pigeonhole Principle",
    ],
    "Other": [
        "Exact Value", "Local Value", "Face Value",
    ],
}

# Flat ordered concept list: index 0..54 == concept ID.
CONCEPTS: list[str] = [c for concepts in CONCEPTS_BY_CATEGORY.values() for c in concepts]
CONCEPT_TO_ID: dict[str, int] = {c: i for i, c in enumerate(CONCEPTS)}
NUM_CONCEPTS = len(CONCEPTS)                          # 55

# concept -> category, and an ordered category list (index == category ID 0..12)
CONCEPT_TO_CATEGORY: dict[str, str] = {
    c: cat for cat, concepts in CONCEPTS_BY_CATEGORY.items() for c in concepts
}
CATEGORIES: list[str] = list(CONCEPTS_BY_CATEGORY.keys())
CATEGORY_TO_ID: dict[str, int] = {cat: i for i, cat in enumerate(CATEGORIES)}
NUM_CATEGORIES = len(CATEGORIES)                      # 13

assert NUM_CONCEPTS == 55, f"expected 55 concepts, got {NUM_CONCEPTS}"
assert NUM_CATEGORIES == 13, f"expected 13 categories, got {NUM_CATEGORIES}"

# ---------------------------------------------------------------------------
# Error types.
# The brief defines a normalized 6-way enum. MathEDU's raw teacher_review uses 8
# human-readable strings (counts from the data shown in comments). We map the 8
# raw strings onto the 6 normalized types. A couple are judgment calls, flagged.
# ---------------------------------------------------------------------------
# Normalized enum (order == error-type ID; "none" last so id 5 == correct/no-error).
ERROR_TYPES: list[str] = [
    "wrong_operation_or_concept",  # 0  conceptual
    "lack_of_concepts",            # 1  conceptual
    "calculation_error",           # 2  careless
    "incomplete_answer",           # 3  careless
    "careless_error",              # 4  careless
    "none",                        # 5  correct answer / no error
]
ERROR_TYPE_TO_ID: dict[str, int] = {e: i for i, e in enumerate(ERROR_TYPES)}
NUM_ERROR_TYPES = len(ERROR_TYPES)                   # 6

# Conceptual-deficiency group vs careless group (brief Section 8). Missing-concept
# prediction is only *meaningful* for the conceptual group; we still report both.
CONCEPTUAL_ERRORS = {"wrong_operation_or_concept", "lack_of_concepts"}
CARELESS_ERRORS = {"calculation_error", "incomplete_answer", "careless_error"}

# Raw MathEDU error_type string  ->  normalized enum value.
# Raw counts observed in the data (for transparency):
#   458  Wrong mathematical operation/concept     -> wrong_operation_or_concept
#   186  Comprehension error                      -> wrong_operation_or_concept  (judgment call: misreading ~ wrong concept application)
#   124  Unfinished answer                        -> incomplete_answer
#    95  Lack of necessary mathematical concepts  -> lack_of_concepts
#    78  Arithmetical error                       -> calculation_error
#    43  Algebraic error                          -> calculation_error
#    30  Careless error                           -> careless_error
#    13  Measurement error                        -> calculation_error
MATHEDU_ERROR_TYPE_MAP: dict[str, str] = {
    "Wrong mathematical operation/concept": "wrong_operation_or_concept",
    "Comprehension error": "wrong_operation_or_concept",      # judgment call — see FINDINGS.md
    "Lack of necessary mathematical concepts": "lack_of_concepts",
    "Unfinished answer": "incomplete_answer",
    "Arithmetical error": "calculation_error",
    "Algebraic error": "calculation_error",
    "Careless error": "careless_error",
    "Measurement error": "calculation_error",
}


def normalize_error_type(raw: str | None) -> str:
    """Map a raw MathEDU error_type string to the normalized enum ('none' if unknown/empty)."""
    if not raw:
        return "none"
    return MATHEDU_ERROR_TYPE_MAP.get(raw.strip(), "none")


# ---------------------------------------------------------------------------
# Sentence-transformer used to embed the analyzer's process_summary (frozen).
# Small + widely available; swap freely (E5, etc.).
# ---------------------------------------------------------------------------
SUMMARY_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SUMMARY_EMBED_DIM = 384          # all-MiniLM-L6-v2 output dim

# ---------------------------------------------------------------------------
# Model / training hyper-parameters (kept small: dataset is tiny, 6 students).
# ---------------------------------------------------------------------------
HIDDEN_SIZE = 64
DROPOUT = 0.4
LEARNING_RATE = 1e-3
MAX_EPOCHS = 60
EARLY_STOP_PATIENCE = 8
VAL_TAIL_FRAC = 0.10             # last 10% of each student's *train* history -> val (early stopping)
FOCAL_GAMMA = 2.0               # focal loss focusing parameter for the imbalanced deficiency head
