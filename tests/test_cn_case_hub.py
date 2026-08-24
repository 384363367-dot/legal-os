from __future__ import annotations
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SKILL=ROOT/'skills/cn-case-hub';FIX=ROOT/'tests/fixtures/cn-case-hub/competition_cases.json'
class CnCaseHubTests(unittest.TestCase):
 def run_script(self,script,*args,expected=0):
  r=subprocess.run([sys.executable,str(SKILL/'scripts'/script),*args],capture_output=True,text=True);self.assertEqual(r.returncode,expected,r.stdout+r.stderr);return r
 def test_legacy_official_fixture_validates(self):self.assertIn('4 case record(s) validated',self.run_script('validate_case_records.py',str(FIX)).stdout)
 def test_query_builder_generates_adverse_and_multiple_queries(self):
  d=json.loads(self.run_script('build_official_queries.py','竞业限制纠纷','--fact','实际产品不同','--court-language','竞争关系').stdout);self.assertGreaterEqual(len(d['queries']),10);self.assertTrue(any('不予支持' in q for q in d['queries']))
 def test_v070_matrix_record_validates(self):
  d=json.loads(FIX.read_text(encoding='utf-8'));r=d['cases'][0];r['relevance_grade']='A';r['direction_grade']='±';r['matrix_grade']='A±';r['procedure_chain']=[];r['decisive_variables']=['实际经营内容'];
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x.json';p.write_text(json.dumps({'cases':[r]},ensure_ascii=False),encoding='utf-8');self.run_script('validate_case_records.py',str(p))
 def test_inconsistent_matrix_rejected(self):
  d=json.loads(FIX.read_text(encoding='utf-8'));r=d['cases'][0];r['relevance_grade']='A';r['direction_grade']='-';r['matrix_grade']='B-'
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'x.json';p.write_text(json.dumps({'cases':[r]},ensure_ascii=False),encoding='utf-8');o=self.run_script('validate_case_records.py',str(p),expected=1);self.assertIn('matrix_grade',o.stderr)
 def test_first_party_boundary(self):self.assertIn('PASS',self.run_script('check_first_party_boundary.py').stdout)
if __name__=='__main__':unittest.main()
