from __future__ import annotations
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];LAW=ROOT/'skills/cn-law-hub';CASE=ROOT/'skills/cn-case-hub'
class ResearchV070Tests(unittest.TestCase):
 def run_script(self,path,*args,expected=0):
  r=subprocess.run([sys.executable,str(path),*args],capture_output=True,text=True);self.assertEqual(r.returncode,expected,r.stdout+r.stderr);return r
 def test_cn_law_query_builder(self):
  d=json.loads(self.run_script(LAW/'scripts/build_authority_queries.py','合同解除条件','--name','民法典','--article','第五百六十三条').stdout);self.assertTrue(any('flk.npc.gov.cn' in q for q in d['queries']))
 def test_authority_record_validator_accepts_official_record(self):
  rec={'title':'示例规范','authority_type':'law','issuing_body':'全国人民代表大会','document_number':None,'promulgated_date':'2020-05-28','effective_date':'2021-01-01','status':'effective','proposition':'示例命题','source_url':'https://flk.npc.gov.cn/','accessed_at':'2026-08-23','verification_status':'verified-source','limitations':[],'supersedes':[],'superseded_by':[]}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.json';p.write_text(json.dumps({'authorities':[rec]},ensure_ascii=False),encoding='utf-8');self.run_script(LAW/'scripts/validate_authority_records.py',str(p))
 def test_non_official_verified_authority_rejected(self):
  rec={'title':'x','authority_type':'law','issuing_body':'x','document_number':None,'promulgated_date':None,'effective_date':None,'status':'effective','proposition':'x','source_url':'https://example.com/x','accessed_at':'2026-08-23','verification_status':'verified-source','limitations':[]}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.json';p.write_text(json.dumps({'authorities':[rec]},ensure_ascii=False),encoding='utf-8');self.run_script(LAW/'scripts/validate_authority_records.py',str(p),expected=1)
 def test_treaty_record_accepts_official_mfa_source(self):
  rec={'title':'示例条约','authority_type':'treaty','issuing_body':'中华人民共和国外交部','document_number':None,'promulgated_date':None,'effective_date':None,'status':'effective','proposition':'示例条约命题','source_url':'https://treaty.mfa.gov.cn/','accessed_at':'2026-08-24','verification_status':'verified-source','limitations':[],'supersedes':[],'superseded_by':[]}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.json';p.write_text(json.dumps({'authorities':[rec]},ensure_ascii=False),encoding='utf-8');self.run_script(LAW/'scripts/validate_authority_records.py',str(p))
 def test_invalid_authority_type_rejected(self):
  rec={'title':'x','authority_type':'case','issuing_body':'x','document_number':None,'promulgated_date':None,'effective_date':None,'status':'effective','proposition':'x','source_url':'https://www.gov.cn/','accessed_at':'2026-08-24','verification_status':'verified-source','limitations':[]}
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.json';p.write_text(json.dumps({'authorities':[rec]},ensure_ascii=False),encoding='utf-8');self.run_script(LAW/'scripts/validate_authority_records.py',str(p),expected=1)
 def test_cn_law_first_party_boundary(self):self.assertIn('PASS',self.run_script(LAW/'scripts/check_first_party_boundary.py').stdout)
 def test_case_skill_has_dual_axis_and_fork_variables(self):
  s=(CASE/'SKILL.md').read_text(encoding='utf-8');self.assertIn('A/B/C/D',s);self.assertIn('裁判分叉变量',s);self.assertIn('胜诉率',s)
 def test_litigation_has_research_handoff(self):
  s=(ROOT/'skills/legal-os-litigation/SKILL.md').read_text(encoding='utf-8');self.assertIn('decision-fork variable',s);self.assertIn('evidence_gap',s);self.assertIn('A-',s)
 def test_no_legacy_crawler_names_exist(self):
  banned={'court_law_crawler.py','tax_law_crawler.py','moj_law_crawler.py','treaty_crawler.py'};self.assertFalse(any(p.name in banned for p in LAW.rglob('*.py')))
if __name__=='__main__':unittest.main()
