#!/usr/bin/env python3
"""Reuse an exact sign-off for strict DOCX format-only changes or make a review candidate."""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
VISUAL_RUN_PROPERTIES = {"b", "bCs", "i", "iCs"}
VISUAL_PARAGRAPH_PROPERTIES = {"jc"}
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"}


class RebindError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_signoff(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RebindError(f"signoff JSON is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise RebindError("signoff must be a JSON object")
    return data


def _nested_hash_matches(nested: object, field: str, expected_hash: str) -> bool:
    """Allow omitted hashes only for metadata-inheriting light contract reviews."""
    if not isinstance(nested, dict):
        return False
    if "artifact_sha256" in nested:
        return nested.get("artifact_sha256") == expected_hash
    return field == "contract_protection_review" and nested.get("review_path") == "light"


def validate_old_signoff(data: dict, signoff_path: Path, old_artifact: Path) -> None:
    old_hash = sha256(old_artifact)
    if data.get("schema_version") != "1.0" or data.get("status") != "approved":
        raise RebindError("old signoff is not a schema 1.0 approved signoff")
    if not str(data.get("reviewer", "")).strip() or not str(data.get("reviewed_at", "")).strip():
        raise RebindError("old signoff reviewer/time is missing")
    if data.get("artifact_sha256") != old_hash:
        raise RebindError("old signoff hash does not match exact old artifact")
    if Path(str(data.get("artifact_path", ""))).expanduser().resolve() != old_artifact.resolve():
        raise RebindError("old signoff path does not match exact old artifact")
    checks = data.get("checks")
    if not isinstance(checks, dict) or any(checks.get(key) is not True for key in ("facts", "authority", "strategy", "format", "privacy")):
        raise RebindError("old signoff does not have all required approved checks")
    if "rebind_candidate" in data:
        raise RebindError("an existing rebind candidate cannot be used as the old approved signoff")
    for field in ("contract_protection_review", "amount_review"):
        nested = data.get(field)
        if nested is not None and not _nested_hash_matches(nested, field, old_hash):
            raise RebindError(f"old {field} is stale or does not match the old artifact")
    if "rebind_record" in data:
        prior_errors = validate_rebind_record(data, old_artifact, signoff_path)
        if prior_errors:
            raise RebindError("old approved rebind sign-off is not valid: " + "; ".join(prior_errors))


def _canonical_xml(path: str, data: bytes) -> bytes:
    try:
        root = etree.fromstring(data)
    except etree.XMLSyntaxError as exc:
        raise RebindError(f"malformed XML in {path}: {exc}") from exc
    for rpr in root.xpath(".//w:rPr", namespaces=NS):
        for child in list(rpr):
            qname = etree.QName(child)
            if qname.namespace == W and qname.localname in VISUAL_RUN_PROPERTIES:
                rpr.remove(child)
    for ppr in root.xpath(".//w:pPr", namespaces=NS):
        for child in list(ppr):
            qname = etree.QName(child)
            if qname.namespace == W and qname.localname in VISUAL_PARAGRAPH_PROPERTIES:
                ppr.remove(child)
    # Empty property containers carry no remaining content after whitelist removal.
    for node in root.xpath(".//w:rPr | .//w:pPr", namespaces=NS):
        if not list(node) and not node.attrib and node.getparent() is not None:
            node.getparent().remove(node)
    return etree.tostring(root, method="c14n", exclusive=True, with_comments=True)


def _format_properties(data: bytes) -> dict[str, str]:
    root = etree.fromstring(data)
    result: dict[str, str] = {}
    for container_name, allowed in (("rPr", VISUAL_RUN_PROPERTIES), ("pPr", VISUAL_PARAGRAPH_PROPERTIES)):
        for container in root.xpath(f".//w:{container_name}", namespaces=NS):
            parent = container.getparent()
            parent_path = root.getroottree().getpath(parent) if parent is not None else "/"
            for child in list(container):
                qname = etree.QName(child)
                if qname.namespace == W and qname.localname in allowed:
                    key = f"{parent_path}/{container_name}/{qname.localname}"
                    result[key] = etree.tostring(child, method="c14n", exclusive=True).decode("utf-8")
    return result


def docx_format_only(old_artifact: Path, new_artifact: Path) -> tuple[bool, list[dict[str, str]], str, list[dict[str, str]]]:
    try:
        with zipfile.ZipFile(old_artifact) as old_zip, zipfile.ZipFile(new_artifact) as new_zip:
            old_name_list = old_zip.namelist()
            new_name_list = new_zip.namelist()
            if len(old_name_list) != len(set(old_name_list)) or len(new_name_list) != len(set(new_name_list)):
                return False, [], "DOCX package has duplicate ZIP member names.", []
            old_names = set(old_name_list)
            new_names = set(new_name_list)
            changed_names = sorted(old_names | new_names)
            changed_names = [name for name in changed_names if name not in old_names or name not in new_names or old_zip.read(name) != new_zip.read(name)]
            changes: list[dict[str, str]] = []
            for name in changed_names:
                old_data = old_zip.read(name) if name in old_names else None
                new_data = new_zip.read(name) if name in new_names else None
                changes.append({
                    "part": name,
                    "old_sha256": hashlib.sha256(old_data).hexdigest() if old_data is not None else "<absent>",
                    "new_sha256": hashlib.sha256(new_data).hexdigest() if new_data is not None else "<absent>",
                })
            if old_names != new_names:
                return False, changes, "DOCX package part inventory changed.", []
            if not changed_names:
                return True, [], "Old and new DOCX packages are byte-identical.", []
            if changed_names != ["word/document.xml"]:
                return False, changes, "Only word/document.xml is eligible for automatic formatting-only comparison; all other OOXML part changes need review.", []
            old_semantic = _canonical_xml("word/document.xml", old_zip.read("word/document.xml"))
            new_semantic = _canonical_xml("word/document.xml", new_zip.read("word/document.xml"))
            if old_semantic != new_semantic:
                return False, changes, "Document XML differs outside the strict run/paragraph visual-format allowlist.", []
            old_props = _format_properties(old_zip.read("word/document.xml"))
            new_props = _format_properties(new_zip.read("word/document.xml"))
            property_changes = [
                {
                    "node_property": key,
                    "old_value": old_props.get(key, "<absent>"),
                    "new_value": new_props.get(key, "<absent>"),
                }
                for key in sorted(old_props.keys() | new_props.keys())
                if old_props.get(key) != new_props.get(key)
            ]
            summary = (
                "word/document.xml is identical after removing only direct w:b/w:bCs/w:i/w:iCs and w:jc properties; "
                "all other package parts are byte-identical. Exact property changes: "
                + json.dumps(property_changes, ensure_ascii=False, sort_keys=True)
            )
            return True, changes, summary, property_changes
    except (OSError, zipfile.BadZipFile, KeyError, RebindError, etree.XMLSyntaxError) as exc:
        return False, [], f"DOCX package cannot be safely compared: {exc}", []


def run_redline_gate(old_artifact: Path, new_artifact: Path) -> tuple[str, dict]:
    gate = Path(__file__).resolve().parents[2] / "legal-os-contract" / "scripts" / "redline_quality_gate.py"
    if not gate.is_file():
        return "FAIL", {"errors": ["Contract redline gate unavailable"]}
    with tempfile.TemporaryDirectory(prefix="legalos-rebind-redline-") as tmp:
        report_path = Path(tmp) / "redline.json"
        result = subprocess.run(
            [sys.executable, str(gate), "--original", str(old_artifact), "--redline", str(new_artifact), "--out-json", str(report_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "FAIL", {"errors": ["Redline gate did not produce readable JSON", result.stderr[-1000:]]}
    return ("PASS" if result.returncode == 0 and report.get("status") == "PASS" else "FAIL"), report


def readable_text_diff(old_artifact: Path, new_artifact: Path) -> str | None:
    if old_artifact.suffix.casefold() not in TEXT_SUFFIXES or new_artifact.suffix.casefold() not in TEXT_SUFFIXES:
        return None
    try:
        old_text = old_artifact.read_text(encoding="utf-8").splitlines(keepends=True)
        new_text = new_artifact.read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeDecodeError):
        return None
    return "".join(difflib.unified_diff(old_text, new_text, fromfile=str(old_artifact), tofile=str(new_artifact)))


def _record_errors(data: dict, new_artifact: Path, signoff_path: Path, *, depth: int = 0) -> list[str]:
    errors: list[str] = []
    record = data.get("rebind_record")
    if not isinstance(record, dict):
        return ["rebind record must be an object"]
    if depth > 5:
        return ["rebind record chain exceeds five links"]
    classification = record.get("classification")
    if record.get("schema_version") != "1.0" or not isinstance(classification, str) or classification not in {"identical", "format-only"}:
        errors.append("only a schema 1.0 identical/format-only rebind can reuse an approved sign-off")
    if record.get("requires_affected_review") is not False:
        errors.append("format-only rebind must not require affected review")
    try:
        old_artifact = Path(str(record.get("old_artifact_path", ""))).expanduser().resolve(strict=True)
        old_signoff_path = Path(str(record.get("old_signoff_path", ""))).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return errors + ["rebind record old artifact/signoff path is missing or unreadable"]
    if old_artifact == new_artifact.resolve():
        errors.append("rebind record old and new artifact paths must differ")
    if old_signoff_path == signoff_path.resolve():
        errors.append("rebind record must refer to a separate old sign-off file")
    if not isinstance(record.get("old_artifact_sha256"), str) or sha256(old_artifact) != record.get("old_artifact_sha256"):
        errors.append("rebind record old artifact hash mismatch")
    try:
        if not isinstance(record.get("new_artifact_path"), str) or Path(record["new_artifact_path"]).expanduser().resolve() != new_artifact.resolve():
            errors.append("rebind record new artifact path mismatch")
    except (OSError, RuntimeError, TypeError, ValueError):
        errors.append("rebind record new artifact path is invalid")
    try:
        current_new_hash = sha256(new_artifact)
        old_signoff_hash = sha256(old_signoff_path)
    except OSError as exc:
        return errors + [f"rebind proof input cannot be read: {exc}"]
    if current_new_hash != record.get("new_artifact_sha256"):
        errors.append("rebind record new artifact hash mismatch")
    if old_signoff_hash != record.get("old_signoff_sha256"):
        errors.append("rebind record old sign-off hash mismatch")
    try:
        old_data = load_signoff(old_signoff_path)
    except RebindError as exc:
        return errors + [f"rebind record old sign-off is invalid: {exc}"]
    if old_data.get("schema_version") != "1.0" or old_data.get("status") != "approved":
        errors.append("rebind record old sign-off is not an approved schema 1.0 sign-off")
    if old_data.get("artifact_sha256") != record.get("old_artifact_sha256"):
        errors.append("rebind record does not start from the exact artifact approved by old sign-off")
    if Path(str(old_data.get("artifact_path", ""))).expanduser().resolve() != old_artifact.resolve():
        errors.append("rebind record old sign-off artifact path mismatch")
    if "rebind_candidate" in old_data:
        errors.append("rebind record old sign-off is a pending candidate")
    if not isinstance(old_data.get("checks"), dict) or any(old_data["checks"].get(key) is not True for key in ("facts", "authority", "strategy", "format", "privacy")):
        errors.append("rebind record old sign-off does not retain all approved checks")
    for field in ("contract_protection_review", "amount_review"):
        nested = old_data.get(field)
        if nested is not None and not _nested_hash_matches(nested, field, record.get("old_artifact_sha256")):
            errors.append(f"rebind record old {field} hash is stale")
    expected = copy.deepcopy(old_data)
    actual = copy.deepcopy(data)
    expected.pop("rebind_record", None)
    actual.pop("rebind_record", None)
    expected["artifact_path"] = str(new_artifact.resolve())
    expected["artifact_sha256"] = current_new_hash
    for field in ("contract_protection_review", "amount_review"):
        nested = expected.get(field)
        if isinstance(nested, dict) and "artifact_sha256" in nested:
            nested["artifact_sha256"] = current_new_hash
    if expected != actual:
        errors.append("rebind changed sign-off fields outside artifact path/hash and unchanged nested review hashes")
    if old_data.get("rebind_record") is not None:
        errors.extend(_record_errors(old_data, old_artifact, old_signoff_path, depth=depth + 1))
    try:
        is_format, changed_parts, summary, property_changes = docx_format_only(old_artifact, new_artifact)
    except (TypeError, ValueError, OSError, KeyError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        return errors + [f"rebind format proof cannot be recomputed: {exc}"]
    expected_classification = "identical" if is_format and not changed_parts else "format-only" if is_format else None
    if expected_classification is None:
        errors.append("rebind artifacts are not identical or strict format-only")
    if record.get("classification") != expected_classification:
        errors.append("rebind classification does not match recomputed DOCX proof")
    if record.get("changed_parts") != changed_parts:
        errors.append("rebind changed-parts evidence does not match recomputed DOCX proof")
    if record.get("diff_summary") != summary:
        errors.append("rebind diff summary does not match recomputed DOCX proof")
    if record.get("visual_property_changes") != property_changes:
        errors.append("rebind visual-property evidence does not match recomputed DOCX proof")
    return errors


def validate_rebind_record(data: dict, new_artifact: Path, signoff_path: Path) -> list[str]:
    try:
        return _record_errors(data, new_artifact, signoff_path)
    except (TypeError, ValueError, OSError, KeyError, RuntimeError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        return [f"rebind record structure is invalid: {exc}"]


def export_candidate(args: argparse.Namespace) -> tuple[dict, dict]:
    for input_path, label in ((args.signoff, "signoff"), (args.old_artifact, "old artifact"), (args.new_artifact, "new artifact")):
        if not input_path.is_file():
            raise RebindError(f"{label} file missing: {input_path}")
    output = args.out_candidate.resolve()
    for input_path, label in ((args.signoff, "signoff"), (args.old_artifact, "old artifact"), (args.new_artifact, "new artifact")):
        same_file = output.exists() and input_path.exists() and output.samefile(input_path)
        if output == input_path.resolve() or same_file:
            raise RebindError(f"candidate output must not overwrite input {label}")

    data = load_signoff(args.signoff)
    validate_old_signoff(data, args.signoff, args.old_artifact)
    old_hash = sha256(args.old_artifact)
    new_hash = sha256(args.new_artifact)
    if args.old_artifact.resolve() == args.new_artifact.resolve():
        raise RebindError("old and new artifact paths must differ")

    is_docx = args.old_artifact.suffix.casefold() == ".docx" and args.new_artifact.suffix.casefold() == ".docx"
    format_only, changed_parts, format_summary, property_changes = docx_format_only(args.old_artifact, args.new_artifact) if is_docx else (False, [], "Non-DOCX changes are never auto-classified as format-only.", [])
    redline_status = "not-applicable"
    diff_summary = format_summary
    classification = "identical" if format_only and not changed_parts else "format-only" if format_only else "content-change"

    if not format_only:
        if is_docx:
            redline_status, redline = run_redline_gate(args.old_artifact, args.new_artifact)
            changes = redline.get("change_text", [])
            if changes:
                diff_summary = "Actual tracked redline changes:\n" + json.dumps(changes, ensure_ascii=False, indent=2)
            else:
                diff_summary = "DOCX package changes:\n" + format_summary + "\nRedline gate findings:\n" + "\n".join(str(item) for item in redline.get("errors", []))
            if redline_status != "PASS":
                classification = "manual-review-required"
        else:
            diff = readable_text_diff(args.old_artifact, args.new_artifact)
            if diff is None:
                raise RebindError("changed non-DOCX artifact has no supported readable diff; no candidate produced")
            diff_summary = "Readable text diff:\n" + diff
            redline_status = "not-applicable"
        for key, value in (("scope", args.scope), ("semantic_review", args.semantic_review), ("reviewed_by", args.reviewed_by), ("reviewed_at", args.reviewed_at)):
            if not isinstance(value, str) or not value.strip():
                raise RebindError(f"content changes require {key.replace('_', ' ')}")

    candidate = copy.deepcopy(data)
    candidate["artifact_path"] = str(args.new_artifact.resolve())
    candidate["artifact_sha256"] = new_hash
    if format_only:
        for field in ("contract_protection_review", "amount_review"):
            nested = candidate.get(field)
            if isinstance(nested, dict) and "artifact_sha256" in nested:
                nested["artifact_sha256"] = new_hash
        candidate.pop("rebind_candidate", None)
        candidate["rebind_record"] = {
            "schema_version": "1.0",
            "classification": classification,
            "old_artifact_path": str(args.old_artifact.resolve()),
            "old_artifact_sha256": old_hash,
            "old_signoff_path": str(args.signoff.resolve()),
            "old_signoff_sha256": sha256(args.signoff),
            "new_artifact_path": str(args.new_artifact.resolve()),
            "new_artifact_sha256": new_hash,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "changed_parts": changed_parts,
            "visual_property_changes": property_changes,
            "diff_summary": diff_summary,
            "requires_affected_review": False,
        }
        decision = "REUSED_PRIOR_APPROVAL_AFTER_STRICT_FORMAT_PROOF"
        report_status = "REBOUND"
    else:
        candidate["status"] = "pending"
        candidate.pop("rebind_record", None)
        candidate["rebind_candidate"] = {
            "schema_version": "1.0",
            "classification": classification,
            "old_artifact_path": str(args.old_artifact.resolve()),
            "old_artifact_sha256": old_hash,
            "new_artifact_path": str(args.new_artifact.resolve()),
            "new_artifact_sha256": new_hash,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "changed_parts": changed_parts,
            "diff_summary": diff_summary,
            "redline_gate_status": redline_status,
            "requires_affected_review": True,
        }
        candidate["rebind_candidate"].update({
            "scope": args.scope.strip(),
            "semantic_review": args.semantic_review.strip(),
            "reviewed_by": args.reviewed_by.strip(),
            "reviewed_at": args.reviewed_at.strip(),
        })
        decision = "PENDING_HUMAN_REVIEW"
        report_status = "CANDIDATE"
    report = {
        "status": report_status,
        "classification": classification,
        "decision": decision,
        "out_signoff": str(args.out_candidate),
        "artifact_sha256": new_hash,
        "redline_gate_status": redline_status,
        "requires_affected_review": not format_only,
    }
    return candidate, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signoff", required=True, type=Path)
    parser.add_argument("--old-artifact", required=True, type=Path)
    parser.add_argument("--new-artifact", required=True, type=Path)
    parser.add_argument("--out-signoff", "--out-candidate", dest="out_candidate", required=True, type=Path)
    parser.add_argument("--scope")
    parser.add_argument("--semantic-review")
    parser.add_argument("--reviewed-by")
    parser.add_argument("--reviewed-at")
    args = parser.parse_args()
    try:
        candidate, report = export_candidate(args)
    except (RebindError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    args.out_candidate.parent.mkdir(parents=True, exist_ok=True)
    args.out_candidate.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
