from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class NativeOfficePolicyTests(unittest.TestCase):
 def test_policy_is_source_first_and_conditional(self):
  p=(ROOT/'docs/native-office-quality-gate.md').read_text(encoding='utf-8')
  for token in ('Structured source inspection','`off` or `conditional`','status alone is not a trigger','ENVIRONMENT_LIMITATION','actual content, structure, privacy or authorization blockers'):self.assertIn(token,p)
 def test_unified_intake_has_conditional_visual_modes(self):
  s=(ROOT/'skills/legal-os-unified-intake/references/office-source-policy.md').read_text(encoding='utf-8')
  for token in ('`off`','`conditional`','正式提交、正式对外或要求可直接使用，不单独构成自动渲染理由'):self.assertIn(token,s)
  self.assertNotIn('`final`',s)
 def test_no_default_unapproved_headless_converter_instruction(self):
  hits=[]
  for base in (ROOT/'docs',ROOT/'skills'):
   for p in base.rglob('*.md'):
    t=p.read_text(encoding='utf-8',errors='ignore').lower()
    if 'libreoffice' in t and 'not' not in t and 'do not' not in t:hits.append(str(p))
  self.assertEqual(hits,[])
if __name__=='__main__':unittest.main()
