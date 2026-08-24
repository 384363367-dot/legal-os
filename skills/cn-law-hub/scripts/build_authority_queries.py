#!/usr/bin/env python3
"""Build privacy-conscious official-source queries for Chinese current-law research."""
from __future__ import annotations
import argparse,json
def clean(v):return ' '.join(v.split())
def build(proposition,name=None,article=None):
 p=clean(proposition);n=clean(name) if name else None;a=clean(article) if article else None;base=' '.join(x for x in (n,a,p) if x)
 queries=[f'site:flk.npc.gov.cn "{base}"',f'site:npc.gov.cn "{base}"',f'site:gov.cn "{base}"',f'site:court.gov.cn "{base}" 司法解释',f'site:gov.cn "{base}" 修改 废止 施行']
 return {'proposition':p,'authority_name':n,'article':a,'queries':list(dict.fromkeys(queries)),'verification_note':'Search results are leads; open an authoritative source and verify version/effectiveness before relying on the rule.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('proposition');ap.add_argument('--name');ap.add_argument('--article');x=ap.parse_args();print(json.dumps(build(x.proposition,x.name,x.article),ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
