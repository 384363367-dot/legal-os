#!/usr/bin/env python3
"""Validate synthetic Unified Intake decisions against the public manifest."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
RISKS={'R0','R1','R2','R3'};GAPS={'G0','G1','G2','G3'};MODES={'route-only','route-and-run'};STATUSES={'routed','ready','stopped','awaiting-authorization'}
def validate_scenarios(manifest,scenarios):
 errors=[];routes={r['id']:r for r in manifest['routes']}
 for i,s in enumerate(scenarios):
  label=s.get('id',f'scenario-{i}');d=s.get('expected_decision',{});mode=d.get('mode');primary=d.get('primary_route');aux=d.get('auxiliary_routes',[]);risk=d.get('risk');gap=d.get('gap');status=d.get('status')
  if mode not in MODES:errors.append(f"{label}: invalid execution mode {mode!r}")
  if primary not in routes:errors.append(f"{label}: exactly one known primary_route is required");continue
  if not isinstance(aux,list) or len(aux)!=len(set(aux)):errors.append(f"{label}: auxiliary_routes must be a unique list");aux=[]
  if primary in aux:errors.append(f"{label}: primary route cannot also be auxiliary")
  unk=sorted(set(aux)-set(routes));
  if unk:errors.append(f"{label}: unknown auxiliary routes {unk}")
  if risk not in RISKS:errors.append(f"{label}: invalid risk {risk!r}")
  if gap not in GAPS:errors.append(f"{label}: invalid gap {gap!r}")
  if status not in STATUSES:errors.append(f"{label}: invalid status {status!r}")
  req=set(s.get('intake',{}).get('task_types',[]));covered=set()
  for rid in [primary,*aux]:covered.update(routes[rid].get('intake_types',[]))
  unc=sorted(req-covered)
  if unc:errors.append(f"{label}: requested task types are not covered by the decision: {unc}")
  flags=set(s.get('intake',{}).get('flags',[]))
  if 'core-conflict' in flags and (gap!='G3' or status!='stopped'):errors.append(f"{label}: a core conflict must produce G3/stopped")
  if gap=='G3' and status!='stopped':errors.append(f"{label}: G3 must stop execution")
  if mode=='route-only' and status not in {'routed','stopped'}:errors.append(f"{label}: route-only may only return routed or stopped")
  if mode=='route-and-run' and status=='routed':errors.append(f"{label}: route-and-run cannot end with routed status")
  if 'external-action-requested' in flags and mode=='route-and-run' and status!='awaiting-authorization':errors.append(f"{label}: external actions require awaiting-authorization")
  if 'high-impact' in flags and risk not in {'R2','R3'}:errors.append(f"{label}: high-impact tasks must be R2 or R3")
 return errors
def main():
 p=argparse.ArgumentParser();root=Path(__file__).resolve().parents[1];p.add_argument('--manifest',type=Path,default=root/'legalos.manifest.json');p.add_argument('--scenarios',type=Path,default=root/'tests/fixtures/unified_intake_scenarios.json');a=p.parse_args();m=json.loads(a.manifest.read_text(encoding='utf-8'));s=json.loads(a.scenarios.read_text(encoding='utf-8'));e=validate_scenarios(m,s)
 if e:print('Routing scenario validation: FAIL');[print('-',x) for x in e];return 1
 print(f'Routing scenario validation: PASS ({len(s)} synthetic scenarios)');return 0
if __name__=='__main__':sys.exit(main())
