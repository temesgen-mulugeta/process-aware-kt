"""Render report tables and interpretation from the completed revision matrix."""
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import config as C, metrics as M

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'report/generated'
DATA = ROOT / 'results/revisions'


def escape(s):
    return str(s).replace('&', r'\&').replace('_', r'\_').replace('%', r'\%')


def save(name, text):
    (OUT / f'{name}.tex').write_text(text + '\n')


def table(name, caption, headers, rows, layout=None, long=False):
    layout = layout or ('l' + 'r' * (len(headers) - 1))
    body = [' & '.join(map(str, row)) + r'\\' for row in rows]
    if long:
        text = (r'\small\begin{longtable}{@{}' + layout + r'@{}}' + '\n'
                + r'\caption{' + caption + r'}\label{tab:' + name + r'}\\' + '\n'
                + r'\toprule ' + ' & '.join(headers) + r'\\\midrule\endfirsthead' + '\n'
                + r'\toprule ' + ' & '.join(headers) + r'\\\midrule\endhead' + '\n'
                + '\n'.join(body) + '\n' + r'\bottomrule\end{longtable}\normalsize')
    else:
        text = (r'\begin{table}[htbp]\centering\small' + '\n'
                + r'\caption{' + caption + r'}\label{tab:' + name + '}' + '\n'
                + r'\begin{tabular}{@{}' + layout + r'@{}}\toprule' + '\n'
                + ' & '.join(headers) + r'\\\midrule' + '\n'
                + '\n'.join(body) + '\n' + r'\bottomrule\end{tabular}\end{table}')
    save(name, text)


