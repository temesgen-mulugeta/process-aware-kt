"""Reproduce advisor experiments with a strict real-cache-only feature boundary.

GEMINI_MODEL=gemini-3.1-flash-lite .venv/bin/python -m src.revisions
Saves each run immediately; rerunning resumes completed runs in the same directory.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess

import numpy as np
import torch

from src import config as C, dataset as D, features as F, llm_analyzer as L
from src import metrics as M, train as T, revision_analysis as R

OUT = Path(os.environ.get('KT_RESULTS_DIR', str(C.RESULTS / 'revisions')))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def provenance(table):
    cache = hashlib.sha256()
    for r in table:
        path = L._cache_path(L._cache_key(L.build_prompt(r)))
        cache.update(path.name.encode())
        cache.update(path.read_bytes())
    source = hashlib.sha256()
    for path in sorted(Path('src').glob('*.py')):
        source.update(path.name.encode())
        source.update(path.read_bytes())
    return {"base_commit": subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            "source_sha256": source.hexdigest(), "table_sha256": hashlib.sha256(C.PROCESSED_TABLE.read_bytes()).hexdigest(),
            "cache_sha256": cache.hexdigest(), "seeds": C.SEEDS, "model": C.GEMINI_MODEL,
            "python": platform.python_version(), "torch": torch.__version__, "numpy": np.__version__,
            "threads": torch.get_num_threads(), "hidden": C.HIDDEN_SIZE, "dropout": C.DROPOUT,
            "learning_rate": C.LEARNING_RATE, "max_epochs": C.MAX_EPOCHS,
            "patience": C.EARLY_STOP_PATIENCE, "threshold_grid": T._THRESH_GRID,
            "mock": False, "loso_seed": 0, "summary_model": C.SUMMARY_EMBED_MODEL}


def compatible_provenance(prior, current):
    """A documentation/release commit alone does not alter an experiment."""
    return ({k: v for k, v in prior.items() if k != 'base_commit'} ==
            {k: v for k, v in current.items() if k != 'base_commit'})


def main():
    if L.MOCK:
        raise RuntimeError('Scientific revision runs require real cached features')
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    OUT.mkdir(parents=True, exist_ok=True)
    table = json.loads(C.PROCESSED_TABLE.read_text())
    if any(not L.use_cached(r) for r in table):
        raise RuntimeError('Incomplete analyzer cache; no API calls permitted')
    meta = provenance(table)
    prior = OUT / 'provenance.json'
    if prior.exists():
        recorded = json.loads(prior.read_text())
        if not compatible_provenance(recorded, meta):
            raise RuntimeError('Provenance changed: use a fresh result directory')
        meta = recorded  # Preserve the original execution identity on resume.
    else:
        write(prior, meta)
    log = T.Logger(OUT / 'train_log.txt')
    log('Building real feature store; CPU deterministic, one thread')
    store = F.build_feature_store(table)
    analyses = [L.analyze(r) for r in table]
    write(OUT / 'analyzer_agreement.json', R.analyzer_agreement(table, analyses))
    example_idx = next(i for i, r in enumerate(table) if r['missing_concepts'] and not r['correct'])
    rec, analysis = table[example_idx], analyses[example_idx]
    sf = store[(rec['student_id'], rec['seq_pos'])]
    write(OUT / 'feature_example.json', {'student': 'S*', 'problem': 'Q*', 'solution': rec['student_process'],
          'answer': rec['student_answer'], 'correct': rec['correct'], 'analyzer': analysis.model_dump(),
          'associated_indices': np.flatnonzero(sf.assoc_multihot).tolist(),
          'llm_missing_indices': np.flatnonzero(sf.llm_missing_multihot).tolist(),
          'error_id': sf.llm_error_type_id, 'summary_norm': float(np.linalg.norm(sf.summary_embed))})
    results = {'meta': meta, 'arms': {}, 'loso': {}}
    for arm in F.ALL_ARMS:
        seqs = D.build_sequences(table, store, arm)
        runs = []
        for seed in C.SEEDS:
            name = f'{arm}_seed{seed}'
            path = OUT / f'{name}.json'
            if path.exists():
                run = json.loads(path.read_text())
            else:
                run = T.train_one(seqs, arm, seed, log, prediction_path=OUT / f'{name}.npz')
                run['diagnostics'] = R.prediction_summary(OUT / f'{name}.npz')
                write(path, run)
            runs.append(run)
        results['arms'][arm] = {'runs': runs, 'f1_13': R.mean_ci([r['flat']['def_f1_13'] for r in runs]),
                               'aggregate': M.aggregate([r['flat'] for r in runs])}
    for arm in F.ARMS:
        seqs = D.build_sequences(table, store, arm)
        folds = []
        for held in seqs:
            training = [s for s in seqs if s.student_id != held.student_id]
            name = f'LOSO_{arm}_student{held.student_id}'
            path = OUT / f'{name}.json'
            if path.exists():
                run = json.loads(path.read_text())
            else:
                run = T.train_one(training, arm, 0, log, evaluation_sequences=[held],
                                  prediction_path=OUT / f'{name}.npz')
                run['held_student'] = held.student_id
                run['diagnostics'] = R.prediction_summary(OUT / f'{name}.npz')
                write(path, run)
            folds.append(run)
        results['loso'][arm] = folds
    for before, after in [('A', 'B'), ('B', 'C')]:
        results[f'{after}_minus_{before}'] = R.paired_test(
            [r['flat']['def_f1_13'] for r in results['arms'][before]['runs']],
            [r['flat']['def_f1_13'] for r in results['arms'][after]['runs']])
    write(OUT / 'summary.json', results)
    log(f'Completed all revisions; live API calls={L.API_CALLS}')
    log.close()


if __name__ == '__main__':
    main()
