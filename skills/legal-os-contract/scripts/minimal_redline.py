from __future__ import annotations

import argparse
import datetime as dt
import json
import zipfile
from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W}
AUTHOR = "法务"


def qn(local: str) -> str:
    return f"{{{W}}}{local}"


def wrapper_text(wrapper: etree._Element) -> str:
    tag = "delText" if wrapper.tag == qn("del") else "t"
    return "".join(wrapper.xpath(f".//w:{tag}/text()", namespaces=NS))


def wrapper_rpr(wrapper: etree._Element) -> etree._Element | None:
    run = wrapper.find("w:r", namespaces=NS)
    if run is None:
        return None
    rpr = run.find("w:rPr", namespaces=NS)
    return deepcopy(rpr) if rpr is not None else None


def make_run(text: str, rpr: etree._Element | None) -> etree._Element:
    run = etree.Element(qn("r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    node = etree.SubElement(run, qn("t"))
    if text[:1].isspace() or text[-1:].isspace() or "\n" in text:
        node.set(f"{{{XML}}}space", "preserve")
    node.text = text
    return run


def make_change(kind: str, text: str, rpr: etree._Element | None, change_id: int, now: str) -> etree._Element:
    wrapper = etree.Element(qn(kind))
    wrapper.set(qn("id"), str(change_id))
    wrapper.set(qn("author"), AUTHOR)
    wrapper.set(qn("date"), now)
    run = etree.SubElement(wrapper, qn("r"))
    if rpr is not None:
        run.append(deepcopy(rpr))
    tag = "delText" if kind == "del" else "t"
    node = etree.SubElement(run, qn(tag))
    if text[:1].isspace() or text[-1:].isspace() or "\n" in text:
        node.set(f"{{{XML}}}space", "preserve")
    node.text = text
    return wrapper


def choose_rpr(primary: etree._Element | None, fallback: etree._Element | None) -> etree._Element | None:
    return primary if primary is not None else fallback


def max_id(root: etree._Element) -> int:
    values: list[int] = []
    for el in root.xpath("//*[@w:id]", namespaces=NS):
        try:
            values.append(int(el.get(qn("id"))))
        except (TypeError, ValueError):
            pass
    return max(values, default=0)


def split_pair(old: str, new: str, old_rpr: etree._Element | None, new_rpr: etree._Element | None,
               next_id: int, now: str) -> tuple[list[etree._Element], int, dict[str, int]]:
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    result: list[etree._Element] = []
    deleted = inserted = same = regions = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        left, right = old[i1:i2], new[j1:j2]
        if tag == "equal":
            if left:
                result.append(make_run(left, choose_rpr(new_rpr, old_rpr)))
                same += len(left)
            continue
        if tag in ("delete", "replace") and left:
            result.append(make_change("del", left, old_rpr, next_id, now))
            next_id += 1
            deleted += len(left)
        if tag in ("insert", "replace") and right:
            result.append(make_change("ins", right, choose_rpr(new_rpr, old_rpr), next_id, now))
            next_id += 1
            inserted += len(right)
        regions += 1
    return result, next_id, {
        "same_chars": same,
        "deleted_chars": deleted,
        "inserted_chars": inserted,
        "changed_regions": regions,
    }


# 整段新增规范化：采用 Word 标准"段落标记修订"结构。
# 结构依据：ECMA-376 Part 1 §17.3.1.29（w:pPr）、§17.3.2.8（w:rPr）——
# w:pPr/w:rPr 允许 w:ins/w:del 作为段落标记（paragraph mark）本身的修订标记
# （CT_ParaRPr 的 EG_RPrTrackChanges 部分）。Word 原生整段新增即：
#   <w:p>
#     <w:pPr><w:rPr><w:ins …/></w:rPr></w:pPr>
#     <w:ins …>…文字…</w:ins>
#   </w:p>
# 段落标记标记为新增后，"拒绝修订"时段落标记一并删除，整段消失、不残留空段；
# "接受修订"时段落保留。w:p 始终位于 body/tc 等合法块级位置，w:ins 不包含 w:p。
_INS_AUX_TAGS = {
    qn("pPr"), qn("bookmarkStart"), qn("bookmarkEnd"),
    qn("commentRangeStart"), qn("commentRangeEnd"), qn("proofErr"),
    qn("customXml"), qn("sdt"), qn("smartTag"),
}


def is_whole_paragraph_ins(paragraph: etree._Element) -> etree._Element | None:
    """若段落为段内整段新增（唯一内容=单个非空 w:ins），返回该 ins；否则返回 None。"""
    ins_list: list[etree._Element] = []
    for child in paragraph:
        if child.tag == qn("ins"):
            ins_list.append(child)
        elif child.tag in _INS_AUX_TAGS:
            continue
        else:
            return None  # 存在 ins 之外的内容元素，非整段新增
    if len(ins_list) != 1:
        return None
    ins = ins_list[0]
    if not list(ins):
        return None
    return ins


def _mark_paragraph_ins(paragraph: etree._Element, ins: etree._Element, next_id: int) -> int:
    """给段落的段落标记（paragraph mark）附加新增修订标记 w:pPr/w:rPr/w:ins。

    返回新的 next_id。author/date 继承自 ins；id 使用新值（修订元素 id 需唯一）。
    若段落标记已存在同作者的 w:ins 标记则不再重复添加。"""
    ppr = paragraph.find(qn("pPr"))
    if ppr is None:
        ppr = etree.Element(qn("pPr"))
        paragraph.insert(0, ppr)
    rpr = ppr.find(qn("rPr"))
    if rpr is None:
        rpr = etree.Element(qn("rPr"))
        ppr.append(rpr)
    author = ins.get(qn("author"))
    for mark in rpr.findall(qn("ins")):
        if mark.get(qn("author")) == author:
            return next_id
    mark = etree.Element(qn("ins"))
    mark.set(qn("id"), str(next_id))
    if author is not None:
        mark.set(qn("author"), author)
    if ins.get(qn("date")) is not None:
        mark.set(qn("date"), ins.get(qn("date")))
    rpr.append(mark)
    return next_id + 1


def normalize_whole_paragraph_ins(root: etree._Element, next_id: int) -> tuple[int, int]:
    """将整段新增规范化为标准"段落标记修订"结构。

    处理两种输入：
    A. 段外整段新增（历史产物 <w:ins><w:p>…</w:p></w:ins>，非法块级嵌套）：把 w:p
       移回 body/tc 等合法块级位置，补段落标记修订，删除外层 ins；
    B. 段内整段新增（<w:p><w:ins>…</w:ins></w:p>）：补段落标记修订即可。

    返回 (规范化段落数, next_id)。
    """
    normalized = 0
    # A. 段外 ins 直接包含 w:p（历史非标准结构）→ 移回合法块级位置、补段落标记修订、
    #    并将文字 run 包进段内 w:ins（保留"文字属于新增"语义，符合 ECMA-376 标准整段新增形态）
    for outer in list(root.xpath(".//w:ins[w:p]", namespaces=NS)):
        parent = outer.getparent()
        if parent is None:
            continue
        idx = parent.index(outer)
        paragraphs = outer.findall(qn("p"))
        parent.remove(outer)
        for p in paragraphs:
            next_id = _mark_paragraph_ins(p, outer, next_id)
            # 段内文字 ins：包裹 p 内除 pPr 外的全部内容元素
            inner = etree.Element(qn("ins"))
            inner.set(qn("id"), str(next_id))
            next_id += 1
            if outer.get(qn("author")) is not None:
                inner.set(qn("author"), outer.get(qn("author")))
            if outer.get(qn("date")) is not None:
                inner.set(qn("date"), outer.get(qn("date")))
            for child in list(p):
                if child.tag != qn("pPr"):
                    p.remove(child)
                    inner.append(child)
            p.append(inner)
            parent.insert(idx, p)
            idx += 1
            normalized += 1
    # B. 段内整段新增 → 补段落标记修订（跳过已规范化段落，避免重复计数）
    for paragraph in root.xpath(".//w:p", namespaces=NS):
        ins = is_whole_paragraph_ins(paragraph)
        if ins is None:
            continue
        ppr = paragraph.find(qn("pPr"))
        if ppr is not None:
            rpr = ppr.find(qn("rPr"))
            if rpr is not None and rpr.findall(qn("ins")):
                continue  # 段落标记已标记新增（A 型产物），跳过
        next_id = _mark_paragraph_ins(paragraph, ins, next_id)
        normalized += 1
    return normalized, next_id


def main() -> None:
    ap = argparse.ArgumentParser(description="Split broad tracked replacements into minimal character-level redlines.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--report", required=True)
    args = ap.parse_args()
    source = Path(args.input)
    target = Path(args.output)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    with zipfile.ZipFile(source, "r") as zin:
        document = etree.fromstring(zin.read("word/document.xml"))
        next_id = max_id(document) + 1
        pairs = 0
        reports: list[dict[str, object]] = []

        for paragraph in document.xpath(".//w:p", namespaces=NS):
            children = list(paragraph)
            index = 0
            while index < len(children) - 1:
                old_wrapper = children[index]
                new_wrapper = children[index + 1]
                if (
                    old_wrapper.tag == qn("del")
                    and new_wrapper.tag == qn("ins")
                    and old_wrapper.get(qn("author")) == AUTHOR
                    and new_wrapper.get(qn("author")) == AUTHOR
                ):
                    old_text = wrapper_text(old_wrapper)
                    new_text = wrapper_text(new_wrapper)
                    replacement, next_id, metrics = split_pair(
                        old_text,
                        new_text,
                        wrapper_rpr(old_wrapper),
                        wrapper_rpr(new_wrapper),
                        next_id,
                        now,
                    )
                    start = list(paragraph).index(old_wrapper)
                    paragraph.remove(old_wrapper)
                    paragraph.remove(new_wrapper)
                    for offset, node in enumerate(replacement):
                        paragraph.insert(start + offset, node)
                    children = list(paragraph)
                    pairs += 1
                    reports.append({"old": old_text, "new": new_text, **metrics})
                    index = start + len(replacement)
                    continue
                index += 1

        normalized_paragraphs, next_id = normalize_whole_paragraph_ins(document, next_id)

        overrides = {
            "word/document.xml": etree.tostring(
                document, xml_declaration=True, encoding="UTF-8", standalone="yes"
            )
        }
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = overrides.get(item.filename, zin.read(item.filename))
                zout.writestr(item, data)

    Path(args.report).write_text(
        json.dumps(
            {
                "source": str(source),
                "output": str(target),
                "author": AUTHOR,
                "pairs_regranularized": pairs,
                "whole_paragraph_ins_normalized": normalized_paragraphs,
                "changes": reports,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"pairs_regranularized": pairs, "whole_paragraph_ins_normalized": normalized_paragraphs, "report": args.report}, ensure_ascii=False))


if __name__ == "__main__":
    main()
