#!/usr/bin/env python3
"""Validate the public Legal OS repository without third-party YAML parsers."""
from __future__ import annotations
import argparse,re,sys
from pathlib import Path
from urllib.parse import unquote
try:from scripts.validate_manifest import validate_manifest
except ModuleNotFoundError:from validate_manifest import validate_manifest
try:from scripts.validate_public_surface import validate_public_surface
except ModuleNotFoundError:from validate_public_surface import validate_public_surface
NAME_RE=re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE=re.compile(r"\A---\s*\n(?P<data>.*?)\n---\s*(?:\n|\Z)",re.DOTALL)
MARKDOWN_LINK_RE=re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
RESOURCE_RE=re.compile(r"`((?:scripts|references)/[^`\s]+)`")
SKILL_REFERENCE_RE=re.compile(r"`((?:legal-os|cn-law|cn-case)-[a-z0-9-]+|legal-quality-gate)`")
INTERNAL_DIRECTIVE_RE=re.compile(r"(?:\bFor (?:Claude|Codex):|superpowers:)",re.IGNORECASE)
def parse_frontmatter(path:Path):
 errors=[];text=path.read_text(encoding='utf-8');m=FRONTMATTER_RE.match(text)
 if not m:return {},[f"{path}: missing YAML frontmatter"]
 meta={}
 for line in m.group('data').splitlines():
  if not line.strip() or line.lstrip().startswith('#'):continue
  if ':' not in line:errors.append(f"{path}: invalid frontmatter line: {line!r}");continue
  k,v=line.split(':',1);meta[k.strip()]=v.strip().strip('"').strip("'")
 extra=sorted(set(meta)-{'name','description'})
 if extra:errors.append(f"{path}: unsupported frontmatter keys: {extra}")
 return meta,errors
def local_target(source:Path,raw:str):
 target=raw.strip().split(maxsplit=1)[0].strip('<>')
 if not target or target.startswith('#') or re.match(r'^(?:https?|mailto):',target):return None
 target=unquote(target.split('#',1)[0].split('?',1)[0]);return source.parent/target
def validate_repository(root:Path):
 root=root.resolve();errors=[];errors.extend(validate_public_surface(root));sr=root/'skills';dirs=sorted(p for p in sr.iterdir() if p.is_dir()) if sr.is_dir() else []
 if not dirs:errors.append(f"{sr}: no Skill directories found")
 published={p.name for p in dirs};errors.extend(validate_manifest(root))
 for d in dirs:
  sf=d/'SKILL.md'
  if not sf.is_file():errors.append(f"{d}: missing SKILL.md");continue
  meta,e=parse_frontmatter(sf);errors.extend(e);name=meta.get('name','');desc=meta.get('description','')
  if name!=d.name:errors.append(f"{sf}: name {name!r} does not match folder {d.name!r}")
  if not NAME_RE.fullmatch(name):errors.append(f"{sf}: invalid skill name {name!r}")
  if not desc:errors.append(f"{sf}: description is empty")
  af=d/'agents/openai.yaml'
  if not af.is_file():errors.append(f"{d}: missing agents/openai.yaml")
  else:
   at=af.read_text(encoding='utf-8')
   if 'interface:' not in at or 'default_prompt:' not in at:errors.append(f"{af}: missing interface/default_prompt metadata")
   if f'${name}' not in at:errors.append(f"{af}: default prompt does not mention ${name}")
  txt=sf.read_text(encoding='utf-8')
  for m in RESOURCE_RE.finditer(txt):
   if not (d/m.group(1)).exists():errors.append(f"{sf}: missing bundled resource {m.group(1)!r}")
  for m in SKILL_REFERENCE_RE.finditer(txt):
   dep=m.group(1)
   if dep not in published:errors.append(f"{sf}: unbundled named Skill dependency {dep!r}")
 for md in sorted(root.rglob('*.md')):
  text=md.read_text(encoding='utf-8')
  if INTERNAL_DIRECTIVE_RE.search(text):errors.append(f"{md.relative_to(root)}: internal agent instruction found")
  for m in MARKDOWN_LINK_RE.finditer(text):
   target=local_target(md,m.group(1))
   if target is not None and not target.exists():errors.append(f"{md.relative_to(root)}: broken local link {m.group(1)!r}")
 return errors
def main():
 p=argparse.ArgumentParser();p.add_argument('root',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();errs=validate_repository(a.root)
 if errs:
  print('Repository validation: FAIL');[print('-',e) for e in errs];return 1
 print('Repository validation: PASS');return 0
if __name__=='__main__':sys.exit(main())
