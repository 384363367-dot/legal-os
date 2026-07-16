from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_manifest import validate_manifest


class ManifestValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))

    def test_current_manifest_is_consistent(self) -> None:
        self.assertEqual(validate_manifest(ROOT), [])

    def test_missing_route_is_reported(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["routes"] = manifest["routes"][:-1]

        errors = validate_manifest(ROOT, manifest)

        self.assertTrue(any("T-01 through T-12" in error for error in errors), errors)

    def test_private_profile_cannot_be_distributed(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        next(profile for profile in manifest["profiles"] if profile["id"] == "private-controlled")["distributed"] = True

        errors = validate_manifest(ROOT, manifest)

        self.assertTrue(any("undistributed overlay" in error for error in errors), errors)

    def test_invocation_policy_must_match_agent_metadata(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["invocation_policy"]["legal-os-contract"]["allow_implicit_invocation"] = False

        errors = validate_manifest(ROOT, manifest)

        self.assertTrue(any("implicit invocation contradicts" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
