from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_routing_scenarios import validate_scenarios


class UnifiedIntakeRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))
        cls.scenarios = json.loads(
            (ROOT / "tests" / "fixtures" / "unified_intake_scenarios.json").read_text(encoding="utf-8")
        )

    def test_fifteen_synthetic_scenarios_pass(self) -> None:
        self.assertEqual(len(self.scenarios), 15)
        self.assertEqual(validate_scenarios(self.manifest, self.scenarios), [])

    def test_g3_without_stop_is_rejected(self) -> None:
        scenarios = copy.deepcopy(self.scenarios)
        scenarios[-1]["expected_decision"]["status"] = "ready"

        errors = validate_scenarios(self.manifest, [scenarios[-1]])

        self.assertTrue(any("G3" in error for error in errors), errors)

    def test_external_action_without_authorization_gate_is_rejected(self) -> None:
        scenario = copy.deepcopy(next(item for item in self.scenarios if item["id"] == "formal-letter-send-request"))
        scenario["expected_decision"]["status"] = "ready"

        errors = validate_scenarios(self.manifest, [scenario])

        self.assertTrue(any("external actions require" in error for error in errors), errors)

    def test_mixed_task_must_cover_every_requested_type(self) -> None:
        scenario = copy.deepcopy(next(item for item in self.scenarios if item["id"] == "contract-with-data-check"))
        scenario["expected_decision"]["auxiliary_routes"] = []

        errors = validate_scenarios(self.manifest, [scenario])

        self.assertTrue(any("not covered" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
