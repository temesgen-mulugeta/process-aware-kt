# Reproducing the submitted results

The submission archive contains corrected code, tests, all 63 saved prediction/label arrays and run summaries, the diagnostic supplement, and post-review controls. It does **not** contain raw worked solutions, the analyzer cache, or encoder weights. No new analyzer extraction or model training was performed for the submission-review fixes.

## What can be reproduced without the analyzer cache

From the repository/archive root, in an environment with the declared dependencies:

```sh
python scripts/verify_revision_artifacts.py
python scripts/submission_checks.py
```

These recompute saved F1, check masks/thresholds/supports, validate the archived execution-source fingerprint, and calculate the mask-only baseline, analyzer majority comparison and frozen-prediction sensitivity analysis. If the processed source table is absent, the verifier explicitly skips independent source-label alignment. The complete six-record audit is retained in `results/submission/mask_exceptions.json`.

This verifies saved predictions; it does not independently retrain the models or verify source labels against upstream raw data without those data.

## Immutable experiment identity

- `results/revisions/source_snapshot/` is the exact Python source used for the 63 fits. Its combined SHA-256 matches the original `provenance.json`, and per-file hashes are in `artifact_manifest.json`.
- Original `provenance.json`, `summary.json`, predictions and environment records are preserved unchanged. Later maintenance fixes are not retroactively described as the source of those runs.
- `results/revisions/environment.txt` contains the exact resolved package versions. `requirements.txt` specifies compatible ranges, not a lock file.
- Sentence encoder snapshot: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`; weight SHA-256: `53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`. The complete file hashes are in `artifact_manifest.json`.
- Upstream dataset commits are recorded in that manifest.

## What retraining additionally requires

The original 3,962-file analyzer cache, matching processed table, encoder snapshot and recorded software/runtime settings are required to reproduce the original training condition. Re-extracting with Gemini produces a new condition even at temperature zero. Cache and encoder hashes must match the manifest; fixed seeds alone do not ensure cross-platform identity.

Use the archived source snapshot to reconstruct the exact original execution code in a separate checkout and train into an empty results directory. For new runs with the maintained code, set `KT_RESULTS_DIR` to a fresh directory, for example:

```sh
GEMINI_MODEL=gemini-3.1-flash-lite HF_HUB_OFFLINE=1 KT_RESULTS_DIR=results/new-runs python -m src.revisions
```

The current runner ignores only a change in Git HEAD when checking resume compatibility. Any source/data/cache/runtime difference still blocks mixing runs. It preserves the original run commit on resume. The historical snapshot retains its original strict resume behavior.

The release is prepared locally. Sharing the source archive or pushing the referenced commit is a separate publication step; no remote release was published automatically.
