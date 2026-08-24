import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V070GovernanceTests(unittest.TestCase):
    def test_main_artifacts_and_official_license_hashes_are_locked(self):
        expected = {
            "LICENSE": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
            "legal-os-banner.png": "0c92cbc57c2075ffa7d6abab6661ade15afde659432bbd8db2698839f745a375",
            "docs/plans/2026-07-15-repository-consistency-repair.md": "68518b9442bd62cf5bdac35e4c938786476a06a4cbd9624bbac9cd5e9c9d1bf0",
        }
        for relative_path, expected_sha256 in expected.items():
            with self.subTest(path=relative_path):
                actual = hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()
                self.assertEqual(actual, expected_sha256)

    def test_litigation_handoff_term_is_normalized(self):
        skill = (ROOT / "skills/legal-os-litigation/SKILL.md").read_text(encoding="utf-8")
        reference = (
            ROOT / "skills/legal-os-litigation/references/case-research-handoff.md"
        ).read_text(encoding="utf-8")
        old_term = "argument" + "/" + "action"
        self.assertIn("argument/procedural action", skill)
        self.assertIn("Argument / procedural action", reference)
        self.assertNotIn(old_term, skill)

    def test_open_source_boundary_discloses_v070_research_change(self):
        boundary = (ROOT / "OPEN_SOURCE_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("## v0.7.0 first-party research boundary", boundary)
        self.assertIn("### Change disclosure", boundary)
        self.assertIn("do not bypass the control", boundary)
        self.assertIn("does not claim ownership", boundary)

    def test_changelog_discloses_license_and_boundary_repairs(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("不是静默替换", changelog)
        self.assertIn("OPEN_SOURCE_BOUNDARY.md", changelog)
        self.assertIn("legal-os-banner.png", changelog)

    def test_release_documents_disclose_governance_repairs(self):
        for filename in ("UPGRADE_REPORT_v0.7.0.md", "RELEASE_NOTES_v0.7.0.md"):
            with self.subTest(filename=filename):
                text = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn("LICENSE", text)
                self.assertIn("OPEN_SOURCE_BOUNDARY.md", text)
                self.assertIn("argument/procedural action", text)
                self.assertIn("legal-os-banner.png", text)


if __name__ == "__main__":
    unittest.main()
