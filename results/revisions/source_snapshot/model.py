"""
model.py — a small DKT-style LSTM with two prediction heads (brief Section 10).

One model class serves all three arms; the arm only changes the input layout:
  * Arm A (baseline)      : dense = [assoc multi-hot, correctness]
  * Arm B (process-aware) : + LLM missing multi-hot, summary embed, error embed
  * Arm C (gold upper bnd): + gold missing multi-hot, (zero summary), gold error embed

Heads, applied to the hidden state that predicts the NEXT interaction:
  * correctness head : Linear -> 1 logit  (BCE)
  * deficiency head  : Linear -> 55 logits, MASKED to the target question's
                       associated concepts (missing ⊂ associated), trained with
                       focal BCE to cope with heavy class imbalance.

Deliberately basic. TODO: for stronger backbones (AKT / SAKT / GKT / DKVMN)
swap this module for a pyKT model — see FINDINGS.md "How to extend this".
"""

from __future__ import annotations

import torch
import torch.nn as nn

from src import config as C
from src import features as F

ERROR_EMBED_DIM = 8
NEG_INF = -1e9                       # masked-out logits


class ProcessAwareDKT(nn.Module):
    def __init__(self, arm: str, hidden_size: int = C.HIDDEN_SIZE, dropout: float = C.DROPOUT):
        super().__init__()
        self.arm = arm
        self.uses_error = F.USES_ERROR_EMBED[arm]

        dense = F.dense_dim(arm)
        in_dim = dense + (ERROR_EMBED_DIM if self.uses_error else 0)

        # learned error-type embedding (only used by B/C)
        self.error_embed = nn.Embedding(C.NUM_ERROR_TYPES, ERROR_EMBED_DIM)

        self.lstm = nn.LSTM(in_dim, hidden_size, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.correct_head = nn.Linear(hidden_size, 1)
        self.deficiency_head = nn.Linear(hidden_size, C.NUM_CONCEPTS)

    def _assemble_input(self, dense: torch.Tensor, err_id: torch.Tensor) -> torch.Tensor:
        """[T, dense] (+ error embed) -> [T, in_dim]."""
        if self.uses_error:
            err = self.error_embed(err_id)                 # [T, ERROR_EMBED_DIM]
            return torch.cat([dense, err], dim=-1)
        return dense

    def forward(self, dense: torch.Tensor, err_id: torch.Tensor, next_assoc: torch.Tensor):
        """Run one student's sequence.

        Args:
          dense:      [T, dense_dim]
          err_id:     [T]
          next_assoc: [T-1, 55]  associated-concept mask of each target interaction
        Returns:
          correct_logits: [T-1]
          deficiency_logits: [T-1, 55]  (masked: non-associated -> NEG_INF)
        """
        x = self._assemble_input(dense, err_id).unsqueeze(0)   # [1, T, in_dim]
        out, _ = self.lstm(x)                                   # [1, T, H]
        out = self.dropout(out.squeeze(0))                      # [T, H]

        # hidden state after step i predicts interaction i+1 -> use steps 0..T-2
        h = out[:-1]                                            # [T-1, H]
        correct_logits = self.correct_head(h).squeeze(-1)       # [T-1]
        deficiency_logits = self.deficiency_head(h)             # [T-1, 55]
        # mask to associated concepts of the target question
        deficiency_logits = deficiency_logits.masked_fill(next_assoc < 0.5, NEG_INF)
        return correct_logits, deficiency_logits


# ---------------------------------------------------------------------------
# Losses
# ---------------------------------------------------------------------------
def correctness_loss(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    return nn.functional.binary_cross_entropy_with_logits(logits, target)


def focal_deficiency_loss(logits: torch.Tensor, target: torch.Tensor,
                          assoc_mask: torch.Tensor, gamma: float = C.FOCAL_GAMMA) -> torch.Tensor:
    """Masked focal BCE over the associated-concept entries only.

    Only positions where the concept is *associated* with the target question are
    valid candidates (missing ⊂ associated), so we average the focal loss over
    those entries. Focal loss down-weights easy negatives, which dominate here.
    """
    valid = assoc_mask > 0.5                                  # [T-1, 55] bool
    if valid.sum() == 0:
        return logits.sum() * 0.0                            # no-op, keep graph
    p = torch.sigmoid(logits)
    ce = nn.functional.binary_cross_entropy_with_logits(logits, target, reduction="none")
    p_t = target * p + (1 - target) * (1 - p)               # prob of the true class
    focal = (1 - p_t).clamp(min=1e-6) ** gamma * ce
    return focal[valid].mean()
