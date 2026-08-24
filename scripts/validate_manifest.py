#!/usr/bin/env python3
"""Validate the Legal OS public manifest and its repository projections."""
from __future__ import annotations
import json,re
from pathlib import Path
from typing import Any
SEMVER_RE=re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
EXPECTED_ROUTES={f"T-{n:02d}" for n in range(1,13)}
EXPECTED_PROFILES={"public-generic","private-controlled"}
def load_json(path:Path)->Any:return json.loads(path.read_text(encoding="utf-8"))
def _implicit_invocation(agent_file:Path)->bool:
 text=agent_file.read_text(encoding="utf-8");m=re.search(r"^\s*allow_implicit_invocation:\s*(true|false)\s*$",text,re.MULTILINE);return m is not None and m.group(1)=="true"
def validate_manifest(root:Path,manifest:dict[str,Any]|None=None)->list[str]:
 root=root.resolve();errors=[];mp=root/'legalos.manifest.json';sp=root/'schemas/legalos-manifest.schema.json'
 if not mp.is_file():return [f"{mp}: missing public manifest"]
 if not sp.is_file():errors.append(f"{sp}: missing manifest schema")
 try:manifest=manifest if manifest is not None else load_json(mp)
 except (json.JSONDecodeError,OSError) as e:return [f"{mp}: invalid JSON: {e}"]
 required={"$schema","schema_version","product","authority","profiles","execution_modes","skills","routes","invocation_policy","template_runtime","quality_gates"}
 missing=sorted(required-set(manifest));
 if missing:errors.append(f"{mp}: missing required fields {missing}")
 if not isinstance(manifest.get('schema_version'),str) or not SEMVER_RE.fullmatch(manifest['schema_version']):errors.append(f"{mp}: schema_version must be SemVer")
 product=manifest.get('product',{});version=product.get('public_version') if isinstance(product,dict) else None
 if not isinstance(version,str) or not SEMVER_RE.fullmatch(version):errors.append(f"{mp}: product.public_version must be SemVer")
 profiles=manifest.get('profiles',[])
 if not isinstance(profiles,list):errors.append(f"{mp}: profiles must be a list");profiles=[]
 ids={x.get('id') for x in profiles if isinstance(x,dict)}
 if ids!=EXPECTED_PROFILES:errors.append(f"{mp}: profiles must be exactly {sorted(EXPECTED_PROFILES)}")
 defaults=[x.get('id') for x in profiles if isinstance(x,dict) and x.get('default') is True]
 if defaults!=['public-generic']:errors.append(f"{mp}: public-generic must be the only default profile")
 pub=next((x for x in profiles if isinstance(x,dict) and x.get('id')=='public-generic'),{})
 priv=next((x for x in profiles if isinstance(x,dict) and x.get('id')=='private-controlled'),{})
 if pub.get('distributed') is not True or pub.get('private_overlay') is not False:errors.append(f"{mp}: public-generic distribution boundary is invalid")
 if priv.get('distributed') is not False or priv.get('private_overlay') is not True:errors.append(f"{mp}: private-controlled must remain an undistributed overlay")
 items=manifest.get('skills',[]);mSkills={x.get('name') for x in items if isinstance(x,dict)};sroot=root/'skills';rSkills={p.name for p in sroot.iterdir() if p.is_dir()} if sroot.is_dir() else set()
 if mSkills!=rSkills:errors.append(f"{mp}: Skill inventory mismatch; manifest={sorted(mSkills)}, repository={sorted(rSkills)}")
 routes=manifest.get('routes',[]);rids={x.get('id') for x in routes if isinstance(x,dict)}
 if rids!=EXPECTED_ROUTES:errors.append(f"{mp}: routes must be exactly T-01 through T-12")
 for route in routes:
  if not isinstance(route,dict):errors.append(f"{mp}: each route must be an object");continue
  ex=route.get('executor',{})
  if not isinstance(ex,dict):errors.append(f"{mp}: route {route.get('id')} executor must be an object");continue
  refs=[]
  if ex.get('skill'):refs.append(ex['skill'])
  if isinstance(ex.get('skill_by_intake_type'),dict):refs.extend(ex['skill_by_intake_type'].values())
  for skill in refs:
   if skill not in mSkills:errors.append(f"{mp}: route {route.get('id')} references unknown Skill {skill!r}")
  if ex.get('kind')=='bundled-research-family':
   dispatch=ex.get('skill_by_intake_type',{})
   if set(dispatch)!=set(route.get('intake_types',[])):errors.append(f"{mp}: route {route.get('id')} research dispatch must cover every intake type")
 policy=manifest.get('invocation_policy',{})
 if set(policy)!=mSkills:errors.append(f"{mp}: invocation policy must cover every and only published Skill")
 for skill in sorted(rSkills):
  expected=policy.get(skill,{}).get('allow_implicit_invocation')
  if not isinstance(expected,bool):errors.append(f"{mp}: {skill} invocation policy must be boolean");continue
  af=sroot/skill/'agents/openai.yaml'
  if af.is_file() and _implicit_invocation(af)!=expected:errors.append(f"{af}: implicit invocation contradicts legalos.manifest.json")
 router=manifest.get('authority',{}).get('router')
 if router!='legal-os-unified-intake' or router not in mSkills:errors.append(f"{mp}: authority.router must be legal-os-unified-intake")
 if isinstance(version,str):
  for proj in [root/'README.md',root/'CHANGELOG.md',root/'docs/capability-matrix.md']:
   if proj.is_file() and f"v{version}" not in proj.read_text(encoding='utf-8'):errors.append(f"{proj}: does not project manifest version v{version}")
 tr=manifest.get('template_runtime',{})
 if not isinstance(tr,dict):errors.append(f"{mp}: template_runtime must be an object")
 else:
  for key in ('catalog','resolver'):
   value=tr.get(key)
   if not isinstance(value,str) or not (root/value).is_file():errors.append(f"{mp}: template_runtime.{key} must reference an existing file")
  if tr.get('content_model')!='fixed-shell-flexible-body':errors.append(f"{mp}: template_runtime.content_model is invalid")
  if tr.get('private_overlay')!='supported-not-distributed':errors.append(f"{mp}: private template overlays must remain undistributed")
  if tr.get('no_template_status')!='TEMPLATE_REQUIRED':errors.append(f"{mp}: no-template status must be TEMPLATE_REQUIRED")
 try:
  schema=load_json(sp)
  if schema.get('properties',{}).get('$schema',{}).get('const')!=manifest.get('$schema'):errors.append(f"{sp}: schema self-reference does not match manifest")
 except (json.JSONDecodeError,OSError) as e:errors.append(f"{sp}: invalid JSON: {e}")
 return errors
