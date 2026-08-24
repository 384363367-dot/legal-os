from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "legal-os-unified-intake" / "references" / "office-source-policy.md"


class OfficeSourcePolicyTests(unittest.TestCase):
    def test_source_first_conditional_visual_modes_exist(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        required = [
            "visual_check_mode",
            "`off`",
            "`conditional`",
            "正式提交、正式对外或要求可直接使用，不单独构成自动渲染理由",
            "ENVIRONMENT_LIMITATION",
            "不得把平台名称写死为长期规则",
            "不得声称“视觉 QA 已通过”",
        ]
        self.assertEqual([token for token in required if token not in text], [])
        self.assertNotIn("`final`", text)

    def test_no_downstream_default_render_override_in_skill_entrypoints(self) -> None:
        targets = [
            "legal-os-unified-intake/SKILL.md",
            "legal-os-contract/SKILL.md",
            "legal-os-correspondence/SKILL.md",
            "legal-os-business-communication/SKILL.md",
            "legal-os-reporting-presentation/SKILL.md",
            "legal-os-matter-memory/SKILL.md",
            "legal-os-litigation/SKILL.md",
        ]
        retired = ["默认必须渲染", "must always render", "必须全量渲染"]
        hits = []
        for relative in targets:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in retired:
                if token in text:
                    hits.append(f"{relative}: {token}")
        self.assertEqual(hits, [])

    def test_explicit_no_render_remains_hard_stop(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        self.assertIn("属于硬停止", text)
        self.assertIn("任何下游 Skill 或辅助工具的“必须渲染”规则均不得覆盖", text)


if __name__ == "__main__":
    unittest.main()
