#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_ROOT / "scripts"
GATE = SCRIPT_DIR / "redline_quality_gate.py"
sys.path.insert(0, str(SCRIPT_DIR))
import redline_quality_gate as gate  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def run(text: str) -> str:
    return f"<w:r><w:t>{esc(text)}</w:t></w:r>"


def insertion(text: str, revision_id: int = 2) -> str:
    return f'<w:ins w:id="{revision_id}" w:author="法务" w:date="2026-07-14T00:00:00Z">{run(text)}</w:ins>'


def deletion(text: str, revision_id: int = 1) -> str:
    return f'<w:del w:id="{revision_id}" w:author="法务" w:date="2026-07-14T00:00:00Z"><w:r><w:delText>{esc(text)}</w:delText></w:r></w:del>'


def historical_insertion(text: str, revision_id: int = 40, author: str = "legal") -> str:
    return f'<w:ins w:id="{revision_id}" w:author="{esc(author)}" w:date="2026-07-01T00:00:00Z">{run(text)}</w:ins>'


def paragraph(inner: str) -> str:
    return f"<w:p>{inner}</w:p>"


def write_docx(path: Path, paragraphs: list[str], *, track: bool = False, point_comment: bool = False, orphan_comment: bool = False, extra_parts: dict[str, str] | None = None) -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""
    reference = ""
    comments = None
    if point_comment:
        reference = '<w:r><w:commentReference w:id="0"/></w:r>'
        comments = f'<?xml version="1.0" encoding="UTF-8"?><w:comments xmlns:w="{W}"><w:comment w:id="0" w:author="法务"><w:p>{run("测试批注")}</w:p></w:comment></w:comments>'
    elif orphan_comment:
        comments = f'<?xml version="1.0" encoding="UTF-8"?><w:comments xmlns:w="{W}"><w:comment w:id="0" w:author="法务"><w:p>{run("孤立批注")}</w:p></w:comment></w:comments>'
    body = "".join(paragraphs)
    if reference and paragraphs:
        body = body.replace("</w:p>", reference + "</w:p>", 1)
    document = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>{body}<w:sectPr/></w:body></w:document>'
    settings = f'<?xml version="1.0" encoding="UTF-8"?><w:settings xmlns:w="{W}">{"<w:trackRevisions/>" if track else ""}</w:settings>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/settings.xml", settings)
        if comments is not None:
            archive.writestr("word/comments.xml", comments)
        for name, content in (extra_parts or {}).items():
            archive.writestr(name, content)


class RedlineGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original = self.root / "original.docx"
        self.redline = self.root / "redline.docx"
        self.report = self.root / "report.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, expected_comments: int | None = None):
        command = [sys.executable, str(GATE), "--original", str(self.original), "--redline", str(self.redline), "--out-json", str(self.report)]
        if expected_comments is not None:
            command.extend(["--expected-comments", str(expected_comments)])
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        return completed, json.loads(self.report.read_text(encoding="utf-8"))

    def make_short_valid(self, *, untracked_prefix: str = "", **options) -> None:
        write_docx(self.original, [paragraph(run("付款期限为三十日。"))])
        write_docx(self.redline, [paragraph(run(untracked_prefix + "付款期限为") + deletion("三十") + insertion("十五") + run("日。"))], track=True, **options)

    def make_long_valid(self) -> None:
        added = "乙方累计赔偿责任总额以本合同已支付价款总额为限。"
        write_docx(self.original, [paragraph(run("本合同生效。"))])
        write_docx(self.redline, [paragraph(run("本合同生效。") + insertion(added))], track=True)

    def test_short_character_level_redline_passes(self) -> None:
        self.make_short_valid(); completed, report = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr); self.assertEqual(report["status"], "PASS")

    def test_historical_revision_is_preserved(self) -> None:
        history = historical_insertion("历史修订")
        write_docx(self.original, [paragraph(run("条款") + history)])
        write_docx(
            self.redline,
            [paragraph(run("条款") + history + insertion("新增", revision_id=41))],
            track=True,
        )
        completed, report = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["status"], "PASS")

    def test_accepting_historical_revision_fails(self) -> None:
        history = historical_insertion("历史修订")
        write_docx(self.original, [paragraph(run("条款") + history)])
        write_docx(
            self.redline,
            [paragraph(run("条款历史修订") + insertion("新增", revision_id=41))],
            track=True,
        )
        completed, report = self.invoke()
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("historical tracked revisions changed" in x for x in report["errors"]))

    def test_untracked_text_change_fails(self) -> None:
        self.make_short_valid(untracked_prefix="擅自新增"); completed, report = self.invoke()
        self.assertNotEqual(completed.returncode, 0); self.assertTrue(any("source vs redline rejected" in x for x in report["errors"]))

    def test_accepted_view_is_readable_without_clean_copy(self) -> None:
        self.make_short_valid(); completed, report = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr); self.assertTrue(report["accepted_view_readable"])

    def test_long_addition_passes_without_length_approval(self) -> None:
        self.make_long_valid(); completed, report = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["source_matches_rejected_view"])
        self.assertTrue(report["accepted_view_readable"])

    def test_point_comment_passes(self) -> None:
        self.make_short_valid(point_comment=True); completed, report = self.invoke(expected_comments=1)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr); self.assertEqual(report["comment_range_starts"], 0)

    def test_orphan_comment_fails(self) -> None:
        self.make_short_valid(orphan_comment=True); completed, report = self.invoke(expected_comments=1)
        self.assertNotEqual(completed.returncode, 0); self.assertTrue(any("comment IDs/references" in x for x in report["errors"]))

    def test_untracked_header_change_fails(self) -> None:
        header_a = f'<?xml version="1.0" encoding="UTF-8"?><w:hdr xmlns:w="{W}">{paragraph(run("原页眉"))}</w:hdr>'
        header_b = f'<?xml version="1.0" encoding="UTF-8"?><w:hdr xmlns:w="{W}">{paragraph(run("被改页眉"))}</w:hdr>'
        write_docx(self.original, [paragraph(run("付款期限为三十日。"))], extra_parts={"word/header1.xml": header_a})
        write_docx(self.redline, [paragraph(run("付款期限为") + deletion("三十") + insertion("十五") + run("日。"))], track=True, extra_parts={"word/header1.xml": header_b})
        completed, report = self.invoke()
        self.assertNotEqual(completed.returncode, 0); self.assertTrue(any("word/header1.xml" in x for x in report["errors"]))

    def test_critical_style_change_fails(self) -> None:
        styles_a = f'<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Normal"/></w:styles>'
        styles_b = f'<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Changed"/></w:style></w:styles>'
        write_docx(self.original, [paragraph(run("付款期限为三十日。"))], extra_parts={"word/styles.xml": styles_a})
        write_docx(self.redline, [paragraph(run("付款期限为") + deletion("三十") + insertion("十五") + run("日。"))], track=True, extra_parts={"word/styles.xml": styles_b})
        completed, report = self.invoke()
        self.assertNotEqual(completed.returncode, 0); self.assertTrue(any("critical style" in x for x in report["errors"]))

    def test_unapproved_relationship_change_fails(self) -> None:
        empty_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
        changed_rels = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.invalid" TargetMode="External"/></Relationships>'
        write_docx(self.original, [paragraph(run("付款期限为三十日。"))], extra_parts={"word/_rels/document.xml.rels": empty_rels})
        write_docx(self.redline, [paragraph(run("付款期限为") + deletion("三十") + insertion("十五") + run("日。"))], track=True, extra_parts={"word/_rels/document.xml.rels": changed_rels})
        completed, report = self.invoke()
        self.assertNotEqual(completed.returncode, 0); self.assertTrue(any("critical story relationships" in x for x in report["errors"]))


if __name__ == "__main__":
    unittest.main()
