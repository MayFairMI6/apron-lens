"""PROCEDURAL: genuine-model checks of the controller replay service over HTTP.

Needs `python -m backend.replay` running. Development checks, not a held-out set.
"""
import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--port', type=int, default=8767)
    args = parser.parse_args()
    token = (ROOT / 'work/qwen-server-token.txt').read_text().strip()
    base = f'http://127.0.0.1:{args.port}'

    def call(path, body=None):
        request = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                         headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=120) as reply:
                return reply.status, json.loads(reply.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b'{}')

    health = call('/health')[1]
    run = health['runId']

    def act(**body):
        view = call('/replay')[1]
        return call('/replay/action', dict(actionId=uuid4().hex, runId=run, viewRevision=view['viewRevision'], **body))[1]

    def ask(question):
        view = call('/replay')[1]
        started = time.time()
        status, answer = call('/replay/question', dict(requestId=uuid4().hex, runId=run,
                                                      viewRevision=view['viewRevision'], question=question))
        return status, answer, round(time.time() - started, 2), view

    rows = [dict(record='run', health=health)]

    def record(case, status, answer, seconds, view, **checks):
        claims = [c['fact_id'] for c in answer.get('display', {}).get('claims', [])] if status == 200 else []
        row = dict(record='case', id=case, httpStatus=status, cutoff=view['cutoff'], aircraftId=view['selectedAircraft'],
                   accepted=answer.get('accepted'), errors=answer.get('errors'), citedFacts=claims,
                   unknowns=answer.get('display', {}).get('unknowns') if status == 200 else None,
                   answer=answer.get('display', {}).get('answer') if status == 200 else answer,
                   latencySeconds=seconds, checks=checks, passed=all(checks.values()))
        rows.append(row)
        print(case, 'PASS' if row['passed'] else 'FAIL', status, claims, checks, flush=True)

    act(action='select', aircraftId='A1')
    act(action='jump', markerId='R-F003')
    s, a, t, v = ask('Why is TRN101 going around?')
    record('go-around-at-receipt', s, a, t, v, accepted=bool(a.get('accepted')),
           citesGoAround='F003:movement_condition' in [c['fact_id'] for c in a.get('display', {}).get('claims', [])],
           noLaterReport=not any(c['fact_id'].startswith(('F004', 'F005')) for c in a.get('display', {}).get('claims', [])))
    act(action='jump', markerId='R-F005')
    s, a, t, v = ask('Is another approach confirmed for TRN101?')
    record('next-approach-unconfirmed', s, a, t, v, accepted=bool(a.get('accepted')),
           citesUnconfirmed='F005:movement_condition' in [c['fact_id'] for c in a.get('display', {}).get('claims', [])])
    act(action='seek', cutoff=90)
    s, a, t, v = ask('What is the latest reported movement for this flight?')
    record('backward-seek-before-go-around', s, a, t, v, accepted=bool(a.get('accepted')),
           noFutureReport=not any(c['fact_id'].startswith(('F003', 'F004', 'F005')) for c in a.get('display', {}).get('claims', [])))
    act(action='jump', markerId='R-F004')
    act(action='select', aircraftId='A2')
    s, a, t, v = ask('What is the latest report for TRN102?')
    cited = [c['fact_id'] for c in a.get('display', {}).get('claims', [])]
    record('switched-aircraft-trn102', s, a, t, v, accepted=bool(a.get('accepted')),
           citesOnlyTrn102=cited == ['F002:movement_status'], referent=a.get('referent', {}) and a['referent'].get('flightInstance') == 'TRN102')
    # An answer still being generated when the reviewer seeks must be refused.
    act(action='select', aircraftId='A1')
    act(action='jump', markerId='R-F003')
    result = {}
    thread = threading.Thread(target=lambda: result.update(zip(('s', 'a', 't', 'v'), ask('Why is TRN101 going around?'))))
    thread.start()
    time.sleep(2)
    moved = act(action='seek', cutoff=60)
    thread.join()
    record('seek-while-answering', result['s'], result['a'], result['t'], result['v'],
           refused=result['s'] == 409, viewMoved=moved.get('cutoff') == 60,
           notPending=call('/replay')[1]['assistantPending'] is False)
    end = call('/health')[1]
    rows.append(dict(record='end', scenarioHashUnchanged=end['scenarioHash'] == health['scenarioHash'], notes=len(call('/replay')[1]['notes'])))
    with args.output.open('x') as stream:
        for row in rows:
            stream.write(json.dumps(row) + '\n')


if __name__ == '__main__':
    main()
