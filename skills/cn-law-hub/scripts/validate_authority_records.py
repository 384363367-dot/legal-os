#!/usr/bin/env python3
"""Validate current-law authority records using the standard library."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from urllib.parse import urlparse
STAT={'effective','amended','repealed','expired','pending','unresolved'};VER={'verified-source','verified-metadata-only','lead-only','blocked'}
TYPES={'law','administrative-regulation','judicial-interpretation','department-rule','local-regulation','local-rule','treaty','other'}
REQ={'title','authority_type','issuing_body','status','proposition','source_url','accessed_at','verification_status','limitations'}
OFFICIAL_SUFFIXES=('.gov.cn','.npc.gov.cn','.court.gov.cn','.spp.gov.cn')
def is_official(url):
 h=(urlparse(url).hostname or '').lower();return h.endswith('.gov.cn') or h in {'gov.cn','www.gov.cn','npc.gov.cn','www.npc.gov.cn','flk.npc.gov.cn','court.gov.cn','www.court.gov.cn','spp.gov.cn','www.spp.gov.cn'}
def val(r,i):
 p=f'record[{i}]';e=[]
 if not isinstance(r,dict):return [f'{p}: must be an object']
 m=sorted(REQ-r.keys());
 if m:e.append(f"{p}: missing fields: {', '.join(m)}")
 if r.get('authority_type') not in TYPES:e.append(f'{p}: invalid authority_type')
 if r.get('status') not in STAT:e.append(f'{p}: invalid status')
 if r.get('verification_status') not in VER:e.append(f'{p}: invalid verification_status')
 if r.get('verification_status')=='verified-source' and not is_official(r.get('source_url','')):e.append(f'{p}: verified-source requires an official URL')
 if r.get('status') in {'amended','repealed','expired'} and not (r.get('superseded_by') or r.get('limitations')):e.append(f'{p}: changed/ended status requires supersession or limitation information')
 for k in ('limitations','supersedes','superseded_by'):
  if k in r and not isinstance(r[k],list):e.append(f'{p}: {k} must be an array')
 return e
def main():
 ap=argparse.ArgumentParser();ap.add_argument('json_file',type=Path);a=ap.parse_args()
 try:d=json.loads(a.json_file.read_text(encoding='utf-8'))
 except Exception as x:print(f'ERROR: {x}',file=sys.stderr);return 2
 rs=d if isinstance(d,list) else d.get('authorities') if isinstance(d,dict) else None
 if not isinstance(rs,list):print('ERROR: top level must be an array or object with authorities',file=sys.stderr);return 2
 es=[x for i,r in enumerate(rs) for x in val(r,i)]
 if es:print('\n'.join(es),file=sys.stderr);return 1
 print(f'OK: {len(rs)} authority record(s) validated');return 0
if __name__=='__main__':raise SystemExit(main())
