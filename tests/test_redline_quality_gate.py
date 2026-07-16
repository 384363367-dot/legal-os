from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "skills" / "legal-os-contract" / "scripts" / "redline_quality_gate.py"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def document_xml(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'


def paragraph(text: str) -> str:
    return f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>"


def write_docx(path: Path, document: str, *, track_revisions: bool = False) -> None:
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
    relationships = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    settings = f'<?xml version="1.0" encoding="UTF-8"?><w:settings xmlns:w="{W}">{"<w:trackRevisions/>" if track_revisions else ""}</w:settings>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/settings.xml", settings)


class RedlineQualityGateTests(unittest.TestCase):
    def run_gate(
        self, *, tracked: bool, clean_text: str = "新文"
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            original = directory / "original.docx"
            redline = directory / "redline.docx"
            clean = directory / "clean.docx"
            write_docx(original, document_xml(paragraph("原文")))
            redline_body = (
                '<w:p><w:del w:author="法务"><w:r><w:delText>原</w:delText></w:r></w:del>'
                '<w:ins w:author="法务"><w:r><w:t>新</w:t></w:r></w:ins>'
                '<w:r><w:t>文</w:t></w:r></w:p>'
            )
            write_docx(redline, document_xml(redline_body), track_revisions=tracked)
            write_docx(clean, document_xml(paragraph(clean_text)))
            environment = os.environ.copy()
            environment["PYTHONUTF8"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    str(GATE),
                    "--original",
                    str(original),
                    "--redline",
                    str(redline),
                    "--clean",
                    str(clean),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
            )
            return result, json.loads(result.stdout)

    def test_valid_granular_redline_passes(self) -> None:
        result, report = self.run_gate(tracked=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["status"], "PASS")

    def test_missing_track_revisions_fails_closed(self) -> None:
        result, report = self.run_gate(tracked=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("trackRevisions" in error for error in report["errors"]))

    def test_clean_copy_mismatch_fails_closed(self) -> None:
        result, report = self.run_gate(tracked=True, clean_text="不一致")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
