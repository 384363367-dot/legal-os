#!/usr/bin/env python3
"""Block Legal OS Final delivery unless deterministic controls pass."""

from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP
from pathlib import Path


FINAL_INTENTS = {"internal-final", "external-final", "filing", "publishing"}
FORMAL_SOURCE_TYPES = {
    "law", "administrative-regulation", "judicial-interpretation",
    "department-rule", "local-rule", "case", "policy", "official-publication",
}
DECIMAL_ROUNDING = {
    "half-up": ROUND_HALF_UP,
    "half-even": ROUND_HALF_EVEN,
    "down": ROUND_DOWN,
    "up": ROUND_UP,
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


def _decimal(value: object, label: str, errors: list[str]) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        errors.append(f"{label} must be a finite number")
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"{label} must be a finite number")
        return None
    if not result.is_finite():
        errors.append(f"{label} must be a finite number")
        return None
    return result


def _required_text(data: dict, key: str, label: str, errors: list[str]) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} missing")
        return ""
    return value.strip()


def validate_contract_protection_review(data: object, artifact: Path, errors: list[str]) -> None:
    if not isinstance(data, dict):
        errors.append("contract Final requires a structured protection review")
        return
    if data.get("schema_version") != "1.0":
        errors.append("contract protection review schema_version must be 1.0")
    if data.get("artifact_sha256") != sha256(artifact):
        errors.append("contract protection review hash does not match delivery artifact")
    _required_text(data, "reviewer", "contract protection reviewer", errors)
    _required_text(data, "reviewed_at", "contract protection review time", errors)
    _required_text(data, "review_scope", "contract protection review scope", errors)
    if data.get("status") != "approved":
        errors.append("contract protection review is not approved")
    if data.get("all_supported_core_risks_mapped") is not True:
        errors.append("contract protection review does not confirm complete core-risk coverage")

    risk_status = data.get("core_risks_status")
    mappings = data.get("risk_mappings")
    if not isinstance(mappings, list):
        errors.append("contract protection risk_mappings must be an array")
        return
    if risk_status == "none":
        if mappings:
            errors.append("zero-core-risk review cannot contain risk mappings")
        _required_text(data, "no_core_risks_rationale", "zero-core-risk rationale", errors)
        return
    if risk_status != "identified":
        errors.append("contract protection core_risks_status must be identified or none")
        return
    if not mappings:
        errors.append("identified core risks require at least one protection mapping")

    seen_ids: set[str] = set()
    for index, item in enumerate(mappings):
        label = f"contract risk mapping {index}"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        risk_id = _required_text(item, "risk_id", f"{label} risk_id", errors)
        if risk_id and risk_id in seen_ids:
            errors.append(f"{label} has duplicate risk_id")
        seen_ids.add(risk_id)
        for key in (
            "core_risk",
            "intended_protection",
            "first_pass_agreed_protection",
            "final_clause_excerpt_or_absence_reason",
            "review_judgment",
        ):
            _required_text(item, key, f"{label} {key}", errors)
        refs = item.get("final_clause_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append(f"{label} final_clause_refs must be an array of non-empty references")
        if item.get("cross_references_complete") is not True:
            errors.append(f"{label} cross-references are incomplete")
        outcome = item.get("outcome")
        if not isinstance(outcome, str) or outcome not in {"preserved", "approved_compromise"}:
            errors.append(f"{label} protection outcome is missing, unresolved, or weakened")
        if outcome == "preserved" and isinstance(refs, list) and not refs:
            errors.append(f"{label} preserved protection requires at least one final clause reference")
        if outcome == "approved_compromise":
            compromise = item.get("compromise")
            if not isinstance(compromise, dict):
                errors.append(f"{label} approved compromise evidence missing")
                continue
            for key in (
                "approval_ref",
                "approved_by",
                "approved_at",
                "proportionality_reason",
                "retained_protection_or_rationale",
            ):
                _required_text(compromise, key, f"{label} compromise {key}", errors)
            approval_source = compromise.get("approval_source")
            if not isinstance(approval_source, str) or approval_source not in {
                "current-user-instruction",
                "matter-document",
                "approved-negotiation-policy",
            }:
                errors.append(f"{label} compromise approval_source is invalid")


def validate_amount_review(data: object, artifact: Path, errors: list[str]) -> None:
    if not isinstance(data, dict):
        errors.append("amount review must be an object")
        return
    if data.get("schema_version") != "1.0":
        errors.append("amount review schema_version must be 1.0")
    if data.get("artifact_sha256") != sha256(artifact):
        errors.append("amount review hash does not match delivery artifact")
    _required_text(data, "reviewer", "amount reviewer", errors)
    _required_text(data, "reviewed_at", "amount review time", errors)
    _required_text(data, "scope", "amount review scope", errors)
    _required_text(data, "conclusion_review", "amount conclusion review", errors)
    if data.get("artifact_amounts_reconciled") is not True:
        errors.append("amount review does not confirm the artifact amounts and conclusions were reconciled")
    if data.get("status") != "verified":
        errors.append("amount review is unable to verify or failed")
    chains = data.get("chains")
    if not isinstance(chains, list) or not chains:
        errors.append("amount review requires at least one calculation chain")
        return

    chain_ids: set[str] = set()
    for chain_index, chain in enumerate(chains):
        label = f"amount chain {chain_index}"
        if not isinstance(chain, dict):
            errors.append(f"{label} must be an object")
            continue
        chain_id = _required_text(chain, "chain_id", f"{label} chain_id", errors)
        if chain_id and chain_id in chain_ids:
            errors.append(f"{label} has duplicate chain_id")
        chain_ids.add(chain_id)
        _required_text(chain, "currency", f"{label} currency", errors)
        rounding = chain.get("rounding")
        if not isinstance(rounding, dict):
            errors.append(f"{label} rounding rule missing")
            rounding = {}
        places = rounding.get("decimal_places")
        if isinstance(places, bool) or not isinstance(places, int) or not 0 <= places <= 6:
            errors.append(f"{label} rounding decimal_places must be an integer from 0 to 6")
            places = 2
        mode = rounding.get("mode")
        if not isinstance(mode, str) or mode not in DECIMAL_ROUNDING:
            errors.append(f"{label} rounding mode is invalid")
            mode = "half-up"
        quantum = Decimal(1).scaleb(-places)

        def rounded(value: Decimal) -> Decimal:
            try:
                return value.quantize(quantum, rounding=DECIMAL_ROUNDING[mode])
            except InvalidOperation:
                errors.append(f"{label} value cannot be represented under its stated rounding rule")
                return value

        original = chain.get("original_amount")
        if not isinstance(original, dict):
            errors.append(f"{label} original amount/source missing")
            continue
        if original.get("evidence_status") != "confirmed":
            errors.append(f"{label} original amount is missing or unverified; unable to verify")
        _required_text(original, "source_ref", f"{label} original source_ref", errors)
        original_value = _decimal(original.get("value"), f"{label} original value", errors)
        if original_value is None:
            continue
        initial_factors = chain.get("initially_included_factor_ids")
        if not isinstance(initial_factors, list) or any(not isinstance(x, str) or not x.strip() for x in initial_factors):
            errors.append(f"{label} initially_included_factor_ids must be an array of non-empty ids")
            initial_factors = []
        else:
            initial_factors = [factor_id.strip() for factor_id in initial_factors]
        factor_ids = set(initial_factors)
        if len(factor_ids) != len(initial_factors):
            errors.append(f"{label} initially_included_factor_ids contains duplicates")

        expected_results: dict[str, Decimal] = {"original_amount": rounded(original_value)}
        adjustment_total = Decimal(0)
        remaining_balance = rounded(original_value)
        adjustments = chain.get("adjustments")
        if not isinstance(adjustments, list):
            errors.append(f"{label} adjustments must be an array")
            adjustments = []
        adjustment_ids: set[str] = set()
        for step_index, step in enumerate(adjustments):
            step_label = f"{label} adjustment {step_index}"
            if not isinstance(step, dict):
                errors.append(f"{step_label} must be an object")
                continue
            step_id = _required_text(step, "adjustment_id", f"{step_label} adjustment_id", errors)
            if step_id and step_id in adjustment_ids:
                errors.append(f"{step_label} has duplicate adjustment_id")
            if step_id and step_id in expected_results:
                errors.append(f"{step_label} adjustment_id reuses an existing calculation basis id")
            adjustment_ids.add(step_id)
            factor_id = _required_text(step, "factor_id", f"{step_label} factor_id", errors)
            if factor_id and factor_id in factor_ids:
                errors.append(f"{step_label} reapplies an adjustment factor already included or applied")
            if factor_id:
                factor_ids.add(factor_id)
            _required_text(step, "source_ref", f"{step_label} source_ref", errors)
            _required_text(step, "nature", f"{step_label} nature", errors)
            if step.get("evidence_status") != "confirmed":
                errors.append(f"{step_label} source is missing or unverified; unable to verify")
            basis_from = step.get("basis_from")
            if not isinstance(basis_from, str) or basis_from not in expected_results:
                errors.append(f"{step_label} basis_from must reference original_amount or an earlier adjustment")
                expected_basis = None
            else:
                expected_basis = expected_results[basis_from]
            basis = _decimal(step.get("basis_amount"), f"{step_label} basis_amount", errors)
            if basis is not None and expected_basis is not None and rounded(basis) != rounded(expected_basis):
                errors.append(f"{step_label} basis_amount is stale or does not match its dependency")
            kind = step.get("kind")
            if kind == "percentage":
                rate = _decimal(step.get("rate"), f"{step_label} rate", errors)
                if rate is not None and rate < Decimal(0):
                    errors.append(f"{step_label} percentage rate cannot be negative")
                deduction = rounded(expected_basis * rate) if expected_basis is not None and rate is not None else None
            elif kind == "fixed":
                deduction = _decimal(step.get("fixed_amount"), f"{step_label} fixed_amount", errors)
                if deduction is not None:
                    deduction = rounded(deduction)
                    if deduction < 0:
                        errors.append(f"{step_label} fixed_amount cannot be negative")
            else:
                errors.append(f"{step_label} kind must be percentage or fixed")
                deduction = None
            declared_deduction = _decimal(step.get("deduction_amount"), f"{step_label} deduction_amount", errors)
            if deduction is not None and declared_deduction is not None and rounded(declared_deduction) != deduction:
                errors.append(f"{step_label} deduction_amount does not match the stated basis and factor")
            result = rounded(remaining_balance - deduction) if deduction is not None else None
            declared_result = _decimal(step.get("resulting_amount"), f"{step_label} resulting_amount", errors)
            if result is not None and declared_result is not None and rounded(declared_result) != result:
                errors.append(f"{step_label} resulting_amount does not match remaining balance less this adjustment")
            if step_id and result is not None:
                expected_results[step_id] = result
                remaining_balance = result
            if deduction is not None:
                adjustment_total += deduction

        def sum_source_rows(key: str, amount_key: str) -> Decimal:
            rows = chain.get(key)
            if not isinstance(rows, list):
                errors.append(f"{label} {key} must be an array")
                return Decimal(0)
            total = Decimal(0)
            row_ids: set[str] = set()
            for row_index, row in enumerate(rows):
                row_label = f"{label} {key} {row_index}"
                if not isinstance(row, dict):
                    errors.append(f"{row_label} must be an object")
                    continue
                identity_key = "offset_id" if key == "offsets" else "record_id"
                identity = _required_text(row, identity_key, f"{row_label} {identity_key}", errors)
                if identity and identity in row_ids:
                    errors.append(f"{row_label} has duplicate {identity_key}")
                row_ids.add(identity)
                _required_text(row, "source_ref", f"{row_label} source_ref", errors)
                if row.get("evidence_status") != "confirmed":
                    errors.append(f"{row_label} source is missing or unverified; unable to verify")
                factor_id = _required_text(row, "factor_id", f"{row_label} factor_id", errors)
                if factor_id and factor_id in factor_ids:
                    errors.append(f"{row_label} reapplies an adjustment factor already included or applied")
                if factor_id:
                    factor_ids.add(factor_id)
                if key == "offsets":
                    _required_text(row, "nature", f"{row_label} nature", errors)
                amount = _decimal(row.get(amount_key), f"{row_label} {amount_key}", errors)
                if amount is not None:
                    if amount < 0:
                        errors.append(f"{row_label} {amount_key} cannot be negative")
                    total += rounded(amount)
            return total

        payments_total = sum_source_rows("payments", "amount")
        offsets_total = sum_source_rows("offsets", "amount")
        adjusted_gross = remaining_balance
        if rounded(original_value - adjustment_total) != rounded(adjusted_gross):
            errors.append(f"{label} adjusted_gross does not reconcile to gross less adjustments_total")
        net_total = rounded(adjusted_gross - payments_total - offsets_total)
        expected_totals = {
            "gross": rounded(original_value),
            "adjustments_total": rounded(adjustment_total),
            "adjusted_gross": rounded(adjusted_gross),
            "paid_total": rounded(payments_total),
            "offsets_total": rounded(offsets_total),
            "net_total": rounded(net_total),
        }
        reported = chain.get("reported_totals")
        if not isinstance(reported, dict):
            errors.append(f"{label} reported_totals missing")
            continue
        for key, expected in expected_totals.items():
            reported_value = _decimal(reported.get(key), f"{label} reported_totals.{key}", errors)
            if reported_value is not None and rounded(reported_value) != expected:
                errors.append(f"{label} reported total {key} is stale or inconsistent")


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
    if level in {"S1", "S2", "S3"} and "Legal_OS_Public" in output.resolve().parts:
        errors.append(f"{level} matter output cannot be placed in public repository")
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
    parser.add_argument(
        "--amount-review-required",
        action="store_true",
        help="Require a source-locked amount review in the human signoff for amount-based formal conclusions.",
    )
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
            if args.contract and final_requested:
                validate_contract_protection_review(
                    signoff.get("contract_protection_review"), args.artifact, errors
                )
            amount_review = signoff.get("amount_review")
            if args.amount_review_required and final_requested and amount_review is None:
                errors.append("amount-sensitive Final requires a structured amount review")
            if amount_review is not None:
                validate_amount_review(amount_review, args.artifact, errors)

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
