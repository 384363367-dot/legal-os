from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/'skills/legal-os-litigation'
class ClaimantStanceRuleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.skill=(ROOT/'SKILL.md').read_text(encoding='utf-8');cls.rules=(ROOT/'references/pleading-drafting-rules.md').read_text(encoding='utf-8');cls.gate=(ROOT/'references/pleading-quality-gate.md').read_text(encoding='utf-8')
 def test_stance_gate_present(self):self.assertIn('pleading_stage',self.skill);self.assertIn('initial-claim stance gate',self.skill);self.assertIn('R1–R16',self.skill)
 def test_negative_controls_present(self):
  for x in ('hypothetical opponent defence','opponent evidence roadmap','adjudicator investigation plan','unverified favourable fact'):self.assertIn(x,self.rules)
 def test_exception_not_absolute_word_ban(self):self.assertIn('actually raised',self.rules);self.assertIn('They do not automatically fail',self.rules)
 def test_internal_analysis_preserved(self):self.assertIn('do not destroy the underlying analysis',self.rules);self.assertIn('preserve useful analysis',self.gate)
 def test_quality_gate_stage_separation(self):self.assertIn('one represented-party stance',self.gate);self.assertIn('have not been mixed into the initial pleading',self.gate)
if __name__=='__main__':unittest.main()
