"""Static behavior contracts for the v0.8.1 public rules.

These tests validate policy placement and required decisions. They do not claim
to test a language model's generated legal advice.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def rule(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


QUALITY = "skills/legal-quality-gate/SKILL.md"
CHECKLIST = "skills/legal-quality-gate/references/checklist.md"
EXPRESSION = "skills/legal-os-unified-intake/references/external-expression-boundary.md"
CONTRACT = "skills/legal-os-contract/SKILL.md"
REPORT = "skills/legal-os-reporting-presentation/SKILL.md"
DELIVERY = "skills/legal-os-file-delivery/SKILL.md"


class V081RuleRegressions(unittest.TestCase):
    def test_repeated_risk_has_one_full_home_but_short_references_remain(self):
        # Fixture: the same risk arrives under situation, analysis and conclusion.
        input_sections = {
            "总体情况": "同一付款风险的完整描述",
            "风险分析": "同一付款风险的完整描述",
            "结论": "同一付款风险的完整描述",
        }
        self.assertEqual(len(input_sections), 3)
        policy = rule(QUALITY)
        self.assertIn("fully state each core fact, risk, reason, evidence chain or legal argument once", policy)
        self.assertIn("Later sections may refer to it briefly", policy)
        self.assertIn("must preserve facts, risks, conditions and actions", policy)
        self.assertEqual(policy.count("semantic deduplication and unique placement"), 1)

    def test_matter_ranking_is_distinct_from_task_risk(self):
        policy = rule(QUALITY)
        for phrase in ("核心风险", "重要风险", "一般提示", "first identify all supported risks", "R0", "R3"):
            self.assertIn(phrase, policy)
        self.assertIn("If no material risk is found", policy)
        self.assertIn("../legal-quality-gate/SKILL.md", rule(CONTRACT))

    def test_no_redline_review_only_and_performance_advice(self):
        policy = rule(CONTRACT)
        self.assertIn("review-only / no-redline", policy)
        self.assertIn("不能或不再修改、来不及修改", policy)
        self.assertIn("不生成修订版或模拟红线", policy)
        self.assertIn("简明审核结论", policy)
        self.assertIn("可执行的履约建议", policy)
        self.assertIn("用户只要其中一种时，只输出所需部分", policy)
        self.assertIn("不得因该模式降低质量门", policy)
        self.assertIn("修订交付时运行红线硬门", policy)
        self.assertIn("仅在拟修订或谈判时形成事项级 negotiation policy", policy)

    def test_finished_word_artifact_has_no_version_or_process_labels_anywhere(self):
        policy = rule(EXPRESSION)
        for surface in ("body", "title", "subtitle", "headers", "footers", "filename", "version label", "attachment names", "contents page", "cover"):
            self.assertIn(surface, policy)
        for label in ("简版", "内部版", "AI生成", "临时", "草稿供讨论", "草案", "送审稿", "修订稿"):
            self.assertIn(label, policy)
        self.assertIn("A finished Word artifact must contain no historical version labels", policy)
        self.assertIn("internal communication or opinions, descriptions of modifications or deletions", policy)
        self.assertIn("in any of these locations", policy)
        self.assertIn("preserve substantive facts and legally necessary procedural dates", policy)
        self.assertNotIn("may remain when its formal purpose", policy)
        self.assertIn("external-expression-boundary.md", rule(DELIVERY))
        self.assertIn("external-expression-boundary.md", rule(QUALITY))

    def test_leadership_risk_report_keeps_adverse_result_and_response_distinct(self):
        policy = rule(REPORT)
        for phrase in ("adverse outcome", "why or under what condition", "concrete response", "owners only when needed", "stages only where real time or procedural stages exist", "conclusion, major risks and decisions first"):
            self.assertIn(phrase, policy)
        self.assertIn("never invent either", policy)
        self.assertIn("actual scheduled actions with supported owners and dates", policy)
        self.assertIn("../legal-quality-gate/SKILL.md", policy)

    def test_ai_image_text_is_not_a_final_chinese_text_path(self):
        # Static fixture: an AI-rendered bitmap containing the final wording
        # must fail the reporting/presentation rule, while vector text is allowed.
        policy = rule(REPORT)
        self.assertIn("must not generate the final Chinese words", policy)
        self.assertIn("SVG/vector text or PPT text", policy)
        self.assertIn("amounts, figures, dates", policy)
        self.assertIn("garbling, wrong characters", policy)

    def test_cost_list_does_not_prove_performance_or_debt(self):
        policy = rule(CHECKLIST)
        for phrase in ("Cost lists", "quotations", "payment requests", "internal statistics", "unilateral statements", "prove only what they record or assert", "actual performance, acceptance or debt"):
            self.assertIn(phrase, policy)
        self.assertEqual(policy.count("Cost lists"), 1)


if __name__ == "__main__":
    unittest.main()
