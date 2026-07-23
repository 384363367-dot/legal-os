#!/usr/bin/env python3
"""Block Legal OS Final delivery unless deterministic controls pass."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


FINAL_INTENTS = {"internal-final", "external-final", "filing", "publishing"}
FORMAL_SOURCE_TYPES = {
    "law", "administrative-regulation", "judicial-interpretation",
    "department-rule", "local-rule", "case", "policy", "official-publication",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load(path: Path | None, label: str, errors: list[str]) -> dict:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} unreadable: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return data


def validate_signoff(
    data: dict,
    artifact: Path,
    risk: str,
    intent: str,
    matter_task_id: str,
    errors: list[str],
) -> None:
    if data.get("schema_version") != "1.0":
        errors.append("signoff schema_version must be 1.0")
    if data.get("status") != "approved":
        errors.append("signoff status is not approved")
    if not str(data.get("reviewer", "")).strip() or not str(data.get("reviewed_at", "")).strip():
        errors.append("signoff reviewer/reviewed_at missing")
    if data.get("artifact_sha256") != sha256(artifact):
        errors.append("signoff artifact hash does not match delivery artifact")
    try:
        signed_path = Path(str(data.get("artifact_path", ""))).expanduser().resolve()
    except OSError:
        signed_path = Path("/__invalid_signoff_path__")
    if signed_path != artifact.resolve():
        errors.append("signoff artifact_path does not match delivery artifact")
    if data.get("matter_task_id") != matter_task_id:
        errors.append("signoff matter_task_id does not match matter manifest")
    if data.get("risk_level") != risk:
        errors.append("signoff risk_level does not match release request")
    if data.get("permitted_use") != intent:
        errors.append("signoff permitted_use does not match release intent")
    checks = data.get("checks", {})
    for key in ("facts", "authority", "strategy", "format", "privacy"):
        if checks.get(key) is not True:
            errors.append(f"signoff check not approved: {key}")


def validate_authority(data: dict, matter_task_id: str, errors: list[str]) -> None:
    if data.get("schema_version") != "1.0":
        errors.append("authority package schema_version must be 1.0")
    if not str(data.get("verified_by", "")).strip() or not str(data.get("verified_at", "")).strip():
        errors.append("authority package verifier/time missing")
    if data.get("matter_task_id") != matter_task_id:
        errors.append("authority package matter_task_id does not match matter manifest")
    propositions = data.get("propositions")
    if not isinstance(propositions, list) or not propositions:
        errors.append("authority package has no propositions")
        return
    ids: set[str] = set()
    for index, item in enumerate(propositions):
        if not isinstance(item, dict):
            errors.append(f"authority proposition {index} is not an object")
            continue
        pid = str(item.get("proposition_id", ""))
        if not pid or pid in ids:
            errors.append(f"authority proposition {index} has missing/duplicate id")
        ids.add(pid)
        source_type = item.get("source_type")
        if source_type not in FORMAL_SOURCE_TYPES:
            errors.append(f"authority proposition {pid}: invalid source_type")
        expected_status = "verified-source" if source_type == "case" else "effective"
        if item.get("current_status") != expected_status:
            errors.append(f"authority proposition {pid}: current_status must be {expected_status}")
        for key in ("text", "authority_id", "title", "issuing_body", "locator", "pinpoint", "accessed_at", "support", "scope"):
            if not str(item.get(key, "")).strip():
                errors.append(f"authority proposition {pid}: missing {key}")
        if item.get("review_status") != "approved":
            errors.append(f"authority proposition {pid}: not approved")
        if not isinstance(item.get("contrary_sources"), list):
            errors.append(f"authority proposition {pid}: contrary_sources must be an array")


def validate_matter(
    data: dict,
    output: Path,
    intent: str,
    public_roots: list[Path],
    errors: list[str],
) -> str:
    if data.get("schema_version") != "1.0":
        errors.append("matter manifest schema_version must be 1.0")
    level = data.get("classification")
    if level not in {"S0", "S1", "S2", "S3"}:
        errors.append("matter classification invalid")
    if not str(data.get("owner", "")).strip():
        errors.append("matter owner missing")
    task_id = str(data.get("matter_task_id", "")).strip()
    if not task_id:
        errors.append("matter task id missing")
    matter_root_value = str(data.get("matter_root", "")).strip()
    matter_root = Path(matter_root_value).expanduser().resolve() if matter_root_value else None
    if matter_root is None or not matter_root.is_dir():
        errors.append("matter root missing or not a directory")
    if level in {"S1", "S2", "S3"} and data.get("public_export_allowed") is not False:
        errors.append(f"{level} matter must set public_export_allowed=false")
    for public_root in public_roots:
        if is_within(output, public_root) and (
            level != "S0" or data.get("public_export_allowed") is not True
        ):
            errors.append(
                "output under a declared public root requires S0 classification "
                "and public_export_allowed=true"
            )
    if intent == "publishing" and (level != "S0" or data.get("public_export_allowed") is not True):
        errors.append("publishing requires S0 classification and public_export_allowed=true")
    if data.get("retention_status") == "deleted":
        errors.append("deleted matter cannot produce a new release")
    sources = data.get("source_files")
    if not isinstance(sources, list) or not sources:
        errors.append("matter manifest must list at least one source file")
    elif matter_root is not None:
        for index, item in enumerate(sources):
            if not isinstance(item, dict):
                errors.append(f"matter source {index} is not an object")
                continue
            source_value = str(item.get("path", "")).strip()
            source_path = Path(source_value).expanduser()
            if not source_value:
                errors.append(f"matter source {index} path missing")
                continue
            if source_path.is_absolute():
                resolved = source_path.resolve()
            else:
                resolved = (matter_root / source_path).resolve()
            if not is_within(resolved, matter_root):
                errors.append(f"matter source {index} escapes matter root")
                continue
            if not resolved.is_file():
                errors.append(f"matter source {index} missing: {source_value}")
            elif item.get("sha256") != sha256(resolved):
                errors.append(f"matter source {index} hash mismatch")
            if item.get("role") not in {"original", "attachment", "evidence", "reference"}:
                errors.append(f"matter source {index} role invalid")
    return task_id


def validate_policy(data: dict, matter_task_id: str, errors: list[str]) -> None:
    if not data:
        return
    if data.get("schema_version") != "1.0":
        errors.append("negotiation policy schema_version must be 1.0")
    if not str(data.get("approved_by", "")).strip() or not str(data.get("approved_at", "")).strip():
        errors.append("negotiation policy is not approved")
    if data.get("matter_task_id") != matter_task_id:
        errors.append("negotiation policy matter_task_id does not match matter manifest")
    for item in data.get("parameters", []):
        if item.get("status") != "approved" or item.get("source") == "pending-choice":
            errors.append(f"negotiation parameter is pending: {item.get('key')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--output-path", required=True, type=Path)
    parser.add_argument("--intent", required=True, choices=["internal-draft", "internal-final", "external-final", "filing", "publishing"])
    parser.add_argument("--risk-level", required=True, choices=["R0", "R1", "R2", "R3"])
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--redline-report", type=Path)
    parser.add_argument("--authority-required", action="store_true")
    parser.add_argument("--authority-package", type=Path)
    parser.add_argument("--signoff", type=Path)
    parser.add_argument("--matter-manifest", required=True, type=Path)
    parser.add_argument("--negotiation-policy", type=Path)
    parser.add_argument(
        "--public-root",
        action="append",
        default=[],
        type=Path,
        help="Declared public repository or export root; may be supplied more than once.",
    )
    parser.add_argument("--out-json", type=Path)
    args = parser.parse_args()
    errors: list[str] = []

    if not args.artifact.is_file():
        errors.append("delivery artifact missing")
    matter = load(args.matter_manifest, "matter manifest", errors)
    matter_task_id = validate_matter(
        matter,
        args.output_path,
        args.intent,
        args.public_root,
        errors,
    )

    if args.contract:
        report = load(args.redline_report, "redline report", errors) if args.redline_report else {}
        if not report:
            errors.append("contract release requires a redline report")
        elif report.get("status") != "PASS":
            errors.append("redline quality gate did not PASS")
        elif report.get("hashes", {}).get("redline") != sha256(args.artifact):
            errors.append("redline report hash does not match delivery artifact")

    if args.authority_required:
        authority = load(args.authority_package, "authority package", errors) if args.authority_package else {}
        if not authority:
            errors.append("formal legal authority is required but authority package is missing")
        else:
            validate_authority(authority, matter_task_id, errors)

    validate_policy(load(args.negotiation_policy, "negotiation policy", errors), matter_task_id, errors)

    final_requested = args.intent in FINAL_INTENTS
    if final_requested or args.risk_level in {"R2", "R3"}:
        signoff = load(args.signoff, "review signoff", errors) if args.signoff else {}
        if not signoff:
            errors.append("Final/R2/R3 release requires human review signoff")
        elif args.artifact.is_file():
            validate_signoff(signoff, args.artifact, args.risk_level, args.intent, matter_task_id, errors)

    decision = "RELEASE" if not errors and final_requested else "DRAFT_ONLY" if not errors else "BLOCKED"
    report = {
        "schema_version": "1.0",
        "status": "PASS" if not errors else "FAIL",
        "decision": decision,
        "artifact": str(args.artifact),
        "artifact_sha256": sha256(args.artifact) if args.artifact.is_file() else None,
        "output_path": str(args.output_path),
        "intent": args.intent,
        "risk_level": args.risk_level,
        "errors": errors,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
