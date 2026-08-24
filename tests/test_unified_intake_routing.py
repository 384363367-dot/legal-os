from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.validate_routing_scenarios import validate_scenarios
class UnifiedIntakeRoutingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=json.loads((ROOT/'legalos.manifest.json').read_text(encoding='utf-8'));cls.scenarios=json.loads((ROOT/'tests/fixtures/unified_intake_scenarios.json').read_text(encoding='utf-8'))
 def test_sixteen_synthetic_scenarios_pass(self):self.assertEqual(len(self.scenarios),16);self.assertEqual(validate_scenarios(self.manifest,self.scenarios),[])
 def test_case_and_current_law_both_route_t05(self):
  ids={x['id']:x for x in self.scenarios};self.assertEqual(ids['case-research']['expected_decision']['primary_route'],'T-05');self.assertEqual(ids['current-law-research']['expected_decision']['primary_route'],'T-05')
 def test_g3_without_stop_rejected(self):
  s=copy.deepcopy(self.scenarios[-1]);s['expected_decision']['status']='ready';self.assertTrue(any('G3' in e for e in validate_scenarios(self.manifest,[s])))
 def test_external_action_requires_authorization(self):
  s=copy.deepcopy(next(x for x in self.scenarios if x['id']=='formal-letter-send-request'));s['expected_decision']['status']='ready';self.assertTrue(any('external actions require' in e for e in validate_scenarios(self.manifest,[s])))
 def test_mixed_task_covers_every_type(self):
  s=copy.deepcopy(next(x for x in self.scenarios if x['id']=='contract-with-data-check'));s['expected_decision']['auxiliary_routes']=[];self.assertTrue(any('not covered' in e for e in validate_scenarios(self.manifest,[s])))
if __name__=='__main__':unittest.main()
