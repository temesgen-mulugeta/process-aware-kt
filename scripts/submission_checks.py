"""Recompute review diagnostics from frozen predictions, with no model/API calls.

If processed data are present, also audit all source-mask exceptions. Otherwise the
saved corpus audit remains available and test-mask reachability is checked directly.
"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config as C, metrics as M, data_integrity as I

BASE = C.RESULTS / 'revisions'
OUT = C.RESULTS / 'submission'


def mask_only(y, assoc):
    """Fixed diagnostic: associated concepts are all predicted missing."""
    return M.deficiency_metrics(y, assoc > .5)


def sensitivity(y, pred, assoc):
    """Exclude inconsistent target rows; never use gold labels to widen masks."""
    keep = ~((y > 0) & (assoc < .5)).any(axis=1)
    return {'excluded_targets': int((~keep).sum()),
            'metrics': M.deficiency_metrics(y[keep], pred[keep])}


def main():
    OUT.mkdir(exist_ok=True)
    with np.load(BASE / 'A_seed0.npz') as d:
        y, assoc = d['y'], d['assoc']
        result = {'mask_only': mask_only(y, assoc),
                  'mask_only_consistent_targets': sensitivity(y, assoc > .5, assoc),
                  'test_concept_positives': int(y.sum()),
                  'reachable_test_concept_positives': int((y * assoc).sum()),
                  'unreachable_test_targets': [
                      {'student_id': int(d['student'][i]), 'seq_pos': int(d['position'][i])}
                      for i in np.flatnonzero(((y > 0) & (assoc < .5)).any(axis=1))]}
    result['sensitivity'] = {}
    hashes = {}
    for arm in ('A', 'B', 'C'):
        runs = []
        for seed in range(5):
            path = BASE / f'{arm}_seed{seed}.npz'
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            with np.load(path) as d:
                np.testing.assert_array_equal(y, d['y'])
                np.testing.assert_array_equal(assoc, d['assoc'])
                runs.append(sensitivity(d['y'], d['p'] >= d['threshold'], d['assoc']))
        result['sensitivity'][arm] = {'runs': runs, 'mean_f1_55': float(np.mean([
            r['metrics']['concept55']['macro_f1'] for r in runs])),
            'mean_f1_13': float(np.mean([r['metrics']['category13']['macro_f1'] for r in runs]))}
    agreement = json.loads((BASE / 'analyzer_agreement.json').read_text())
    errors = agreement['error_types']
    majority = max(agreement['error_labels'], key=lambda label: errors[label]['support'])
    result['analyzer'] = {'majority_class': majority,
                          'majority_accuracy': errors[majority]['support'] / agreement['n_wrong_annotated_validation'],
                          'analyzer_accuracy': agreement['agreement'],
                          'macro_f1': errors['macro avg']['f1-score']}
    result['prediction_sha256'] = hashes
    result['policy'] = ('Post-review diagnostics on frozen predictions. Main results keep all gold labels; '
                        'sensitivity excludes entire inconsistent test rows, without refitting or threshold tuning. '
                        'Masks are never expanded from target missing labels.')
    (OUT / 'diagnostics.json').write_text(json.dumps(result, indent=2) + '\n')
    if C.PROCESSED_TABLE.exists():
        audit = I.mask_exceptions(json.loads(C.PROCESSED_TABLE.read_text()))
        (OUT / 'mask_exceptions.json').write_text(json.dumps(audit, indent=2) + '\n')
        print('Corpus mask exceptions:', len(audit))
    print(json.dumps({k: v for k, v in result.items() if k in ('mask_only', 'analyzer')}, indent=2))
    print('Sensitivity:', {a: {k: v for k, v in r.items() if k != 'runs'} for a, r in result['sensitivity'].items()})


if __name__ == '__main__':
    main()
