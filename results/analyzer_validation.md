# Expanded analyzer validation

Census of all 87 wrong annotated answers in chronological validation tails. Real cached Gemini outputs; no API calls.

Error-type agreement: **44/87 = 50.6%**. The earlier 20-record check is historical (`historical/analyzer_validation.md`).

| Gold error type | Support | Precision | Recall |
|---|---:|---:|---:|
| wrong_operation_or_concept | 54 | 0.695 | 0.759 |
| lack_of_concepts | 11 | 0.000 | 0.000 |
| calculation_error | 8 | 0.176 | 0.375 |
| incomplete_answer | 13 | 0.000 | 0.000 |
| careless_error | 1 | 0.000 | 0.000 |
| none | 0 | 0.000 | 0.000 |

Among 45 gold-deficiency validation records (49 positive concept labels): micro precision 27.0%, recall 20.4%. These are conditional scores; they exclude false alarms on gold-negative records. Full per-concept scores and error confusion matrix: `revisions/analyzer_agreement.json`.
