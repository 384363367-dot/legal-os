from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CAT = SKILLS / "legal-os-template-runtime/references/template-catalog.json"
RUN = SKILLS / "legal-os-template-runtime/scripts/template_runtime.py"


class TemplateRuntimeTests(unittest.TestCase):
    def resolve(self, *args):
        process = subprocess.run(
            [sys.executable, str(RUN), "resolve", "--skills-root", str(SKILLS), *args],
            capture_output=True, text=True,
        )
        return process.returncode, json.loads(process.stdout)

    def fixture(self, directory, *, paired=True, status="approved", digest=None, exists=True):
        root = Path(directory)
        source = root / "template.docx"
        if exists:
            source.write_bytes(b"synthetic template")
        entry = {
            "id": "TEST-ANSWER", "document_type": "civil-answer",
            "skill": "legal-os-litigation", "relative_path": str(source), "priority": 100,
            "status": status, "sha256": digest or hashlib.sha256(b"synthetic template").hexdigest(),
            "paired_document_type": "evidence-catalog",
        }
        entries = [entry]
        if paired:
            entries.append({**entry, "id": "TEST-CATALOGUE", "document_type": "evidence-catalog"})
        catalog = root / "catalog.json"
        catalog.write_text(json.dumps({"templates": entries}))
        return catalog, source, entries

    def test_catalog_has_hash_bound_assets(self):
        catalog = json.loads(CAT.read_text(encoding="utf-8"))
        types = {item["document_type"] for item in catalog["templates"]}
        self.assertTrue({"civil-complaint", "civil-answer", "evidence-catalog"} <= types)
        for entry in catalog["templates"]:
            source = SKILLS / entry["skill"] / entry["relative_path"]
            self.assertTrue(source.is_file(), entry["id"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), entry["sha256"], entry["id"])

    def test_all_office_assets_are_valid_zip_packages(self):
        for path in SKILLS.glob("*/assets/templates/*"):
            if path.suffix.lower() in {".docx", ".xlsx"}:
                self.assertTrue(zipfile.is_zipfile(path), str(path))

    def test_memory_candidate_diff_resolves(self):
        code, result = self.resolve("--document-type", "memory-update-candidate-diff")
        self.assertEqual(code, 0, result)
        self.assertEqual(result["template_id"], "MEMORY-CANDIDATE-DIFF-V1.12")

    def test_standalone_ignores_missing_optional_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, _ = self.fixture(directory, paired=False)
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog))
            self.assertEqual(code, 0, result)
            self.assertNotIn("paired_path", result)

    def test_explicit_pair_is_selected(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, _ = self.fixture(directory)
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog), "--with-evidence-catalog")
            self.assertEqual(code, 0, result)
            self.assertEqual(result["paired_document_type"], "evidence-catalog")
            self.assertTrue(Path(result["paired_path"]).is_file())

    def test_required_pair_missing_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, _ = self.fixture(directory, paired=False)
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog), "--with-evidence-catalog")
            self.assertEqual(code, 2)
            self.assertEqual(result["required_by_document_type"], "civil-answer")

    def test_bad_hash_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, _ = self.fixture(directory, digest="0" * 64)
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog))
            self.assertEqual((code, result["status"]), (3, "TEMPLATE_INTEGRITY_FAIL"))

    def test_missing_path_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, _ = self.fixture(directory, exists=False)
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog))
            self.assertEqual((code, result["status"]), (3, "TEMPLATE_INTEGRITY_FAIL"))

    def test_candidate_is_not_approved(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, _ = self.fixture(directory, status="candidate")
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog))
            self.assertEqual((code, result["status"]), (2, "TEMPLATE_REQUIRED"))

    def test_legacy_nonlitigation_candidate_keeps_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, entries = self.fixture(directory, status="candidate")
            entries[0]["skill"] = "legal-os-correspondence"
            entries[0]["document_type"] = "lawyer-letter"
            catalog.write_text(json.dumps({"templates": entries}))
            code, result = self.resolve("--document-type", "lawyer-letter", "--catalog", str(catalog))
            self.assertEqual((code, result["template_id"]), (0, "TEST-ANSWER"))
            entries[0]["approval_state"] = "candidate"
            catalog.write_text(json.dumps({"templates": entries}))
            code, result = self.resolve("--document-type", "lawyer-letter", "--catalog", str(catalog))
            self.assertEqual((code, result["status"]), (2, "TEMPLATE_REQUIRED"))

    def test_missing_registered_hash_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, _, entries = self.fixture(directory)
            del entries[0]["sha256"]
            catalog.write_text(json.dumps({"templates": entries}))
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog))
            self.assertEqual((code, result["status"]), (3, "TEMPLATE_INTEGRITY_FAIL"))

    def test_private_overlay_requires_approval_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, source, _ = self.fixture(directory)
            private = Path(directory) / "private.json"
            entry = {"id": "PRIVATE", "document_type": "civil-answer", "path": str(source),
                     "priority": 200, "approval_state": "candidate"}
            private.write_text(json.dumps({"templates": [entry]}))
            args = ["--document-type", "civil-answer", "--catalog", str(catalog), "--private-catalog", str(private)]
            code, result = self.resolve(*args)
            self.assertEqual((code, result["template_id"]), (0, "TEST-ANSWER"))
            entry["approval_state"] = "approved"
            private.write_text(json.dumps({"templates": [entry]}))
            code, result = self.resolve(*args)
            self.assertEqual((code, result["status"]), (3, "TEMPLATE_INTEGRITY_FAIL"))
            entry["sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            private.write_text(json.dumps({"templates": [entry]}))
            code, result = self.resolve(*args)
            self.assertEqual((code, result["template_id"]), (0, "PRIVATE"))

    def test_explicit_user_template_needs_no_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog, source, _ = self.fixture(directory, paired=False, status="candidate")
            code, result = self.resolve("--document-type", "civil-answer", "--catalog", str(catalog), "--explicit-template", str(source))
            self.assertEqual((code, result["template_scope"]), (0, "explicit-user-template"))

    def test_unknown_template_stops(self):
        code, result = self.resolve("--document-type", "unknown-form")
        self.assertEqual((code, result["status"]), (2, "TEMPLATE_REQUIRED"))


if __name__ == "__main__":
    unittest.main()
