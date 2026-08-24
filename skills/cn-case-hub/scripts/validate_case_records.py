#!/usr/bin/env python3
"""Validate cn-case-hub case records; accepts v0.6 compatibility plus v0.7 matrix fields."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
from urllib.parse import urlparse
OFFICIAL_SUFFIXES=(".court.gov.cn",".chinacourt.gov.cn");OFFICIAL_HOSTS={'court.gov.cn','www.court.gov.cn','rmfyalk.court.gov.cn','gongbao.court.gov.cn','wenshu.court.gov.cn','dyjfalk.court.gov.cn'}
SOURCE_GRADES={'A1','A2','B','C','D'};STATUSES={'verified-source','verified-metadata-only','official-summary','lead-only','blocked'};SIM={'high','medium','low'};DIR={'supports','adverse','mixed','neutral'};REL={'A','B','C','D'};DGR={'+','±','0','-'}
REQ={'title','source_type','source_grade','verification_status','issuing_body','case_numbers','courts','issues','key_facts','holding','result','direction','similarity','source_url','accessed_at','limitations'}
def official(url):
 h=(urlparse(url).hostname or '').lower();return h in OFFICIAL_HOSTS or any(h.endswith(s) for s in OFFICIAL_SUFFIXES)
def validate(r,index):
 p=f'record[{index}]';e=[]
 if not isinstance(r,dict):return [f'{p}: must be an object']
 miss=sorted(REQ-r.keys());
 if miss:e.append(f"{p}: missing fields: {', '.join(miss)}")
 if r.get('source_grade') not in SOURCE_GRADES:e.append(f'{p}: invalid source_grade')
 st=r.get('verification_status')
 if st not in STATUSES:e.append(f'{p}: invalid verification_status')
 if r.get('direction') not in DIR:e.append(f'{p}: invalid direction')
 u=r.get('source_url')
 if st in {'verified-source','verified-metadata-only','official-summary'} and (not isinstance(u,str) or not official(u)):e.append(f'{p}: verified/official record requires an official court URL')
 if st=='verified-source':
  for k in ('holding','result','accessed_at'):
   if not r.get(k):e.append(f'{p}: verified-source requires {k}')
 if st=='official-summary' and not r.get('limitations'):e.append(f'{p}: official-summary requires limitations')
 sim=r.get('similarity')
 if not isinstance(sim,dict):e.append(f'{p}: similarity must be an object')
 else:
  for k in ('overall','legal_relationship','issue','key_facts','procedure_and_level','time_and_law'):
   if sim.get(k) not in SIM:e.append(f'{p}: invalid similarity.{k}')
  if not sim.get('reason'):e.append(f'{p}: similarity.reason is required')
 for k in ('case_numbers','courts','issues','key_facts','limitations'):
  if k in r and not isinstance(r[k],list):e.append(f'{p}: {k} must be an array')
 # v0.7 matrix extension is optional for legacy records but internally consistent when present
 ext=[k in r for k in ('relevance_grade','direction_grade','matrix_grade')]
 if any(ext):
  if not all(ext):e.append(f'{p}: v0.7 matrix fields must be supplied together')
  else:
   rg,dg,mg=r.get('relevance_grade'),r.get('direction_grade'),r.get('matrix_grade')
   if rg not in REL:e.append(f'{p}: invalid relevance_grade')
   if dg not in DGR:e.append(f'{p}: invalid direction_grade')
   if rg in REL and dg in DGR and mg!=f'{rg}{dg}':e.append(f'{p}: matrix_grade must equal relevance_grade + direction_grade')
 if 'procedure_chain' in r and not isinstance(r['procedure_chain'],list):e.append(f'{p}: procedure_chain must be an array')
 if 'decisive_variables' in r and not isinstance(r['decisive_variables'],list):e.append(f'{p}: decisive_variables must be an array')
 return e
def main():
 p=argparse.ArgumentParser();p.add_argument('json_file',type=Path);a=p.parse_args()
 try:payload=json.loads(a.json_file.read_text(encoding='utf-8'))
 except (OSError,json.JSONDecodeError) as x:print(f'ERROR: {x}',file=sys.stderr);return 2
 rec=payload if isinstance(payload,list) else payload.get('cases') if isinstance(payload,dict) else None
 if not isinstance(rec,list):print('ERROR: top level must be an array or an object with a cases array',file=sys.stderr);return 2
 errs=[x for i,r in enumerate(rec) for x in validate(r,i)]
 if errs:print('\n'.join(errs),file=sys.stderr);return 1
 print(f'OK: {len(rec)} case record(s) validated');return 0
if __name__=='__main__':raise SystemExit(main())
