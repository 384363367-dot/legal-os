from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.validate_release_pair import validate_release_pair


class ReleasePairTests(unittest.TestCase):
    def setUp(self):
        self.public = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))
        self.private = {
            "release": {"release_id": "legalos-v0.8.6", "version": "0.8.6"},
            "profile": {"profile_id": "private-controlled"},
            "inventory": {"files": ["PRIVATE_SENTINEL_PATH"]},
            "tree_sha256": "PRIVATE_SENTINEL_HASH",
            "payload": "PRIVATE_SENTINEL_CONTENT",
        }

    def test_matching_identity_and_expected_profiles_pass(self):
        self.assertEqual(validate_release_pair(self.public, self.private), [])

    def test_release_id_and_version_mismatch_fail_without_values(self):
        self.private["release"] = {"release_id": "legalos-v9.9.9", "version": "9.9.9"}
        errors = validate_release_pair(self.public, self.private)
        rendered = " ".join(errors)
        self.assertIn("do not match", rendered)
        self.assertNotIn("legalos-v9.9.9", rendered)
        self.assertNotIn("9.9.9", rendered)

    def test_private_profile_id_must_be_private_controlled(self):
        self.private["profile"]["profile_id"] = "private-profile-secret"
        errors = validate_release_pair(self.public, self.private)
        rendered = " ".join(errors)
        self.assertIn("private profile id is not private-controlled", rendered)
        self.assertNotIn("private-profile-secret", rendered)

    def test_cli_does_not_print_or_copy_private_payload_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            private_manifest = Path(temp_dir) / "manifest.json"
            private_manifest.write_text(json.dumps(self.private), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/validate_release_pair.py"),
                    "--private-manifest",
                    str(private_manifest),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Release pair validation: PASS", result.stdout)
        for private_value in (
            "PRIVATE_SENTINEL_PATH",
            "PRIVATE_SENTINEL_HASH",
            "PRIVATE_SENTINEL_CONTENT",
        ):
            self.assertNotIn(private_value, result.stdout + result.stderr)
        self.assertNotIn(".backup", result.stdout + result.stderr)

    def test_unreadable_private_manifest_returns_generic_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing-private-manifest.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/validate_release_pair.py"),
                    "--private-manifest",
                    str(missing_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("private manifest could not be read", result.stdout)
        self.assertNotIn(str(missing_path), result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
