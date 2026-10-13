#!/usr/bin/env python3
"""Build the existing amount_review sign-off section from the workbook ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP
from pathlib import Path
from xml.etree import ElementTree as ET


MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN}
RECORD_COLUMNS = {
    "record_id": 1, "source_ref": 2, "nature": 3, "currency": 5,
    "source_amount": 10, "paid_amount": 11, "evidence_status": 12,
    "chain_id": 14, "record_type": 15, "factor_id": 16, "basis_from": 17,
    "factor_kind": 18, "factor_value": 19, "initial_factors": 20,
    "decimal_places": 21, "rounding_mode": 22,
    "payment_source_ref": 23, "payment_evidence_status": 24,
}
ROUNDING = {
    "half-up": ROUND_HALF_UP,
    "half-even": ROUND_HALF_EVEN,
    "down": ROUND_DOWN,
    "up": ROUND_UP,
}


class ExportError(ValueError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def column_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref.upper())
    if not letters:
        return 0
    result = 0
    for char in letters.group(0):
        result = result * 26 + ord(char) - 64
    return result


def _xlsx_cells(path: Path) -> list[dict[int, str]]:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ExportError(f"workbook is unreadable: {exc}") from exc
    with archive:
        bad = archive.testzip()
        if bad:
            raise ExportError(f"workbook ZIP member is corrupt: {bad}")
        names = set(archive.namelist())
        try:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        except (KeyError, ET.ParseError) as exc:
            raise ExportError(f"workbook structure is incomplete: {exc}") from exc
        relation_map = {item.get("Id", ""): item.get("Target", "") for item in relations.findall(f"{{{PKG_REL}}}Relationship")}
        target = None
        for sheet in workbook.findall(f".//{{{MAIN}}}sheet"):
            if sheet.get("name") == "原始记录_输入":
                target = relation_map.get(sheet.get(f"{{{DOC_REL}}}id", ""))
                break
        if not target:
            raise ExportError("workbook lacks the existing 原始记录_输入 sheet")
        sheet_path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
        if sheet_path not in names:
            raise ExportError("原始记录_输入 relationship points to a missing sheet")
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            try:
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                shared = ["".join(node.text or "" for node in item.findall(f".//{{{MAIN}}}t")) for item in shared_root.findall(f"{{{MAIN}}}si")]
            except ET.ParseError as exc:
                raise ExportError(f"shared strings are malformed: {exc}") from exc
        try:
            sheet_root = ET.fromstring(archive.read(sheet_path))
        except ET.ParseError as exc:
            raise ExportError(f"原始记录_输入 XML is malformed: {exc}") from exc
        rows: list[dict[int, str]] = []
        for row in sheet_root.findall(f".//{{{MAIN}}}sheetData/{{{MAIN}}}row"):
            values: dict[int, str] = {}
            for cell in row.findall(f"{{{MAIN}}}c"):
                index = column_index(cell.get("r", ""))
                formula = cell.find(f"{{{MAIN}}}f")
                value = cell.find(f"{{{MAIN}}}v")
                inline = cell.find(f"{{{MAIN}}}is")
                if formula is not None:
                    values[index] = "<FORMULA>"
                    continue
                if inline is not None:
                    values[index] = "".join(node.text or "" for node in inline.findall(f".//{{{MAIN}}}t"))
                    continue
                raw = value.text if value is not None else ""
                if cell.get("t") == "s" and raw:
                    try:
                        raw = shared[int(raw)]
                    except (ValueError, IndexError) as exc:
                        raise ExportError(f"invalid shared string index in {cell.get('r')}") from exc
                values[index] = raw or ""
            rows.append(values)
        return rows


def text(row: dict[int, str], field: str) -> str:
    value = row.get(RECORD_COLUMNS[field], "")
    if value == "<FORMULA>":
        raise ExportError(f"{field} must be a direct ledger value, not a formula")
    return value.strip()


def number(row: dict[int, str], field: str, label: str) -> Decimal | None:
    value = text(row, field)
    if not value or value == "待核":
        return None
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ExportError(f"{label} is not numeric: {value}") from exc
    if not result.is_finite():
        raise ExportError(f"{label} is not finite")
    return result


def evidence_status(value: str, source_ref: str) -> tuple[str, bool]:
    key = value.strip().casefold()
    if not source_ref:
        return "missing", True
    if key in {"已核", "已确认", "confirmed"}:
        return "confirmed", False
    if key in {"冲突", "conflicted"}:
        return "conflicted", True
    if key in {"缺失", "缺来源", "missing"}:
        return "missing", True
    return "unverified", True


def json_number(value: Decimal | None):
    if value is None:
        return None
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def _round(value: Decimal, places: int, mode: str) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUNDING[mode])


def build_chains(rows: list[dict[int, str]]) -> tuple[list[dict], list[str]]:
    chains: OrderedDict[str, list[dict]] = OrderedDict()
    seen_record_ids: set[str] = set()
    gaps: list[str] = []
    for row_number, row in enumerate(rows, start=1):
        record_id = text(row, "record_id")
        if not record_id or record_id.startswith("DEMO-") or record_id in {"记录ID", "record_id"}:
            continue
        chain_id = text(row, "chain_id")
        record_type = text(row, "record_type")
        if not chain_id and not record_type:
            unassigned_source = number(row, "source_amount", f"{record_id} source_amount")
            unassigned_paid = number(row, "paid_amount", f"{record_id} paid_amount")
            pending_source = text(row, "source_amount") == "待核"
            pending_paid = text(row, "paid_amount") == "待核"
            if unassigned_source not in (None, Decimal(0)) or unassigned_paid not in (None, Decimal(0)):
                gaps.append(f"{record_id}: non-zero amount in existing column J/K has no amount-chain type in columns N:O and was not included")
            elif pending_source or pending_paid:
                gaps.append(f"{record_id}: amount in existing column J/K is marked 待核 and has no amount-chain type in columns N:O")
            continue
        if not chain_id or not record_type:
            raise ExportError(f"raw ledger row {row_number}: chain_id and record_type must both be supplied")
        if record_id in seen_record_ids:
            raise ExportError(f"duplicate raw ledger record_id in amount chains: {record_id}")
        seen_record_ids.add(record_id)
        if record_type not in {"original_amount", "adjustment", "payment", "offset"}:
            raise ExportError(f"raw ledger row {row_number}: unsupported record_type {record_type!r}")
        source_ref = text(row, "source_ref")
        status, has_gap = evidence_status(text(row, "evidence_status"), source_ref)
        if has_gap:
            gaps.append(f"{record_id}: source locator or evidence status is incomplete")
        initial_factors_text = text(row, "initial_factors")
        initial_factors = [] if initial_factors_text.casefold() in {"无", "none", "no factors", "[]"} else [
            item.strip() for item in initial_factors_text.replace("；", ";").split(";") if item.strip()
        ]
        entry = {
            "record_id": record_id,
            "record_type": record_type,
            "source_ref": source_ref,
            "nature": text(row, "nature"),
            "currency": text(row, "currency"),
            "evidence_status": status,
            "factor_id": text(row, "factor_id"),
            "basis_from": text(row, "basis_from"),
            "factor_kind": text(row, "factor_kind"),
            "factor_value": number(row, "factor_value", f"{record_id} factor_value"),
            "factor_value_pending": text(row, "factor_value") == "待核",
            "source_amount": number(row, "source_amount", f"{record_id} source_amount"),
            "source_amount_pending": text(row, "source_amount") == "待核",
            "paid_amount": number(row, "paid_amount", f"{record_id} paid_amount"),
            "paid_amount_pending": text(row, "paid_amount") == "待核",
            "paid_amount_blank": not text(row, "paid_amount"),
            "initial_factors": initial_factors,
            "initial_factors_recorded": bool(initial_factors_text),
            "decimal_places": text(row, "decimal_places"),
            "rounding_mode": text(row, "rounding_mode"),
            "payment_source_ref": text(row, "payment_source_ref"),
            "payment_evidence_status": text(row, "payment_evidence_status"),
        }
        chains.setdefault(chain_id, []).append(entry)
    if not chains:
        raise ExportError("no amount-chain rows found; fill the chain columns N:V in 原始记录_输入")

    output: list[dict] = []
    for chain_id, entries in chains.items():
        originals = [entry for entry in entries if entry["record_type"] == "original_amount"]
        if len(originals) != 1:
            raise ExportError(f"chain {chain_id} must have exactly one original_amount row")
        original = originals[0]
        try:
            places = int(original["decimal_places"])
        except (TypeError, ValueError) as exc:
            raise ExportError(f"chain {chain_id} original row needs decimal_places") from exc
        mode = original["rounding_mode"].casefold()
        if not 0 <= places <= 6 or mode not in ROUNDING:
            raise ExportError(f"chain {chain_id} original row needs a supported rounding rule")
        currency = original["currency"]
        for entry in entries:
            if entry["currency"] and entry["currency"] != currency:
                raise ExportError(f"chain {chain_id} mixes currencies")
            if entry["record_id"] != original["record_id"] and not entry["currency"]:
                gaps.append(f"{entry['record_id']}: currency is missing")

        original_value = original["source_amount"]
        if original_value is None:
            gaps.append(f"chain {chain_id}: original source amount is missing")
        original_ref = original["source_ref"]
        original_status = original["evidence_status"]
        initially_included = original["initial_factors"]
        if not original["initial_factors_recorded"]:
            gaps.append(f"chain {chain_id}: initially included factor inventory is not recorded; enter explicit 无 or factor ids in column T")
        expected_results: dict[str, Decimal] = {}
        remaining = _round(original_value, places, mode) if original_value is not None else None
        known_calculation_ids = {"original_amount"}
        if remaining is not None:
            expected_results["original_amount"] = remaining
        adjustments = []
        payments = []
        offsets = []
        factor_ids = set(initially_included)
        adjustments_total = Decimal(0)
        adjustments_complete = True
        payments_total = Decimal(0)
        payments_complete = True
        offsets_total = Decimal(0)
        offsets_complete = True
        embedded_paid_rows = [entry for entry in entries if entry["record_type"] == "original_amount" and entry["paid_amount"] not in (None, Decimal(0))]
        separate_payment_rows = [entry for entry in entries if entry["record_type"] == "payment"]
        if embedded_paid_rows and separate_payment_rows:
            raise ExportError(
                f"chain {chain_id} records payment in both original-row column K and dedicated payment rows; choose one entry path"
            )
        for entry in entries:
            kind = entry["record_type"]
            record_id = entry["record_id"]
            if kind == "original_amount":
                if entry["paid_amount"] is not None and entry["paid_amount"] < 0:
                    raise ExportError(f"{record_id}: paid/received amount cannot be negative")
                if entry["paid_amount"] in (None, Decimal(0)) and not entry["paid_amount_pending"] and (
                    entry["payment_source_ref"] or entry["payment_evidence_status"]
                ):
                    raise ExportError(f"{record_id}: columns W:X are only used when the original row has a non-zero amount in column K")
                if entry["paid_amount_pending"]:
                    gaps.append(f"{record_id}: existing column K payment is marked 待核 and cannot be included in a verified total")
                    payments_complete = False
                    paid_source = entry["payment_source_ref"]
                    paid_status, _ = evidence_status(entry["payment_evidence_status"], paid_source)
                    payments.append({
                        "record_id": f"PAYMENT-FROM-{record_id}",
                        "factor_id": f"payment-from:{record_id}",
                        "source_ref": paid_source,
                        "evidence_status": paid_status,
                        "amount": None,
                    })
                elif entry["paid_amount_blank"] and not separate_payment_rows:
                    gaps.append(
                        f"{record_id}: existing column K is blank; confirm no payment with an explicit 0 or record payments in dedicated payment rows"
                    )
                    payments_complete = False
                    payments.append({
                        "record_id": f"PAYMENT-FROM-{record_id}",
                        "factor_id": f"payment-from:{record_id}",
                        "source_ref": "",
                        "evidence_status": "missing",
                        "amount": None,
                    })
                if entry["paid_amount"] not in (None, Decimal(0)):
                    paid_source = entry["payment_source_ref"]
                    paid_status, paid_gap = evidence_status(entry["payment_evidence_status"], paid_source)
                    if paid_gap:
                        gaps.append(f"{record_id}: existing column K payment is retained but needs its own payment source and confirmation in columns W:X")
                        payments_complete = False
                    if entry["payment_evidence_status"].casefold() in {"已核", "已确认", "confirmed"} and not paid_source:
                        paid_status = "missing"
                    payments.append({
                        "record_id": f"PAYMENT-FROM-{record_id}",
                        "factor_id": f"payment-from:{record_id}",
                        "source_ref": paid_source,
                        "evidence_status": paid_status,
                        "amount": json_number(entry["paid_amount"]),
                    })
                    if paid_status != "confirmed" or not paid_source:
                        payments_complete = False
                    else:
                        payments_total += _round(entry["paid_amount"], places, mode)
                if entry["factor_value"] is not None or entry["factor_value_pending"]:
                    raise ExportError(f"{record_id}: original_amount row cannot use factor_value in column S")
                continue
            factor_id = entry["factor_id"]
            if not factor_id:
                raise ExportError(f"{record_id}: factor_id is required for adjustment/payment/offset rows")
            if factor_id in factor_ids:
                # Keep the full row in output so the existing gate reports the exact duplicate factor.
                gaps.append(f"{record_id}: factor_id duplicates a previously included/applied factor")
            factor_ids.add(factor_id)
            if kind == "adjustment":
                basis_from = entry["basis_from"]
                if not basis_from:
                    raise ExportError(f"{record_id}: basis_from is required for an adjustment")
                if entry["factor_kind"] not in {"percentage", "fixed"}:
                    raise ExportError(f"{record_id}: factor_kind must be percentage or fixed")
                basis_amount = expected_results.get(basis_from)
                if basis_from not in known_calculation_ids:
                    raise ExportError(f"{record_id}: basis_from must reference original_amount or an earlier adjustment record_id")
                if basis_amount is None:
                    gaps.append(f"{record_id}: calculation basis is unavailable")
                if entry["paid_amount"] not in (None, Decimal(0)):
                    raise ExportError(f"{record_id}: adjustment rows cannot use paid/received column K")
                if entry["factor_kind"] == "percentage":
                    if entry["source_amount"] is not None or entry["source_amount_pending"]:
                        raise ExportError(f"{record_id}: percentage adjustment uses rate in column S; clear column J to avoid duplicate amounts")
                    value = entry["factor_value"]
                else:
                    if entry["factor_value"] is not None or entry["factor_value_pending"]:
                        raise ExportError(f"{record_id}: fixed adjustment uses its single deduction amount in column J; clear column S")
                    value = entry["source_amount"]
                if value is None:
                    gaps.append(f"{record_id}: factor value is missing")
                if entry["evidence_status"] != "confirmed" or not entry["source_ref"] or not entry["nature"]:
                    gaps.append(f"{record_id}: adjustment source/nature is not verified")
                if entry["factor_kind"] == "percentage":
                    rate = value
                    fixed_amount = None
                    deduction = _round(basis_amount * rate, places, mode) if basis_amount is not None and rate is not None else None
                else:
                    rate = None
                    fixed_amount = value
                    deduction = _round(fixed_amount, places, mode) if fixed_amount is not None else None
                if remaining is not None and deduction is not None:
                    result = _round(remaining - deduction, places, mode)
                    remaining = result
                    expected_results[record_id] = result
                    adjustments_total += deduction
                else:
                    result = None
                    remaining = None
                    adjustments_complete = False
                adjustments.append({
                    "adjustment_id": record_id,
                    "factor_id": factor_id,
                    "source_ref": entry["source_ref"],
                    "nature": entry["nature"],
                    "evidence_status": entry["evidence_status"],
                    "basis_from": basis_from,
                    "basis_amount": json_number(basis_amount),
                    "kind": entry["factor_kind"],
                    **({"rate": json_number(rate)} if entry["factor_kind"] == "percentage" else {"fixed_amount": json_number(fixed_amount)}),
                    "deduction_amount": json_number(deduction),
                    "resulting_amount": json_number(result),
                })
                known_calculation_ids.add(record_id)
            elif kind == "payment":
                amount = entry["paid_amount"]
                if entry["source_amount"] is not None or entry["source_amount_pending"] or entry["factor_value"] is not None or entry["factor_value_pending"]:
                    raise ExportError(f"{record_id}: payment rows use column K only; clear columns J and S")
                if amount is None or entry["evidence_status"] != "confirmed" or not entry["source_ref"]:
                    gaps.append(f"{record_id}: payment source/amount is not verified")
                    payments_complete = False
                elif amount < 0:
                    raise ExportError(f"{record_id}: payment amount cannot be negative")
                else:
                    payments_total += _round(amount, places, mode)
                payments.append({
                    "record_id": record_id, "factor_id": factor_id, "source_ref": entry["source_ref"],
                    "evidence_status": entry["evidence_status"], "amount": json_number(amount),
                })
            else:
                amount = entry["source_amount"]
                if entry["paid_amount"] not in (None, Decimal(0)) or entry["paid_amount_pending"] or entry["factor_value"] is not None or entry["factor_value_pending"]:
                    raise ExportError(f"{record_id}: offset rows use column J only; clear columns K and S")
                if amount is None or entry["evidence_status"] != "confirmed" or not entry["source_ref"] or not entry["nature"]:
                    gaps.append(f"{record_id}: offset source/amount/nature is not verified")
                    offsets_complete = False
                elif amount < 0:
                    raise ExportError(f"{record_id}: offset amount cannot be negative")
                else:
                    offsets_total += _round(amount, places, mode)
                offsets.append({
                    "offset_id": record_id, "factor_id": factor_id, "source_ref": entry["source_ref"],
                    "nature": entry["nature"], "evidence_status": entry["evidence_status"], "amount": json_number(amount),
                })

        totals = {
            "gross": json_number(_round(original_value, places, mode)) if original_value is not None else None,
            "adjustments_total": json_number(_round(adjustments_total, places, mode)) if adjustments_complete else None,
            "adjusted_gross": json_number(remaining) if remaining is not None else None,
            "paid_total": json_number(_round(payments_total, places, mode)) if payments_complete else None,
            "offsets_total": json_number(_round(offsets_total, places, mode)) if offsets_complete else None,
            "net_total": json_number(_round(remaining - payments_total - offsets_total, places, mode))
            if remaining is not None and payments_complete and offsets_complete else None,
        }
        if not original_ref or original_status != "confirmed":
            gaps.append(f"chain {chain_id}: original amount source is not verified")
        output.append({
            "chain_id": chain_id,
            "currency": currency,
            "rounding": {"decimal_places": places, "mode": mode},
            "original_amount": {
                "value": json_number(original_value), "source_ref": original_ref,
                "evidence_status": original_status,
            },
            "initially_included_factor_ids": initially_included,
            "adjustments": adjustments,
            "payments": payments,
            "offsets": offsets,
            "reported_totals": totals,
        })
    return output, gaps


def export(args: argparse.Namespace) -> tuple[dict, list[str]]:
    for path, label in ((args.workbook, "workbook"), (args.artifact, "artifact"), (args.signoff, "signoff")):
        if not path.is_file():
            raise ExportError(f"{label} file missing: {path}")
    try:
        signoff = json.loads(args.signoff.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"signoff JSON unreadable: {exc}") from exc
    if not isinstance(signoff, dict):
        raise ExportError("signoff must be a JSON object")
    output_resolved = args.output.resolve()
    for input_path, label in ((args.workbook, "workbook"), (args.artifact, "artifact"), (args.signoff, "signoff")):
        same_file = output_resolved.exists() and input_path.exists() and output_resolved.samefile(input_path)
        if output_resolved == input_path.resolve() or same_file:
            raise ExportError(f"output must not overwrite the input {label}")
    artifact_hash = sha256(args.artifact)
    if signoff.get("artifact_sha256") != artifact_hash:
        raise ExportError("existing signoff hash does not match artifact; re-review before export")
    try:
        signoff_path = Path(str(signoff.get("artifact_path", ""))).expanduser().resolve()
    except OSError:
        signoff_path = Path("/__invalid_signoff_path__")
    if signoff_path != args.artifact.resolve():
        raise ExportError("existing signoff path does not match artifact")

    rows = _xlsx_cells(args.workbook)
    chains, data_gaps = build_chains(rows)
    prior = signoff.get("amount_review")
    generated_chains_match = (
        isinstance(prior, dict)
        and prior.get("chains") == chains
    )
    if isinstance(prior, dict) and prior.get("status") == "verified" and not generated_chains_match:
        data_gaps.append("existing amount review no longer matches the workbook-generated source/calculation/factor chains; affected amount review is required")
    human_review_valid = (
        isinstance(prior, dict)
        and prior.get("artifact_sha256") == artifact_hash
        and prior.get("status") == "verified"
        and prior.get("artifact_amounts_reconciled") is True
        and generated_chains_match
        and isinstance(prior.get("conclusion_review"), str)
        and bool(prior["conclusion_review"].strip())
        and isinstance(prior.get("reviewer"), str)
        and bool(prior["reviewer"].strip())
        and isinstance(prior.get("reviewed_at"), str)
        and bool(prior["reviewed_at"].strip())
    )
    source_complete = not data_gaps
    status = "verified" if source_complete and human_review_valid else "unable-to-verify"
    reviewer = str(prior.get("reviewer", "")).strip() if isinstance(prior, dict) and generated_chains_match else ""
    reviewed_at = str(prior.get("reviewed_at", "")).strip() if isinstance(prior, dict) and generated_chains_match else ""
    scope = str(prior.get("scope", "")).strip() if isinstance(prior, dict) and generated_chains_match else ""
    conclusion = str(prior.get("conclusion_review", "")).strip() if isinstance(prior, dict) and generated_chains_match else ""
    scope = scope or "工作簿金额链待复核：" + ", ".join(item["chain_id"] for item in chains)
    if not conclusion:
        conclusion = "待人工金额复核；本记录由原始账本整理来源字段和算术，尚未确认来源语义、计算依据或金额结论。"
    amount_review = {
        "schema_version": "1.0",
        "artifact_sha256": artifact_hash,
        "scope": scope,
        "status": status,
        "artifact_amounts_reconciled": bool(status == "verified" and human_review_valid),
        "conclusion_review": conclusion,
        "chains": chains,
    }
    if reviewer:
        amount_review["reviewer"] = reviewer
    if reviewed_at:
        amount_review["reviewed_at"] = reviewed_at
    if data_gaps:
        amount_review["review_note"] = "; ".join(dict.fromkeys(data_gaps))
    signoff["amount_review"] = amount_review
    return signoff, data_gaps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--signoff", required=True, type=Path, help="Existing human sign-off JSON bound to the artifact")
    parser.add_argument("--out-signoff", required=True, dest="output", type=Path)
    args = parser.parse_args()
    try:
        signoff, gaps = export(args)
    except (ExportError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "BLOCKED", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(signoff, ensure_ascii=False, indent=2, default=json_number) + "\n", encoding="utf-8")
    amount = signoff["amount_review"]
    payload = {
        "status": "PASS" if amount["status"] == "verified" else "WARN",
        "decision": "review-ready" if amount["status"] == "verified" else "DRAFT_ONLY",
        "out_signoff": str(args.output),
        "artifact_sha256": amount["artifact_sha256"],
        "chain_count": len(amount["chains"]),
        "warnings": gaps,
        "human_amount_review_reused": amount["status"] == "verified",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
