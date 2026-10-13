#!/usr/bin/env python3
"""Block Legal OS Final delivery unless deterministic controls pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, ROUND_UP
from pathlib import Path

from rebind_signoff import validate_rebind_record


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
    signoff_path: Path,
    errors: list[str],
) -> None:
    if "rebind_candidate" in data:
        errors.append("rebind candidate is not releasable; obtain a fresh human-approved sign-off")
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
    if not isinstance(checks, dict):
        errors.append("signoff checks must be an object")
        return
    for key in ("facts", "authority", "strategy", "format", "privacy"):
        if checks.get(key) is not True:
            errors.append(f"signoff check not approved: {key}")
    if "rebind_record" in data:
        for issue in validate_rebind_record(data, artifact, signoff_path):
            errors.append(f"signoff format-rebind proof invalid: {issue}")


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


CONTRACT_CORE_DOMAIN_CHINESE = (
    "付款", "支付", "价款", "费用", "金额", "责任", "义务", "违约", "赔偿", "免责", "责任上限",
    "解除", "终止", "期限", "验收", "交付", "范围", "知识产权", "个人信息", "隐私", "保密",
    "承担", "补偿", "赔付", "担保", "保证", "权利", "自动续期",
)
CONTRACT_CORE_DOMAIN_ENGLISH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?:intellectual\s+property|liabilit(?:y|ies)|indemn\w*|payments?|"
    r"terminations?|acceptances?|warrant(?:y|ies)|obligations?|dut(?:y|ies)|damages?|"
    r"compensations?|confidential(?:ity)?|privacy|personal\s+data|deliver(?:y|ies)?|scope|terms?|deadlines?|"
    r"effective\s+date|due\s+date)(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
CONTRACT_EFFECT_ENGLISH_TERMS = (
    "not", "no", "never", "without", "unless", "except", "only", "shall", "must", "may", "will",
    "cannot", "can", "required", "entitled", "right to", "duty", "duties", "responsible", "liable", "waive",
    "consent", "approve", "permit", "prohibit", "allow", "provide", "deliver", "pay", "accept",
    "terminate", "release", "revoke", "assign", "undertake", "perform", "ensure", "represent",
)
CONTRACT_EFFECT_CHINESE_TERMS = (
    "不得", "应当", "必须", "除非", "除外", "否则", "有权", "权利", "义务", "负责", "允许", "可以",
    "同意", "授权", "批准", "提供", "履行", "执行", "转让", "放弃", "撤销", "删除", "修改", "享有",
    "负有", "到期", "届满", "之前", "以后", "以内", "仅", "须", "不", "未", "无",
)
CONTRACT_EFFECT_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?:" + "|".join(
        re.escape(term).replace(r"\ ", r"\s+")
        for term in sorted(CONTRACT_EFFECT_ENGLISH_TERMS, key=len, reverse=True)
    ) + r")(?![A-Za-z0-9_])|(?:" + "|".join(
        re.escape(term) for term in sorted(CONTRACT_EFFECT_CHINESE_TERMS, key=len, reverse=True)
    ) + r")",
    re.IGNORECASE,
)


def protected_core_domain_matches(changes: object) -> list[str]:
    """Return protected subject-matter terms found in actual change context."""
    if not isinstance(changes, list):
        return []
    matched: list[str] = []
    for item in changes:
        if not isinstance(item, dict):
            continue
        context = " ".join(
            value for value in (item.get("text"), item.get("context_before"), item.get("context_after"))
            if isinstance(value, str)
        )
        for term in CONTRACT_CORE_DOMAIN_CHINESE:
            if term in context and term not in matched:
                matched.append(term)
        for term in CONTRACT_CORE_DOMAIN_ENGLISH_PATTERN.findall(context):
            normalized = term.casefold()
            if normalized not in matched:
                matched.append(normalized)
    return matched


def has_changed_legal_effect_marker(changes: object) -> bool:
    """Compare actual before/after paragraph markers; unchanged modals do not force Full."""
    if not isinstance(changes, list):
        return False
    for item in changes:
        if not isinstance(item, dict):
            continue
        before = item.get("context_before")
        after = item.get("context_after")
        if not isinstance(before, str) or not isinstance(after, str):
            continue
        before_markers = [value.casefold() for value in CONTRACT_EFFECT_PATTERN.findall(before)]
        after_markers = [value.casefold() for value in CONTRACT_EFFECT_PATTERN.findall(after)]
        if before_markers != after_markers:
            return True
    return False

LIGHT_QUANTITY_VALUE = re.compile(
    r"(?:\([-+−]?\d+(?:[,，]\d{3})*(?:[.．]\d+)?\)|(?<![A-Za-z0-9])[-+−]?\d+(?:[,，]\d{3})*(?:[.．]\d+)?(?![A-Za-z0-9])|[零〇一二两三四五六七八九十百千万亿廿卅]+|"
    r"(?<![A-Za-z])(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|"
    r"sixty|seventy|eighty|ninety|hundred|thousand|million|billion|first|second|third|fourth|"
    r"fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirtieth|dozen|half|quarter|"
    r"once|twice|double|doubled|triple|tripled)(?![A-Za-z]))",
    re.IGNORECASE,
)
LIGHT_QUANTITY_UNIT = re.compile(
    r"(?:[%％‰$€£¥￥]|(?<![A-Za-z])(?:percent(?:age)?|per\s+cent|bps?|basis\s+points?|"
    r"ratio|proportion|rate|interest|discount|day|days|business\s+days?|calendar\s+days?|"
    r"week|weeks|month|months|year|years|hour|hours|minute|minutes|second|seconds|date|deadline|"
    r"due|within|before|after|until|from|prior\s+to|following|daily|weekly|monthly|quarterly|annual|annually|yearly|january|february|march|april|may|"
    r"june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|"
    r"friday|saturday|sunday|usd|cny|rmb|eur|gbp|jpy|hkd)(?![A-Za-z])|"
    r"人民币|美元|欧元|英镑|日元|港币|港元|元|万元|亿元|日历日|自然日|工作日|自然月|个月|月|年|季度|"
    r"周|星期|天|日|小时|分钟|秒|比例|比率|占比|费率|利率|税率|百分比|百分之|倍数|折扣|折|款项|金额)",
    re.IGNORECASE,
)


def has_changed_quantity_or_time_marker(changes: object) -> bool:
    """Keep value, date, duration, currency and rate edits out of Light review."""
    if not isinstance(changes, list):
        return False
    for item in changes:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        before = item.get("context_before")
        after = item.get("context_after")
        if not all(isinstance(value, str) for value in (text, before, after)):
            continue
        if LIGHT_QUANTITY_VALUE.search(text) or LIGHT_QUANTITY_UNIT.search(text):
            return True
        if LIGHT_QUANTITY_VALUE.findall(before) != LIGHT_QUANTITY_VALUE.findall(after):
            return True
        if [value.casefold() for value in LIGHT_QUANTITY_UNIT.findall(before)] != [
            value.casefold() for value in LIGHT_QUANTITY_UNIT.findall(after)
        ]:
            return True
    return False


def change_list_sha256(changes: object) -> str | None:
    if not isinstance(changes, list) or not changes:
        return None
    normalized = []
    for item in changes:
        if not isinstance(item, dict) or not isinstance(item.get("kind"), str) or item.get("kind") not in {"insert", "delete"}:
            return None
        if not isinstance(item.get("text"), str) or not item["text"]:
            return None
        context_before = item.get("context_before")
        context_after = item.get("context_after")
        if not isinstance(context_before, str) or not isinstance(context_after, str):
            return None
        normalized.append({
            "kind": item["kind"],
            "text": item["text"],
            "context_before": context_before,
            "context_after": context_after,
        })
    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_contract_source_report(report: dict, matter: dict, artifact: Path, errors: list[str]) -> str | None:
    original_value = report.get("original")
    redline_value = report.get("redline")
    hashes = report.get("hashes")
    if not isinstance(original_value, str) or not original_value.strip():
        errors.append("contract redline report original path missing")
        return None
    original = Path(original_value).expanduser().resolve()
    if not original.is_file():
        errors.append("contract redline original file missing")
        return None
    if not isinstance(hashes, dict) or hashes.get("original") != sha256(original):
        errors.append("contract redline report original hash does not match source file")
        return None
    if not isinstance(redline_value, str) or Path(redline_value).expanduser().resolve() != artifact.resolve():
        errors.append("contract redline report redline path does not match delivery artifact")
    sources = matter.get("source_files")
    matched = False
    if isinstance(sources, list):
        for item in sources:
            if not isinstance(item, dict) or item.get("role") != "original":
                continue
            value = str(item.get("path", "")).strip()
            if not value:
                continue
            candidate = Path(value).expanduser()
            matter_root_value = matter.get("matter_root")
            matter_root = Path(str(matter_root_value)).expanduser().resolve() if isinstance(matter_root_value, str) else original.parent
            candidate = candidate.resolve() if candidate.is_absolute() else (matter_root / candidate).resolve()
            if candidate == original and item.get("sha256") == sha256(original):
                matched = True
                break
    if not matched:
        errors.append("contract redline original is not a hash-matched manifest original")
    if not isinstance(hashes, dict) or hashes.get("redline") != sha256(artifact):
        errors.append("contract redline report hash does not match delivery artifact")
    for key in ("source_matches_rejected_view", "accepted_view_readable", "track_revisions"):
        if report.get(key) is not True:
            errors.append(f"contract redline report does not confirm {key}")
    return hashes.get("original") if isinstance(hashes, dict) and isinstance(hashes.get("original"), str) else None


def validate_actual_light_redline(report: dict, original: Path, artifact: Path, errors: list[str]) -> dict:
    """Rebuild the redline evidence from the exact DOCX pair used by light review."""
    contract_gate = Path(__file__).resolve().parents[2] / "legal-os-contract" / "scripts" / "redline_quality_gate.py"
    if not contract_gate.is_file():
        errors.append("light contract review cannot verify the actual redline because the Contract redline gate is unavailable")
        return {}
    author = report.get("author")
    if not isinstance(author, str) or not author.strip():
        errors.append("light contract review redline report author missing")
        return {}
    with tempfile.TemporaryDirectory(prefix="legalos-light-redline-") as tmp:
        output = Path(tmp) / "actual-redline-report.json"
        result = subprocess.run(
            [
                sys.executable,
                str(contract_gate),
                "--original", str(original),
                "--redline", str(artifact),
                "--author", author,
                "--out-json", str(output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if not output.is_file():
            errors.append("light contract review could not rebuild a readable redline report")
            return {}
        try:
            actual = json.loads(output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"light contract review rebuilt redline report is unreadable: {exc}")
            return {}
    if result.returncode != 0 or not isinstance(actual, dict) or actual.get("status") != "PASS":
        errors.append("light contract review actual source/redline pair does not PASS the Contract redline gate")
        return actual if isinstance(actual, dict) else {}
    if actual.get("change_text") != report.get("change_text"):
        errors.append("light contract review change text/context does not match the actual redline")
    if actual.get("hashes") != report.get("hashes"):
        errors.append("light contract review hashes do not match the actual source/redline pair")
    return actual


def validate_contract_protection_review(
    data: object,
    artifact: Path,
    errors: list[str],
    *,
    parent_signoff: dict,
    risk_level: str,
    redline_report: dict,
    source_hash: str | None,
) -> None:
    if not isinstance(data, dict):
        errors.append("contract Final requires a structured protection review")
        return
    review_path = data.get("review_path", "full")
    light = isinstance(review_path, str) and review_path == "light"
    effective = dict(data)
    if light:
        for field in ("schema_version", "artifact_sha256", "reviewer", "reviewed_at", "status"):
            if field in data and data[field] != parent_signoff.get(field):
                errors.append(f"light contract review {field} must match the enclosing sign-off")
            effective.setdefault(field, parent_signoff.get(field))
    if effective.get("schema_version") != "1.0":
        errors.append("contract protection review schema_version must be 1.0")
    if effective.get("artifact_sha256") != sha256(artifact):
        errors.append("contract protection review hash does not match delivery artifact")
    _required_text(effective, "reviewer", "contract protection reviewer", errors)
    _required_text(effective, "reviewed_at", "contract protection review time", errors)
    _required_text(data, "review_scope", "contract protection review scope", errors)
    if effective.get("status") != "approved":
        errors.append("contract protection review is not approved")
    if not light and data.get("all_supported_core_risks_mapped") is not True:
        errors.append("contract protection review does not confirm complete core-risk coverage")

    review_round = data.get("review_round", "subsequent")
    if not isinstance(review_round, str) or review_round not in {"single", "subsequent"}:
        errors.append("contract protection review_round must be single or subsequent")
    if not isinstance(review_path, str) or review_path not in {"full", "light"}:
        errors.append("contract protection review_path must be full or light")
    if review_path == "light":
        if risk_level not in {"R0", "R1"}:
            errors.append("light contract review is limited to R0/R1")
        if source_hash is None:
            errors.append("light contract review source hash does not match verified redline original")
        elif "reviewed_source_sha256" in data and data.get("reviewed_source_sha256") != source_hash:
            errors.append("light contract review source hash does not match verified redline original")
        diff_hash = change_list_sha256(redline_report.get("change_text"))
        if diff_hash is None:
            errors.append("light contract review requires readable text changes from the redline gate")
        elif "reviewed_diff_sha256" in data and data.get("reviewed_diff_sha256") != diff_hash:
            errors.append("light contract review diff hash does not match the actual redline changes")
        if "semantic_review" in data:
            _required_text(data, "semantic_review", "light contract semantic review", errors)
        if data.get("core_risks_status") != "none":
            errors.append("light contract review must confirm no supported core risk is affected")
        changes = redline_report.get("change_text")
        if isinstance(changes, list):
            matched_terms = protected_core_domain_matches(changes)
            if matched_terms:
                errors.append("light contract review touches a protected legal domain; full review required: " + ", ".join(matched_terms))
            if has_changed_quantity_or_time_marker(changes):
                errors.append("light contract review changes a numeric, date, amount, currency, deadline, duration or rate marker; full review required")
            if has_changed_legal_effect_marker(changes):
                errors.append("light contract review changes a negation, right, duty, permission, liability or other legal-effect marker; full review required")

    risk_status = data.get("core_risks_status")
    mappings = data.get("risk_mappings", [] if review_path == "light" and risk_status == "none" else None)
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
        review_fields = [
            "core_risk",
            "intended_protection",
            "final_clause_excerpt_or_absence_reason",
            "review_judgment",
        ]
        if review_round != "single":
            review_fields.append("first_pass_agreed_protection")
        for key in review_fields:
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


def _amount_text(
    data: dict,
    key: str,
    label: str,
    errors: list[str],
    gaps: list[str],
) -> str:
    if key not in data:
        errors.append(f"{label} missing")
        return ""
    value = data[key]
    if not isinstance(value, str):
        errors.append(f"{label} must be text")
        return ""
    if not value.strip():
        gaps.append(f"{label} is not source-verified")
        return ""
    return value.strip()


def _amount_decimal(
    data: dict,
    key: str,
    label: str,
    errors: list[str],
    gaps: list[str],
) -> Decimal | None:
    if key not in data:
        errors.append(f"{label} missing")
        return None
    value = data[key]
    if value is None or value == "":
        gaps.append(f"{label} is unavailable; dependent amounts are unable to verify")
        return None
    if isinstance(value, bool):
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


def validate_amount_review(
    data: object,
    artifact: Path,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Separate missing verification evidence from malformed or wrong arithmetic."""
    if not isinstance(data, dict):
        errors.append("amount review must be an object")
        return
    gaps: list[str] = []
    if data.get("schema_version") != "1.0":
        errors.append("amount review schema_version must be 1.0")
    if data.get("artifact_sha256") != sha256(artifact):
        errors.append("amount review hash does not match delivery artifact")
    _required_text(data, "scope", "amount review scope", errors)
    _required_text(data, "conclusion_review", "amount conclusion review", errors)
    if "artifact_amounts_reconciled" not in data or not isinstance(data.get("artifact_amounts_reconciled"), bool):
        errors.append("amount review artifact_amounts_reconciled must be a boolean")
    elif data["artifact_amounts_reconciled"] is not True:
        gaps.append("amount reviewer has not confirmed artifact amounts and conclusions were reconciled")
    status = data.get("status")
    if not isinstance(status, str) or status not in {"verified", "unable-to-verify", "failed"}:
        errors.append("amount review status is invalid")
    elif status == "unable-to-verify":
        gaps.append("amount review is unable-to-verify")
    elif status == "failed":
        errors.append("amount review failed")

    for key, label in (("reviewer", "amount reviewer"), ("reviewed_at", "amount review time")):
        if status == "verified":
            _required_text(data, key, label, errors)
        elif key not in data or data.get(key) in (None, ""):
            gaps.append(f"{label} is not recorded; human amount review remains pending")
        elif not isinstance(data.get(key), str):
            errors.append(f"{label} must be text")
        elif not data[key].strip():
            gaps.append(f"{label} is not recorded; human amount review remains pending")

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
            errors.append(f"{label} rounding rule missing or malformed")
            continue
        places = rounding.get("decimal_places")
        if isinstance(places, bool) or not isinstance(places, int) or not 0 <= places <= 6:
            errors.append(f"{label} rounding decimal_places must be an integer from 0 to 6")
            continue
        mode = rounding.get("mode")
        if not isinstance(mode, str) or mode not in DECIMAL_ROUNDING:
            errors.append(f"{label} rounding mode is invalid")
            continue
        quantum = Decimal(1).scaleb(-places)

        def rounded(value: Decimal) -> Decimal:
            try:
                return value.quantize(quantum, rounding=DECIMAL_ROUNDING[mode])
            except InvalidOperation:
                errors.append(f"{label} value cannot be represented under its stated rounding rule")
                return value

        original = chain.get("original_amount")
        if not isinstance(original, dict):
            errors.append(f"{label} original amount/source structure missing")
            continue
        evidence_status = original.get("evidence_status")
        if not isinstance(evidence_status, str) or evidence_status not in {"confirmed", "missing", "conflicted", "unverified"}:
            errors.append(f"{label} original evidence_status is invalid")
        elif evidence_status != "confirmed":
            gaps.append(f"{label} original amount source is {evidence_status}; unable to verify")
        _amount_text(original, "source_ref", f"{label} original source_ref", errors, gaps)
        original_value = _amount_decimal(original, "value", f"{label} original value", errors, gaps)
        initial_factors = chain.get("initially_included_factor_ids")
        if not isinstance(initial_factors, list) or any(not isinstance(x, str) or not x.strip() for x in initial_factors):
            errors.append(f"{label} initially_included_factor_ids must be an array of non-empty ids")
            initial_factors = []
        else:
            initial_factors = [factor_id.strip() for factor_id in initial_factors]
        factor_ids = set(initial_factors)
        if len(factor_ids) != len(initial_factors):
            errors.append(f"{label} initially_included_factor_ids contains duplicates")

        expected_results: dict[str, Decimal] = {}
        known_calculation_ids = {"original_amount"}
        remaining_balance = rounded(original_value) if original_value is not None else None
        if remaining_balance is not None:
            expected_results["original_amount"] = remaining_balance
        adjustment_total = Decimal(0)
        adjustments_complete = True
        adjustments = chain.get("adjustments")
        if not isinstance(adjustments, list):
            errors.append(f"{label} adjustments must be an array")
            adjustments = []
        adjustment_ids: set[str] = set()
        for step_index, step in enumerate(adjustments):
            step_label = f"{label} adjustment {step_index}"
            if not isinstance(step, dict):
                errors.append(f"{step_label} must be an object")
                adjustments_complete = False
                continue
            step_id = _required_text(step, "adjustment_id", f"{step_label} adjustment_id", errors)
            if step_id and (step_id in adjustment_ids or step_id in known_calculation_ids):
                errors.append(f"{step_label} adjustment_id is duplicate or reuses an existing calculation basis id")
            if step_id:
                adjustment_ids.add(step_id)
            factor_id = _required_text(step, "factor_id", f"{step_label} factor_id", errors)
            if factor_id and factor_id in factor_ids:
                errors.append(f"{step_label} reapplies an adjustment factor already included or applied")
            if factor_id:
                factor_ids.add(factor_id)
            _amount_text(step, "source_ref", f"{step_label} source_ref", errors, gaps)
            _amount_text(step, "nature", f"{step_label} nature", errors, gaps)
            evidence_status = step.get("evidence_status")
            if not isinstance(evidence_status, str) or evidence_status not in {"confirmed", "missing", "conflicted", "unverified"}:
                errors.append(f"{step_label} evidence_status is invalid")
            elif evidence_status != "confirmed":
                gaps.append(f"{step_label} source is {evidence_status}; unable to verify")
            basis_from = step.get("basis_from")
            if not isinstance(basis_from, str) or not basis_from.strip():
                errors.append(f"{step_label} basis_from must reference original_amount or an earlier adjustment; value is missing or malformed")
                expected_basis = None
            elif basis_from not in known_calculation_ids:
                errors.append(f"{step_label} basis_from must reference original_amount or an earlier adjustment")
                expected_basis = None
            else:
                expected_basis = expected_results.get(basis_from)
                if expected_basis is None:
                    gaps.append(f"{step_label} basis depends on an unverified earlier amount")
            basis = _amount_decimal(step, "basis_amount", f"{step_label} basis_amount", errors, gaps)
            if basis is not None and expected_basis is not None and rounded(basis) != rounded(expected_basis):
                errors.append(f"{step_label} basis_amount is stale or does not match its dependency")
            kind = step.get("kind")
            if not isinstance(kind, str) or kind not in {"percentage", "fixed"}:
                errors.append(f"{step_label} kind must be percentage or fixed")
                kind = None
            if kind == "percentage":
                if "fixed_amount" in step:
                    errors.append(f"{step_label} percentage adjustment cannot also declare fixed_amount")
                rate = _amount_decimal(step, "rate", f"{step_label} rate", errors, gaps)
                if rate is not None and rate < 0:
                    errors.append(f"{step_label} percentage rate cannot be negative")
                deduction = rounded(expected_basis * rate) if expected_basis is not None and rate is not None else None
            elif kind == "fixed":
                if "rate" in step:
                    errors.append(f"{step_label} fixed adjustment cannot also declare rate")
                fixed = _amount_decimal(step, "fixed_amount", f"{step_label} fixed_amount", errors, gaps)
                if fixed is not None and fixed < 0:
                    errors.append(f"{step_label} fixed_amount cannot be negative")
                deduction = rounded(fixed) if fixed is not None else None
            else:
                deduction = None
            declared_deduction = _amount_decimal(step, "deduction_amount", f"{step_label} deduction_amount", errors, gaps)
            if deduction is not None and declared_deduction is not None and rounded(declared_deduction) != deduction:
                errors.append(f"{step_label} deduction_amount does not match the stated basis and factor")
            result = rounded(remaining_balance - deduction) if remaining_balance is not None and deduction is not None else None
            declared_result = _amount_decimal(step, "resulting_amount", f"{step_label} resulting_amount", errors, gaps)
            if result is not None and declared_result is not None and rounded(declared_result) != result:
                errors.append(f"{step_label} resulting_amount does not match remaining balance less this adjustment")
            if step_id and result is not None:
                expected_results[step_id] = result
                remaining_balance = result
            if step_id:
                # A calculation may only depend on the original or an earlier
                # adjustment. Add this ID after checking its basis to reject
                # self-references and forward references as structural errors.
                known_calculation_ids.add(step_id)
            if deduction is not None:
                adjustment_total += deduction
            else:
                adjustments_complete = False

        def sum_source_rows(key: str, amount_key: str) -> tuple[Decimal, bool]:
            rows = chain.get(key)
            if not isinstance(rows, list):
                errors.append(f"{label} {key} must be an array")
                return Decimal(0), False
            total = Decimal(0)
            complete = True
            row_ids: set[str] = set()
            for row_index, row in enumerate(rows):
                row_label = f"{label} {key} {row_index}"
                if not isinstance(row, dict):
                    errors.append(f"{row_label} must be an object")
                    complete = False
                    continue
                identity_key = "offset_id" if key == "offsets" else "record_id"
                identity = _required_text(row, identity_key, f"{row_label} {identity_key}", errors)
                if identity and identity in row_ids:
                    errors.append(f"{row_label} has duplicate {identity_key}")
                row_ids.add(identity)
                _amount_text(row, "source_ref", f"{row_label} source_ref", errors, gaps)
                evidence_status = row.get("evidence_status")
                if not isinstance(evidence_status, str) or evidence_status not in {"confirmed", "missing", "conflicted", "unverified"}:
                    errors.append(f"{row_label} evidence_status is invalid")
                elif evidence_status != "confirmed":
                    gaps.append(f"{row_label} source is {evidence_status}; unable to verify")
                factor_id = _required_text(row, "factor_id", f"{row_label} factor_id", errors)
                if factor_id and factor_id in factor_ids:
                    errors.append(f"{row_label} reapplies an adjustment factor already included or applied")
                if factor_id:
                    factor_ids.add(factor_id)
                if key == "offsets":
                    _amount_text(row, "nature", f"{row_label} nature", errors, gaps)
                amount = _amount_decimal(row, amount_key, f"{row_label} {amount_key}", errors, gaps)
                if amount is not None:
                    if amount < 0:
                        errors.append(f"{row_label} {amount_key} cannot be negative")
                    total += rounded(amount)
                else:
                    complete = False
            return total, complete

        payments_total, payments_complete = sum_source_rows("payments", "amount")
        offsets_total, offsets_complete = sum_source_rows("offsets", "amount")
        adjusted_gross = remaining_balance
        if original_value is not None and adjustments_complete and rounded(original_value - adjustment_total) != rounded(adjusted_gross):
            errors.append(f"{label} adjusted_gross does not reconcile to gross less adjustments_total")
        elif original_value is None or not adjustments_complete:
            gaps.append(f"{label} adjusted gross cannot be fully calculated")
        expected_totals: dict[str, Decimal | None] = {
            "gross": rounded(original_value) if original_value is not None else None,
            "adjustments_total": rounded(adjustment_total) if adjustments_complete else None,
            "adjusted_gross": rounded(adjusted_gross) if adjusted_gross is not None else None,
            "paid_total": rounded(payments_total) if payments_complete else None,
            "offsets_total": rounded(offsets_total) if offsets_complete else None,
            "net_total": rounded(adjusted_gross - payments_total - offsets_total)
            if adjusted_gross is not None and payments_complete and offsets_complete else None,
        }
        reported = chain.get("reported_totals")
        if not isinstance(reported, dict):
            errors.append(f"{label} reported_totals missing or malformed")
            continue
        for key, expected in expected_totals.items():
            reported_value = _amount_decimal(reported, key, f"{label} reported_totals.{key}", errors, gaps)
            if expected is not None and reported_value is not None and rounded(reported_value) != expected:
                errors.append(f"{label} reported total {key} is stale or inconsistent")
            elif expected is None:
                gaps.append(f"{label} reported total {key} cannot be reconciled from unverified inputs")

    if gaps and status == "verified":
        warnings.append("amount review says verified but source/review gaps remain; treated as unable-to-verify")
    warnings.extend(gaps)


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
    warnings: list[str] = []
    final_requested = args.intent in FINAL_INTENTS
    redline_report: dict = {}
    contract_source_hash: str | None = None
    contract_review_binding: dict[str, str] | None = None

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
        redline_report = load(args.redline_report, "redline report", errors) if args.redline_report else {}
        if not redline_report:
            errors.append("contract release requires a redline report")
        elif redline_report.get("status") != "PASS":
            errors.append("redline quality gate did not PASS")
        elif not isinstance(redline_report.get("hashes"), dict) or redline_report["hashes"].get("redline") != sha256(args.artifact):
            errors.append("redline report hash does not match delivery artifact")

    if args.authority_required:
        authority = load(args.authority_package, "authority package", errors) if args.authority_package else {}
        if not authority:
            errors.append("formal legal authority is required but authority package is missing")
        else:
            validate_authority(authority, matter_task_id, errors)

    validate_policy(load(args.negotiation_policy, "negotiation policy", errors), matter_task_id, errors)

    signoff: dict = load(args.signoff, "review signoff", errors) if args.signoff else {}
    signoff_required = final_requested or args.risk_level in {"R2", "R3"}
    if signoff_required and not signoff:
        errors.append("Final/R2/R3 release requires human review signoff")
    if signoff and args.artifact.is_file():
        if signoff_required:
            validate_signoff(signoff, args.artifact, args.risk_level, args.intent, matter_task_id, args.signoff, errors)
        if args.contract and final_requested:
            contract_review = signoff.get("contract_protection_review")
            if isinstance(contract_review, dict) and contract_review.get("review_path", "full") == "light":
                contract_source_hash = validate_contract_source_report(
                    redline_report, matter, args.artifact, errors
                )
                original_value = redline_report.get("original")
                if contract_source_hash and isinstance(original_value, str):
                    actual_report = validate_actual_light_redline(
                        redline_report, Path(original_value).expanduser().resolve(), args.artifact, errors
                    )
                    if actual_report:
                        redline_report = actual_report
                        actual_diff_hash = change_list_sha256(actual_report.get("change_text"))
                        actual_hashes = actual_report.get("hashes")
                        if contract_source_hash and actual_diff_hash and isinstance(actual_hashes, dict):
                            contract_review_binding = {
                                "source_sha256": contract_source_hash,
                                "redline_sha256": str(actual_hashes.get("redline", "")),
                                "change_context_sha256": actual_diff_hash,
                            }
            validate_contract_protection_review(
                contract_review,
                args.artifact,
                errors,
                parent_signoff=signoff,
                risk_level=args.risk_level,
                redline_report=redline_report,
                source_hash=contract_source_hash,
            )
        amount_review = signoff.get("amount_review")
        if args.amount_review_required and final_requested and amount_review is None:
            errors.append("amount-sensitive Final requires a structured amount review")
        if amount_review is not None:
            amount_warnings: list[str] = []
            validate_amount_review(amount_review, args.artifact, errors, amount_warnings)
            if final_requested:
                errors.extend(f"amount review unresolved: {warning}" for warning in amount_warnings)
            else:
                warnings.extend(amount_warnings)

    decision = "RELEASE" if not errors and final_requested else "DRAFT_ONLY" if not errors else "BLOCKED"
    report = {
        "schema_version": "1.0",
        "status": "FAIL" if errors else "WARN" if warnings else "PASS",
        "decision": decision,
        "artifact": str(args.artifact),
        "artifact_sha256": sha256(args.artifact) if args.artifact.is_file() else None,
        "output_path": str(args.output_path),
        "intent": args.intent,
        "risk_level": args.risk_level,
        "errors": errors,
        "warnings": warnings,
    }
    if contract_review_binding is not None:
        report["contract_review_binding"] = contract_review_binding
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
