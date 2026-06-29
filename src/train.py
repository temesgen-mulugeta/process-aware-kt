"""
train.py — train + evaluate all arms over 5 seeds, log everything (brief Sec. 11).

One command runs the whole modeling stage:

    python -m src.train                 # arms A, B, C over 5 seeds
    python -m src.train --arms A B      # subset of arms
    python -m src.train --seeds 0 1     # subset of seeds

It writes:
    results/metrics.json                # raw per-seed + aggregated metrics
    results/train_log.txt               # full run log (not just stdout)
and then calls evaluate.py to render results/comparison_table.md.

Data flow recap:
    processed table -> feature store (analyzer cache / mock) -> per-arm
    leakage-safe sequences -> ProcessAwareDKT -> correctness + masked deficiency
    heads -> metrics.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

import numpy as np
import torch

from src import config as C
from src import dataset as D
from src import features as F
from src import metrics as M
from src import model as Model


# ---------------------------------------------------------------------------
# Logging helper (stdout + file)
# ---------------------------------------------------------------------------
class Logger:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8")

    def __call__(self, msg: str = ""):
        print(msg)
        self.f.write(msg + "\n")
        self.f.flush()

    def close(self):
        self.f.close()


# ---------------------------------------------------------------------------
# One sequence's loss / predictions for a target subset ("train"|"val"|"test")
# ---------------------------------------------------------------------------
def _kind_mask(seq: D.Sequence, kind: str) -> torch.Tensor:
    return torch.tensor([k == kind for k in seq.target_kind], dtype=torch.bool)


def _seq_loss(net: Model.ProcessAwareDKT, seq: D.Sequence, kind: str) -> torch.Tensor:
    mask = _kind_mask(seq, kind)
    if mask.sum() == 0:
        return torch.zeros((), requires_grad=True)
    cl, dl = net(seq.dense, seq.err_id, seq.next_assoc)
    loss_c = Model.correctness_loss(cl[mask], seq.next_correct[mask])
    loss_d = Model.focal_deficiency_loss(dl[mask], seq.next_missing[mask], seq.next_assoc[mask])
    return loss_c + loss_d


@torch.no_grad()
def _collect_probs(net: Model.ProcessAwareDKT, sequences: list[D.Sequence], kind: str):
    """Gather correctness probs + deficiency PROBS (not thresholded) for a kind."""
    net.eval()
    c_true, c_prob, d_true, d_prob = [], [], [], []
    for seq in sequences:
        mask = _kind_mask(seq, kind)
        if mask.sum() == 0:
            continue
        cl, dl = net(seq.dense, seq.err_id, seq.next_assoc)
        c_prob.append(torch.sigmoid(cl[mask]).cpu().numpy())
        c_true.append(seq.next_correct[mask].cpu().numpy())
        d_prob.append(torch.sigmoid(dl[mask]).cpu().numpy())   # non-associated -> ~0
        d_true.append(seq.next_missing[mask].cpu().numpy().astype(int))
    net.train()
    return (
        np.concatenate(c_true) if c_true else np.zeros(0),
        np.concatenate(c_prob) if c_prob else np.zeros(0),
        np.concatenate(d_true) if d_true else np.zeros((0, C.NUM_CONCEPTS)),
        np.concatenate(d_prob) if d_prob else np.zeros((0, C.NUM_CONCEPTS)),
    )


# Decision-threshold grid for the imbalanced multi-label deficiency head.
_THRESH_GRID = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]


def _tune_threshold(d_true: np.ndarray, d_prob: np.ndarray) -> float:
    """Pick the threshold maximizing macro-F1 on the VAL set (never test).

    Falls back to 0.5 when val has no positive labels to tune on.
    """
    if d_true.size == 0 or d_true.sum() == 0:
        return 0.5
    best_t, best_f1 = 0.5, -1.0
    for t in _THRESH_GRID:
        dm = M.deficiency_metrics(d_true, (d_prob >= t).astype(int))
        f1 = dm["category13"]["macro_f1"]
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t


# ---------------------------------------------------------------------------
# Train one (arm, seed)
# ---------------------------------------------------------------------------
def train_one(sequences: list[D.Sequence], arm: str, seed: int, log: Logger) -> dict:
    C.set_seed(seed)
    net = Model.ProcessAwareDKT(arm)
    opt = torch.optim.Adam(net.parameters(), lr=C.LEARNING_RATE)

    best_val, best_state, patience = float("inf"), None, 0
    for epoch in range(C.MAX_EPOCHS):
        net.train()
        # shuffle student order each epoch for a little stochasticity
        order = list(range(len(sequences)))
        np.random.shuffle(order)
        for i in order:
            opt.zero_grad()
            loss = _seq_loss(net, sequences[i], "train")
            loss.backward()
            opt.step()

        # ---- early stopping on val loss ----
        net.eval()
        with torch.no_grad():
            val_loss = float(np.mean([_seq_loss(net, s, "val").item()
                                      for s in sequences if _kind_mask(s, "val").sum() > 0]))
        if val_loss < best_val - 1e-4:
            best_val, best_state, patience = val_loss, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            patience += 1
            if patience >= C.EARLY_STOP_PATIENCE:
                break

    if best_state is not None:
        net.load_state_dict(best_state)

    # ---- tune deficiency threshold on VAL, then evaluate on TEST ----
    _, _, dv_true, dv_prob = _collect_probs(net, sequences, "val")
    thresh = _tune_threshold(dv_true, dv_prob)

    c_true, c_prob, d_true, d_prob = _collect_probs(net, sequences, "test")
    cm = M.correctness_metrics(c_true, c_prob)
    dm = M.deficiency_metrics(d_true, (d_prob >= thresh).astype(int))

    flat = {
        "correct_acc": cm["acc"],
        "correct_auc": cm["auc"],
        "def_f1_55": dm["concept55"]["macro_f1"],
        "def_prec_55": dm["concept55"]["macro_precision"],
        "def_recall_55": dm["concept55"]["macro_recall"],
        "def_f1_13": dm["category13"]["macro_f1"],
        "def_prec_13": dm["category13"]["macro_precision"],
        "def_recall_13": dm["category13"]["macro_recall"],
    }
    log(f"  [arm {arm} seed {seed}] epochs={epoch+1} val_loss={best_val:.4f} thr={thresh:.2f} | "
        f"acc={flat['correct_acc']:.4f} auc={flat['correct_auc']:.4f} "
        f"F1@55={flat['def_f1_55']:.4f} F1@13={flat['def_f1_13']:.4f}")
    return {"flat": flat, "per_category_f1": dm["per_category_f1"],
            "n_test_targets": dm["n_targets"], "n_pos_labels": dm["n_positive_concept_labels"]}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=list(F.ARMS), choices=list(F.ARMS))
    ap.add_argument("--seeds", nargs="+", type=int, default=C.SEEDS)
    ap.add_argument("--no-eval", action="store_true", help="skip evaluate.py rendering")
    args = ap.parse_args()

    log = Logger(C.RESULTS / "train_log.txt")
    mock = os.environ.get("KT_MOCK_ANALYZER", "") == "1"
    log(f"\n===== run {datetime.now(timezone.utc).isoformat()} =====")
    log(f"model={C.GEMINI_MODEL} arms={args.arms} seeds={args.seeds} "
        f"analyzer={'MOCK (synthetic features!)' if mock else 'real (cached Gemini)'}")

    # processed table + feature store (built ONCE; reused across arms & seeds)
    with open(C.PROCESSED_TABLE, encoding="utf-8") as f:
        table = json.load(f)
    log("building feature store (summary embeddings)...")
    store = F.build_feature_store(table)

    results = {"meta": {"mock": mock, "model": C.GEMINI_MODEL,
                        "seeds": args.seeds, "arms": args.arms,
                        "timestamp": datetime.now(timezone.utc).isoformat()},
               "arms": {}}

    for arm in args.arms:
        sequences = D.build_sequences(table, store, arm)        # leakage assertion runs inside
        log(f"\n--- ARM {arm} (dense_dim={sequences[0].dense.shape[1]}) ---")
        per_seed_flat, per_seed_cat = [], []
        for seed in args.seeds:
            r = train_one(sequences, arm, seed, log)
            per_seed_flat.append(r["flat"])
            per_seed_cat.append(r["per_category_f1"])

        agg = M.aggregate(per_seed_flat)
        # mean per-category F1 across seeds (for error analysis)
        cat_mean = {cat: float(np.mean([c[cat] for c in per_seed_cat])) for cat in C.CATEGORIES}
        results["arms"][arm] = {
            "aggregate": agg, "per_seed": per_seed_flat,
            "per_category_f1_mean": cat_mean,
            "n_test_targets": r["n_test_targets"], "n_pos_labels": r["n_pos_labels"],
        }
        log(f"  ARM {arm} mean: acc={agg['correct_acc']['mean']:.4f}±{agg['correct_acc']['std']:.4f} "
            f"F1@55={agg['def_f1_55']['mean']:.4f}±{agg['def_f1_55']['std']:.4f} "
            f"F1@13={agg['def_f1_13']['mean']:.4f}±{agg['def_f1_13']['std']:.4f}")

    with open(C.RESULTS / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    log(f"\nwrote {C.RESULTS / 'metrics.json'}")
    log.close()

    if not args.no_eval:
        from src import evaluate
        evaluate.main()


if __name__ == "__main__":
    main()
