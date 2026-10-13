from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "skills/legal-os-data-verification/assets/templates/Legal_OS_v1.7_Amount_Data_Verification_Workspace.xlsx"
EXPORTER = REPO / "skills/legal-os-data-verification/scripts/export_amount_review.py"
GATE = REPO / "skills/legal-quality-gate/scripts/release_gate.py"
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
ET.register_namespace("x", MAIN)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_cell(root: ET.Element, ref: str, value: object) -> None:
    row_number = "".join(character for character in ref if character.isdigit())
    sheet_data = root.find(f"{{{MAIN}}}sheetData")
    assert sheet_data is not None
    row = next((item for item in sheet_data.findall(f"{{{MAIN}}}row") if item.get("r") == row_number), None)
    if row is None:
        row = ET.Element(f"{{{MAIN}}}row", {"r": row_number})
        existing = list(sheet_data)
        index = next((i for i, item in enumerate(existing) if int(item.get("r", "0")) > int(row_number)), len(existing))
        sheet_data.insert(index, row)
    for cell in list(row):
        if cell.get("r") == ref:
            row.remove(cell)
    cell = ET.SubElement(row, f"{{{MAIN}}}c", {"r": ref})
    if value is None or value == "":
        return
    if isinstance(value, (int, float)):
        cell.set("t", "n")
        ET.SubElement(cell, f"{{{MAIN}}}v").text = str(value)
    else:
        cell.set("t", "str")
        ET.SubElement(cell, f"{{{MAIN}}}v").text = str(value)


def write_workbook(path: Path, rows: list[dict[str, object]]) -> None:
    shutil.copy2(TEMPLATE, path)
    with zipfile.ZipFile(path, "r") as source:
        parts = {info.filename: (info, source.read(info.filename)) for info in source.infolist()}
    worksheet = ET.fromstring(parts["xl/worksheets/sheet2.xml"][1])
    for row_index, values in enumerate(rows, start=16):
        for column, value in values.items():
            set_cell(worksheet, f"{column}{row_index}", value)
    parts["xl/worksheets/sheet2.xml"] = (
        parts["xl/worksheets/sheet2.xml"][0],
        ET.tostring(worksheet, encoding="utf-8", xml_declaration=True),
    )
    temp_path = path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(temp_path, "w") as target:
        for name, (info, data) in parts.items():
            target.writestr(info, data)
    temp_path.replace(path)


def original_row(*, amount: int = 1000, paid: int | str | None = 0, source: str = "合同第3条", payment_source: str = "", payment_status: str = "") -> dict[str, object]:
    return {
        "A": "RAW-1", "B": source, "C": "合同总价", "E": "CNY", "J": amount, "K": paid,
        "L": "已核" if source else "待核", "N": "CHAIN-1", "O": "original_amount", "T": "无", "U": 2,
        "V": "half-up", "W": payment_source, "X": payment_status,
    }


def percent_adjustment(record_id: str, *, factor_id: str, basis_from: str, rate: float, source: str, nature: str) -> dict[str, object]:
    return {
        "A": record_id, "B": source, "C": nature, "E": "CNY", "L": "已核", "N": "CHAIN-1",
        "O": "adjustment", "P": factor_id, "Q": basis_from, "R": "percentage", "S": rate,
    }


class AmountWorkbookExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workbook = self.root / "ledger.xlsx"
        self.artifact = self.root / "artifact.txt"
        self.artifact.write_text("source-locked artifact", encoding="utf-8")
        self.signoff = self.root / "signoff.json"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def base_signoff(self, intent: str = "internal-final", risk: str = "R2") -> dict:
        return {
            "schema_version": "1.0", "matter_task_id": "MATTER-001",
            "artifact_path": str(self.artifact.resolve()), "artifact_sha256": sha256(self.artifact),
            "risk_level": risk, "reviewer": "人工审阅人", "reviewed_at": "2026-10-13T09:00:00+08:00",
            "status": "approved", "permitted_use": intent,
            "checks": {key: True for key in ("facts", "authority", "strategy", "format", "privacy")},
        }

    def invoke_export(self, workbook: Path | None = None, signoff: Path | None = None, output: Path | None = None):
        workbook = workbook or self.workbook
        signoff = signoff or self.signoff
        output = output or self.root / "signoff.amount.json"
        return subprocess.run(
            [sys.executable, str(EXPORTER), "--workbook", str(workbook), "--artifact", str(self.artifact), "--signoff", str(signoff), "--out-signoff", str(output)],
            capture_output=True, text=True, check=False,
        ), output

    def test_single_ledger_generates_correct_chain_and_reuses_only_matching_human_review(self) -> None:
        write_workbook(self.workbook, [
            original_row(),
            percent_adjustment("ADJ-1", factor_id="DISCOUNT-20", basis_from="original_amount", rate=0.2, source="合同第3.2条", nature="价格折让"),
            percent_adjustment("ADJ-2", factor_id="RETENTION-10", basis_from="original_amount", rate=0.1, source="合同第8.1条", nature="质保金"),
        ])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        generated, amount_path = self.invoke_export()
        self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
        data = json.loads(amount_path.read_text(encoding="utf-8"))
        amount = data["amount_review"]
        self.assertEqual(amount["status"], "unable-to-verify")
        self.assertIs(amount["artifact_amounts_reconciled"], False)
        self.assertNotIn("reviewer", amount)
        chain = amount["chains"][0]
        self.assertEqual([step["basis_from"] for step in chain["adjustments"]], ["original_amount", "original_amount"])
        self.assertEqual(chain["adjustments"][0]["deduction_amount"], 200)
        self.assertEqual(chain["adjustments"][1]["deduction_amount"], 100)
        self.assertEqual(chain["reported_totals"], {
            "gross": 1000, "adjustments_total": 300, "adjusted_gross": 700,
            "paid_total": 0, "offsets_total": 0, "net_total": 700,
        })

        amount.update({
            "status": "verified", "artifact_amounts_reconciled": True,
            "reviewer": "金额复核人", "reviewed_at": "2026-10-13T10:00:00+08:00",
            "conclusion_review": "人工核对原件与金额链，确认正式文件总额和分项一致。",
        })
        amount_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        reused, reused_path = self.invoke_export(signoff=amount_path, output=self.root / "reused.json")
        self.assertEqual(reused.returncode, 0, reused.stdout + reused.stderr)
        reused_data = json.loads(reused_path.read_text(encoding="utf-8"))
        self.assertEqual(reused_data["amount_review"]["status"], "verified")
        self.assertEqual(reused_data["amount_review"]["reviewer"], "金额复核人")

        # A new amount in the same workbook must invalidate the reused conclusion.
        write_workbook(self.workbook, [
            original_row(amount=1100),
            percent_adjustment("ADJ-1", factor_id="DISCOUNT-20", basis_from="original_amount", rate=0.2, source="合同第3.2条", nature="价格折让"),
            percent_adjustment("ADJ-2", factor_id="RETENTION-10", basis_from="original_amount", rate=0.1, source="合同第8.1条", nature="质保金"),
        ])
        changed, changed_path = self.invoke_export(signoff=reused_path, output=self.root / "changed.json")
        self.assertEqual(changed.returncode, 0, changed.stdout + changed.stderr)
        changed_amount = json.loads(changed_path.read_text(encoding="utf-8"))["amount_review"]
        self.assertEqual(changed_amount["status"], "unable-to-verify")
        self.assertIs(changed_amount["artifact_amounts_reconciled"], False)
        self.assertNotIn("reviewer", changed_amount)
        self.assertIn("affected amount review is required", changed_amount["review_note"])

    def test_pending_fixed_and_percentage_values_export_as_gaps_not_zero(self) -> None:
        cases = (
            ("J", {"A": "ADJ-J", "B": "补充协议第2条", "C": "固定折让", "E": "CNY", "J": "待核", "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FIX-PENDING", "Q": "original_amount", "R": "fixed"}),
            ("S", {"A": "ADJ-S", "B": "合同第3.2条", "C": "比例调整", "E": "CNY", "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "RATE-PENDING", "Q": "original_amount", "R": "percentage", "S": "待核"}),
        )
        for field, adjustment in cases:
            with self.subTest(field=field):
                write_workbook(self.workbook, [original_row(), adjustment])
                self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
                result, output = self.invoke_export()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(json.loads(result.stdout)["decision"], "DRAFT_ONLY")
                amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
                self.assertEqual(amount["status"], "unable-to-verify")
                step = amount["chains"][0]["adjustments"][0]
                self.assertIsNone(step["deduction_amount"])
                self.assertIsNone(step["resulting_amount"])
                self.assertIsNone(amount["chains"][0]["reported_totals"]["adjustments_total"])
                self.assertIsNone(amount["chains"][0]["reported_totals"]["adjusted_gross"])
                self.assertIn("factor value is missing", amount["review_note"])

    def test_pending_prior_step_is_known_but_cannot_supply_a_numeric_basis(self) -> None:
        pending_fixed = {"A": "ADJ-1", "B": "补充协议第2条", "C": "固定折让", "E": "CNY", "J": "待核", "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FIX-PENDING", "Q": "original_amount", "R": "fixed"}
        next_step = percent_adjustment("ADJ-2", factor_id="RATE-2", basis_from="ADJ-1", rate=0.1, source="合同第4条", nature="后续扣减")
        write_workbook(self.workbook, [original_row(), pending_fixed, next_step])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        self.assertEqual(amount["status"], "unable-to-verify")
        first, second = amount["chains"][0]["adjustments"]
        self.assertEqual(second["basis_from"], "ADJ-1")
        self.assertIsNone(second["basis_amount"])
        self.assertIsNone(second["deduction_amount"])
        self.assertIsNone(amount["chains"][0]["reported_totals"]["adjusted_gross"])
        self.assertIn("calculation basis is unavailable", amount["review_note"])

    def test_malformed_numeric_text_still_blocks_instead_of_becoming_a_gap(self) -> None:
        cases = (
            {"A": "ADJ-J", "B": "补充协议第2条", "C": "固定折让", "E": "CNY", "J": "abc", "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FIX-BAD", "Q": "original_amount", "R": "fixed"},
            {"A": "ADJ-S", "B": "合同第3.2条", "C": "比例调整", "E": "CNY", "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "RATE-BAD", "Q": "original_amount", "R": "percentage", "S": "abc"},
        )
        for row in cases:
            with self.subTest(record=row["A"]):
                write_workbook(self.workbook, [original_row(), row])
                self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
                result, _ = self.invoke_export()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("is not numeric: abc", result.stdout)

    def test_exporter_still_blocks_self_and_forward_basis_references(self) -> None:
        rows = (
            [{"A": "ADJ-1", "B": "合同第2条", "C": "固定扣减", "E": "CNY", "J": 10, "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FACTOR-1", "Q": "ADJ-1", "R": "fixed"}],
            [
                {"A": "ADJ-1", "B": "合同第2条", "C": "固定扣减", "E": "CNY", "J": 10, "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FACTOR-1", "Q": "ADJ-2", "R": "fixed"},
                {"A": "ADJ-2", "B": "合同第3条", "C": "固定扣减", "E": "CNY", "J": 5, "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FACTOR-2", "Q": "original_amount", "R": "fixed"},
            ],
        )
        for index, adjustments in enumerate(rows, start=1):
            with self.subTest(case=index):
                write_workbook(self.workbook, [original_row(), *adjustments])
                self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
                result, _ = self.invoke_export()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("basis_from must reference original_amount or an earlier adjustment record_id", result.stdout)

    def test_column_k_payment_is_not_dropped_or_treated_as_proven_by_original_locator(self) -> None:
        write_workbook(self.workbook, [original_row(paid=50)])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        chain = amount["chains"][0]
        self.assertEqual(len(chain["payments"]), 1)
        self.assertEqual(chain["payments"][0]["amount"], 50)
        self.assertEqual(chain["payments"][0]["source_ref"], "")
        self.assertEqual(chain["payments"][0]["evidence_status"], "missing")
        self.assertIsNone(chain["reported_totals"]["paid_total"])
        self.assertIn("payment source and confirmation", amount["review_note"])

    def test_pending_original_k_payment_exports_null_and_unverified_totals(self) -> None:
        write_workbook(self.workbook, [original_row(paid="待核")])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["decision"], "DRAFT_ONLY")
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        chain = amount["chains"][0]
        self.assertEqual(amount["status"], "unable-to-verify")
        self.assertEqual(len(chain["payments"]), 1)
        self.assertIsNone(chain["payments"][0]["amount"])
        self.assertIsNone(chain["reported_totals"]["paid_total"])
        self.assertIsNone(chain["reported_totals"]["net_total"])
        self.assertIn("column K payment is marked 待核", amount["review_note"])

    def test_blank_original_k_is_unknown_and_invalidates_reused_zero_payment_review(self) -> None:
        rows = [
            original_row(),
            percent_adjustment("ADJ-1", factor_id="DISCOUNT-30", basis_from="original_amount", rate=0.3, source="合同第3.2条", nature="价格折让"),
        ]
        write_workbook(self.workbook, rows)
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        first, prior_path = self.invoke_export(output=self.root / "explicit-zero-prior.json")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        amount = prior["amount_review"]
        self.assertEqual(amount["chains"][0]["reported_totals"]["paid_total"], 0)
        self.assertEqual(amount["chains"][0]["reported_totals"]["net_total"], 700)
        amount.update({
            "status": "verified", "artifact_amounts_reconciled": True,
            "reviewer": "金额复核人", "reviewed_at": "2026-10-13T10:00:00+08:00",
            "conclusion_review": "已核原件并确认原始账本K列明确记录0，未发生付款。",
        })
        prior_path.write_text(json.dumps(prior, ensure_ascii=False), encoding="utf-8")

        write_workbook(self.workbook, [original_row(paid=None), rows[1]])
        result, output = self.invoke_export(signoff=prior_path, output=self.root / "blank-k-review.json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(json.loads(result.stdout)["human_amount_review_reused"])
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        chain = amount["chains"][0]
        self.assertEqual(amount["status"], "unable-to-verify")
        self.assertIs(amount["artifact_amounts_reconciled"], False)
        self.assertNotIn("reviewer", amount)
        self.assertEqual(len(chain["payments"]), 1)
        self.assertIsNone(chain["payments"][0]["amount"])
        self.assertIsNone(chain["reported_totals"]["paid_total"])
        self.assertIsNone(chain["reported_totals"]["net_total"])
        self.assertIn("column K is blank", amount["review_note"])

    def test_blank_original_k_uses_dedicated_payment_rows_without_duplicate_unknown(self) -> None:
        write_workbook(self.workbook, [
            original_row(paid=None),
            {"A": "ADJ-1", "B": "补充协议第2条", "C": "固定折让", "E": "CNY", "J": 300, "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FIX-1", "Q": "original_amount", "R": "fixed"},
            {"A": "PAY-1", "B": "银行回单#1", "C": "已付款", "E": "CNY", "K": 50, "L": "已核", "N": "CHAIN-1", "O": "payment", "P": "PAYMENT-1"},
        ])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(output.read_text(encoding="utf-8"))
        amount = data["amount_review"]
        chain = amount["chains"][0]
        self.assertNotIn("column K is blank", amount.get("review_note", ""))
        self.assertEqual(len(chain["payments"]), 1)
        self.assertEqual(chain["payments"][0]["record_id"], "PAY-1")
        self.assertEqual(chain["reported_totals"]["paid_total"], 50)
        self.assertEqual(chain["reported_totals"]["net_total"], 650)

    def test_missing_source_is_never_promoted_to_verified(self) -> None:
        write_workbook(self.workbook, [original_row(source="")])
        base = self.base_signoff()
        base["amount_review"] = {
            "schema_version": "1.0", "artifact_sha256": sha256(self.artifact), "scope": "old",
            "status": "verified", "artifact_amounts_reconciled": True,
            "reviewer": "金额复核人", "reviewed_at": "2026-10-13T10:00:00+08:00",
            "conclusion_review": "旧确认", "chains": [],
        }
        self.signoff.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        self.assertEqual(amount["status"], "unable-to-verify")
        self.assertIs(amount["artifact_amounts_reconciled"], False)
        self.assertEqual(amount["chains"][0]["original_amount"]["evidence_status"], "missing")

    def test_nonzero_raw_j_or_k_without_chain_type_is_visible_as_unverified_gap(self) -> None:
        write_workbook(self.workbook, [
            original_row(),
            {"A": "RAW-ORPHAN", "B": "待核单据", "C": "杂项金额", "E": "CNY", "J": 33, "K": 7, "L": "待核"},
        ])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        self.assertEqual(amount["status"], "unable-to-verify")
        self.assertIn("RAW-ORPHAN", amount["review_note"])

    def test_blank_initial_factor_inventory_does_not_claim_verified_chain(self) -> None:
        row = original_row()
        row.pop("T")
        write_workbook(self.workbook, [row])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        self.assertEqual(amount["status"], "unable-to-verify")
        self.assertIn("initially included factor inventory", amount["review_note"])

    def test_fixed_percent_payment_and_offset_reuse_single_ledger_values(self) -> None:
        write_workbook(self.workbook, [
            original_row(amount=1000),
            {"A": "ADJ-FIX", "B": "补充协议第2条", "C": "固定折让", "E": "CNY", "J": 100, "L": "已核", "N": "CHAIN-1", "O": "adjustment", "P": "FIX-A", "Q": "original_amount", "R": "fixed"},
            percent_adjustment("ADJ-PCT", factor_id="RATE-B", basis_from="ADJ-FIX", rate=0.2, source="订单第4条", nature="二次折让"),
            {"A": "PAY-1", "B": "银行回单#1", "C": "已付款", "E": "CNY", "K": 50, "L": "已核", "N": "CHAIN-1", "O": "payment", "P": "PAYMENT-1"},
            {"A": "OFF-1", "B": "对账单#2", "C": "已确认抵扣", "E": "CNY", "J": 20, "L": "已核", "N": "CHAIN-1", "O": "offset", "P": "OFFSET-1"},
        ])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        chain = json.loads(output.read_text(encoding="utf-8"))["amount_review"]["chains"][0]
        self.assertEqual([item["kind"] for item in chain["adjustments"]], ["fixed", "percentage"])
        self.assertEqual([item["basis_from"] for item in chain["adjustments"]], ["original_amount", "ADJ-FIX"])
        self.assertEqual([item["deduction_amount"] for item in chain["adjustments"]], [100, 180])
        self.assertEqual(chain["payments"][0]["amount"], 50)
        self.assertEqual(chain["offsets"][0]["amount"], 20)
        self.assertEqual(chain["reported_totals"]["net_total"], 650)

    def test_original_k_payment_can_reuse_existing_value_with_separate_proof_fields(self) -> None:
        write_workbook(self.workbook, [original_row(paid=50, payment_source="银行回单1", payment_status="已核")])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        result, output = self.invoke_export()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        amount = json.loads(output.read_text(encoding="utf-8"))["amount_review"]
        self.assertEqual(amount["chains"][0]["payments"][0]["source_ref"], "银行回单1")
        self.assertEqual(amount["chains"][0]["reported_totals"]["paid_total"], 50)

    def test_reapplying_twenty_percent_factor_remains_a_gate_error(self) -> None:
        write_workbook(self.workbook, [
            original_row(),
            percent_adjustment("ADJ-1", factor_id="DISCOUNT-20", basis_from="original_amount", rate=0.2, source="合同第3.2条", nature="价格折让"),
            percent_adjustment("ADJ-2", factor_id="DISCOUNT-20", basis_from="ADJ-1", rate=0.2, source="合同第3.2条", nature="价格折让"),
        ])
        self.signoff.write_text(json.dumps(self.base_signoff("internal-draft", "R1"), ensure_ascii=False), encoding="utf-8")
        generated, amount_path = self.invoke_export()
        self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
        manifest = self.root / "matter.json"
        source = self.root / "source.txt"
        source.write_text("source", encoding="utf-8")
        manifest.write_text(json.dumps({
            "schema_version": "1.0", "matter_task_id": "MATTER-001", "owner": "使用者",
            "classification": "S2", "matter_root": str(self.root), "public_export_allowed": False,
            "retention_status": "active", "source_files": [{"path": source.name, "sha256": sha256(source), "role": "original"}],
        }, ensure_ascii=False), encoding="utf-8")
        report = self.root / "gate.json"
        result = subprocess.run([
            sys.executable, str(GATE), "--artifact", str(self.artifact), "--output-path", str(self.root / "delivery.txt"),
            "--intent", "internal-draft", "--risk-level", "R1", "--matter-manifest", str(manifest),
            "--signoff", str(amount_path), "--out-json", str(report),
        ], capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        release = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(release["decision"], "BLOCKED")
        self.assertTrue(any("reapplies an adjustment factor" in error for error in release["errors"]))

    def test_exporter_refuses_to_overwrite_any_input(self) -> None:
        write_workbook(self.workbook, [original_row()])
        self.signoff.write_text(json.dumps(self.base_signoff(), ensure_ascii=False), encoding="utf-8")
        inputs = ((self.workbook, "workbook"), (self.artifact, "artifact"), (self.signoff, "signoff"))
        for input_path, label in inputs:
            with self.subTest(input=label, alias=False):
                before = {path: sha256(path) for path, _ in inputs}
                result, _ = self.invoke_export(output=input_path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"must not overwrite the input {label}", result.stdout)
                self.assertEqual(before, {path: sha256(path) for path in before})

        for input_path, label in inputs:
            with self.subTest(input=label, alias=True):
                alias = self.root / f"{label}-alias.json"
                alias.symlink_to(input_path)
                before = {path: sha256(path) for path, _ in inputs}
                result, _ = self.invoke_export(output=alias)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"must not overwrite the input {label}", result.stdout)
                self.assertEqual(before, {path: sha256(path) for path in before})
                alias.unlink()


if __name__ == "__main__":
    unittest.main()
