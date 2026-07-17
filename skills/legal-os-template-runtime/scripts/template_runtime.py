#!/usr/bin/env python3
"""Resolve approved LegalOS templates and audit derived DOCX fidelity."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
PLACEHOLDER_RE = re.compile(
    r"[【〔][^】〕\n]{0,100}(?:填写|待核|日期|名称|金额|合同|项目|期限|如有|收函方|发函方|签名|盖章|起算日|基数|人民法院|________)[^】〕\n]{0,100}[】〕]"
    r"|\[填写[^\]]*\]|模板控制提示|_{4,}"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit(payload: dict, code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(entry: dict, skills_root: Path, catalog_path: Path, private: bool) -> Path:
    if private:
        raw = entry.get("path") or entry.get("source")
        if not raw:
            raise ValueError(f"private template {entry.get('id')} has no path")
        path = Path(raw).expanduser()
        return path if path.is_absolute() else (catalog_path.parent / path).resolve()
    return (skills_root / entry["skill"] / entry["relative_path"]).resolve()


def resolve_template(args: argparse.Namespace) -> int:
    skills_root = args.skills_root.expanduser().resolve()
    catalog_path = args.catalog.expanduser().resolve()

    if args.explicit_template:
        path = args.explicit_template.expanduser().resolve()
        if not path.is_file():
            return emit({"status": "TEMPLATE_REQUIRED", "reason": "explicit template not found", "path": str(path)}, 2)
        return emit({
            "status": "SELECTED",
            "template_id": args.explicit_id,
            "template_scope": "explicit-user-template",
            "document_type": args.document_type,
            "path": str(path),
            "sha256": sha256(path),
            "selection_reason": "explicit user template overrides registered templates"
        })

    public_catalog = load_json(catalog_path)
    candidates: list[tuple[dict, Path, str]] = []
    for entry in public_catalog.get("templates", []):
        if entry.get("document_type") != args.document_type:
            continue
        candidates.append((entry, resolve_path(entry, skills_root, catalog_path, False), "bundled-generic-template"))

    if args.private_catalog:
        private_path = args.private_catalog.expanduser().resolve()
        private_catalog = load_json(private_path)
        for entry in private_catalog.get("templates", []):
            if entry.get("approval_state") != "approved":
                continue
            if entry.get("document_type") != args.document_type:
                continue
            organization = entry.get("organization")
            if organization and organization != args.organization:
                continue
            candidates.append((entry, resolve_path(entry, skills_root, private_path, True), "approved-private-template"))

    if not candidates:
        return emit({"status": "TEMPLATE_REQUIRED", "document_type": args.document_type, "reason": "no approved matching template"}, 2)

    max_priority = max(int(item[0].get("priority", 0)) for item in candidates)
    winners = [item for item in candidates if int(item[0].get("priority", 0)) == max_priority]
    if len(winners) != 1:
        return emit({
            "status": "TEMPLATE_AMBIGUOUS",
            "document_type": args.document_type,
            "candidates": [item[0].get("id") for item in winners]
        }, 4)

    entry, path, scope = winners[0]
    if not path.is_file():
        return emit({"status": "TEMPLATE_INTEGRITY_FAIL", "template_id": entry.get("id"), "reason": "registered file missing", "path": str(path)}, 3)
    actual = sha256(path)
    expected = entry.get("sha256")
    if expected and actual != expected:
        return emit({
            "status": "TEMPLATE_INTEGRITY_FAIL",
            "template_id": entry.get("id"),
            "path": str(path),
            "expected_sha256": expected,
            "actual_sha256": actual
        }, 3)

    return emit({
        "status": "SELECTED",
        "template_id": entry.get("id"),
        "template_scope": scope,
        "document_type": args.document_type,
        "organization": args.organization,
        "path": str(path),
        "sha256": actual,
        "font_profile": entry.get("font_profile"),
        "selection_reason": f"highest approved priority {max_priority}"
    })


def attr(node: ET.Element | None, name: str) -> str | None:
    return None if node is None else node.attrib.get(f"{{{W}}}{name}")


def docx_signature(path: Path) -> dict:
    with zipfile.ZipFile(path) as package:
        bad = package.testzip()
        if bad:
            raise ValueError(f"corrupt ZIP member: {bad}")
        names = set(package.namelist())
        if "word/document.xml" not in names:
            raise ValueError("not a DOCX package")
        root = ET.fromstring(package.read("word/document.xml"))

    sections = []
    for section in root.findall(".//w:sectPr", NS):
        size = section.find("w:pgSz", NS)
        margin = section.find("w:pgMar", NS)
        sections.append({
            "size": {key: attr(size, key) for key in ("w", "h", "orient")},
            "margin": {key: attr(margin, key) for key in ("top", "right", "bottom", "left", "header", "footer", "gutter")}
        })

    fonts = set()
    for node in root.findall(".//w:rFonts", NS):
        value = attr(node, "eastAsia")
        if value:
            fonts.add(value)

    text = "".join(node.text or "" for node in root.findall(".//w:t", NS))
    return {
        "sections": sections,
        "headers": sorted(name for name in names if re.fullmatch(r"word/header\d+\.xml", name)),
        "footers": sorted(name for name in names if re.fullmatch(r"word/footer\d+\.xml", name)),
        "drawings": len(root.findall(".//w:drawing", NS)),
        "pict": len(root.findall(".//w:pict", NS)),
        "tables": len(root.findall(".//w:tbl", NS)),
        "east_asia_fonts": sorted(fonts),
        "text": text
    }


def audit_docx(args: argparse.Namespace) -> int:
    template = args.template.expanduser().resolve()
    output = args.output.expanduser().resolve()
    issues: list[str] = []
    try:
        base = docx_signature(template)
        derived = docx_signature(output)
    except (OSError, zipfile.BadZipFile, ET.ParseError, ValueError) as exc:
        return emit({"status": "FAIL", "issues": [str(exc)]}, 5)

    if base["sections"] != derived["sections"]:
        issues.append("section geometry or margins differ from template")
    for key in ("headers", "footers"):
        missing = sorted(set(base[key]) - set(derived[key]))
        if missing:
            issues.append(f"missing required {key}: {missing}")
    if derived["drawings"] < base["drawings"] or derived["pict"] < base["pict"]:
        issues.append("template drawing or VML fallback was removed")
    if derived["tables"] < base["tables"]:
        issues.append("required template table was removed")
    missing_fonts = sorted(set(base["east_asia_fonts"]) - set(derived["east_asia_fonts"]))
    if missing_fonts:
        issues.append(f"required East Asian fonts missing: {missing_fonts}")
    placeholders = sorted(set(PLACEHOLDER_RE.findall(derived["text"])))
    if placeholders and not args.allow_placeholders:
        issues.append(f"unresolved placeholders or template notes remain: {placeholders[:10]}")

    report = {
        "status": "PASS" if not issues else "FAIL",
        "template": str(template),
        "template_sha256": sha256(template),
        "output": str(output),
        "output_sha256": sha256(output),
        "fixed_shell": {
            "sections": derived["sections"],
            "east_asia_fonts": derived["east_asia_fonts"],
            "drawings": derived["drawings"],
            "tables": derived["tables"]
        },
        "flexible_body_policy": "body length and subsection count are intentionally not compared",
        "issues": issues
    }
    return emit(report, 0 if not issues else 5)


def build_parser() -> argparse.ArgumentParser:
    skill_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve")
    resolve.add_argument("--document-type", required=True)
    resolve.add_argument("--organization", default="")
    resolve.add_argument("--skills-root", type=Path, default=skill_root.parent)
    resolve.add_argument("--catalog", type=Path, default=skill_root / "references" / "template-catalog.json")
    resolve.add_argument("--private-catalog", type=Path)
    resolve.add_argument("--explicit-template", type=Path)
    resolve.add_argument("--explicit-id", default="EXPLICIT-USER-TEMPLATE")
    resolve.set_defaults(func=resolve_template)

    audit = sub.add_parser("audit-docx")
    audit.add_argument("--template", type=Path, required=True)
    audit.add_argument("--output", type=Path, required=True)
    audit.add_argument("--allow-placeholders", action="store_true")
    audit.set_defaults(func=audit_docx)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
