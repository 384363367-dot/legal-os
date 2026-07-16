from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_repo import validate_repository


class RepositoryValidationTests(unittest.TestCase):
    def test_current_repository_is_consistent(self) -> None:
        self.assertEqual(validate_repository(ROOT), [])

    def test_broken_bundled_resource_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            skill = root / "skills" / "example-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: example-skill\n"
                "description: Example validation Skill.\n"
                "---\n\n"
                "Run `scripts/missing.py`.\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  default_prompt: "Use $example-skill."\n',
                encoding="utf-8",
            )

            errors = validate_repository(root)

            self.assertTrue(any("scripts/missing.py" in error for error in errors), errors)

    def test_unbundled_named_skill_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            skill = root / "skills" / "example-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: example-skill\n"
                "description: Example validation Skill.\n"
                "---\n\n"
                "Run `legal-os-missing`.\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  default_prompt: "Use $example-skill."\n',
                encoding="utf-8",
            )

            errors = validate_repository(root)

            self.assertTrue(any("unbundled named Skill" in error for error in errors), errors)

    def test_internal_agent_instruction_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            skill = root / "skills" / "example-skill"
            (skill / "agents").mkdir(parents=True)
            (root / "docs").mkdir()
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: example-skill\n"
                "description: Example validation Skill.\n"
                "---\n",
                encoding="utf-8",
            )
            (skill / "agents" / "openai.yaml").write_text(
                'interface:\n  default_prompt: "Use $example-skill."\n',
                encoding="utf-8",
            )
            (root / "docs" / "plan.md").write_text(
                "For Claude: use superpowers:executing-plans.\n",
                encoding="utf-8",
            )

            errors = validate_repository(root)

            self.assertTrue(any("internal agent instruction" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
