#!/usr/bin/env python3
"""minimal_redline 整段新增规范化回归测试。

覆盖（Codex 主管 2026-08-10 返工指令要求）：
1. 生成结果不存在 .//w:ins/w:p；
2. 新增段落结构符合选定方案（段落标记修订：w:pPr/w:rPr/w:ins + 段内 w:ins）；
3. 接受修订后得到预期段落；
4. 拒绝修订后与原合同逐段一致且无空段残留；
5. 原有普通段内 ins/del 行为不受影响；
6. 不同作者的修订不会被错误接受、跳过或删除；
7. 质量门拒绝任何 .//w:ins/w:p 结构。
"""
from __future__ import annotations

import sys
import unittest
import zipfile
from pathlib import Path

from lxml import etree

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import minimal_redline as mr  # noqa: E402
import redline_quality_gate as gate  # noqa: E402

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
qn = lambda t: f"{{{W}}}{t}"
AUTHOR = "法务"
FOREIGN = "张三"


def run(text: str) -> str:
    return f"<w:r><w:t xml:space='preserve'>{text}</w:t></w:r>"


def para(inner: str) -> str:
    return f"<w:p>{inner}</w:p>"


def text_para(text: str) -> str:
    """普通文本段落（w:r/w:t 完整包装，避免文本裸露在 w:p 内被解析丢弃）。"""
    return para(run(text))


def ins(text: str, cid: int, author: str = AUTHOR) -> str:
    return f'<w:ins w:id="{cid}" w:author="{author}" w:date="2026-08-10T00:00:00Z">{run(text)}</w:ins>'


def write_docx(path: Path, body_inner: str, track: bool = True) -> None:
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
        "</Relationships>"
    )
    settings = (
        f'<?xml version="1.0" encoding="UTF-8"?><w:settings xmlns:w="{W}">'
        f'{"<w:trackRevisions/>" if track else ""}</w:settings>'
    )
    document = f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{W}"><w:body>{body_inner}</w:body></w:document>'
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/settings.xml", settings)


def load_document(path: Path) -> etree._Element:
    with zipfile.ZipFile(path) as z:
        return etree.fromstring(z.read("word/document.xml"))


def assert_no_ins_w_p(testcase: unittest.TestCase, root: etree._Element) -> None:
    hits = root.xpath(".//w:ins/w:p", namespaces=NS)
    testcase.assertEqual(hits, [], f"非法结构 .//w:ins/w:p 出现 {len(hits)} 处")


class MinimalRedlineWholeParagraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile_gettempdir())
        self.src = self.tmp / "mr_src.docx"
        self.red = self.tmp / "mr_red.docx"
        self.out = self.tmp / "mr_out.docx"

    def tearDown(self) -> None:
        for p in (self.src, self.red, self.out):
            p.unlink(missing_ok=True)

    def _normalize(self, red_path: Path, body_inner: str, out_path: Path) -> int:
        write_docx(red_path, body_inner)
        root = load_document(red_path)
        count, _next_id = mr.normalize_whole_paragraph_ins(root, mr.max_id(root) + 1)
        document = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")
        with zipfile.ZipFile(red_path) as zin, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = document if item.filename == "word/document.xml" else zin.read(item.filename)
                zout.writestr(item, data)
        return count

    # 1) 生成结果不存在 .//w:ins/w:p；2) 结构符合段落标记修订方案
    def test_normalized_structure_has_paragraph_mark_revision(self) -> None:
        body = para(ins("新增整段条款文字", 1))  # 段内整段 ins
        count = self._normalize(self.red, body, self.out)
        self.assertEqual(count, 1)
        root = load_document(self.out)
        assert_no_ins_w_p(self, root)
        # 段落标记修订存在：w:pPr/w:rPr/w:ins 且 author 继承
        marks = root.xpath(".//w:pPr/w:rPr/w:ins", namespaces=NS)
        self.assertEqual(len(marks), 1, "应存在段落标记修订 w:pPr/w:rPr/w:ins")
        self.assertEqual(marks[0].get(qn("author")), AUTHOR)
        # 文字仍由段内 w:ins 承载
        text_ins = root.xpath(".//w:ins", namespaces=NS)
        self.assertTrue(any("新增整段条款文字" in "".join(t.text or "" for t in i.xpath(".//w:t", namespaces=NS)) for i in text_ins))

    # 1) 历史段外 ins 产物也能转换回合规结构，w:p 回到合法块级位置
    def test_outer_ins_legacy_converted_to_standard(self) -> None:
        outer = f'<w:ins w:id="1" w:author="{AUTHOR}" w:date="2026-08-10T00:00:00Z">{para(run("历史段外新增"))}</w:ins>'
        body = text_para("第一条 原有") + outer + text_para("第二条 原有")
        count = self._normalize(self.red, body, self.out)
        self.assertEqual(count, 1)
        root = load_document(self.out)
        assert_no_ins_w_p(self, root)
        # w:p 直接位于 body 下（块级位置），且带段落标记修订
        body_el = root.find(qn("body"))
        p_tags = [c for c in body_el if c.tag == qn("p")]
        self.assertEqual(len(p_tags), 3, "w:p 应回到 body 块级位置")
        marks = root.xpath(".//w:pPr/w:rPr/w:ins", namespaces=NS)
        self.assertEqual(len(marks), 1)

    # 3) 接受修订后得到预期段落
    def test_accept_matches_expected_paragraphs(self) -> None:
        src_body = text_para("第一条 合作内容。") + text_para("第三条 争议解决。")
        red_body = text_para("第一条 合作内容。") + para(ins("第二条 新增付款条款。", 1)) + text_para("第三条 争议解决。")
        write_docx(self.src, src_body)
        count = self._normalize(self.red, red_body, self.out)
        self.assertEqual(count, 1)
        acc = gate.story_view(self.out, "accept", AUTHOR)
        self.assertEqual(
            acc["word/document.xml"]["paragraphs"],
            ["第一条 合作内容。", "第二条 新增付款条款。", "第三条 争议解决。"],
        )

    # 4) 拒绝修订后与原合同逐段一致且无空段残留
    def test_reject_matches_source_no_empty_paragraphs(self) -> None:
        src_body = text_para("第一条 合作内容。") + text_para("第三条 争议解决。")
        red_body = text_para("第一条 合作内容。") + para(ins("第二条 新增付款条款。", 1)) + text_para("第三条 争议解决。")
        write_docx(self.src, src_body)
        count = self._normalize(self.red, red_body, self.out)
        self.assertEqual(count, 1)
        rej = gate.story_view(self.out, "reject", AUTHOR)
        src = gate.story_view(self.src, "accept", AUTHOR)
        self.assertEqual(rej, src, "拒绝视图应与原合同逐段一致")
        self.assertEqual(len(rej["word/document.xml"]["paragraphs"]), 2, "拒绝后不得残留空段")

    # 5) 原有普通段内 ins/del 行为不受影响
    def test_inline_ins_del_unaffected(self) -> None:
        body = para(
            run("第二条 付款")
            + f'<w:del w:id="1" w:author="{AUTHOR}" w:date="2026-08-10T00:00:00Z"><w:r><w:delText>百分之五十</w:delText></w:r></w:del>'
            + ins("百分之六十", 2)
            + run("。")
        )
        count = self._normalize(self.red, body, self.out)
        self.assertEqual(count, 0, "普通局部修订不应被标记为整段新增")
        root = load_document(self.out)
        marks = root.xpath(".//w:pPr/w:rPr/w:ins", namespaces=NS)
        self.assertEqual(len(marks), 0, "局部修订段落不应被打上段落标记新增")
        # 局部 del/ins 结构保持
        self.assertEqual(len(root.xpath(".//w:del", namespaces=NS)), 1)
        self.assertEqual(len(root.xpath(".//w:ins", namespaces=NS)), 1)

    # 6) 不同作者的修订不会被错误接受、跳过或删除
    def test_foreign_author_revision_respected(self) -> None:
        src_body = text_para("第一条 原有。")
        red_body = (
            text_para("第一条 原有。")
            + para(ins("法务新增段。", 1, AUTHOR))
            + para(ins("对方新增段。", 2, FOREIGN))
        )
        write_docx(self.src, src_body)
        count = self._normalize(self.red, red_body, self.out)
        self.assertEqual(count, 2)
        rej = gate.story_view(self.out, "reject", AUTHOR)
        # 拒绝法务修订：法务段消失、对方段保留 → 共 2 段
        paras = rej["word/document.xml"]["paragraphs"]
        self.assertEqual(len(paras), 2, "拒绝法务修订后：法务段应消失、对方段应保留")
        self.assertIn("对方新增段。", paras)
        self.assertNotIn("法务新增段。", paras)

    # 7) 质量门硬拒绝 .//w:ins/w:p
    def test_gate_rejects_illegal_outer_ins(self) -> None:
        bad = self.tmp / "mr_bad.docx"
        outer = f'<w:ins w:id="1" w:author="{AUTHOR}" w:date="2026-08-10T00:00:00Z">{para(run("非法段外新增"))}</w:ins>'
        write_docx(bad, text_para("第一条 原有。") + outer)
        errors: list[str] = []
        gate.check_illegal_paragraph_nesting(bad, errors)
        self.assertTrue(any("illegal whole-paragraph insertion" in e for e in errors), f"应拒绝 .//w:ins/w:p，errors={errors}")


def tempfile_gettempdir() -> str:
    import tempfile
    return tempfile.gettempdir()


if __name__ == "__main__":
    unittest.main()
