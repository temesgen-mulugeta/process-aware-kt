"""Audit source labels without changing prediction masks or gold annotations."""
from src import dataset as D


def mask_exceptions(table):
    issues = []
    for sid, rows in D._student_order(table).items():
        validation = D._assign_val(rows)
        for r in rows:
            outside = sorted(set(r['missing_concepts']) - set(r['associated_concepts']))
            if outside:
                role = ('test' if r['split'] == 'test' else
                        'validation' if r['seq_pos'] in validation else 'training')
                issues.append({'student_id': sid, 'seq_pos': r['seq_pos'], 'role': role,
                               'outside_mask': outside})
    return issues
