from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "install.sh"


class InstallerTests(unittest.TestCase):
    def test_dry_run_lists_all_skills_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "missing-parent" / ".." / "skills"
            result = subprocess.run(
                [str(INSTALL), "--dry-run", "--target", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("15 Skill(s) validated", result.stdout)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(temp_dir).iterdir()), [])

    def test_clean_install_copies_complete_skill_suite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            physical_parent = base / "physical-parent"
            physical_parent.mkdir()
            alias_parent = base / "alias-parent"
            alias_parent.symlink_to(physical_parent, target_is_directory=True)
            target = alias_parent / "missing-parent" / ".." / "skills"
            canonical_target = physical_parent / "skills"
            result = subprocess.run(
                [str(INSTALL), "--target", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = [path for path in canonical_target.iterdir() if path.is_dir()]
            self.assertEqual(len(installed), 15)
            for skill in (ROOT / "skills").iterdir():
                if skill.is_dir():
                    self.assertEqual((canonical_target / skill.name / "SKILL.md").read_bytes(), (skill / "SKILL.md").read_bytes())
            self.assertEqual(list(physical_parent.glob(".legal-os-stage.*")), [])

    def test_root_aliases_are_rejected_before_dry_run_or_writes(self):
        aliases = ("/../", "/tmp/..", "/tmp/legalos-missing/../../..")
        skill_names = [path.name for path in (ROOT / "skills").iterdir() if path.is_dir()]
        root = Path("/")
        before = {name: (root / name).exists() for name in skill_names}

        for target in aliases:
            for extra_args in (("--dry-run",), ()):
                result = subprocess.run(
                    [str(INSTALL), *extra_args, "--target", target],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
                self.assertIn("unsafe --target path", result.stderr)

        self.assertEqual({name: (root / name).exists() for name in skill_names}, before)

    def test_protected_temporary_root_is_rejected(self):
        for extra_args in (("--dry-run",), ()):
            result = subprocess.run(
                [str(INSTALL), *extra_args, "--target", "/tmp"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            self.assertTrue(
                "unsafe --target path" in result.stderr or "symlink target" in result.stderr,
                result.stderr,
            )

    def test_replace_preserves_prior_skill_as_rollback_material(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "skills"
            (target / "cn-case-hub").mkdir(parents=True)
            (target / "cn-case-hub" / "old.txt").write_text("old", encoding="utf-8")
            result = subprocess.run(
                [str(INSTALL), "--replace", "--target", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            backups = list((target / ".backup").iterdir())
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "cn-case-hub" / "old.txt").read_text(encoding="utf-8"), "old")
            self.assertTrue((target / "cn-case-hub" / "SKILL.md").is_file())
            self.assertEqual(list(Path(temp_dir).glob(".legal-os-stage.*")), [])

    def test_mid_suite_failure_rolls_back_every_replaced_and_new_skill(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            target = base / "skills"
            bin_dir = base / "bin"
            bin_dir.mkdir()
            (target / "cn-case-hub").mkdir(parents=True)
            (target / "cn-case-hub" / "old.txt").write_text("old-case", encoding="utf-8")
            (target / "cn-legal-research").mkdir()
            (target / "cn-legal-research" / "old.txt").write_text("old-research", encoding="utf-8")

            mv_wrapper = bin_dir / "mv"
            mv_wrapper.write_text(
                "#!/bin/sh\n"
                "case \"$1\" in\n"
                "  */.legal-os-stage.*/skills/cn-legal-research) exit 97 ;;\n"
                "esac\n"
                "exec /bin/mv \"$@\"\n",
                encoding="utf-8",
            )
            mv_wrapper.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")

            result = subprocess.run(
                [str(INSTALL), "--replace", "--target", str(target)],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("ROLLBACK: complete", result.stderr)
            self.assertEqual((target / "cn-case-hub" / "old.txt").read_text(encoding="utf-8"), "old-case")
            self.assertEqual((target / "cn-legal-research" / "old.txt").read_text(encoding="utf-8"), "old-research")
            self.assertFalse((target / "cn-case-hub" / "SKILL.md").exists())
            self.assertFalse((target / "cn-law-hub").exists())
            self.assertFalse((target / ".backup").exists())
            self.assertEqual(list(base.glob(".legal-os-stage.*")), [])

    def test_existing_target_requires_replace_before_mutation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "skills"
            (target / "cn-case-hub").mkdir(parents=True)
            marker = target / "cn-case-hub" / "old.txt"
            marker.write_text("old", encoding="utf-8")
            result = subprocess.run(
                [str(INSTALL), "--target", str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 5)
            self.assertEqual(marker.read_text(encoding="utf-8"), "old")
            self.assertEqual(list(Path(temp_dir).iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
