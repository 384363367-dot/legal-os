#!/usr/bin/env python3
"""Build privacy-conscious multi-round queries for official Chinese case sources."""
from __future__ import annotations
import argparse,json
from urllib.parse import quote
def clean(v):return " ".join(v.split()) if v else None
def build(issue:str,fact:str|None=None,court_language:list[str]|None=None)->dict[str,object]:
 issue=clean(issue);fact=clean(fact);court_language=[clean(x) for x in (court_language or []) if clean(x)]
 if not issue:raise ValueError('issue must not be empty')
 base=issue if not fact else f'{issue} {fact}'
 adverse='不予支持 OR 驳回 OR 不构成 OR 无效 OR 未证明'
 q=[f'site:court.gov.cn "{issue}" 指导案例',f'site:court.gov.cn "{issue}" 入库参考案例',f'site:court.gov.cn "{base}" 典型案例 裁判结果',f'site:gongbao.court.gov.cn "{issue}" 案例',f'site:court.gov.cn "{base}" ({adverse})',f'site:chinacourt.gov.cn "{base}" 案例',f'site:court.gov.cn "{base}" 二审',f'site:court.gov.cn "{base}" 再审']
 for lang in court_language:q.extend([f'site:court.gov.cn "{issue}" "{lang}"',f'site:chinacourt.gov.cn "{base}" "{lang}"'])
 # stable dedupe
 q=list(dict.fromkeys(q))
 return {'issue':issue,'fact':fact,'court_language':court_language,'privacy_note':'Only submit de-identified legal issues and necessary fact patterns.','queries':q,'official_entry_urls':{'people_court_case_database':'https://rmfyalk.court.gov.cn/','spc_search':f'https://www.court.gov.cn/search.html?content={quote(issue)}','spc_gazette':'https://gongbao.court.gov.cn/','judgments_online':'https://wenshu.court.gov.cn/'}}
def main():
 p=argparse.ArgumentParser();p.add_argument('issue');p.add_argument('--fact');p.add_argument('--court-language',action='append',default=[]);a=p.parse_args();print(json.dumps(build(a.issue,a.fact,a.court_language),ensure_ascii=False,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
