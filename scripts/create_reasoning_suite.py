"""Original fictional scenarios. Gold ID/status selections are authored below, not computed by resolver."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/reasoning_v1'

def e(i,p,v,t=0,r=None,aircraft='A2',flight='F2-R1',sup=(),start=None,end=None):
 f={'property':p,'value':v,'supersedes':list(sup)}
 if start is not None:f['validFrom']=start
 if end is not None:f['validUntil']=end
 return dict(id=i,aircraftId=aircraft,flightInstance=flight,source='fictional-coordinator',eventTime=t,receiptTime=t if r is None else r,
             message=f'{p} reported as {v}.',facts=[f])
def q(t,kind,props,claims,unknown=()):return dict(checkpoint=t,queryType=kind,properties=props,expected=claims,unknown=list(unknown))
# Every family stays wholly within one split. H families combine mechanisms not co-occurring in a D family.
specs=[
('D01','dev','late-service',[
 e('E11','baggage_status','pending'),e('E12','baggage_status','complete',8,18,sup=['E11:baggage_status'])],
 [q(10,'current',['baggage_status'],[('E11:baggage_status','current')]),q(18,'current',['baggage_status'],[('E12:baggage_status','current')]),q(20,'change',['baggage_status'],[('E11:baggage_status','superseded'),('E12:baggage_status','current')])]),
('D02','dev','identity-and-rotation',[
 e('E21','stand','B'),e('E22','stand','C',10,aircraft='A1',flight='F1-R1'),e('E23','baggage_status','complete',15,flight='F2-R0')],
 [q(20,'current',['stand'],[('E21:stand','current')]),q(20,'current',['baggage_status'],[],['baggage_status']),q(20,'latest',[],[('E21:stand','current')])]),
('D03','dev','plan-replacement',[
 e('E31','route','east'),e('E32','route','west',10,sup=['E31:route'])],
 [q(9,'current',['route'],[('E31:route','current')]),q(20,'current',['route'],[('E32:route','current')]),q(20,'change',['route'],[('E31:route','superseded'),('E32:route','current')])]),
('D04','dev','out-of-order-targets',[
 e('E41','tobt','40 s'),e('E42','tobt','55 s',8,28,sup=['E41:tobt']),e('E43','tobt','70 s',16,18,sup=['E41:tobt','E42:tobt'])],
 [q(20,'current',['tobt'],[('E43:tobt','current')]),q(30,'current',['tobt'],[('E43:tobt','current')]),q(30,'latest',['tobt'],[('E42:tobt','superseded')])]),
('D05','dev','future-effective-assignment',[
 e('E51','stand','B'),e('E52','stand','C',10,12,sup=['E51:stand'],start=25)],
 [q(15,'current',['stand'],[('E51:stand','current')]),q(15,'change',['stand'],[('E51:stand','current'),('E52:stand','scheduled')]),q(26,'current',['stand'],[('E52:stand','current')])]),
('D06','dev','validity-expiry',[
 e('E61','fuel_status','complete',10,end=20)],
 [q(19,'current',['fuel_status'],[('E61:fuel_status','current')]),q(20,'current',['fuel_status'],[],['fuel_status']),q(25,'change',['fuel_status'],[('E61:fuel_status','expired')],['fuel_status'])]),
('D07','dev','unresolved-conflict',[
 e('E71','route','east'),e('E72','route','north',10)],
 [q(9,'current',['route'],[('E71:route','current')]),q(20,'current',['route'],[],['route']),q(20,'change',['route'],[('E71:route','conflicting'),('E72:route','conflicting')],['route'])]),
('D08','dev','service-not-readiness',[
 e('E81','baggage_status','pending'),e('E82','baggage_status','complete',12,14,sup=['E81:baggage_status']),e('E83','fuel_status','complete',15),e('E84','tobt','30 s',17,aircraft='A1',flight='F1-R1')],
 [q(18,'latest',[],[('E83:fuel_status','current')]),q(18,'current',['baggage_status','fuel_status'],[('E82:baggage_status','current'),('E83:fuel_status','current')]),q(18,'current',['overall_readiness'],[],['overall_readiness'])]),
('H01','heldout','late-reassignment-with-rotation-distractor',[
 e('E101','stand','B'),e('E102','stand','D',7,22,sup=['E101:stand']),e('E103','stand','F',20,21,flight='F2-R0')],
 [q(21,'current',['stand'],[('E101:stand','current')]),q(22,'current',['stand'],[('E102:stand','current')]),q(25,'change',['stand'],[('E101:stand','superseded'),('E102:stand','current')])]),
('H02','heldout','delayed-old-plan-and-replacement-expiry',[
 e('E201','route','south',end=60),e('E202','route','west',8,26,sup=['E201:route']),e('E203','route','north',15,17,sup=['E201:route','E202:route'],end=35)],
 [q(20,'current',['route'],[('E203:route','current')]),q(30,'current',['route'],[('E203:route','current')]),q(35,'current',['route'],[],['route'])]),
('H03','heldout','conflict-resolution-with-other-flight-target',[
 e('E301','tobt','40 s'),e('E302','tobt','60 s',10),e('E303','tobt','75 s',20,25,sup=['E301:tobt','E302:tobt']),e('E304','tobt','15 s',22,aircraft='A1',flight='F1-R1')],
 [q(15,'current',['tobt'],[],['tobt']),q(25,'current',['tobt'],[('E303:tobt','current')]),q(25,'change',['tobt'],[('E301:tobt','superseded'),('E302:tobt','superseded'),('E303:tobt','current')])]),
('H04','heldout','late-correction-expiry-and-interleaved-services',[
 e('E401','fuel_status','complete',2,3,end=25),e('E402','fuel_status','complete',15,aircraft='A1',flight='F1-R1'),e('E403','baggage_status','complete',6,18),e('E404','fuel_status','complete',20,22,flight='F2-R0'),e('E405','fuel_status','pending',24,27,sup=['E401:fuel_status'])],
 [q(19,'current',['fuel_status','baggage_status'],[('E401:fuel_status','current'),('E403:baggage_status','current')]),q(26,'current',['fuel_status'],[],['fuel_status']),q(28,'change',['fuel_status'],[('E401:fuel_status','superseded'),('E405:fuel_status','current')])]),
]
queries=[]
for sid,split,family,events,qs in specs:
 data=dict(scenarioId=sid,duration=90,aircraft=[dict(id='A1',flightInstance='F1-R1'),dict(id='A2',flightInstance='F2-R1')],events=events)
 (OUT/'scenarios'/f'{sid}.json').write_text(json.dumps(data,indent=2)+'\n')
 for n,item in enumerate(qs,1):
  lookup={e['id']+':'+f['property']:(e,f) for e in events for f in e['facts']}
  gold={'claims':[dict(fact_id=fid,value=lookup[fid][1]['value'],status=status,evidence_ids=[lookup[fid][0]['id']]) for fid,status in item.pop('expected')],
        'unknown_properties':item.pop('unknown')}
  qid=f'{sid}-Q{n}'
  # Context schematic is intentionally identical across time and facts: negative-control image.
  image=Image.new('RGB',(672,448),'#10232e');draw=ImageDraw.Draw(image)
  draw.rectangle((70,80,600,330),outline='#c4d0d2',width=3)
  draw.line((80,260,590,260),fill='#7e8d94',width=20)
  for x,label,col in [(180,'A1 / F1-R1','#36cde1'),(440,'A2 / F2-R1','#ffbe55')]:
   draw.line((x,120,x,230),fill=col,width=7);draw.line((x-30,175,x+30,175),fill=col,width=6);draw.text((x-35,100),label,fill='white')
  draw.text((80,360),'SCHEMATIC ONLY. Plans and services are not visually observable.',fill='white')
  image.save(OUT/'images'/f'{qid}.png')
  item.update(id=qid,scenarioId=sid,split=split,family=family,aircraftId='A2',
              question=f"{item['queryType'].capitalize()} evidence for {', '.join(item['properties']) or 'the selected flight'} at {item['checkpoint']} s.",
              image=f'images/{qid}.png',gold=gold)
  queries.append(item)
(OUT/'queries.json').write_text(json.dumps(queries,indent=2)+'\n')
manifest={'version':'reasoning-v1','provenance':'Original fictional data; labels authored by the same developer, not independently expert-reviewed.',
          'split':'8 development families / 4 author-known held-out composition families; no family shared',
          'questions':len(queries),'image_note':'Identical non-diagnostic schematic negative control. Does not test visual reasoning.',
          'files':{str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'}}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Wrote {len(specs)} scenarios and {len(queries)} labeled queries')
