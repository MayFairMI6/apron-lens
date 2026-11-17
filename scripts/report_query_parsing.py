"""Build outputs/query_parsing_v1/REPORT.md from saved test runs; nothing is re-scored by hand.

    python scripts/report_query_parsing.py work/test-apron-qwen2.5-vl-3b work/test-apron-qwen3-vl-4b ...

Each argument is an evaluate_query_parsing.py output folder (summary.json + results.jsonl).
Results and summaries are copied next to the report so it stands alone.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/query_parsing_v1'
LABELS = {'direct': 'Direct inference (model picks the facts)', 'pal': 'PAL: model-written Python, sandboxed',
          'generated': 'Model-written query + code', 'choice': 'Model choice + code (service)', 'keyword': 'Keywords + code'}


def main(folders):
    runs = []
    for folder in map(Path, folders):
        summary = json.loads((folder / 'summary.json').read_text())
        rows = [json.loads(line) for line in (folder / 'results.jsonl').read_text().splitlines()]
        name = f"test-{summary['dataset']}-{summary['modelName']}"
        target = OUT / 'runs' / name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy(folder / 'summary.json', target / 'summary.json')
        shutil.copy(folder / 'results.jsonl', target / 'results.jsonl')
        runs.append((summary, rows, name))
    lines = ['# Answering coordinator questions: five methods on frozen test sets', '',
             'Every method answers the same typed questions about one aircraft at a fixed replay moment',
             '(apron: flight A2 at 20 s; tower: EZY123 at 50 s, both aircraft\'s reports visible). The',
             'correct answer is what the deterministic rules return for the labelled query. Test sets were',
             'hash-frozen and committed before any parser existed; thresholds were set on dev only',
             '(`dev-tuning.json`). CPU, float16, greedy decoding.', '',
             '## Correct final answers', '',
             '| Dataset | Model | ' + ' | '.join(LABELS[m] for m in LABELS) + ' |',
             '|---|---|' + '---:|' * len(LABELS)]
    for summary, rows, _ in runs:
        scores = summary['answerScore']
        cells = []
        for method in LABELS:
            s = scores.get(method)
            cells.append('—' if s is None else f"{s['exact']}/{s['total']}" + (f" ({s['invalid']} invalid)" if s['invalid'] else ''))
        lines.append(f"| {summary['dataset']} | {summary['modelName']} | " + ' | '.join(cells) + ' |')
    lines += ['', '"Invalid" means output the method could not use: a query outside the grammar, JSON that did not',
              'parse, or code rejected by the sandbox or failing at run time. Invalid outputs count as wrong.', '',
              '## Query accuracy for the parsing methods', '',
              '| Dataset | Model | Choice | Model-written | Keywords |', '|---|---|---:|---:|---:|']
    for summary, rows, _ in runs:
        q = summary['queryScore']
        lines.append(f"| {summary['dataset']} | {summary['modelName']} | " +
                     ' | '.join(f"{q[m]['exact']}/{q[m]['total']}" for m in ('choice', 'generated', 'keyword')) + ' |')
    lines += ['', '## Median seconds per question (4-core CPU)', '',
              '| Dataset | Model | Choice | Model-written | Direct | PAL |', '|---|---|---:|---:|---:|---:|']
    for summary, rows, _ in runs:
        t = summary['medianSeconds']
        lines.append(f"| {summary['dataset']} | {summary['modelName']} | " +
                     ' | '.join(f"{t[m]:.1f}" for m in ('choice', 'generated', 'direct', 'pal')) + ' |')
    lines += ['', '## Limits', '',
              '- Questions and labels were written by the AI assistant that wrote the parsers, without',
              '  independent human review; one scenario and one replay moment per dataset. Development-scale.',
              '- The keyword rules were written from the dev questions; test wording differs on purpose. While',
              '  testing this report script with a fake model, the tower test set was read once before the real',
              '  runs, which showed the keyword baseline\'s tower score; the rules were already committed and',
              '  were not changed afterwards.',
              '- Direct inference and PAL see both aircraft\'s reports; parsing methods only produce a query',
              '  and the rules handle identity, so the comparison is between whole designs, not prompts.',
              '- The PAL sandbox suits a disposable evaluation container; the service never runs model code.', '',
              'Raw outputs, option scores, model-written queries and code, and errors for every question are in',
              '`runs/`. ' + ', '.join(f'`runs/{name}`' for _, _, name in runs) + '.']
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    print((OUT / 'REPORT.md').read_text())


if __name__ == '__main__':
    main(sys.argv[1:])