def pct(v):
    return f'{100*v:.2f}'


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    results = json.loads((DATA / 'summary.json').read_text())
    arms = results['arms']
    means = {a: arms[a]['f1_13']['mean'] for a in arms}
    save('macros', '\n'.join(r'\newcommand{\Fone' + a + '}{' + pct(means[a]) + '}' for a in 'ABC'))
    main_rows = []
    for a in 'ABC':
        ag = arms[a]['aggregate']
        ci = arms[a]['f1_13']['ci95']
        main_rows.append([a, pct(ag['correct_acc']['mean']), f"{ag['correct_auc']['mean']:.3f}",
                          pct(ag['def_f1_55']['mean']),
                          f"{pct(means[a])} $\\pm$ {pct(arms[a]['f1_13']['std'])}",
                          f'[{pct(ci[0])}, {pct(ci[1])}]',
                          pct(ag['def_prec_13']['mean']), pct(ag['def_recall_13']['mean'])])
    table('main', r'Corrected official test results. Percent except AUC; F1@13 includes seed SD and a 95\% seed-mean interval.',
          ['Arm', 'Acc.', 'AUC', 'F1@55', 'F1@13 $\\pm$ SD', '95\\% CI', 'P@13', 'R@13'], main_rows)
    sigrows = []
    for label in ['B_minus_A', 'C_minus_B']:
        s = results[label]
        ci = s['delta']['ci95']
        sigrows.append([label.replace('_minus_', '$-$'), pct(s['delta']['mean']),
                        f'[{pct(ci[0])}, {pct(ci[1])}]', f"{s['paired_t_p']:.3f}",
                        f"{s['sign_flip_p']:.4f}", f"{s['paired_t_p_bonferroni']:.3f}"])
    table('significance', r'Paired F1@13 differences in percentage points. Two-sided tests; final column adjusts the two paired $t$ comparisons. Exact tests also receive Bonferroni adjustment in JSON.',
          ['Pair', '$\\Delta$', '95\\% CI ($\\Delta$)', '$p_t$', '$p_{exact}$', '$p_{t,adj}$'], sigrows)
    s = results['B_minus_A']
    save('primary_interpretation',
         f"B changes mean F1@13 by {100*(means['B']-means['A']):+.2f} percentage points relative to A. "
         f"The paired $t$ test gives $p={s['paired_t_p']:.3f}$ (two-comparison adjusted $p={s['paired_t_p_bonferroni']:.3f}$), "
         f"and the exact sign-flip test gives $p={s['sign_flip_p']:.4f}$. "
         "Neither primary comparison establishes a statistically reliable gain at the 5\\% level under the exact test. "
         "Mean ordering must not be described as an ordering that holds for every seed, or as proof that the gain is independent of thresholding.")
    order = ['A', 'B_M', 'B_E', 'B_S', 'B_ME', 'B_MS', 'B_ES', 'B', 'C']
    labels = {'A':'A', 'B':'A + M + E + S (B)', 'C':'Gold M + E (C)'}
    abrows=[]
    for a in order:
        label = labels.get(a, 'A + ' + ' + '.join(a[2:]))
        abrows.append([label, pct(means[a]), pct(arms[a]['f1_13']['std']),
                       f'{100*(means[a]-means["A"]):+.2f}', str(arms[a]['runs'][0]['parameters'])])
    table('ablations', 'All signal subsets on the same five seeds and official split. M: missing concepts; E: error type; S: summary. Parameters include the allocated error embedding, even where unused.',
          ['Inputs', 'F1@13', 'SD', '$\\Delta$ vs A (pp)', 'Parameters'], abrows)
    best = max([a for a in means if a.startswith('B')], key=means.get)
    save('ablation_interpretation',
         f"The highest exploratory mean among analyzer variants is {escape(labels.get(best, 'A + ' + ' + '.join(best[2:])))} ({pct(means[best])}\\%). "
         f"Removing summary from full B changes F1@13 by {100*(means['B_ME']-means['B']):+.2f} points "
         f"(ME {pct(means['B_ME'])}\\% versus MES {pct(means['B'])}\\%). "
         "The full feature bundle is therefore not automatically preferable. These contrasts share the exposed test set; "
         "they characterize this prototype and should be validated independently before selecting a production variant.")
    catrows=[]
    for cat in C.CATEGORIES:
        support=arms['A']['runs'][0]['diagnostics']['categories'][cat]['support']
        vals={a:np.mean([r['per_category_f1'][cat] for r in arms[a]['runs']]) for a in 'ABC'}
        catrows.append([escape(cat), support, *[f'{vals[a]:.3f}' for a in 'ABC'],f"{vals['B']-vals['A']:+.3f}"])
    table('categories', 'All-category F1 with positive test interaction support. F1 is a proportion and averaged over seeds.',
          ['Category','Positives','A','B','C','$\\Delta$ B$-$A'],catrows)
    studentrows=[]
    for sid in range(1,7):
        diagnostic=arms['A']['runs'][0]['diagnostics']['students'][str(sid)]
        chron=[np.mean([r['diagnostics']['students'][str(sid)]['category13']['macro_f1'] for r in arms[a]['runs']]) for a in 'ABC']
        loso=[next(r for r in results['loso'][a] if r['held_student']==sid)['flat']['def_f1_13'] for a in 'ABC']
        studentrows.append([f'S{sid}',diagnostic['n_targets'],diagnostic['n_positive_concept_labels'],*[pct(x) for x in chron],*[pct(x) for x in loso]])
    table('students', 'Per-student F1@13 (percent): chronological means over five seeds, LOSO at seed 0. Pos. counts concept labels.',
          ['Student','Targets','Pos.','A','B','C','LOSO A','LOSO B','LOSO C'],studentrows)
    pooled={}
    for a in 'ABC':
        ys,ps=[],[]
        for sid in range(1,7):
            with np.load(DATA / f'LOSO_{a}_student{sid}.npz') as d:
                ys.append(d['y']);ps.append(d['p']>=float(d['threshold']))
        pooled[a]=M.deficiency_metrics(np.concatenate(ys),np.concatenate(ps))['category13']['macro_f1']
    table('losopooled', 'Pooled LOSO predictions versus matched chronological seed 0 (F1@13 percent); all 404 test targets.',
          ['Arm','Chronological seed 0','Pooled LOSO','Difference (pp)'],
          [[a,pct(arms[a]['runs'][0]['flat']['def_f1_13']),pct(pooled[a]),f"{100*(pooled[a]-arms[a]['runs'][0]['flat']['def_f1_13']):+.2f}"] for a in 'ABC'])
    (OUT/'losopooled.tex').rename(OUT/'loso.tex')
    save('loso_interpretation',
         f"Pooling the held-student test predictions gives A={pct(pooled['A'])}\\%, B={pct(pooled['B'])}\\% and C={pct(pooled['C'])}\\%. "
         "Individual student scores vary substantially; a pooled score is not evidence that every student benefits. "
         "The LOSO folds share training students, so their six results are dependent and are not treated as six independent significance-test observations.")
    table('calibration', 'Associated-entry calibration on the test set, mean over five seeds. Lower ECE and Brier are better; no post-hoc probability calibration was fitted.',
          ['Arm','Entries per seed','ECE','Brier'],
          [[a,arms[a]['runs'][0]['diagnostics']['calibration']['n'],
            f"{np.mean([r['diagnostics']['calibration']['ece'] for r in arms[a]['runs']]):.4f}",
            f"{np.mean([r['diagnostics']['calibration']['brier'] for r in arms[a]['runs']]):.4f}"] for a in 'ABC'])
    thresholdrows=[]
    for a in order:
        thresholdrows.append([escape(a),*[f"{r['threshold']:.2f} / {r['epochs']}" for r in arms[a]['runs']]])
    table('thresholds','Global threshold / epochs executed (including patience) for every chronological seed.',
          ['Arm','Seed 0','Seed 1','Seed 2','Seed 3','Seed 4'],thresholdrows)
    extra=[]
    for sid in range(1,7):
        extra.append([f'S{sid}',*[f"{next(r for r in results['loso'][a] if r['held_student']==sid)['threshold']:.2f}" for a in 'ABC']])
    table('losothresholds','LOSO thresholds, selected only from the other five students.', ['Held student','A','B','C'],extra)
    with (OUT/'thresholds.tex').open('a') as f:f.write((OUT/'losothresholds.tex').read_text())
    confrows=[]
    for cat in C.CATEGORIES:
        for a in 'ABC':
            counts={k:np.mean([r['diagnostics']['categories'][cat][k] for r in arms[a]['runs']]) for k in ['support','tp','fp','fn','tn']}
            confrows.append([escape(cat),a,int(counts['support']),*[f'{counts[k]:.1f}' for k in ['tp','fp','fn','tn']]])
    table('confusions','One-vs-rest category counts, mean across five seeds; hence fractional counts. Each row totals 404 targets.',
          ['Category','Arm','Pos.','TP','FP','FN','TN'],confrows,long=True)
    analyzer=json.loads((DATA/'analyzer_agreement.json').read_text())
    short=['Wrong operation/concept','Lack of concepts','Calculation','Incomplete answer','Careless','None']
    table('analyzer','Error-type agreement on all 87 annotated wrong validation answers. Undefined precision/recall is reported as zero.',
          ['Gold class','Support','Precision','Recall'],
          [[short[i],int(analyzer['error_types'][cat]['support']),f"{analyzer['error_types'][cat]['precision']:.3f}",f"{analyzer['error_types'][cat]['recall']:.3f}"] for i,cat in enumerate(C.ERROR_TYPES)])
    table('analyzerconfusion','Analyzer error confusion matrix; rows gold, columns predicted. W: wrong operation/concept; L: lack; C: calculation; I: incomplete; E: careless; N: none.',
          ['Gold / Pred.','W','L','C','I','E','N'],[[short[i],*r] for i,r in enumerate(analyzer['error_confusion'])])
    conceptrows=[]
    for cat in C.CONCEPTS:
        d=analyzer['concepts'][cat]
        conceptrows.append([escape(cat),int(d['support']),f"{d['precision']:.3f}",f"{d['recall']:.3f}"])
    table('analyzerconcepts','Concept agreement on the 45 gold-positive validation records. All 55 concepts shown; zero-support rows have undefined recall reported as zero.',
          ['Concept','Support','Precision','Recall'],conceptrows,layout='p{.60\\linewidth}rrr',long=True)
    save('analyzer_details',r'Tables~\ref{tab:analyzerconfusion} and~\ref{tab:analyzerconcepts} provide the full class and concept diagnostics.'+'\n'+(OUT/'analyzerconfusion.tex').read_text()+(OUT/'analyzerconcepts.tex').read_text())
    save('discussion',
         f"The corrected experiment yields a mean B$-$A difference of {100*(means['B']-means['A']):+.2f} F1@13 points. "
         "This is a conditional empirical result for a fixed tiny corpus, not a general proof that offline LLM signals improve KT. "
         "The feature subsets show why a bundled comparison alone is insufficient, and the expanded agreement study reveals substantial analyzer noise. "
         "A gold-feature reference measures one alternative input condition; it cannot quantify an assured amount of recoverable headroom. "
         "In particular, a percentage of the A-to-C gap should not be interpreted as the fraction of knowledge captured by the analyzer.")
    save('conclusion',
         f"We implemented and evaluated offline process features for a small causal knowledge-tracing model. "
         f"After correcting occurrence identity, five-seed macro-F1@13 is {pct(means['A'])}\\% (A), {pct(means['B'])}\\% (B) and {pct(means['C'])}\\% (C). "
         "All signal subsets, paired tests, category support, student-level results, LOSO and calibration are reported. "
         "The result supports further study of offline process features, while the five-seed uncertainty, six-student sample and 50.6\\% analyzer error-type agreement prevent a strong claim of reliable generalization. "
         "The principal deliverable is a corrected, auditable experimental pipeline and an explicit account of where the evidence remains limited.")
    print('Rendered all report tables from',DATA/'summary.json')


if __name__ == '__main__':
    main()
