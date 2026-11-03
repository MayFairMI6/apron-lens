"""Training-only evidence selector; frozen research inference is unchanged.

The model chooses a flight, fact IDs and missing properties. The adapter expands
those references into the existing proposal schema; the unchanged validator
still checks identity, values, temporal status, citations and missing facts.
Original selector output and the exact prompt are audited separately because
the conversation server's rawModelOutput field sees the expanded proposal.
"""
import json
import re
from dataclasses import replace
from pathlib import Path
from backend.evidence import FIELDS
from modelaccess.local_backbone import LocalBackboneAdapter
from modelaccess.contract import Adapter

TRAINING_PROMPT_VERSION='training-evidence-selector-v4'
SELECTOR_FORMAT_VERSION='single-json-or-fence-v1'
ROLES={r['id']:r for r in json.loads((Path(__file__).resolve().parents[1]/'data/training/role_profiles.json').read_text())}

def selector_context(base_prompt,role='controller_awareness'):
    prefix,tail=base_prompt.split('Candidate flights and received facts: ',1)
    candidates,end=json.JSONDecoder().raw_decode(tail)
    question=tail[end:].removeprefix('\nUser: ')
    memory,_=json.JSONDecoder().raw_decode(prefix.split('Memory: ',1)[1])
    selection=next((line for line in prefix.splitlines() if 'Selected in the app:' in line),'')
    compact=[]
    for c in candidates:
        current={f['property'] for f in c['facts'] if f['status']=='current'}
        compact.append(dict(aircraftId=c['aircraftId'],flightInstance=c['flightInstance'],
            facts=[{k:f[k] for k in ('fact_id','property','value','status','receiptTime')} for f in c['facts']],
            missingProperties=sorted(set(FIELDS)-current)))
    prompt=(
        'You select evidence for an airport training question. Return ONLY one compact JSON object: '
        '{"aircraftId":"...","flightInstance":"...","fact_ids":["ID:property"],"unknowns":[]}. '
        'Choose the flight intended by the question and selection or conversation memory. '
        'If ambiguous, use null for both identities and empty lists. '
        'Select at most THREE distinct fact_ids that directly answer the question. '
        'For latest update, choose the most recently received CURRENT relevant facts. '
        'Use superseded facts only for a history or correction question. '
        'For readiness, select the relevant current service or movement facts and include overall_readiness '
        'in unknowns if it is in missingProperties. A completed service or time estimate is not departure clearance. '
        'A current report with a negative, incomplete or restricted state is a KNOWN answer, '
        'including for a yes/no question. Select its fact_id; do not mark that property unknown. '
        'unknowns means the requested property has NO current reported value; it does not mean '
        'the answer is no, the requested condition is unmet, or a positive confirmation is absent. '
        'Only include properties actually asked about AND listed in that flight\'s missingProperties. '
        'Do not copy unrelated missingProperties into unknowns. If the selected reports answer the '
        'question, unknowns must be []. Never put the property of a selected current fact in unknowns. '
        'Images do not establish operational clearance or service completion. Do not add observations, '
        'rationale, prose, duplicate IDs or any other keys. Close the JSON object.\n'
        +'Assigned training role: '+ROLES[role]['label']+'. '+ROLES[role]['assistantFocus']+'\n'
        +selection+'\nMemory: '+json.dumps(memory)+'\nFlights: '+json.dumps(compact)+'\nQuestion: '+question)
    return prompt,candidates

def expand_selection(text,candidates):
    # Accept one complete JSON document or one JSON-only Markdown fence.
    # Do not search prose for objects, repair JSON, or alter selected evidence.
    text=text.strip()
    fence=re.fullmatch(r"```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```",text)
    if fence:text=fence.group(1)
    selection=json.loads(text)
    if not isinstance(selection,dict) or set(selection)!={'aircraftId','flightInstance','fact_ids','unknowns'}:
        raise ValueError('selector schema')
    ids=selection['fact_ids'];unknowns=selection['unknowns']
    if not isinstance(ids,list) or len(ids)>3 or not all(isinstance(i,str) for i in ids) or not isinstance(unknowns,list) or not all(isinstance(u,str) for u in unknowns):
        raise ValueError('selector references')
    ref=None if selection['aircraftId'] is None and selection['flightInstance'] is None else {k:selection[k] for k in ('aircraftId','flightInstance')}
    candidate=next((c for c in candidates if ref is not None and all(c[k]==ref[k] for k in ref)),None)
    # Preserve bad model references for the unchanged validator to reject.
    lookup={} if candidate is None else {f['fact_id']:f for f in candidate['facts']}
    claims=[]
    for fid in ids:
        fact=lookup.get(fid)
        claims.append(dict(fact_id=fid,value='' if fact is None else fact['value'],
            status='current' if fact is None else fact['status'],evidence_ids=[] if fact is None else [fact['event_id']]))
    previous=candidate.get('previousAnswer') if candidate else None
    changes=previous['changedSincePreviousAnswer'] if previous else []
    proposal=dict(status='clarify' if ref is None else 'answer',referent=ref,claims=claims,unknowns=unknowns,
        explanationChanged=bool(changes) if previous else None,changesNotDiscussed=[i for i in changes if i not in ids],
        memoryUpdate=None,rationale='',observations=[])
    if ref is None and (ids or unknowns):raise ValueError('ambiguous selection with claims')
    return json.dumps(proposal)

class _PracticeReviewAdapter(Adapter):
    """Contract validation over the already-loaded engine, without the selector."""
    def __init__(self, owner):
        super().__init__(owner.capabilities);self.owner=owner;self.provider=owner.provider
    def _generate(self, request, effective):
        return LocalBackboneAdapter._generate(self.owner,request,effective)

class TrainingAdapter(LocalBackboneAdapter):
    def __init__(self,*args,prompt_audit_path,training_role='controller_awareness',**kwargs):
        super().__init__(*args,**kwargs)
        self.prompt_audit_path=Path(prompt_audit_path)
        if training_role not in ROLES:raise ValueError('Unknown training role')
        self.training_role=training_role
    def review(self,request):
        return _PracticeReviewAdapter(self).generate(request)
    def _generate(self,request,effective):
        prompt,candidates=selector_context(request.messages[0][1],self.training_role)
        reply=super()._generate(replace(request,messages=(('user',prompt),)),effective)
        original=reply.text
        try:reply.text=expand_selection(original,candidates)
        except (ValueError,TypeError,KeyError):pass # invalid JSON/schema is withheld downstream
        self.prompt_audit_path.parent.mkdir(parents=True,exist_ok=True)
        with self.prompt_audit_path.open('a') as audit:
            audit.write(json.dumps(dict(requestId=request.request_id,promptVersion=TRAINING_PROMPT_VERSION,trainingRole=self.training_role,
                selectorFormatVersion=SELECTOR_FORMAT_VERSION,prompt=prompt,rawSelectorOutput=original,expandedProposal=reply.text))+'\n')
        return reply
