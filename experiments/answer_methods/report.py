"""Build outputs/answer-methods-v1/REPORT.md from saved test runs; nothing is re-scored by hand.

    python -m experiments.answer_methods.report RUN_FOLDER [RUN_FOLDER ...]

Each argument is an evaluate.py output folder (summary.json + results.jsonl).
Results and summaries are copied next to the report so it stands alone.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/answer-methods-v1'
LABELS = {'direct': 'Direct inference (model picks the facts)', 'pal': 'PAL: model-written Python, sandboxed',
          'generated': 'Model-written query + code', 'choice': 'Model choice + code', 'keyword': 'Keywords + code'}


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
             '(`dev-tuning.json`). Greedy decoding; run settings are listed below.', '',
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
    lines += ['', '## Run settings', '',
              '| Dataset | Model | Revision | Device | Number type | Attention | Code commit | transformers |',
              '|---|---|---|---|---|---|---|---|']
    unrecorded = False
    for summary, rows, _ in runs:
        runtime = summary.get('runtime') or {}
        attention = runtime.get('attn_implementation')
        unrecorded = unrecorded or attention is None
        lines.append(f"| {summary['dataset']} | {summary['modelName']} | `{summary['model']['revision'][:7]}` | "
                     f"{runtime.get('device', summary.get('device'))} | {runtime.get('dtype', summary.get('dtype'))} | "
                     f"{attention or 'not recorded'} | `{str(summary.get('commit'))[:7]}` | "
                     f"{runtime.get('transformers', summary.get('transformers'))} |")
    if unrecorded:
        lines += ['', 'Runs without a recorded attention setting came from the closed PR #74 code (commit `d7b67ac`),',
                  'where the same method code lived at `scripts/evaluate_query_parsing.py`, `backend/query_parser.py`,',
                  '`backend/direct_answer.py` and `backend/program_answer.py`. Against the modules here it differs only',
                  'in comments and import paths, and it used the same pinned model revisions and test files (identical',
                  'hashes). That engine loaded Qwen2.5-VL with eager attention and other models with the library',
                  'default (SDPA on CPU).']
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
