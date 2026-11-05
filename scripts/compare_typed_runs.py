"""Compare frozen typed-review arms without changing records or labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.training_assessment import validate_review

def checked_review(row, multi_quote=False):
    review=row["review"]
    if review is None:return None
    projection=json.loads(json.dumps(review))
    for point in projection.get("points",[]):
        if "learnerQuotes" not in point:
            if multi_quote:raise ValueError("required multi-quote field absent")
            continue
        quotes=point.pop("learnerQuotes")
        if not isinstance(quotes,list) or len(quotes)>3 or any(not isinstance(q,str) or not q.strip() or len(q)>160 for q in quotes):
            raise ValueError("invalid multi-quote contract")
        if len(set(quotes))!=len(quotes):raise ValueError("duplicate learner quote")
        cursor=0
        for quote in quotes:
            start=row["payload"]["learnerResponse"].find(quote,cursor)
            if start<0:raise ValueError("unordered or overlapping learner quotes")
            cursor=start+len(quote)
        if point.get("learnerQuote")!=(quotes[0] if quotes else ""):
            raise ValueError("legacy quote differs from list")
        if point.get("status")=="missing" and quotes:raise ValueError("missing point quotes")
    validate_review(json.dumps(projection),row["payload"])
    return review


def paired_summary(candidate, baseline, *, candidate_multi_quote=False, baseline_multi_quote=False):
    def indexed(rows):
        result = {r['index']: r for r in rows}
        if len(result) != len(rows):
            raise ValueError('duplicate case index')
        return result
    left, right = indexed(candidate), indexed(baseline)
    if not left or set(left) != set(right):
        raise ValueError('case identity mismatch')
    for index in left:
        if any(left[index][k] != right[index][k] for k in ('payload', 'expected')):
            raise ValueError('paired inputs or fixed labels differ')
    for rows, multi in ((candidate,candidate_multi_quote),(baseline,baseline_multi_quote)):
        for row in rows:checked_review(row,multi)
    def metrics(rows):
        valid = [r for r in rows if all(s == 'met' for s in r['expected'].values())]
        def actual(r):
            return {} if r['review'] is None else {p['criterionId']: p['status'] for p in r['review']['points']}
        exact = {r['index'] for r in rows if actual(r) == r['expected']}
        return dict(count=len(rows), exact=len(exact), validCount=len(valid),
                    validExact=sum(r['index'] in exact for r in valid),
                    delivered=sum(r['review'] is not None for r in rows),
                    falseCredit=[dict(index=r['index'], criterion=k) for r in rows
                                 for k, status in actual(r).items()
                                 if status == 'met' and r['expected'].get(k) != 'met']), exact
    c, ce = metrics(candidate)
    b, be = metrics(baseline)
    if c['validCount'] != 12 or c['count'] != 24:
        raise ValueError('fixed reserve gate requires 24 cases with 12 valid')
    failures = sorted(be - ce)
    gates = dict(validAtLeastTen=c['validExact'] >= 10,
                 zeroFalseCredit=not c['falseCredit'], noNewBaselineFailure=not failures,
                 validAcceptanceAtLeastBaseline=c['validExact'] >= b['validExact'],
                 deliveredAtLeastBaseline=c['delivered'] >= b['delivered'])
    return dict(candidate=c, baseline=b, newlyFailing=failures, gates=gates,
                semanticGatePassed=all(gates.values()),
                note='Independent semantic/provenance review and production/native/runtime/publication gates remain separate. Quote contracts may differ; delivery is not a policy-only comparison.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate', type=Path)
    p.add_argument('baseline', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    paths = [d / 'records.jsonl' for d in (args.candidate, args.baseline)]
    rows = [[json.loads(line) for line in path.read_text().splitlines()] for path in paths]
    locks=[json.loads((d / "lock.json").read_text()) for d in (args.candidate,args.baseline)]
    contracts=[lock.get("quoteContract", "single-exact-160-character-quote") for lock in locks]
    if any(c not in ("single-exact-160-character-quote","up-to-three-exact-160-character-quotes") for c in contracts):
        raise ValueError("unknown quote contract")
    report = paired_summary(*rows,candidate_multi_quote=contracts[0].startswith("up-to-three"),baseline_multi_quote=contracts[1].startswith("up-to-three"))
    report["quoteContracts"]=dict(candidate=contracts[0],baseline=contracts[1])
    report['recordSHA256'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    with args.output.open('x') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print(json.dumps(report['gates']))

if __name__ == '__main__':
    main()
