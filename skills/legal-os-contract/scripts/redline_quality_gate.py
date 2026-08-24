#!/usr/bin/env python3
"""Fail-closed quality gate for Chinese contract DOCX redlines.

The gate compares the source contract with the redline after rejecting this
author's changes and verifies that the accepted view is readable. It checks
every Word story part, not only the main document text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
import zipfile
from pathlib import Path

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
REQUIRED_PACKAGE_PARTS = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
STORY_RE = re.compile(r"^word/(?:document|header\d+|footer\d+|footnotes|endnotes)\.xml$")
STORY_RELS_RE = re.compile(r"^word/_rels/(?:document|header\d+|footer\d+|footnotes|endnotes)\.xml\.rels$")
CRITICAL_STYLE_PARTS = {
    "word/styles.xml",
    "word/numbering.xml",
    "word/fontTable.xml",
    "word/theme/theme1.xml",
}
IGNORED_RELATIONSHIP_SUFFIXES = {
    "/comments",
    "/commentsExtended",
    "/commentsIds",
    "/people",
}
def qn(local: str) -> str:
    return f"{{{W}}}{local}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_package(path: Path, label: str, errors: list[str]) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            missing = sorted(REQUIRED_PACKAGE_PARTS - set(names))
            if missing:
                errors.append(f"{label}: missing required package parts: {missing}")
            duplicate = sorted({name for name in names if names.count(name) > 1})
            if duplicate:
                errors.append(f"{label}: duplicate ZIP members: {duplicate[:5]}")
            bad = archive.testzip()
            if bad:
                errors.append(f"{label}: corrupt ZIP member: {bad}")
            if any(name.lower().endswith("vbaproject.bin") for name in names):
                errors.append(f"{label}: macro payload is not permitted in DOCX delivery")
            return names
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"{label}: unreadable DOCX package: {exc}")
        return []


def read_xml(path: Path, part: str) -> etree._Element:
    with zipfile.ZipFile(path) as archive:
        return etree.fromstring(archive.read(part))


def canonical_xml(node: etree._Element, *, drop_property_changes: bool = False) -> bytes:
    clone = etree.fromstring(etree.tostring(node))
    for item in clone.iter():
        for attribute in list(item.attrib):
            if etree.QName(attribute).localname.startswith("rsid"):
                del item.attrib[attribute]
    if drop_property_changes:
        for item in clone.xpath(".//w:rPrChange | .//w:pPrChange", namespaces=NS):
            parent = item.getparent()
            if parent is not None:
                parent.remove(item)
    return etree.tostring(clone, method="c14n")


def relationship_inventory(path: Path) -> dict[str, list[tuple[str, str, str]]]:
    inventory: dict[str, list[tuple[str, str, str]]] = {}
    with zipfile.ZipFile(path) as archive:
        for part in sorted(name for name in archive.namelist() if STORY_RELS_RE.match(name)):
            root = etree.fromstring(archive.read(part))
            records = []
            for relation in root.xpath(".//*[local-name()='Relationship']"):
                relation_type = relation.get("Type", "")
                if any(relation_type.endswith(suffix) for suffix in IGNORED_RELATIONSHIP_SUFFIXES):
                    continue
                records.append((relation_type, relation.get("Target", ""), relation.get("TargetMode", "")))
            inventory[part] = sorted(records)
    return inventory


def compare_critical_structure(original: Path, redline: Path, errors: list[str]) -> None:
    with zipfile.ZipFile(original) as source_archive, zipfile.ZipFile(redline) as redline_archive:
        source_names = set(source_archive.namelist())
        redline_names = set(redline_archive.namelist())
        for part in sorted(CRITICAL_STYLE_PARTS):
            if (part in source_names) != (part in redline_names):
                errors.append(f"critical style part presence differs: {part}")
                continue
            if part in source_names:
                source = canonical_xml(etree.fromstring(source_archive.read(part)))
                changed = canonical_xml(etree.fromstring(redline_archive.read(part)))
                if source != changed:
                    errors.append(f"critical style/numbering part changed outside revision text: {part}")
    if relationship_inventory(original) != relationship_inventory(redline):
        errors.append("critical story relationships changed outside the permitted comments relationship")


def check_illegal_paragraph_nesting(path: Path, errors: list[str]) -> None:
    """拒绝任何 w:ins 直接包含 w:p 的非标准整段新增嵌套（minimal_redline.py 早期产物形态）。

    合规的整段新增必须是"段落标记修订"结构：w:pPr/w:rPr/w:ins 标记段落本身新增，
    文字由段内 w:ins 承载；w:p 保持位于 body/tc 等块级位置，w:ins 不得包含 w:p。"""
    for part in story_parts(path):
        try:
            root = read_xml(path, part)
        except (OSError, zipfile.BadZipFile, etree.XMLSyntaxError):
            continue  # XML 可解析性由 validate_package 的 ZIP 检查与后续解析兜底
        hits = root.xpath(".//w:ins/w:p", namespaces=NS)
        if hits:
            errors.append(
                f"{part}: illegal whole-paragraph insertion structure w:ins/w:p "
                f"({len(hits)} occurrence(s)) is not permitted; "
                "use paragraph-mark revision (w:pPr/w:rPr/w:ins) instead"
            )


def story_parts(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        return sorted(name for name in archive.namelist() if STORY_RE.match(name))


def collect_text(node: etree._Element, mode: str, author: str, include_deleted: bool = False) -> str:
    tag = node.tag
    if tag == qn("del"):
        if node.get(qn("author")) == author:
            if mode != "reject":
                return ""
            return "".join(collect_text(child, mode, author, True) for child in node)
        return ""
    if tag == qn("ins"):
        if node.get(qn("author")) == author and mode == "reject":
            return ""
        return "".join(collect_text(child, mode, author, include_deleted) for child in node)
    if tag == qn("t"):
        return node.text or ""
    if tag == qn("delText"):
        return (node.text or "") if include_deleted else ""
    if tag == qn("tab"):
        return "\t"
    if tag in {qn("br"), qn("cr")}:
        return "\n"
    return "".join(collect_text(child, mode, author, include_deleted) for child in node)


def run_visible(run: etree._Element, mode: str, author: str) -> bool:
    for ancestor in run.iterancestors():
        if ancestor.tag == qn("ins") and mode == "reject" and ancestor.get(qn("author")) == author:
            return False
        if ancestor.tag == qn("del"):
            if mode == "reject" and ancestor.get(qn("author")) == author:
                continue
            return False
    return True


def run_text(run: etree._Element) -> str:
    chunks: list[str] = []
    for node in run.iterdescendants():
        if node.tag in {qn("t"), qn("delText")}:
            chunks.append(node.text or "")
        elif node.tag == qn("tab"):
            chunks.append("\t")
        elif node.tag in {qn("br"), qn("cr")}:
            chunks.append("\n")
    return "".join(chunks)


def paragraph_format_signature(paragraph: etree._Element, mode: str, author: str) -> dict[str, object]:
    ppr = paragraph.find(qn("pPr"))
    if ppr is None:
        ppr_key = ""
    else:
        ppr_clone = etree.fromstring(etree.tostring(ppr))
        for child in list(ppr_clone):
            if child.tag in {qn("rPr"), qn("pPrChange")}:
                ppr_clone.remove(child)
        ppr_key = (
            ""
            if len(ppr_clone) == 0
            else sha256_bytes(canonical_xml(ppr_clone, drop_property_changes=True))
        )
    chunks: list[list[str]] = []
    for run in paragraph.xpath(".//w:r", namespaces=NS):
        if not run_visible(run, mode, author):
            continue
        text = run_text(run)
        if not text:
            continue
        rpr = run.find(qn("rPr"))
        format_key = "" if rpr is None else sha256_bytes(canonical_xml(rpr, drop_property_changes=True))
        if chunks and chunks[-1][0] == format_key:
            chunks[-1][1] += text
        else:
            chunks.append([format_key, text])
    return {"ppr": ppr_key, "runs": chunks}


def is_pure_insertion(p: etree._Element, author: str) -> bool:
    """段落是否完全由指定作者的插入（w:ins）构成（无其他文本内容）。
    用于拒绝视图：整段新增的独立段落（necessary_addition/structural_completion）
    在 reject 视图下应被跳过，不参与与源合同的逐段比对。

    识别两种标准整段新增形态：
    1. 段落标记新增（ECMA-376 CT_ParaRPr）：w:pPr/w:rPr 内含指定作者的 w:ins，
       表示段落标记本身属于新增——拒绝修订时段落标记删除、整段消失；
    2. 段内整段新增：段落唯一内容为单个指定作者的非空 w:ins。
    拒绝任何 w:ins 直接包含 w:p 的非标准嵌套（由 validate_package 独立拦截）。"""
    # 1) 段落标记本身为新增（w:pPr/w:rPr/w:ins）
    ppr = p.find(qn("pPr"))
    if ppr is not None:
        rpr = ppr.find(qn("rPr"))
        if rpr is not None:
            for mark in rpr.findall(qn("ins")):
                if mark.get(qn("author")) == author:
                    return True
    # 2) 段内整段新增
    has_ins = False
    for node in p.iter(qn("ins")):
        if node.get(qn("author")) == author:
            has_ins = True
    if not has_ins:
        return False
    total = "".join(n.text or "" for n in p.iter() if n.tag in (qn("t"), qn("delText")))
    ins_text = ""
    for node in p.iter(qn("ins")):
        if node.get(qn("author")) == author:
            for n in node.iter():
                if n.tag in (qn("t"), qn("delText")):
                    ins_text += n.text or ""
    return total == ins_text


def story_view(path: Path, mode: str, author: str) -> dict[str, dict[str, object]]:
    view: dict[str, dict[str, object]] = {}
    for part in story_parts(path):
        root = read_xml(path, part)
        paragraphs = []
        formatting = []
        for p in root.xpath(".//w:p", namespaces=NS):
            # 拒绝视图：跳过纯新增段落（独立整段插入），避免新增段落导致逐段比对失败
            if mode == "reject" and is_pure_insertion(p, author):
                continue
            paragraphs.append(collect_text(p, mode, author))
            formatting.append(paragraph_format_signature(p, mode, author))
        table_shapes = []
        for table in root.xpath(".//w:tbl", namespaces=NS):
            rows = table.xpath("./w:tr", namespaces=NS)
            table_shapes.append([len(row.xpath("./w:tc", namespaces=NS)) for row in rows])
        view[part] = {"paragraphs": paragraphs, "table_shapes": table_shapes, "formatting": formatting}
    return view


def compare_views(label: str, left: dict[str, dict[str, object]], right: dict[str, dict[str, object]], errors: list[str]) -> bool:
    if set(left) != set(right):
        errors.append(f"{label}: story part set differs: left={sorted(left)} right={sorted(right)}")
        return False
    for part in sorted(left):
        if left[part]["table_shapes"] != right[part]["table_shapes"]:
            errors.append(f"{label}: table structure differs in {part}")
            return False
        left_p = list(left[part]["paragraphs"])
        right_p = list(right[part]["paragraphs"])
        if left_p != right_p:
            limit = min(len(left_p), len(right_p))
            mismatch = next((i for i in range(limit) if left_p[i] != right_p[i]), limit)
            left_excerpt = left_p[mismatch][:80] if mismatch < len(left_p) else "<missing>"
            right_excerpt = right_p[mismatch][:80] if mismatch < len(right_p) else "<missing>"
            errors.append(
                f"{label}: text differs in {part} paragraph {mismatch}: "
                f"left={left_excerpt!r} right={right_excerpt!r}"
            )
            return False
        if left[part]["formatting"] != right[part]["formatting"]:
            errors.append(f"{label}: direct formatting or paragraph properties differ in {part}")
            return False
    return True


def historical_revision_inventory(path: Path, current_author: str) -> dict[str, list[tuple[str, str, str, str]]]:
    """Inventory pre-existing insertion/deletion revision wrappers by story part.

    Only wrapper identity is compared so a new current-author revision may be
    nested inside historical content without accepting/rejecting or re-authoring
    the historical wrapper itself.
    """
    inventory: dict[str, list[tuple[str, str, str, str]]] = {}
    for part in story_parts(path):
        root = read_xml(path, part)
        rows: list[tuple[str, str, str, str]] = []
        for node in root.xpath(".//w:ins | .//w:del", namespaces=NS):
            author = node.get(qn("author"), "")
            if author == current_author:
                continue
            rows.append((
                etree.QName(node).localname,
                node.get(qn("id"), ""),
                author,
                node.get(qn("date"), ""),
            ))
        inventory[part] = rows
    return inventory


def compare_historical_revisions(original: Path, redline: Path, current_author: str, errors: list[str]) -> bool:
    left = historical_revision_inventory(original, current_author)
    right = historical_revision_inventory(redline, current_author)
    if left != right:
        errors.append(
            "historical tracked revisions changed outside current-author revisions; "
            "do not accept, reject, remove, or re-author pre-existing revisions without authorization"
        )
        return False
    return True


def change_text(node: etree._Element, kind: str) -> str:
    """Return the complete historical text carried by a revision wrapper."""
    del kind
    chunks: list[str] = []
    for descendant in node.iterdescendants():
        if descendant.tag in {qn("t"), qn("delText")}:
            chunks.append(descendant.text or "")
        elif descendant.tag == qn("tab"):
            chunks.append("\t")
        elif descendant.tag in {qn("br"), qn("cr")}:
            chunks.append("\n")
    return "".join(chunks)


def fragments(path: Path, author: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for part in story_parts(path):
        root = read_xml(path, part)
        for node in root.xpath(".//w:ins | .//w:del", namespaces=NS):
            if node.get(qn("author")) != author:
                continue
            # 跳过段落标记修订（w:pPr/w:rPr 内的 ins/del）：无文字内容，不属于文本片段
            parent = node.getparent()
            if parent is not None and parent.tag == qn("rPr"):
                continue
            kind = "insert" if node.tag == qn("ins") else "delete"
            text = change_text(node, kind)
            records.append({
                "kind": kind,
                "text": text,
                "length": len(text),
            })
    return records


def stats(values: list[int]) -> dict[str, object]:
    if not values:
        return {"count": 0, "median": 0, "max": 0, "mean": 0.0}
    return {
        "count": len(values),
        "median": statistics.median(values),
        "max": max(values),
        "mean": round(sum(values) / len(values), 2),
    }


def comment_metrics(path: Path) -> tuple[int, int, int, int, set[str], set[str], set[str], set[str], dict[str, str]]:
    texts: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        count = 0
        ids: set[str] = set()
        if "word/comments.xml" in archive.namelist():
            comments = etree.fromstring(archive.read("word/comments.xml"))
            nodes = comments.xpath(".//w:comment", namespaces=NS)
            count = len(nodes)
            ids = {node.get(qn("id"), "") for node in nodes}
            for node in nodes:
                cid = node.get(qn("id"), "")
                texts[cid] = "".join(node.itertext()).strip()
    refs: set[str] = set()
    starts: set[str] = set()
    ends: set[str] = set()
    for part in story_parts(path):
        root = read_xml(path, part)
        refs.update(node.get(qn("id"), "") for node in root.xpath(".//w:commentReference", namespaces=NS))
        starts.update(node.get(qn("id"), "") for node in root.xpath(".//w:commentRangeStart", namespaces=NS))
        ends.update(node.get(qn("id"), "") for node in root.xpath(".//w:commentRangeEnd", namespaces=NS))
    return count, len(refs), len(starts), len(ends), ids, refs, starts, ends, texts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--redline", required=True, type=Path)
    parser.add_argument("--author", default="法务")
    parser.add_argument("--expected-comments", type=int)
    parser.add_argument("--out-json", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    validate_package(args.original, "original", errors)
    validate_package(args.redline, "redline", errors)
    packages_valid = not errors
    if packages_valid:
        try:
            compare_critical_structure(args.original, args.redline, errors)
            compare_historical_revisions(args.original, args.redline, args.author, errors)
        except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
            errors.append(f"critical structure comparison failed: {exc}")
        check_illegal_paragraph_nesting(args.redline, errors)

    source_hash = sha256_file(args.original)
    redline_hash = sha256_file(args.redline)
    parts = fragments(args.redline, args.author) if packages_valid else []
    insert_lengths = [int(item["length"]) for item in parts if item["kind"] == "insert"]
    delete_lengths = [int(item["length"]) for item in parts if item["kind"] == "delete"]
    insert_stats = stats(insert_lengths)
    delete_stats = stats(delete_lengths)

    try:
        settings = read_xml(args.redline, "word/settings.xml")
        track = bool(settings.xpath(".//w:trackRevisions", namespaces=NS))
    except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError):
        track = False
    if not track:
        errors.append("redline: settings.xml does not enable w:trackRevisions")
    if not parts:
        errors.append(f"redline: no tracked changes found for author {args.author!r}")
    if any(not str(item["text"]) for item in parts):
        errors.append("redline: empty tracked-change wrapper found")

    source_matches_rejected = False
    accepted_view_readable = False
    if not errors or parts:
        try:
            source_view = story_view(args.original, "current", args.author)
            rejected_view = story_view(args.redline, "reject", args.author)
            story_view(args.redline, "accept", args.author)
            accepted_view_readable = True
            source_matches_rejected = compare_views(
                "source vs redline rejected view",
                source_view,
                rejected_view,
                errors,
            )
        except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
            errors.append(f"story comparison failed: {exc}")

    try:
        count, ref_count, start_count, end_count, ids, refs, starts, ends, comment_texts = comment_metrics(
            args.redline
        )
        # Point comments have a reference but no range anchors. Ranged comments
        # must still have balanced start/end anchors and valid IDs.
        if ids != refs or starts != ends or not starts.issubset(ids):
            errors.append(
                "comment IDs/references or range anchors differ: "
                f"comments={sorted(ids)} refs={sorted(refs)} starts={sorted(starts)} ends={sorted(ends)}"
            )
        if args.expected_comments is not None and count != args.expected_comments:
            errors.append(f"expected {args.expected_comments} comments but found {count}")
        # Minimal-comment rule: 30 chars warns, 50 chars fails; each comment must
        # be one concise question for one confirm item; no text -> fail.
        for cid in sorted(ids):
            ctext = comment_texts.get(cid, "")
            ctext_len = len(ctext)
            if ctext_len > 50:
                errors.append(
                    f"comment {cid} exceeds 50 chars ({ctext_len}): {ctext!r}"
                )
            elif ctext_len > 30:
                warnings.append(
                    f"comment {cid} exceeds 30 chars ({ctext_len}); consider shortening: {ctext!r}"
                )
            if ctext_len == 0:
                errors.append(f"comment {cid} is empty (must be a concise confirm item)")
            # Multi-item check:
            # - Punctuation and ordinary conjunctions are only WARNING evidence;
            #   never FAIL on comma/semicolon/question-mark/newline count alone.
            # - FAIL only when an explicit, machine-detectable multi-item pattern
            #   is hit: 2+ question marks; 2+ "是否" or repeated "请确认/需确认";
            #   "分别确认/另请确认/同时请确认/还需确认" introducing a new
            #   independent question; or explicit enumeration ("A/B、1/2、
            #   第一/第二") of multiple confirm items.
            # - Anything ambiguous -> WARNING only, never blocks output.
            _q = ctext.count("？") + ctext.count("?")
            _shi_fo = ctext.count("是否")
            _repeat_confirm = ctext.count("请确认") + ctext.count("需确认")
            _new_indep = any(
                kw in ctext
                for kw in ("分别确认", "另请确认", "同时请确认", "还需确认")
            )
            _enum = bool(
                re.search(r"[A-Za-z0-9]+/[A-Za-z0-9]+", ctext)
                or re.search(r"[一二三四五六七八九十]+/", ctext)
                or re.search(r"[一二三四五六七八九十]+、", ctext)
            )
            if _q >= 2 or _shi_fo >= 2 or _repeat_confirm >= 2 or _new_indep or _enum:
                errors.append(
                    f"comment {cid} contains multiple independent confirm items: {ctext!r}"
                )
            else:
                # Only WARNING-level suspicion from punctuation / conjunctions.
                _punct = sum(1 for ch in ctext if ch in "。；;?？\n")
                if _punct > 0 or ctext.count("，") >= 2:
                    warnings.append(
                        f"comment {cid} may contain multiple items (verify manually): {ctext!r}"
                    )
    except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        count = ref_count = start_count = end_count = 0
        errors.append(f"comment validation failed: {exc}")

    report = {
        "schema_version": "3.0",
        "status": "PASS" if not errors else "FAIL",
        "original": str(args.original),
        "redline": str(args.redline),
        "hashes": {"original": source_hash, "redline": redline_hash},
        "author": args.author,
        "track_revisions": track,
        "source_matches_rejected_view": source_matches_rejected,
        "accepted_view_readable": accepted_view_readable,
        "insert": insert_stats,
        "delete": delete_stats,
        "comment_count": count,
        "comment_refs": ref_count,
        "comment_range_starts": start_count,
        "comment_range_ends": end_count,
        "warnings": warnings,
        "errors": errors,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
