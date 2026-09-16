"""Review regressions: audit labels, preserve masks and quantify simple controls."""
import numpy as np
import torch
from src import config as C, data_integrity as I, model, revisions
from scripts.submission_checks import mask_only, sensitivity


def test_mask_audit_preserves_labels_and_reports_roles():
    table = [dict(student_id=1, seq_pos=i, split='train' if i < 10 else 'test',
                  associated_concepts=['a'], missing_concepts=['b'] if i in (1, 9, 10) else [])
             for i in range(11)]
    issues = I.mask_exceptions(table)
    assert [(r['seq_pos'], r['role']) for r in issues] == [(1, 'training'), (9, 'validation'), (10, 'test')]
    assert table[10]['associated_concepts'] == ['a']
    assert table[10]['missing_concepts'] == ['b']


def test_outside_mask_label_is_ignored_by_loss_but_retained_in_metrics():
    y = np.zeros((2, C.NUM_CONCEPTS)); assoc = y.copy()
    assoc[:, 0] = 1; y[0, 1] = 1; y[1, 0] = 1
    logits = torch.zeros(y.shape)
    target, mask = torch.tensor(y), torch.tensor(assoc)
    original = model.focal_deficiency_loss(logits, target, mask)
    cleaned = target.clone(); cleaned[0, 1] = 0
    torch.testing.assert_close(original, model.focal_deficiency_loss(logits, cleaned, mask))
    full = mask_only(y, assoc)
    assert full['n_positive_concept_labels'] == 2
    assert full['concept55']['macro_recall'] == 1 / C.NUM_CONCEPTS
    check = sensitivity(y, assoc, assoc)
    assert check['excluded_targets'] == 1
    assert check['metrics']['n_targets'] == 1
    assert y[0, 1] == 1 and assoc[0, 1] == 0


def test_release_commit_does_not_change_resume_identity():
    prior = {'base_commit': 'old', 'source_sha256': 'same', 'cache_sha256': 'same'}
    current = {**prior, 'base_commit': 'new'}
    assert revisions.compatible_provenance(prior, current)
    assert not revisions.compatible_provenance(prior, {**current, 'source_sha256': 'changed'})
    assert prior['base_commit'] == 'old'
