from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/'skills/legal-os-litigation'
class ClaimantStanceRuleTests(unittest.TestCase):
 """Static policy-text checks; these do not assert runtime behavior or legal correctness."""
 @classmethod
 def setUpClass(cls):cls.skill=(ROOT/'SKILL.md').read_text(encoding='utf-8');cls.rules=(ROOT/'references/pleading-drafting-rules.md').read_text(encoding='utf-8');cls.gate=(ROOT/'references/pleading-quality-gate.md').read_text(encoding='utf-8');cls.correspondence=(ROOT.parent/'legal-os-correspondence/SKILL.md').read_text(encoding='utf-8')
 def test_stance_gate_present(self):self.assertIn('pleading_stage',self.skill);self.assertIn('initial-claim stance gate',self.skill);self.assertIn('R1–R16',self.skill)
 def test_negative_controls_present(self):
  for x in ('hypothetical opponent defence','opponent evidence roadmap','adjudicator investigation plan','unverified favourable fact'):self.assertIn(x,self.rules)
 def test_exception_not_absolute_word_ban(self):self.assertIn('actually raised',self.rules);self.assertIn('They do not automatically fail',self.rules)
 def test_internal_analysis_preserved(self):self.assertIn('do not destroy the underlying analysis',self.rules);self.assertIn('preserve useful analysis',self.gate)
 def test_quality_gate_stage_separation(self):self.assertIn('one represented-party stance',self.gate);self.assertIn('have not been mixed into the initial pleading',self.gate)
 def test_litigation_rules_do_not_expand_general_nonlitigation_letters(self):
  self.assertIn('General non-litigation lawyer letters, payment notices and claim letters remain with their existing correspondence workflow',self.rules)
  self.assertIn('directly serving an identified case',self.rules)
  self.assertIn('two-stage analysis, dialogue confirmation and drafting sequence',self.correspondence)
 def test_stage_one_analysis_covers_claim_elements_evidence_amounts_and_answer_issues(self):
  for x in ('actual supplied materials and latest verifiable matter status','represented party, parties\' relationship, procedural position and current objective','actively identify additional materially supported claims, defences, demands, procedural routes or compatible alternatives','requested or proposed claim, defence, demand or response','relief or response and amount','relevant contract terms and current verified legal basis','supporting or adverse evidence by name, source and proof function','source and formula for amounts and dates','material unverified facts or gaps and their effect','recommended route and reasons'):
   self.assertIn(x,self.rules)
  self.assertIn('item by item, as R4 requires',self.rules)
 def test_small_gaps_allow_unrelated_analysis_without_invented_due_dates(self):
  self.assertIn('Do not let a small or non-dispositive gap stop analysis of unrelated issues',self.rules)
  self.assertIn('do not invent a due date, overdue start date or interest period',self.rules)
 def test_initial_task_request_does_not_confirm_recommended_strategy(self):
  self.assertIn('A broad initial request such as “I want to sue” or “prepare a complaint” states the task; by itself it does not confirm a route or relief later recommended from the materials.',self.rules)
  self.assertIn('obtain the user\'s clear choice in the conversation',self.rules)
  self.assertIn('without asking again for permission to draft',self.rules)
  self.assertIn('professional source and law verification remains the workflow\'s responsibility',self.rules)
 def test_drafting_prerequisites_and_requested_artifacts(self):
  for text in ('An empty table, headings alone, or unanalyzed pending labels do not satisfy', 'submit the whole-document structure card', "obtain the user's confirmation", 'Submit each section separately', 'only after every section is confirmed', "user's explicit request to draft first"):
   self.assertIn(text,self.rules)
  self.assertIn('actual requested or verified procedural requirement',self.rules)
  self.assertIn('resolve --with-evidence-catalog',self.rules)
  self.assertIn('A missing unrequested catalogue template does not block',self.rules)
 def test_existing_matter_reconfirmation_and_reverification_are_affected_only(self):
  self.assertIn('edits that do not materially change a claim, defence, amount, deadline, right or position',self.rules)
  self.assertIn('renewed analysis and confirmation only for the affected issue',self.rules)
  self.assertIn('preserve unaffected verified work',self.rules)
  self.assertIn('Reopen only affected verification',self.rules)
 def test_light_deliverable_check_preserves_quality_and_authorization_gates(self):
  self.assertIn('existing pleading quality gate with an independent review',self.rules)
  self.assertIn('Existing R1–R16, external-expression limits, template requirements, release labels and quality gates continue to apply',self.rules)
  self.assertIn('does not replace any required formal sign-off or authorize sending, service, filing, signing, publication or other external action',self.rules)
  self.assertIn('Missing external-action authorization blocks sending, service, filing or signing; it does not by itself block analysis or preparation of the draft within the user\'s requested scope',self.correspondence)
if __name__=='__main__':unittest.main()
