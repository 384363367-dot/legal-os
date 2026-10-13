from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GateMirrorConsistencyTests(unittest.TestCase):
    def test_contract_and_quality_gate_machine_contracts_are_byte_identical(self) -> None:
        pairs = (
            ("skills/legal-quality-gate/scripts/release_gate.py", "skills/legal-os-contract/scripts/release_gate.py"),
            ("skills/legal-quality-gate/scripts/rebind_signoff.py", "skills/legal-os-contract/scripts/rebind_signoff.py"),
            ("skills/legal-quality-gate/references/schemas/review-signoff.schema.json", "skills/legal-os-contract/references/schemas/review-signoff.schema.json"),
        )
        for left, right in pairs:
            with self.subTest(pair=(left, right)):
                self.assertEqual((ROOT / left).read_bytes(), (ROOT / right).read_bytes())

    def test_registered_amount_workbook_hash_matches_catalog(self) -> None:
        catalog = json.loads((ROOT / "skills/legal-os-template-runtime/references/template-catalog.json").read_text(encoding="utf-8"))
        entry = next(item for item in catalog["templates"] if item["id"] == "DATA-AMOUNT-NODE-WORKBOOK-V1.7")
        workbook = ROOT / "skills/legal-os-data-verification" / entry["relative_path"]
        self.assertEqual(hashlib.sha256(workbook.read_bytes()).hexdigest(), entry["sha256"])


if __name__ == "__main__":
    unittest.main()
