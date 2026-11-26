from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LITIGATION = ROOT / "skills/legal-os-litigation"
TEMPLATE_RUNTIME = ROOT / "skills/legal-os-template-runtime/scripts/template_runtime.py"


class AdvocacyRuleWiringTests(unittest.TestCase):
    """Structural and resolver checks; semantic legal quality remains matter-specific."""

    @classmethod
    def setUpClass(cls):
        cls.skill_path = LITIGATION / "SKILL.md"
        cls.rules_path = LITIGATION / "references/advocacy-drafting-rules.md"
        cls.gate_path = LITIGATION / "references/pleading-quality-gate.md"
        cls.skill = cls.skill_path.read_text(encoding="utf-8")
        cls.rules = cls.rules_path.read_text(encoding="utf-8")
        cls.gate = cls.gate_path.read_text(encoding="utf-8")

    def test_reference_has_one_ordered_a01_to_a12_sequence(self):
        headings = re.findall(r"^##\s+(A\d{2})\b", self.rules, flags=re.MULTILINE)
        self.assertEqual(headings, [f"A{i:02d}" for i in range(1, 13)])
        self.assertIn("document_variant", self.rules)
        self.assertIn("pleading-quality-gate.md", self.rules)

    def test_skill_exposes_four_variants_and_existing_t02_path(self):
        selectors = re.findall(r"^- `([^`]+)`", self.skill, flags=re.MULTILINE)
        expected = {
            "advocacy-brief",
            "pre-hearing-advocacy-opinion",
            "post-hearing-advocacy-brief",
            "supplemental-advocacy-opinion",
        }
        self.assertTrue(expected <= set(selectors))
        manifest = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))
        route = next(item for item in manifest["routes"] if item["id"] == "T-02")
        self.assertIn("pleading", route["intake_types"])
        self.assertEqual(route["executor"]["skill"], "legal-os-litigation")
        self.assertNotIn("advocacy", {item["id"] for item in manifest["routes"]})

    def test_gate_owns_aq_checks_and_rules_reference_it_without_duplicate_headings(self):
        gate_headings = re.findall(r"^###\s+(A-Q[1-4])\b", self.gate, flags=re.MULTILINE)
        self.assertEqual(gate_headings, [f"A-Q{i}" for i in range(1, 5)])
        self.assertIn("Adjudicative Reasoning Test (ART)", self.gate)
        self.assertNotRegex(self.rules, r"^###\s+A-Q[1-4]\b")
        self.assertRegex(self.rules, r"A-Q1[–-]A-Q4")
        self.assertRegex(self.rules, r"pleading-quality-gate\.md")

    def test_a11_mentions_r2_section_confirmation_and_assembly_controls(self):
        block = re.search(r"^## A11\b(?P<body>.*?)(?=^## A12\b)", self.rules, flags=re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(block)
        body = block.group("body").lower()
        for concept in ("r2", "section", "approval", "non-substantive", "reconfirm", "assemble"):
            with self.subTest(concept=concept):
                self.assertIn(concept, body)

    def test_post_hearing_answer_based_default_has_explicit_scope_overrides(self):
        trigger = re.search(
            r"^## Advocacy-document trigger\b(?P<body>.*?)(?=^## Workflow\b)",
            self.skill,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(trigger)
        trigger_body = " ".join(trigger.group("body").lower().split())
        for concept in (
            "defendant/respondent",
            "already been filed",
            "actual oral assertions",
            "late-filed written opinions",
            "explicit whole-case",
            "explicit narrower",
            "supplemental-advocacy-opinion",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, trigger_body)

        a01 = re.search(r"^## A01\b(?P<body>.*?)(?=^## A02\b)", self.rules, flags=re.MULTILINE | re.DOTALL)
        a09 = re.search(r"^## A09\b(?P<body>.*?)(?=^## A10\b)", self.rules, flags=re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(a01)
        self.assertIsNotNone(a09)
        a01_body = " ".join(a01.group("body").lower().split())
        for concept in ("answer as the baseline", "material actual oral assertions", "late-filed written opinions", "whole-case", "narrower"):
            with self.subTest(concept=concept):
                self.assertIn(concept, a01_body)

        a09_body = " ".join(a09.group("body").lower().split())
        for concept in (
            "both opposing-source locators",
            "hearing-record page",
            "late-opinion page/section",
            "evidence and legal consequence",
            "missing or unverified",
            "r2",
            "r8",
            "art",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, a09_body)

        aq1 = re.search(r"^### A-Q1\b(?P<body>.*?)(?=^### A-Q2\b)", self.gate, flags=re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(aq1)
        aq1_body = " ".join(aq1.group("body").lower().split())
        for concept in (
            "already filed",
            "actual oral assertion",
            "late-filed written opinion",
            "each material",
            "both opposing-source locators",
            "whole-case",
            "narrower",
            "affected scope",
        ):
            with self.subTest(concept=concept):
                self.assertIn(concept, aq1_body)

    def test_resolver_holds_exact_advocacy_variant_when_catalogue_has_no_match(self):
        # The candidate does not invent an approved advocacy template. This
        # exercises the real resolver stop condition with a synthetic catalog.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({"templates": []}), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(TEMPLATE_RUNTIME),
                    "resolve",
                    "--document-type",
                    "advocacy-brief",
                    "--skills-root",
                    str(root / "skills"),
                    "--catalog",
                    str(catalog),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "TEMPLATE_REQUIRED")

    def test_resolver_does_not_use_mismatched_civil_answer_for_advocacy_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "catalog.json"
            catalog.write_text(
                json.dumps({"templates": [{"id": "ANSWER", "document_type": "civil-answer"}]}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(TEMPLATE_RUNTIME),
                    "resolve",
                    "--document-type",
                    "advocacy-brief",
                    "--skills-root",
                    str(root / "skills"),
                    "--catalog",
                    str(catalog),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "TEMPLATE_REQUIRED")


if __name__ == "__main__":
    unittest.main()
