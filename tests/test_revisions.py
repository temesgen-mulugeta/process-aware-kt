"""Regression checks for advisor revisions: causality, feature isolation, statistics."""
import numpy as np
import pytest
import torch

from src import config as C, dataset as D, features as F, llm_analyzer as L
from src import model, revision_analysis as R


class ZeroEmbedder:
    def encode(self, texts):
        return np.zeros((len(texts), C.SUMMARY_EMBED_DIM), dtype=np.float32)


def rows():
    return [dict(id=7, student_id=1, seq_pos=i, split='train' if i < 2 else 'test',
                 correct=False, associated_concepts=[C.CONCEPTS[i]],
                 missing_concepts=[C.CONCEPTS[i]], error_type='lack_of_concepts',
                 student_process='same process', student_answer='0') for i in range(3)]


def test_duplicate_problem_ids_preserve_occurrence_labels(monkeypatch):
    monkeypatch.setattr(L, 'MOCK', True)
    table = rows()
    store = F.build_feature_store(table, ZeroEmbedder())
    assert len(store) == 3
    seq = D.build_sequences(table, store, 'C')[0]
    assert np.flatnonzero(seq.dense[0, 56:111].numpy()).tolist() == [0]
    assert np.flatnonzero(seq.next_missing[0].numpy()).tolist() == [1]
    assert np.flatnonzero(seq.next_missing[1].numpy()).tolist() == [2]
    assert np.flatnonzero(seq.next_assoc[0].numpy()).tolist() == [1]


def test_feature_store_cache_miss_never_calls_api(monkeypatch):
    monkeypatch.setattr(L, 'MOCK', False)
    monkeypatch.setattr(L, 'use_cached', lambda r: False)
    def forbidden(*args, **kwargs):
        pytest.fail('Analyzer called despite missing cache')
    monkeypatch.setattr(L, 'analyze', forbidden)
    with pytest.raises(RuntimeError, match='Missing'):
        F.build_feature_store(rows(), ZeroEmbedder())


@pytest.mark.parametrize('arm', F.ALL_ARMS)
def test_target_and_future_features_cannot_change_current_prediction(arm):
    torch.manual_seed(1)
    net = model.ProcessAwareDKT(arm).eval()
    dense = torch.randn(5, F.dense_dim(arm))
    err = torch.zeros(5, dtype=torch.long)
    assoc = torch.ones(4, 55)
    before = net(dense, err, assoc)
    # Target at sequence position 2 is decoded from hidden state at position 1.
    dense[2:] = 100 * torch.randn_like(dense[2:])
    err[2:] = 4
    after = net(dense, err, assoc)
    for b, a in zip(before, after):
        torch.testing.assert_close(b[:2], a[:2], rtol=0, atol=0)


@pytest.mark.parametrize('arm', ['B_M', 'B_E', 'B_S', 'B_ME', 'B_MS', 'B_ES'])
def test_ablation_contains_only_selected_llm_signals(arm, monkeypatch):
    monkeypatch.setattr(L, 'MOCK', True)
    sf = F.build_feature_store(rows(), ZeroEmbedder())[(1, 0)]
    sf.llm_missing_multihot[:] = 2
    sf.summary_embed[:] = 3
    sf.llm_error_type_id = 4
    sf.gold_missing_multihot[:] = 9
    vector = F.step_dense_vector(sf, arm)
    expected = [sf.assoc_multihot, np.array([0.], dtype=np.float32)]
    if 'M' in F.SIGNALS[arm]:
        expected.append(sf.llm_missing_multihot)
    if 'S' in F.SIGNALS[arm]:
        expected.append(sf.summary_embed)
    np.testing.assert_array_equal(vector, np.concatenate(expected))
    assert len(vector) == F.dense_dim(arm)
    assert F.USES_ERROR_EMBED[arm] == ('E' in F.SIGNALS[arm])
    assert F.step_error_id(sf, arm) == (4 if 'E' in F.SIGNALS[arm] else 5)


def test_five_pair_exact_test_cannot_reach_point_zero_five():
    result = R.paired_test([0]*5, [1, 2, 3, 4, 5])
    assert result['sign_flip_p'] == 2/32
    assert result['delta']['mean'] == 3
    assert R.paired_test([1]*5, [1]*5)['sign_flip_p'] == 1


def test_confidence_interval_uses_sample_standard_error():
    result = R.mean_ci([1, 2, 3, 4, 5])
    assert result['ci95'] == pytest.approx([1.0367568385, 4.9632431615])


def test_calibration_excludes_structurally_masked_zeros_and_includes_one():
    result = R.calibration(np.array([[1, 0, 0]]), np.array([[1., .5, .99]]), np.array([[1, 1, 0]]))
    assert result['n'] == 2
    assert result['ece'] == .25
    assert result['brier'] == .125
    assert sum(b['n'] for b in result['bins']) == 2


def test_analyzer_agreement_uses_validation_wrong_answer_census():
    table = []
    analyses = []
    for i in range(20):
        table.append(dict(seq_pos=i, student_id=1, split='train' if i < 10 else 'test',
                          correct=False, raw_error_type='Arithmetical error',
                          error_type='calculation_error', missing_concepts=[C.CONCEPTS[0]]))
        analyses.append(L.NULL_OUTPUT.model_copy(update={'error_type': 'calculation_error',
                                                         'missing_concepts': [C.CONCEPTS[0]]}))
    result = R.analyzer_agreement(table, analyses)
    assert result['n_wrong_annotated_validation'] == 1
    assert result['agreement'] == 1
    assert result['concepts']['micro avg']['recall'] == 1


def test_loso_training_and_threshold_selection_exclude_held_student(monkeypatch):
    from src import train as T
    monkeypatch.setattr(L, 'MOCK', True)
    monkeypatch.setattr(C, 'MAX_EPOCHS', 1)
    table = rows() + [dict(r, student_id=2) for r in rows()]
    store = F.build_feature_store(table, ZeroEmbedder())
    train_seq, held_seq = D.build_sequences(table, store, 'A')
    loss_calls, collect_calls = [], []
    original_loss, original_collect = T._seq_loss, T._collect_probs
    def loss(net, seq, kind):
        loss_calls.append((seq.student_id, kind))
        return original_loss(net, seq, kind)
    def collect(net, seqs, kind):
        collect_calls.append(([s.student_id for s in seqs], kind))
        return original_collect(net, seqs, kind)
    monkeypatch.setattr(T, '_seq_loss', loss)
    monkeypatch.setattr(T, '_collect_probs', collect)
    T.train_one([train_seq], 'A', 0, lambda msg: None, evaluation_sequences=[held_seq])
    assert all(sid == 1 for sid, kind in loss_calls)
    assert collect_calls == [([1], 'val'), ([2], 'test')]
