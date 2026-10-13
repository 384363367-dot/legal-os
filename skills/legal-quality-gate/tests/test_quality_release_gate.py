#!/usr/bin/env python3
"""Executable regression tests for the P0 release lock."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "release_gate.py"
CONTRACT_ROOT = ROOT if ROOT.name == "legal-os-contract" else ROOT.parent / "legal-os-contract"
REDLINE_GATE = CONTRACT_ROOT / "scripts" / "redline_quality_gate.py"
sys.path.insert(0, str(CONTRACT_ROOT / "tests"))
from test_contract_redline_quality_gate import deletion, insertion, paragraph, run, write_docx  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source.txt"
        self.source.write_text("source facts", encoding="utf-8")
        self.artifact = self.root / "artifact.txt"
        self.artifact.write_text("draft result", encoding="utf-8")
        self.manifest = self.root / "matter.json"
        self.write_manifest()
        self.report = self.root / "release.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_manifest(self, classification: str = "S2", public_export_allowed: bool = False) -> None:
        self.manifest.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "matter_task_id": "MATTER-001",
                    "owner": "个人使用者",
                    "classification": classification,
                    "matter_root": str(self.root),
                    "public_export_allowed": public_export_allowed,
                    "retention_status": "active",
                    "source_files": [
                        {"path": self.source.name, "sha256": sha256(self.source), "role": "original"}
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def write_signoff(
        self,
        *,
        risk: str,
        intent: str,
        artifact_hash: str | None = None,
        contract_review: dict | None = None,
        amount_review: dict | None = None,
    ) -> Path:
        data = {
            "schema_version": "1.0",
            "matter_task_id": "MATTER-001",
            "artifact_path": str(self.artifact.resolve()),
            "artifact_sha256": artifact_hash or sha256(self.artifact),
            "risk_level": risk,
            "reviewer": "人工审核员",
            "reviewed_at": "2026-07-14T09:00:00+08:00",
            "status": "approved",
            "permitted_use": intent,
            "checks": {
                "facts": True,
                "authority": True,
                "strategy": True,
                "format": True,
                "privacy": True,
            },
        }
        if contract_review is not None:
            data["contract_protection_review"] = contract_review
        if amount_review is not None:
            data["amount_review"] = amount_review
        path = self.root / "signoff.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def contract_review(self, outcome: str = "preserved") -> dict:
        review = {
            "schema_version": "1.0",
            "artifact_sha256": sha256(self.artifact),
            "reviewer": "合同主审",
            "reviewed_at": "2026-07-14T09:00:00+08:00",
            "review_scope": "已识别核心风险与二次文字优化后的最终文本",
            "status": "approved",
            "all_supported_core_risks_mapped": True,
            "core_risks_status": "identified",
            "risk_mappings": [
                {
                    "risk_id": "RISK-1",
                    "core_risk": "关键履行节点缺少保护",
                    "intended_protection": "明确验收和付款先后条件",
                    "first_pass_agreed_protection": "首轮已同意设置验收前置条件",
                    "final_clause_refs": ["第4.2条", "第7.1条"],
                    "final_clause_excerpt_or_absence_reason": "第4.2条约定验收完成后付款，第7.1条衔接通知和复验",
                    "cross_references_complete": True,
                    "outcome": outcome,
                    "review_judgment": "逐项核对最终条款与互引后作出判断",
                }
            ],
        }
        if outcome == "approved_compromise":
            review["risk_mappings"][0]["compromise"] = {
                "approval_source": "current-user-instruction",
                "approval_ref": "用户确认的谈判底线",
                "approved_by": "事项负责人",
                "approved_at": "2026-07-14T09:00:00+08:00",
                "proportionality_reason": "保留核心验收前置条件并接受范围有限的时间调整",
                "retained_protection_or_rationale": "最终条款仍保留验收未完成时的付款抗辩",
            }
        return review

    def amount_review(
        self,
        *,
        original: int = 1000,
        repeated_factor: bool = False,
        repeat_payment_as_offset: bool = False,
        missing_source: bool = False,
    ) -> dict:
        first_result = 800
        second_result = 640
        review = {
            "schema_version": "1.0",
            "artifact_sha256": sha256(self.artifact),
            "reviewer": "金额复核人",
            "reviewed_at": "2026-07-14T09:00:00+08:00",
            "scope": "合同总价、两项顺序扣减、已付、抵扣及净额",
            "status": "unable-to-verify" if missing_source else "verified",
            "artifact_amounts_reconciled": True,
            "conclusion_review": "最终文件中的总价、扣减、已付、抵扣和净额与本链逐项核对一致。",
            "chains": [
                {
                    "chain_id": "CHAIN-1",
                    "currency": "CNY",
                    "rounding": {"decimal_places": 2, "mode": "half-up"},
                    "original_amount": {
                        "value": None if missing_source else original,
                        "source_ref": "合同第3条",
                        "evidence_status": "missing" if missing_source else "confirmed",
                    },
                    "initially_included_factor_ids": [],
                    "adjustments": [
                        {
                            "adjustment_id": "ADJ-1",
                            "factor_id": "contract-discount-clause-3",
                            "source_ref": "合同第3.2条",
                            "nature": "价格折让",
                            "evidence_status": "confirmed",
                            "basis_from": "original_amount",
                            "basis_amount": 1000,
                            "kind": "percentage",
                            "rate": 0.2,
                            "deduction_amount": 200,
                            "resulting_amount": first_result,
                        },
                        {
                            "adjustment_id": "ADJ-2",
                            "factor_id": "contract-discount-clause-3" if repeated_factor else "contract-retention-clause-8",
                            "source_ref": "合同第3.2条" if repeated_factor else "合同第8.1条",
                            "nature": "价格折让" if repeated_factor else "质量保证金",
                            "evidence_status": "confirmed",
                            "basis_from": "ADJ-1",
                            "basis_amount": first_result,
                            "kind": "percentage",
                            "rate": 0.2,
                            "deduction_amount": 160,
                            "resulting_amount": second_result,
                        },
                    ],
                    "payments": [
                        {
                            "record_id": "PAYMENT-1",
                            "factor_id": "payment-receipt-1",
                            "source_ref": "银行回单1",
                            "evidence_status": "confirmed",
                            "amount": 100,
                        }
                    ] if repeat_payment_as_offset else [],
                    "offsets": [
                        {
                            "offset_id": "OFFSET-1",
                            "factor_id": "payment-receipt-1" if repeat_payment_as_offset else "independent-offset-1",
                            "source_ref": "银行回单1" if repeat_payment_as_offset else "独立抵扣凭证1",
                            "nature": "已付款" if repeat_payment_as_offset else "独立费用抵扣",
                            "evidence_status": "confirmed",
                            "amount": 100 if repeat_payment_as_offset else 0,
                        }
                    ] if repeat_payment_as_offset else [],
                    "reported_totals": {
                        "gross": 1000,
                        "adjustments_total": 360,
                        "adjusted_gross": 640,
                        "paid_total": 0,
                        "offsets_total": 0,
                        "net_total": 640,
                    },
                }
            ],
        }
        return review

    def invoke(
        self,
        *,
        intent: str = "internal-draft",
        risk: str = "R1",
        output: Path | None = None,
        signoff: Path | None = None,
        extra: list[str] | None = None,
    ):
        command = [
            sys.executable,
            str(GATE),
            "--artifact",
            str(self.artifact),
            "--output-path",
            str(output or (self.root / "delivery" / self.artifact.name)),
            "--intent",
            intent,
            "--risk-level",
            risk,
            "--matter-manifest",
            str(self.manifest),
            "--out-json",
            str(self.report),
        ]
        if signoff:
            command.extend(["--signoff", str(signoff)])
        if extra:
            command.extend(extra)
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        return completed, json.loads(self.report.read_text(encoding="utf-8"))

    def test_r1_internal_draft_is_draft_only(self) -> None:
        completed, report = self.invoke()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")

    def test_r1_draft_with_honest_amount_gap_warns_and_stays_draft_only(self) -> None:
        signoff = self.write_signoff(
            risk="R1", intent="internal-draft", amount_review=self.amount_review(missing_source=True)
        )
        completed, report = self.invoke(signoff=signoff)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")
        self.assertEqual(report["status"], "WARN")
        self.assertTrue(any("unable to verify" in item for item in report["warnings"]))

    def test_r2_internal_draft_amount_gap_warns_with_valid_general_signoff(self) -> None:
        signoff = self.write_signoff(
            risk="R2", intent="internal-draft", amount_review=self.amount_review(missing_source=True)
        )
        completed, report = self.invoke(risk="R2", signoff=signoff)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")
        self.assertTrue(any("unable to verify" in item for item in report["warnings"]))

    def test_r2_internal_draft_without_amount_review_stays_draft_only(self) -> None:
        signoff = self.write_signoff(risk="R2", intent="internal-draft")
        completed, report = self.invoke(risk="R2", signoff=signoff)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")

    def test_r0_draft_with_wrong_amount_arithmetic_is_blocked(self) -> None:
        amount = self.amount_review()
        amount["chains"][0]["adjustments"][0]["deduction_amount"] = 201
        signoff = self.write_signoff(risk="R0", intent="internal-draft", amount_review=amount)
        completed, report = self.invoke(risk="R0", signoff=signoff)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("deduction_amount does not match" in item for item in report["errors"]))

    def test_missing_original_basis_remains_a_draft_warning(self) -> None:
        amount = self.amount_review(missing_source=True)
        signoff = self.write_signoff(risk="R0", intent="internal-draft", amount_review=amount)
        completed, report = self.invoke(risk="R0", signoff=signoff)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")
        self.assertTrue(any("basis depends on an unverified earlier amount" in item for item in report["warnings"]))

    def test_draft_self_and_forward_basis_references_are_blocked(self) -> None:
        for basis_from in ("ADJ-1", "ADJ-2"):
            with self.subTest(basis_from=basis_from):
                amount = self.amount_review()
                amount["chains"][0]["adjustments"][0]["basis_from"] = basis_from
                signoff = self.write_signoff(risk="R0", intent="internal-draft", amount_review=amount)
                completed, report = self.invoke(risk="R0", signoff=signoff)
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(report["decision"], "BLOCKED")
                self.assertTrue(any("basis_from must reference original_amount or an earlier adjustment" in item for item in report["errors"]))

    def test_malformed_amount_enums_are_blocked_without_traceback(self) -> None:
        mutations = (
            lambda review: review.update({"status": []}),
            lambda review: review["chains"][0]["original_amount"].update({"evidence_status": {}}),
            lambda review: review["chains"][0]["adjustments"][0].update({"kind": []}),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                amount = self.amount_review()
                mutate(amount)
                signoff = self.write_signoff(risk="R0", intent="internal-draft", amount_review=amount)
                completed, report = self.invoke(risk="R0", signoff=signoff)
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(report["decision"], "BLOCKED")
                self.assertNotIn("Traceback", completed.stdout + completed.stderr)

    def test_final_or_r2_without_signoff_is_blocked(self) -> None:
        completed, report = self.invoke(intent="external-final", risk="R2")
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("requires human review signoff" in item for item in report["errors"]))

    def test_matching_signoff_allows_final_release(self) -> None:
        signoff = self.write_signoff(risk="R2", intent="external-final")
        completed, report = self.invoke(intent="external-final", risk="R2", signoff=signoff)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_stale_signoff_hash_is_blocked(self) -> None:
        signoff = self.write_signoff(risk="R2", intent="external-final", artifact_hash="0" * 64)
        completed, report = self.invoke(intent="external-final", risk="R2", signoff=signoff)
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("signoff artifact hash" in item for item in report["errors"]))

    def test_sensitive_matter_cannot_enter_public_repo(self) -> None:
        output = self.root / "Legal_OS_Public" / "artifact.txt"
        completed, report = self.invoke(output=output)
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("cannot be placed in public repository" in item for item in report["errors"]))

    def test_publishing_requires_public_s0(self) -> None:
        signoff = self.write_signoff(risk="R1", intent="publishing")
        completed, report = self.invoke(intent="publishing", signoff=signoff)
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("publishing requires S0" in item for item in report["errors"]))
        self.write_manifest(classification="S0", public_export_allowed=True)
        completed, report = self.invoke(intent="publishing", signoff=signoff)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_contract_requires_matching_pass_report(self) -> None:
        redline_report = self.root / "redline.json"
        redline_report.write_text(
            json.dumps({"status": "FAIL", "hashes": {"redline": sha256(self.artifact)}}),
            encoding="utf-8",
        )
        completed, report = self.invoke(extra=["--contract", "--redline-report", str(redline_report)])
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("did not PASS" in item for item in report["errors"]))
        redline_report.write_text(
            json.dumps({"status": "PASS", "hashes": {"redline": "f" * 64}}),
            encoding="utf-8",
        )
        completed, report = self.invoke(extra=["--contract", "--redline-report", str(redline_report)])
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("report hash" in item for item in report["errors"]))

    def test_contract_internal_draft_remains_draft_only_without_protection_record(self) -> None:
        redline_report = self.write_pass_redline_report()
        completed, report = self.invoke(
            extra=["--contract", "--redline-report", str(redline_report)]
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")

    def write_pass_redline_report(self) -> Path:
        redline_report = self.root / "redline.json"
        redline_report.write_text(
            json.dumps({"status": "PASS", "hashes": {"redline": sha256(self.artifact)}}),
            encoding="utf-8",
        )
        return redline_report

    def write_actual_contract_redline(self, before: str, deleted: str, inserted: str, after: str = "") -> Path:
        original = self.root / "contract-original.docx"
        self.artifact = self.root / "contract-redline.docx"
        write_docx(original, [paragraph(run(before + deleted + after))])
        write_docx(
            self.artifact,
            [paragraph(run(before) + deletion(deleted) + insertion(inserted) + run(after))],
            track=True,
        )
        report = self.root / "actual-redline-report.json"
        result = subprocess.run(
            [sys.executable, str(REDLINE_GATE), "--original", str(original), "--redline", str(self.artifact), "--out-json", str(report)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["source_files"] = [
            item for item in manifest["source_files"] if item.get("path") != original.name
        ]
        manifest["source_files"].append({"path": original.name, "sha256": sha256(original), "role": "original"})
        self.manifest.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return report

    def light_contract_review(self, *, rationale: str | None = None) -> dict:
        return {
            "review_path": "light",
            "review_scope": "逐字核对第1段中的拼写差异、原件、实际红线和接受/拒绝视图。",
            "core_risks_status": "none",
            "no_core_risks_rationale": rationale or "主审确认该差异仅更正拼写，不改变句义、法律效果、适用范围或核心风险。",
        }

    def test_contract_technical_pass_without_protection_review_is_blocked(self) -> None:
        redline_report = self.write_pass_redline_report()
        signoff = self.write_signoff(risk="R2", intent="internal-final")
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("structured protection review" in item for item in report["errors"]))

    def test_single_round_full_review_does_not_need_first_pass_record(self) -> None:
        redline_report = self.write_pass_redline_report()
        review = self.contract_review()
        review["review_round"] = "single"
        review["risk_mappings"][0].pop("first_pass_agreed_protection")
        signoff = self.write_signoff(risk="R2", intent="internal-final", contract_review=review)
        completed, report = self.invoke(
            intent="internal-final", risk="R2", signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_actual_unprotected_typo_uses_light_path_with_inherited_signoff_metadata(self) -> None:
        redline_report = self.write_actual_contract_redline("A small typo ", "teh", "the", " appears here.")
        signoff = self.write_signoff(
            risk="R1", intent="internal-final", contract_review=self.light_contract_review()
        )
        completed, report = self.invoke(
            intent="internal-final", risk="R1", signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")
        binding = report["contract_review_binding"]
        self.assertEqual(binding["source_sha256"], json.loads(redline_report.read_text(encoding="utf-8"))["hashes"]["original"])
        self.assertEqual(binding["redline_sha256"], sha256(self.artifact))
        self.assertEqual(len(binding["change_context_sha256"]), 64)

    def test_light_typo_is_not_blocked_by_notice_substrings_or_unchanged_markers(self) -> None:
        examples = (
            ("The company will approve a notice under normal rules; the recipient ", "recieves", "receives", " a notice."),
            ("供应商应当发送通知，客户可以接收但不得转发，联系人 ", "recieves", "receives", " a notice."),
        )
        for before, deleted, inserted, after in examples:
            with self.subTest(context=before):
                redline_report = self.write_actual_contract_redline(before, deleted, inserted, after)
                signoff = self.write_signoff(
                    risk="R1", intent="internal-final", contract_review=self.light_contract_review()
                )
                completed, report = self.invoke(
                    intent="internal-final", risk="R1", signoff=signoff,
                    extra=["--contract", "--redline-report", str(redline_report)],
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertEqual(report["decision"], "RELEASE")

    def test_light_rejects_actual_deadline_and_amount_value_changes_even_if_called_typos(self) -> None:
        examples = (
            ("Materials will be submitted in ", "30", "90", " days."),
            ("The quoted price is ", "100.00", "10.00", " USD."),
        )
        for before, deleted, inserted, after in examples:
            with self.subTest(deleted=deleted, inserted=inserted):
                redline_report = self.write_actual_contract_redline(before, deleted, inserted, after)
                signoff = self.write_signoff(
                    risk="R1", intent="internal-final",
                    contract_review=self.light_contract_review(rationale="主审自称仅为拼写修正，无风险。"),
                )
                completed, report = self.invoke(
                    intent="internal-final", risk="R1", signoff=signoff,
                    extra=["--contract", "--redline-report", str(redline_report)],
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(report["decision"], "BLOCKED")
                self.assertTrue(any("changes a numeric, date, amount" in item for item in report["errors"]))

    def test_light_rejects_actual_negation_and_permission_changes(self) -> None:
        examples = (
            ("The supplier ", "shall", "may", " act."),
            ("The operator ", "may", "may not", " access records."),
        )
        for before, deleted, inserted, after in examples:
            with self.subTest(deleted=deleted, inserted=inserted):
                redline_report = self.write_actual_contract_redline(before, deleted, inserted, after)
                signoff = self.write_signoff(
                    risk="R1", intent="internal-final",
                    contract_review=self.light_contract_review(rationale="主审自称只是小幅措辞修正。"),
                )
                completed, report = self.invoke(
                    intent="internal-final", risk="R1", signoff=signoff,
                    extra=["--contract", "--redline-report", str(redline_report)],
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertEqual(report["decision"], "BLOCKED")
                self.assertTrue(any("legal-effect marker" in item for item in report["errors"]))

    def test_light_rejects_actual_chinese_legal_effect_marker_change(self) -> None:
        redline_report = self.write_actual_contract_redline("供应商", "可以", "不得", "访问记录。")
        signoff = self.write_signoff(
            risk="R1", intent="internal-final", contract_review=self.light_contract_review(
                rationale="主审自称仅为文字调整。"
            )
        )
        completed, report = self.invoke(
            intent="internal-final", risk="R1", signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("legal-effect marker" in item for item in report["errors"]))

    def test_light_self_claim_cannot_hide_protected_duty_change(self) -> None:
        redline_report = self.write_actual_contract_redline("供应商承担", "100", "10", "元赔偿责任。")
        signoff = self.write_signoff(
            risk="R1", intent="internal-final", contract_review=self.light_contract_review(
                rationale="审阅人自称只改数字且无风险。"
            )
        )
        completed, report = self.invoke(
            intent="internal-final", risk="R1", signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("protected legal domain" in item for item in report["errors"]))

    def test_light_review_rejects_tampered_redline_context_and_mismatched_inherited_hash(self) -> None:
        redline_report = self.write_actual_contract_redline("A small typo ", "teh", "the", " appears here.")
        report_data = json.loads(redline_report.read_text(encoding="utf-8"))
        report_data["change_text"][0]["context_before"] = "不含任何合同上下文的伪造文本"
        redline_report.write_text(json.dumps(report_data, ensure_ascii=False), encoding="utf-8")
        review = self.light_contract_review()
        review["artifact_sha256"] = "0" * 64
        signoff = self.write_signoff(risk="R1", intent="internal-final", contract_review=review)
        completed, result = self.invoke(
            intent="internal-final", risk="R1", signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertTrue(any("does not match the actual redline" in item for item in result["errors"]))
        self.assertTrue(any("must match the enclosing sign-off" in item for item in result["errors"]))

    def test_light_claim_requires_actual_bound_redline_not_manual_mode_assertion(self) -> None:
        redline_report = self.root / "asserted-light.json"
        redline_report.write_text(json.dumps({"status": "PASS", "hashes": {"redline": sha256(self.artifact)}}), encoding="utf-8")
        signoff = self.write_signoff(
            risk="R1", intent="internal-final", contract_review=self.light_contract_review()
        )
        completed, report = self.invoke(
            intent="internal-final", risk="R1", signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("contract redline" in item or "light contract review" in item for item in report["errors"]))

    def test_second_pass_weakening_is_blocked(self) -> None:
        redline_report = self.write_pass_redline_report()
        signoff = self.write_signoff(
            risk="R2", intent="internal-final", contract_review=self.contract_review("weakened")
        )
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("weakened" in item for item in report["errors"]))

    def test_contract_protection_review_stale_hash_is_blocked(self) -> None:
        redline_report = self.write_pass_redline_report()
        review = self.contract_review()
        review["artifact_sha256"] = "0" * 64
        signoff = self.write_signoff(risk="R2", intent="internal-final", contract_review=review)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("contract protection review hash" in item for item in report["errors"]))

    def test_approved_proportionate_contract_compromise_can_release(self) -> None:
        approval_source = self.root / "approval-note.txt"
        approval_source.write_text(
            "核心风险：验收合格前不得付款。事项负责人仅批准将复验期限延长五个工作日；未批准取消验收条件或改变未验收前的付款抗辩。\n",
            encoding="utf-8",
        )
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["source_files"].append({"path": approval_source.name, "sha256": sha256(approval_source), "role": "reference"})
        self.manifest.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        review = self.contract_review("approved_compromise")
        mapping = review["risk_mappings"][0]
        mapping["core_risk"] = "验收合格前付款会削弱买方对未交付或未验收工作的保护。"
        mapping["intended_protection"] = "保留验收合格为付款前提，并保留未验收前的付款抗辩。"
        mapping["final_clause_excerpt_or_absence_reason"] = "最终验收合格后付款；复验期限延长五个工作日，不影响未验收前暂停付款。"
        mapping["review_judgment"] = "回读批准材料后确认仅批准五个工作日复验期限调整，验收合格付款条件未变。"
        mapping["compromise"].update({
            "approval_source": "matter-document",
            "approval_ref": "approval-note.txt §1",
            "proportionality_reason": "该范围有限的期限调整有事项负责人批准，且未解除验收付款前提。",
            "retained_protection_or_rationale": "验收未合格前仍可暂停付款，保留当前核心风险保护。",
        })
        redline_report = self.write_pass_redline_report()
        signoff = self.write_signoff(
            risk="R2", intent="internal-final", contract_review=review
        )
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_actual_redline_pass_still_blocks_missing_or_weakened_protection(self) -> None:
        original = self.root / "original.docx"
        self.artifact = self.root / "redline.docx"
        redline_report = self.root / "actual-redline-report.json"
        write_docx(original, [paragraph(run("付款期限为三十日。"))])
        write_docx(
            self.artifact,
            [paragraph(run("付款期限为") + deletion("三十") + insertion("十五") + run("日。"))],
            track=True,
        )
        redline_result = subprocess.run(
            [
                sys.executable,
                str(REDLINE_GATE),
                "--original",
                str(original),
                "--redline",
                str(self.artifact),
                "--out-json",
                str(redline_report),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(redline_result.returncode, 0, redline_result.stdout + redline_result.stderr)
        self.assertEqual(json.loads(redline_report.read_text(encoding="utf-8"))["status"], "PASS")

        for review in (None, self.contract_review("weakened")):
            signoff = self.write_signoff(
                risk="R2", intent="internal-final", contract_review=review
            )
            completed, report = self.invoke(
                intent="internal-final",
                risk="R2",
                signoff=signoff,
                extra=["--contract", "--redline-report", str(redline_report)],
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(report["decision"], "BLOCKED")

    def test_preserved_protection_requires_final_clause_reference(self) -> None:
        review = self.contract_review("preserved")
        review["risk_mappings"][0]["final_clause_refs"] = []
        redline_report = self.write_pass_redline_report()
        signoff = self.write_signoff(risk="R2", intent="internal-final", contract_review=review)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("requires at least one final clause reference" in item for item in report["errors"]))

    def test_zero_core_risks_require_a_substantive_reason(self) -> None:
        redline_report = self.write_pass_redline_report()
        review = self.contract_review("preserved")
        review.update({"core_risks_status": "none", "risk_mappings": []})
        signoff = self.write_signoff(risk="R2", intent="internal-final", contract_review=review)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("zero-core-risk rationale missing" in item for item in report["errors"]))

        review["no_core_risks_rationale"] = "已逐项核对正文、附件和履行材料，未发现需要合同保护的核心风险。"
        signoff = self.write_signoff(risk="R2", intent="internal-final", contract_review=review)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--contract", "--redline-report", str(redline_report)],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_amount_gate_rejects_reapplied_twenty_percent_factor(self) -> None:
        signoff = self.write_signoff(
            risk="R2", intent="internal-final", amount_review=self.amount_review(repeated_factor=True)
        )
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("reapplies an adjustment factor" in item for item in report["errors"]))

    def test_amount_review_stale_hash_is_blocked(self) -> None:
        amount = self.amount_review()
        amount["artifact_sha256"] = "0" * 64
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("amount review hash" in item for item in report["errors"]))

    def test_amount_gate_rejects_factor_already_in_starting_amount(self) -> None:
        amount = self.amount_review()
        amount["chains"][0]["initially_included_factor_ids"] = ["contract-discount-clause-3"]
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("reapplies an adjustment factor" in item for item in report["errors"]))

    def test_amount_gate_normalizes_initial_factor_before_reapply_check(self) -> None:
        amount = self.amount_review()
        chain = amount["chains"][0]
        chain["initially_included_factor_ids"] = [" PRICE-DISCOUNT-20-3.2 "]
        chain["adjustments"][0].update(
            {
                "factor_id": "PRICE-DISCOUNT-20-3.2",
                "source_ref": "合同第3.2条",
                "nature": "价格折让",
            }
        )
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("reapplies an adjustment factor" in item for item in report["errors"]))

    def test_amount_gate_rejects_initial_factor_inventory_duplicates_after_normalizing(self) -> None:
        amount = self.amount_review()
        amount["chains"][0]["initially_included_factor_ids"] = [" factor ", "factor"]
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("initially_included_factor_ids contains duplicates" in item for item in report["errors"]))

    def test_amount_gate_requires_explicit_initial_factor_inventory(self) -> None:
        amount = self.amount_review()
        del amount["chains"][0]["initially_included_factor_ids"]
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("initially_included_factor_ids must be an array" in item for item in report["errors"]))

    def test_amount_gate_recomputes_stale_totals_when_source_basis_changes(self) -> None:
        signoff = self.write_signoff(
            risk="R2", intent="internal-final", amount_review=self.amount_review(original=1200)
        )
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("basis_amount is stale" in item for item in report["errors"]))
        self.assertTrue(any("reported total gross is stale" in item for item in report["errors"]))

    def test_amount_gate_blocks_stale_rollups_after_all_steps_are_recomputed(self) -> None:
        amount = self.amount_review(original=1200)
        first, second = amount["chains"][0]["adjustments"]
        first.update({"basis_amount": 1200, "deduction_amount": 240, "resulting_amount": 960})
        second.update({"basis_amount": 960, "deduction_amount": 192, "resulting_amount": 768})
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(any("basis_amount is stale" in item for item in report["errors"]))
        self.assertTrue(any("reported total gross is stale" in item for item in report["errors"]))
        self.assertTrue(any("reported total adjustments_total is stale" in item for item in report["errors"]))
        self.assertTrue(any("reported total adjusted_gross is stale" in item for item in report["errors"]))
        self.assertTrue(any("reported total net_total is stale" in item for item in report["errors"]))

    def test_amount_gate_allows_independent_sequential_deductions(self) -> None:
        signoff = self.write_signoff(
            risk="R2", intent="internal-final", amount_review=self.amount_review()
        )
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_amount_gate_rejects_payment_reused_as_offset(self) -> None:
        amount = self.amount_review(repeat_payment_as_offset=True)
        amount["chains"][0]["reported_totals"].update(
            {"paid_total": 100, "offsets_total": 100, "net_total": 440}
        )
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("reapplies an adjustment factor" in item for item in report["errors"]))

    def test_amount_gate_reconciles_independent_adjustment_on_original_basis(self) -> None:
        amount = self.amount_review()
        second = amount["chains"][0]["adjustments"][1]
        second.update(
            {"basis_from": "original_amount", "basis_amount": 1000, "rate": 0.1, "deduction_amount": 100, "resulting_amount": 900}
        )
        amount["chains"][0]["reported_totals"].update(
            {"adjustments_total": 300, "adjusted_gross": 900, "net_total": 900}
        )
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("remaining balance less this adjustment" in item for item in report["errors"]))

        second["resulting_amount"] = 700
        amount["chains"][0]["reported_totals"].update({"adjusted_gross": 700, "net_total": 700})
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "RELEASE")

    def test_amount_adjustment_cannot_overwrite_original_amount_basis_id(self) -> None:
        amount = self.amount_review()
        amount["chains"][0]["adjustments"][0]["adjustment_id"] = "original_amount"
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("reuses an existing calculation basis id" in item for item in report["errors"]))

    def test_amount_required_without_review_is_blocked(self) -> None:
        signoff = self.write_signoff(risk="R2", intent="internal-final")
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("requires a structured amount review" in item for item in report["errors"]))

    def test_malformed_amount_basis_returns_blocked_report(self) -> None:
        amount = self.amount_review()
        amount["chains"][0]["adjustments"][1]["basis_from"] = {"unexpected": "object"}
        signoff = self.write_signoff(risk="R2", intent="internal-final", amount_review=amount)
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertTrue(any("basis_from must reference" in item for item in report["errors"]))

    def test_missing_amount_source_stays_unable_to_verify(self) -> None:
        signoff = self.write_signoff(
            risk="R2", intent="internal-final", amount_review=self.amount_review(missing_source=True)
        )
        completed, report = self.invoke(
            intent="internal-final",
            risk="R2",
            signoff=signoff,
            extra=["--amount-review-required"],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("unable to verify" in item for item in report["errors"]))

    def test_unverified_case_authority_is_blocked(self) -> None:
        authority = self.root / "authority.json"
        authority.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "matter_task_id": "MATTER-001",
                    "verified_at": "2026-07-14T09:00:00+08:00",
                    "verified_by": "人工审核员",
                    "propositions": [
                        {
                            "proposition_id": "P1",
                            "text": "裁判观点",
                            "authority_id": "CASE-1",
                            "source_type": "case",
                            "title": "某案",
                            "issuing_body": "某法院",
                            "locator": "https://court.example/case",
                            "pinpoint": "裁判理由第1段",
                            "current_status": "unverified",
                            "accessed_at": "2026-07-14T09:00:00+08:00",
                            "support": "支持命题",
                            "scope": "仅本案事实",
                            "contrary_sources": [],
                            "review_status": "approved",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        completed, report = self.invoke(extra=["--authority-required", "--authority-package", str(authority)])
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("verified-source" in item for item in report["errors"]))

    def test_pending_negotiation_parameter_is_blocked(self) -> None:
        policy = self.root / "policy.json"
        policy.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "matter_task_id": "MATTER-001",
                    "party_position": "seller",
                    "approved_by": "人工审核员",
                    "approved_at": "2026-07-14T09:00:00+08:00",
                    "parameters": [
                        {
                            "key": "delay_liquidated_damages_rate",
                            "value": None,
                            "source": "pending-choice",
                            "scope": "本合同",
                            "status": "pending",
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        completed, report = self.invoke(extra=["--negotiation-policy", str(policy)])
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("negotiation parameter is pending" in item for item in report["errors"]))


if __name__ == "__main__":
    unittest.main()
