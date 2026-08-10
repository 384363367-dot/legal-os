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


def comment_xml(text: str) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><w:comments xmlns:w="{W}">'
        f'<w:comment w:id="0" w:author="法务"><w:p><w:r><w:t>{text}</w:t></w:r></w:p>'
        "</w:comment></w:comments>"
    )


def write_docx(
    path: Path,
    document: str,
    *,
    track_revisions: bool = False,
    comments: str | None = None,
    comment_reference: bool = False,
) -> None:
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>'
    relationships = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    settings = f'<?xml version="1.0" encoding="UTF-8"?><w:settings xmlns:w="{W}">{"<w:trackRevisions/>" if track_revisions else ""}</w:settings>'
    if comment_reference:
        document = document.replace(
            "</w:p>",
            '<w:r><w:commentReference w:id="0"/></w:r></w:p>',
            1,
        )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/settings.xml", settings)
        if comments is not None:
            archive.writestr("word/comments.xml", comments)


class RedlineQualityGateTests(unittest.TestCase):
    def run_gate(
        self, *, tracked: bool, clean_text: str = "新文"
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        redline_body = (
            '<w:p><w:del w:author="法务"><w:r><w:delText>原</w:delText></w:r></w:del>'
            '<w:ins w:author="法务"><w:r><w:t>新</w:t></w:r></w:ins>'
            '<w:r><w:t>文</w:t></w:r></w:p>'
        )
        return self.run_gate_bodies(
            document_xml(paragraph("原文")),
            document_xml(redline_body),
            document_xml(paragraph(clean_text)),
            tracked=tracked,
        )

    def run_gate_bodies(
        self,
        original_document: str,
        redline_document: str,
        clean_document: str,
        *,
        tracked: bool,
        comment_text: str | None = None,
        comment_reference: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            original = directory / "original.docx"
            redline = directory / "redline.docx"
            clean = directory / "clean.docx"
            write_docx(original, original_document)
            write_docx(
                redline,
                redline_document,
                track_revisions=tracked,
                comments=comment_xml(comment_text) if comment_text is not None else None,
                comment_reference=comment_reference,
            )
            write_docx(clean, clean_document)
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

    def test_illegal_whole_paragraph_insertion_fails_closed(self) -> None:
        illegal = (
            paragraph("原文")
            + '<w:ins w:author="法务"><w:p><w:r><w:t>新增段</w:t></w:r></w:p></w:ins>'
        )
        result, report = self.run_gate_bodies(
            document_xml(paragraph("原文")),
            document_xml(illegal),
            document_xml(paragraph("原文") + paragraph("新增段")),
            tracked=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("illegal whole-paragraph insertion" in error for error in report["errors"]))

    def test_paragraph_mark_insertion_reject_view_passes(self) -> None:
        paragraph_mark_insertion = (
            '<w:p><w:pPr><w:rPr><w:ins w:id="3" w:author="法务"/></w:rPr></w:pPr>'
            '<w:ins w:id="4" w:author="法务"><w:r><w:t>新增段</w:t></w:r></w:ins></w:p>'
        )
        inline_redline = (
            '<w:p><w:del w:author="法务"><w:r><w:delText>原</w:delText></w:r></w:del>'
            '<w:ins w:author="法务"><w:r><w:t>新</w:t></w:r></w:ins>'
            '<w:r><w:t>文</w:t></w:r></w:p>'
        )
        result, report = self.run_gate_bodies(
            document_xml(paragraph("原文")),
            document_xml(paragraph_mark_insertion + inline_redline),
            document_xml(paragraph("新增段") + paragraph("新文")),
            tracked=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["source_matches_rejected_view"])
        self.assertTrue(report["accepted_view_matches_clean"])

    def test_unanchored_comment_fails_closed(self) -> None:
        result, report = self.run_gate_bodies(
            document_xml(paragraph("原文")),
            document_xml(
                '<w:p><w:del w:author="法务"><w:r><w:delText>原</w:delText></w:r></w:del>'
                '<w:ins w:author="法务"><w:r><w:t>新</w:t></w:r></w:ins>'
                '<w:r><w:t>文</w:t></w:r></w:p>'
            ),
            document_xml(paragraph("新文")),
            tracked=True,
            comment_text="请确认付款日期",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("comment IDs/references" in error for error in report["errors"]))

    def test_overlong_comment_fails_closed(self) -> None:
        result, report = self.run_gate_bodies(
            document_xml(paragraph("原文")),
            document_xml(
                '<w:p><w:del w:author="法务"><w:r><w:delText>原</w:delText></w:r></w:del>'
                '<w:ins w:author="法务"><w:r><w:t>新</w:t></w:r></w:ins>'
                '<w:r><w:t>文</w:t></w:r></w:p>'
            ),
            document_xml(paragraph("新文")),
            tracked=True,
            comment_text="请确认" + "字" * 51,
            comment_reference=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("exceeds 50 chars" in error for error in report["errors"]))

    def test_multi_item_comment_fails_closed(self) -> None:
        result, report = self.run_gate_bodies(
            document_xml(paragraph("原文")),
            document_xml(
                '<w:p><w:del w:author="法务"><w:r><w:delText>原</w:delText></w:r></w:del>'
                '<w:ins w:author="法务"><w:r><w:t>新</w:t></w:r></w:ins>'
                '<w:r><w:t>文</w:t></w:r></w:p>'
            ),
            document_xml(paragraph("新文")),
            tracked=True,
            comment_text="请确认是否付款及是否验收？",
            comment_reference=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(any("multiple independent confirm items" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
