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

    def test_release_manifest_records_public_profile_without_candidate_package(self):
        import json

        manifest = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))
        from scripts.profile_inventory import profile_payload

        self.assertEqual(manifest["release"], {"release_id": "legalos-v0.8.6", "version": "0.8.6"})
        self.assertEqual(manifest["product"]["public_version"], manifest["release"]["version"])
        self.assertEqual(manifest["profile"]["profile_id"], "public-generic")
        self.assertEqual(manifest["profile"]["payload"], profile_payload(ROOT / "skills"))
        self.assertFalse((ROOT / "PUBLIC_CANDIDATE_MANIFEST.json").exists())

        skills = {item["name"]: item for item in manifest["skills"]}
        self.assertEqual(skills["legal-os-contract"]["maturity"], "stable")
        self.assertEqual(skills["legal-os-unified-intake"]["maturity"], "candidate")
        self.assertEqual(skills["cn-law-hub"]["status"], "compatibility")
        self.assertEqual(skills["cn-law-hub"]["maturity"], "candidate")


if __name__ == "__main__":
    unittest.main()
