#!/usr/bin/env python3
"""Validate cn-law-hub first-party runtime dependency boundary."""
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
legacy={'court_law_crawler.py','tax_law_crawler.py','moj_law_crawler.py','treaty_crawler.py','mod_law_crawler.py','mee_law_crawler.py','party_law_crawler.py'}
found=sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob('*.py') if p.name in legacy)
imports=[]
for p in ROOT.rglob('*.py'):
    t=p.read_text(encoding='utf-8',errors='ignore')
    for lib in ('requests','selenium','playwright'):
        if re.search(rf'(^|\n)\s*(?:import\s+{lib}\b|from\s+{lib}\b)',t):imports.append(f'{p.name}:{lib}')
positive=[]
for p in [ROOT/'SKILL.md',*(ROOT/'references').glob('*.md')]:
    if not p.exists(): continue
    for line in p.read_text(encoding='utf-8',errors='ignore').splitlines():
        low=line.lower();negative=any(x in low for x in ('不依赖','无需','不得','不是','not require','does not require','must not require'))
        if negative: continue
        if ('第三方' in line and 'skill' in low and any(x in line for x in ('必须','需要安装','依赖'))) or ('mcp' in low and any(x in line for x in ('必须','依赖','需要安装'))):positive.append(line.strip())
if found or imports or positive:
    print('FIRST_PARTY_BOUNDARY_FAIL',{'legacy':found,'imports':imports,'declared_hard_dependencies':positive},file=sys.stderr);raise SystemExit(1)
print('FIRST_PARTY_BOUNDARY_PASS: cn-law-hub has no legacy crawler or third-party Skill/MCP SDK hard dependency')
