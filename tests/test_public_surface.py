from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_public_surface import validate_public_surface


class PublicSurfaceTests(unittest.TestCase):
    def test_current_public_surface_is_consistent(self):
        self.assertEqual(validate_public_surface(ROOT), [])

    def test_candidate_manifest_matches_public_inventory(self):
        import json

        candidate = json.loads((ROOT / "PUBLIC_CANDIDATE_MANIFEST.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(candidate["status"], "candidate")
        self.assertFalse(candidate["released"])
        self.assertEqual(candidate["inventory"]["skills"], len(manifest["skills"]))
        self.assertEqual(candidate["inventory"]["routes"], len(manifest["routes"]))
        self.assertEqual(candidate["current_law_route"]["default_skill"], "cn-legal-research")


if __name__ == "__main__":
    unittest.main()
