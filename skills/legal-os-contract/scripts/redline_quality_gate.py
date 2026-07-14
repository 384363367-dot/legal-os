#!/usr/bin/env python3
"""Fail-closed quality gate for Chinese contract DOCX redlines.

The gate compares the source contract with the redline after rejecting this
author's changes, and compares the redline after accepting this author's
changes with the clean copy. It checks every Word story part, not only the
main document text. Long fragments require an exact, approved v2 ledger entry.
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
INSERT_CATEGORIES = {"necessary_addition", "structural_completion"}
DELETE_CATEGORIES = {"necessary_deletion"}
PLACEHOLDERS = {"todo", "tbd", "requires_human_review", "待确认", "待审核", "待补充"}


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
        ppr_key = sha256_bytes(canonical_xml(ppr_clone, drop_property_changes=True))
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


def story_view(path: Path, mode: str, author: str) -> dict[str, dict[str, object]]:
    view: dict[str, dict[str, object]] = {}
    for part in story_parts(path):
        root = read_xml(path, part)
        paragraphs = [collect_text(p, mode, author) for p in root.xpath(".//w:p", namespaces=NS)]
        table_shapes = []
        for table in root.xpath(".//w:tbl", namespaces=NS):
            rows = table.xpath("./w:tr", namespaces=NS)
            table_shapes.append([len(row.xpath("./w:tc", namespaces=NS)) for row in rows])
        formatting = [paragraph_format_signature(p, mode, author) for p in root.xpath(".//w:p", namespaces=NS)]
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
        paragraphs = root.xpath(".//w:p", namespaces=NS)
        paragraph_index = {p: i for i, p in enumerate(paragraphs)}
        change_index = 0
        for node in root.xpath(".//w:ins | .//w:del", namespaces=NS):
            if node.get(qn("author")) != author:
                continue
            kind = "insert" if node.tag == qn("ins") else "delete"
            text = change_text(node, kind)
            ancestors = node.xpath("ancestor::w:p[1]", namespaces=NS)
            p_index = paragraph_index.get(ancestors[0], -1) if ancestors else -1
            location = f"{part}::p={p_index}::change={change_index}"
            digest = sha256_bytes(text.encode("utf-8"))
            fragment_id = sha256_bytes(f"{kind}\0{location}\0{text}".encode("utf-8"))
            records.append({
                "fragment_id": fragment_id,
                "kind": kind,
                "text": text,
                "length": len(text),
                "sha256": digest,
                "location": location,
            })
            change_index += 1
    return records


def stats(values: list[int]) -> dict[str, object]:
    if not values:
        return {"count": 0, "median": 0, "max": 0, "mean": 0.0, "le5": 0, "le15": 0}
    return {
        "count": len(values),
        "median": statistics.median(values),
        "max": max(values),
        "mean": round(sum(values) / len(values), 2),
        "le5": sum(value <= 5 for value in values),
        "le15": sum(value <= 15 for value in values),
    }


def load_ledger(path: Path | None, errors: list[str]) -> dict[str, object]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"ledger unreadable: {exc}")
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != "2.0":
        errors.append("ledger must be an object with schema_version 2.0")
        return {}
    if not isinstance(data.get("exceptions"), list):
        errors.append("ledger exceptions must be an array")
        return {}
    return data


def has_placeholder(value: object) -> bool:
    normalized = str(value).strip().lower()
    return not normalized or any(token in normalized for token in PLACEHOLDERS)


def paragraph_for(fragment: dict[str, object], view: dict[str, dict[str, object]]) -> str:
    match = re.match(r"(.+)::p=(-?\d+)::change=\d+$", str(fragment["location"]))
    if not match:
        return ""
    part, index_text = match.groups()
    index = int(index_text)
    paragraphs = list(view.get(part, {}).get("paragraphs", []))
    return paragraphs[index] if 0 <= index < len(paragraphs) else ""


def validate_long_fragment(
    fragment: dict[str, object],
    item: dict[str, object] | None,
    original_context: str,
    resulting_paragraph: str,
    errors: list[str],
) -> bool:
    prefix = f"long {fragment['kind']} at {fragment['location']}"
    if item is None:
        errors.append(f"{prefix}: no exact ledger entry for fragment_id {fragment['fragment_id']}")
        return False
    exact = {
        "fragment_id": fragment["fragment_id"],
        "kind": fragment["kind"],
        "location": fragment["location"],
        "full_text": fragment["text"],
        "sha256": fragment["sha256"],
        "original_context": original_context,
        "resulting_paragraph": resulting_paragraph,
    }
    mismatches = [key for key, value in exact.items() if item.get(key) != value]
    if mismatches:
        errors.append(f"{prefix}: ledger mismatch in {mismatches}")
        return False
    category = item.get("category")
    allowed = INSERT_CATEGORIES if fragment["kind"] == "insert" else DELETE_CATEGORIES
    if category not in allowed:
        errors.append(f"{prefix}: category {category!r} is not allowed for {fragment['kind']}")
        return False
    for field in ("original_gap", "reason"):
        if len(str(item.get(field, "")).strip()) < 8 or has_placeholder(item.get(field)):
            errors.append(f"{prefix}: {field} is missing, generic or pending")
            return False
    if item.get("review_status") != "approved" or has_placeholder(item.get("approved_by")) or has_placeholder(item.get("approved_at")):
        errors.append(f"{prefix}: human approval is not complete")
        return False
    return True


def comment_metrics(path: Path) -> tuple[int, int, int, int, set[str], set[str], set[str], set[str]]:
    with zipfile.ZipFile(path) as archive:
        count = 0
        ids: set[str] = set()
        if "word/comments.xml" in archive.namelist():
            comments = etree.fromstring(archive.read("word/comments.xml"))
            nodes = comments.xpath(".//w:comment", namespaces=NS)
            count = len(nodes)
            ids = {node.get(qn("id"), "") for node in nodes}
    refs: set[str] = set()
    starts: set[str] = set()
    ends: set[str] = set()
    for part in story_parts(path):
        root = read_xml(path, part)
        refs.update(node.get(qn("id"), "") for node in root.xpath(".//w:commentReference", namespaces=NS))
        starts.update(node.get(qn("id"), "") for node in root.xpath(".//w:commentRangeStart", namespaces=NS))
        ends.update(node.get(qn("id"), "") for node in root.xpath(".//w:commentRangeEnd", namespaces=NS))
    return count, len(refs), len(starts), len(ends), ids, refs, starts, ends


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--redline", required=True, type=Path)
    parser.add_argument("--clean", required=True, type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--author", default="法务")
    parser.add_argument("--max-fragment", type=int, default=15)
    parser.add_argument("--max-median-delete", type=int, default=15)
    parser.add_argument("--max-median-insert", type=int, default=15)
    parser.add_argument("--expected-comments", type=int)
    parser.add_argument("--out-json", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    validate_package(args.original, "original", errors)
    validate_package(args.redline, "redline", errors)
    validate_package(args.clean, "clean", errors)
    packages_valid = not errors
    if packages_valid:
        try:
            compare_critical_structure(args.original, args.redline, errors)
        except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
            errors.append(f"critical structure comparison failed: {exc}")

    source_hash = sha256_file(args.original)
    redline_hash = sha256_file(args.redline)
    clean_hash = sha256_file(args.clean)
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
    accepted_matches_clean = False
    source_view: dict[str, dict[str, object]] = {}
    accepted_view: dict[str, dict[str, object]] = {}
    if not errors or parts:
        try:
            source_view = story_view(args.original, "current", args.author)
            rejected_view = story_view(args.redline, "reject", args.author)
            accepted_view = story_view(args.redline, "accept", args.author)
            clean_view = story_view(args.clean, "current", args.author)
            source_matches_rejected = compare_views(
                "source vs redline rejected view",
                source_view,
                rejected_view,
                errors,
            )
            accepted_matches_clean = compare_views(
                "redline accepted view vs clean",
                accepted_view,
                clean_view,
                errors,
            )
        except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
            errors.append(f"story comparison failed: {exc}")

    ledger = load_ledger(args.ledger, errors)
    entries = {
        str(item.get("fragment_id")): item
        for item in ledger.get("exceptions", [])
        if isinstance(item, dict) and item.get("fragment_id")
    }
    if ledger:
        if ledger.get("source_contract_sha256") != source_hash:
            errors.append("ledger source_contract_sha256 does not match original")
        if ledger.get("redline_sha256") != redline_hash:
            errors.append("ledger redline_sha256 does not match redline")
        if ledger.get("author") != args.author:
            errors.append("ledger author does not match gate author")

    approved_long = 0
    long_fragments = [item for item in parts if int(item["length"]) > args.max_fragment]
    for fragment in long_fragments:
        if validate_long_fragment(
            fragment,
            entries.get(str(fragment["fragment_id"])),
            paragraph_for(fragment, source_view),
            paragraph_for(fragment, accepted_view),
            errors,
        ):
            approved_long += 1
    extra_entries = sorted(set(entries) - {str(item["fragment_id"]) for item in long_fragments})
    if extra_entries:
        errors.append(f"ledger contains {len(extra_entries)} stale/unmatched exception entries")

    if float(delete_stats["median"]) > args.max_median_delete:
        warnings.append(f"delete median {delete_stats['median']} exceeds {args.max_median_delete}")
    if float(insert_stats["median"]) > args.max_median_insert:
        warnings.append(f"insert median {insert_stats['median']} exceeds {args.max_median_insert}")

    try:
        count, ref_count, start_count, end_count, ids, refs, starts, ends = comment_metrics(args.redline)
        # Point comments have a reference but no range anchors. Ranged comments
        # must still have balanced start/end anchors and valid IDs.
        if ids != refs or starts != ends or not starts.issubset(ids):
            errors.append(
                "comment IDs/references or range anchors differ: "
                f"comments={sorted(ids)} refs={sorted(refs)} starts={sorted(starts)} ends={sorted(ends)}"
            )
        if args.expected_comments is not None and count != args.expected_comments:
            errors.append(f"expected {args.expected_comments} comments but found {count}")
    except (KeyError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        count = ref_count = start_count = end_count = 0
        errors.append(f"comment validation failed: {exc}")

    report = {
        "schema_version": "2.0",
        "status": "PASS" if not errors else "FAIL",
        "original": str(args.original),
        "redline": str(args.redline),
        "clean": str(args.clean),
        "hashes": {"original": source_hash, "redline": redline_hash, "clean": clean_hash},
        "author": args.author,
        "track_revisions": track,
        "source_matches_rejected_view": source_matches_rejected,
        "accepted_view_matches_clean": accepted_matches_clean,
        "insert": insert_stats,
        "delete": delete_stats,
        "long_fragments": len(long_fragments),
        "approved_long_fragment_exceptions": approved_long,
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
