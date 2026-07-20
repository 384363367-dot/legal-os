from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
RUNTIME = SKILLS / "legal-os-template-runtime" / "scripts" / "template_runtime.py"
CATALOG = SKILLS / "legal-os-template-runtime" / "references" / "template-catalog.json"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def run_runtime(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNTIME), *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as package:
        root = ET.fromstring(package.read("word/document.xml"))
    return "".join(node.text or "" for node in root.findall(f".//{{{W}}}t"))


class TemplateRuntimeTests(unittest.TestCase):
    def test_catalog_has_24_hash_bound_existing_assets(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["templates"]), 24)
        for item in catalog["templates"]:
            path = SKILLS / item["skill"] / item["relative_path"]
            self.assertTrue(path.is_file(), item["id"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"], item["id"])

    def test_changed_existing_litigation_templates_record_supersession(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        by_type = {item["document_type"]: item for item in catalog["templates"]}
        self.assertEqual(by_type["arbitration-application"]["supersedes"], "LIT-ARB-APPLICATION-V1.5")
        self.assertEqual(by_type["arbitration-answer"]["supersedes"], "LIT-ARB-ANSWER-V1.5")
        self.assertEqual(by_type["litigation-format-guide"]["supersedes"], "LIT-FORMAT-GUIDE-V1.5")

    def test_resolves_civil_complaint(self) -> None:
        result = run_runtime("resolve", "--document-type", "civil-complaint", "--skills-root", str(SKILLS))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "SELECTED")
        self.assertEqual(payload["template_id"], "LIT-CIV-COMPLAINT-V1.5")
        self.assertEqual(payload["paired_document_type"], "evidence-catalog")
        self.assertEqual(payload["paired_template_id"], "LIT-EVIDENCE-CATALOG-V1.5")
        self.assertTrue(Path(payload["paired_path"]).is_file())

    def test_resolves_labor_answer_with_paired_evidence_catalog(self) -> None:
        result = run_runtime("resolve", "--document-type", "labor-arbitration-answer", "--skills-root", str(SKILLS))
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["template_id"], "LIT-LABOR-ANSWER-V1.5.1")
        self.assertEqual(payload["paired_template_id"], "LIT-EVIDENCE-CATALOG-V1.5")

    def test_all_pleadings_declare_pair_and_omit_evidence_source_chapter(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        pleading_types = {
            "civil-complaint", "civil-answer", "arbitration-application", "arbitration-answer",
            "labor-arbitration-application", "labor-arbitration-answer",
        }
        entries = [item for item in catalog["templates"] if item["document_type"] in pleading_types]
        self.assertEqual({item["document_type"] for item in entries}, pleading_types)
        for item in entries:
            self.assertEqual(item.get("paired_document_type"), "evidence-catalog", item["id"])
            text = docx_text(SKILLS / item["skill"] / item["relative_path"])
            self.assertNotIn("证据和证据来源", text, item["id"])

    def test_labor_templates_do_not_request_arbitration_costs(self) -> None:
        for filename in ("劳动人事争议仲裁申请书_标准模板.docx", "劳动人事争议仲裁答辩状_标准模板.docx"):
            text = docx_text(SKILLS / "legal-os-litigation" / "assets" / "templates" / filename)
            self.assertNotIn("仲裁费用", text, filename)
            self.assertNotIn("仲裁费由", text, filename)

    def test_labor_answer_uses_placeholders_and_keeps_flexible_structure(self) -> None:
        text = docx_text(SKILLS / "legal-os-litigation" / "assets" / "templates" / "劳动人事争议仲裁答辩状_标准模板.docx")
        for required in ("一、答辩请求", "二、答辩意见", "三、事实与理由", "四、综合意见"):
            self.assertIn(required, text)
        self.assertIn("〔单位名称或姓名〕", text)
        self.assertNotRegex(text, r"\d{5,}")
        self.assertNotRegex(text, r"人民币\s*\d")

    def test_missing_template_stops(self) -> None:
        result = run_runtime("resolve", "--document-type", "unknown-form", "--skills-root", str(SKILLS))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "TEMPLATE_REQUIRED")

    def test_private_organization_template_overrides_generic(self) -> None:
        public_template = SKILLS / "legal-os-correspondence" / "assets" / "templates" / "催款及履约通知函_标准模板.docx"
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "private.json"
            catalog.write_text(json.dumps({
                "schema_version": "1.0.0",
                "templates": [{
                    "id": "PRIVATE-EXAMPLE-PAYMENT",
                    "document_type": "payment-performance-notice",
                    "organization": "Example Organization",
                    "path": str(public_template),
                    "sha256": hashlib.sha256(public_template.read_bytes()).hexdigest(),
                    "priority": 200,
                    "approval_state": "approved",
                    "font_profile": "example-private"
                }]
            }), encoding="utf-8")
            result = run_runtime(
                "resolve", "--document-type", "payment-performance-notice",
                "--organization", "Example Organization", "--skills-root", str(SKILLS),
                "--private-catalog", str(catalog)
            )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["template_id"], "PRIVATE-EXAMPLE-PAYMENT")
        self.assertEqual(payload["template_scope"], "approved-private-template")

    def test_registered_hash_mismatch_stops(self) -> None:
        source = json.loads(CATALOG.read_text(encoding="utf-8"))
        source["templates"] = [dict(source["templates"][0], sha256="0" * 64)]
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "bad.json"
            catalog.write_text(json.dumps(source), encoding="utf-8")
            result = run_runtime(
                "resolve", "--document-type", "civil-complaint", "--skills-root", str(SKILLS),
                "--catalog", str(catalog)
            )
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["status"], "TEMPLATE_INTEGRITY_FAIL")

    def test_docx_audit_allows_placeholders_only_for_draft(self) -> None:
        template = SKILLS / "legal-os-litigation" / "assets" / "templates" / "民事起诉状_标准模板.docx"
        draft = run_runtime("audit-docx", "--template", str(template), "--output", str(template), "--allow-placeholders")
        self.assertEqual(draft.returncode, 0, draft.stderr + draft.stdout)
        final = run_runtime("audit-docx", "--template", str(template), "--output", str(template))
        self.assertEqual(final.returncode, 5)
        self.assertIn("placeholders", " ".join(json.loads(final.stdout)["issues"]))


if __name__ == "__main__":
    unittest.main()
