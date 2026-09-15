"""Independently verify saved runs against corrected source labels and summaries."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config as C, features as F, metrics as M, revision_analysis as R

base = C.RESULTS / 'revisions'
summary = json.loads((base / 'summary.json').read_text())
table = json.loads(C.PROCESSED_TABLE.read_text()) if C.PROCESSED_TABLE.exists() else None
lookup = {(r['student_id'], r['seq_pos']): r for r in table} if table is not None else None
reference = None
n = 0
for path in sorted(base.glob('*.npz')):
    saved = json.loads(path.with_suffix('.json').read_text())
    with np.load(path) as d:
        keys = list(zip(d['student'].tolist(), d['position'].tolist()))
        assert len(keys) == len(set(keys))
        if lookup is not None:
            assert all(lookup[key]['split'] == 'test' for key in keys)
            expected_y = np.stack([F.multihot(lookup[key]['missing_concepts']) for key in keys])
            expected_a = np.stack([F.multihot(lookup[key]['associated_concepts']) for key in keys])
            np.testing.assert_array_equal(d['y'], expected_y)
            np.testing.assert_array_equal(d['assoc'], expected_a)
        assert (d['p'][d['assoc'] == 0] == 0).all()
        assert np.isfinite(d['p']).all()
        assert float(d['threshold']) == saved['threshold']
        metrics = M.deficiency_metrics(d['y'], d['p'] >= saved['threshold'])
        assert abs(metrics['category13']['macro_f1'] - saved['flat']['def_f1_13']) < 1e-12
        if path.name.startswith('LOSO_'):
            assert set(d['student'].tolist()) == {saved['held_student']}
        else:
            assert len(keys) == 404 and d['y'].sum() == 59
            if reference is None:
                reference = keys
            assert reference == keys
        for cat, counts in saved['diagnostics']['categories'].items():
            assert counts['tp'] + counts['fp'] + counts['fn'] + counts['tn'] == len(keys)
            assert counts['tp'] + counts['fn'] == counts['support']
    n += 1
assert n == 63
for arm, data in summary['arms'].items():
    assert [r['seed'] for r in data['runs']] == [0, 1, 2, 3, 4]
    assert data['f1_13'] == R.mean_ci([r['flat']['def_f1_13'] for r in data['runs']])
source = hashlib.sha256()
# Saved runs belong to the immutable execution snapshot, not later maintenance.
for path in sorted((base / 'source_snapshot').glob('*.py')):
    source.update(path.name.encode())
    source.update(path.read_bytes())
assert source.hexdigest() == summary['meta']['source_sha256']
print('PASS: 63 saved runs, thresholds, F1, supports and archived execution-source fingerprint.')
print('Source-label alignment: verified against processed data.' if lookup is not None else
      'Source-label alignment: not checked; processed data absent. Metrics use archived gold arrays.')
