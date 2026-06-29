"""Model forward shapes, deficiency masking, and losses — untested in both
original projects. The masking and last-timestep alignment are the riskiest
numeric code in the modeling path.
"""

from __future__ import annotations

import torch

from src import config as C
from src import features as F
from src import model as Model


def _inputs(arm: str, T: int = 4):
    dense = torch.randn(T, F.dense_dim(arm))
    err_id = torch.zeros(T, dtype=torch.long)
    next_assoc = torch.zeros(T - 1, C.NUM_CONCEPTS)
    next_assoc[1, 0] = 1.0              # only concept 0 associated for target row 1
    next_assoc[2, 3] = 1.0
    return dense, err_id, next_assoc


def test_input_size_includes_error_embed_only_for_b_and_c():
    assert Model.ProcessAwareDKT("A").lstm.input_size == F.dense_dim("A")
    assert Model.ProcessAwareDKT("A").uses_error is False
    for arm in ("B", "C"):
        net = Model.ProcessAwareDKT(arm)
        assert net.uses_error is True
        assert net.lstm.input_size == F.dense_dim(arm) + Model.ERROR_EMBED_DIM


def test_forward_shapes_predict_next_interaction():
    for arm in ("A", "B", "C"):
        net = Model.ProcessAwareDKT(arm)
        dense, err_id, next_assoc = _inputs(arm)
        cl, dl = net(dense, err_id, next_assoc)
        assert cl.shape == (3,)                       # T-1 correctness logits
        assert dl.shape == (3, C.NUM_CONCEPTS)        # T-1 x 55 deficiency logits


def test_deficiency_logits_masked_to_associated_concepts():
    net = Model.ProcessAwareDKT("A")
    dense, err_id, next_assoc = _inputs("A")
    _, dl = net(dense, err_id, next_assoc)
    # row 0 has no associated concept -> every logit masked to NEG_INF
    assert torch.all(dl[0] == Model.NEG_INF)
    # row 1 has concept 0 associated -> that logit is finite, the rest masked
    assert dl[1, 0] > Model.NEG_INF / 2
    assert torch.all(dl[1, 1:] == Model.NEG_INF)


def test_correctness_loss_is_a_nonnegative_scalar():
    logits = torch.tensor([0.5, -0.5, 2.0])
    target = torch.tensor([1.0, 0.0, 1.0])
    loss = Model.correctness_loss(logits, target)
    assert loss.ndim == 0 and loss.item() >= 0.0


def test_focal_loss_is_zero_when_nothing_is_associated():
    logits = torch.randn(3, C.NUM_CONCEPTS)
    target = torch.zeros(3, C.NUM_CONCEPTS)
    assoc = torch.zeros(3, C.NUM_CONCEPTS)            # no valid entries
    loss = Model.focal_deficiency_loss(logits, target, assoc)
    assert loss.item() == 0.0


def test_focal_loss_positive_and_differentiable_when_wrong():
    logits = torch.full((1, C.NUM_CONCEPTS), -5.0, requires_grad=True)
    target = torch.zeros(1, C.NUM_CONCEPTS)
    target[0, 0] = 1.0                                # positive the model misses
    assoc = torch.zeros(1, C.NUM_CONCEPTS)
    assoc[0, 0] = 1.0
    loss = Model.focal_deficiency_loss(logits, target, assoc)
    assert loss.item() > 0.0
    loss.backward()
    assert logits.grad is not None and torch.any(logits.grad != 0)


def test_full_training_step_flows_gradients():
    net = Model.ProcessAwareDKT("B")
    dense, err_id, next_assoc = _inputs("B")
    next_correct = torch.tensor([1.0, 0.0, 1.0])
    next_missing = torch.zeros(3, C.NUM_CONCEPTS)
    next_missing[1, 0] = 1.0
    cl, dl = net(dense, err_id, next_assoc)
    loss = Model.correctness_loss(cl, next_correct) + \
        Model.focal_deficiency_loss(dl, next_missing, next_assoc)
    loss.backward()
    grads = [p.grad for p in net.parameters() if p.grad is not None]
    assert grads and any(torch.any(g != 0) for g in grads)
