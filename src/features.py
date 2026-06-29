"""
features.py — turn each interaction's analyzer JSON + gold labels into the
numeric components the model consumes (brief Section 9).

We build ONE feature store (a dict keyed by (id, student_id)) holding, per
interaction, every component any arm might need. The model/dataset then selects
which components to concatenate per arm:

  component            shape   used by            source
  -------------------- ------- ------------------ ----------------------------
  assoc_multihot       [55]    A, B, C (+ mask)   gold associated_concepts
  correct              [1]     A, B, C            grading
  llm_missing_multihot [55]    B                  analyzer.missing_concepts
  llm_error_type_id    int     B                  analyzer.error_type
  summary_embed        [384]   B                  frozen ST(analyzer.summary)
  gold_missing_multihot[55]    C (+ TARGET)       gold missing_concepts
  gold_error_type_id   int     C                  gold (normalized) error_type

Targets for predicting the NEXT interaction:
  * correctness target  = next.correct
  * deficiency target   = next.gold_missing_multihot, MASKED to next.assoc_multihot

Note: associated concepts are a known property of the question (available at
prediction time), so using them as input/mask is NOT leakage. gold missing
concepts are the TARGET; they are only ever used as INPUT for the arm-C
upper-bound, and only for PAST steps (enforced in dataset.py).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src import config as C
from src import llm_analyzer


def multihot(concepts: list[str]) -> np.ndarray:
    v = np.zeros(C.NUM_CONCEPTS, dtype=np.float32)
    for c in concepts:
        i = C.CONCEPT_TO_ID.get(c)
        if i is not None:
            v[i] = 1.0
    return v


@dataclass
class StepFeatures:
    id: int
    student_id: int
    seq_pos: int
    split: str
    correct: float
    assoc_multihot: np.ndarray          # [55]
    llm_missing_multihot: np.ndarray    # [55]
    llm_error_type_id: int
    summary_embed: np.ndarray           # [SUMMARY_EMBED_DIM]
    gold_missing_multihot: np.ndarray   # [55]  (target source; arm-C input)
    gold_error_type_id: int


class SummaryEmbedder:
    """Frozen sentence-transformer for process_summary, loaded lazily once."""

    def __init__(self, model_name: str = C.SUMMARY_EMBED_MODEL):
        self.model_name = model_name
        self._model = None

    def _ensure(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._ensure()
        # empty strings -> zero vectors (handled by replacing with a single space)
        clean = [t if t.strip() else " " for t in texts]
        emb = model.encode(clean, batch_size=64, show_progress_bar=False,
                           convert_to_numpy=True, normalize_embeddings=True)
        return emb.astype(np.float32)


def build_feature_store(table: list[dict], embedder: SummaryEmbedder | None = None
                        ) -> dict[tuple[int, int], StepFeatures]:
    """Build the per-interaction feature store for the whole table.

    Reads analyzer outputs through llm_analyzer.analyze() (disk cache in real
    mode, synthetic in KT_MOCK_ANALYZER mode), so no API calls happen here when
    the cache is warm.
    """
    embedder = embedder or SummaryEmbedder()

    analyses = [llm_analyzer.analyze(rec) for rec in table]
    summaries = [a.process_summary for a in analyses]
    summary_embeds = embedder.encode(summaries)            # [N, 384]

    store: dict[tuple[int, int], StepFeatures] = {}
    for rec, a, emb in zip(table, analyses, summary_embeds):
        store[(rec["id"], rec["student_id"])] = StepFeatures(
            id=rec["id"],
            student_id=rec["student_id"],
            seq_pos=rec["seq_pos"],
            split=rec["split"],
            correct=1.0 if rec["correct"] else 0.0,
            assoc_multihot=multihot(rec["associated_concepts"]),
            llm_missing_multihot=multihot(a.missing_concepts),
            llm_error_type_id=C.ERROR_TYPE_TO_ID.get(a.error_type, C.ERROR_TYPE_TO_ID["none"]),
            summary_embed=emb,
            gold_missing_multihot=multihot(rec["missing_concepts"]),
            gold_error_type_id=C.ERROR_TYPE_TO_ID.get(rec["error_type"], C.ERROR_TYPE_TO_ID["none"]),
        )
    return store


# Per-arm input layout: which components feed the LSTM at each step.
# The error-type embedding is LEARNED in the model, so here we emit the dense
# part of the vector plus a separate integer error-type id; model.py looks the
# id up in an nn.Embedding and concatenates. (Mask always uses the TARGET step's
# assoc_multihot.)
ARMS = ("A", "B", "C")
USES_ERROR_EMBED = {"A": False, "B": True, "C": True}


def step_dense_vector(sf: StepFeatures, arm: str) -> np.ndarray:
    """Dense (non-embedded) part of the per-step input for an arm."""
    correct = np.array([sf.correct], dtype=np.float32)
    if arm == "A":                       # correctness-only DKT baseline
        return np.concatenate([sf.assoc_multihot, correct])
    if arm == "B":                       # LLM process-aware
        return np.concatenate([sf.assoc_multihot, correct,
                               sf.llm_missing_multihot, sf.summary_embed])
    if arm == "C":                       # gold-feature upper bound (no LLM summary)
        zero_summary = np.zeros(C.SUMMARY_EMBED_DIM, dtype=np.float32)
        return np.concatenate([sf.assoc_multihot, correct,
                               sf.gold_missing_multihot, zero_summary])
    raise ValueError(f"unknown arm {arm!r}")


def step_error_id(sf: StepFeatures, arm: str) -> int:
    """Error-type id fed to the model's learned embedding (B uses LLM, C gold)."""
    if arm == "B":
        return sf.llm_error_type_id
    if arm == "C":
        return sf.gold_error_type_id
    return C.ERROR_TYPE_TO_ID["none"]     # arm A: unused (no error embed)


def dense_dim(arm: str) -> int:
    """Width of step_dense_vector for an arm."""
    base = C.NUM_CONCEPTS + 1                       # assoc + correctness
    if arm == "A":
        return base
    return base + C.NUM_CONCEPTS + C.SUMMARY_EMBED_DIM   # + missing(55) + summary(384)
