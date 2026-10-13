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

REPO = Path(__file__).resolve().parents[3]
REBINER = REPO / "skills/legal-quality-gate/scripts/rebind_signoff.py"
GATE = REPO / "skills/legal-quality-gate/scripts/release_gate.py"
REDLINE_GATE = REPO / "skills/legal-os-contract/scripts/redline_quality_gate.py"
CONTRACT_TESTS = REPO / "skills/legal-os-contract/tests"
sys.path.insert(0, str(CONTRACT_TESTS))
from test_contract_redline_quality_gate import deletion, insertion, paragraph, run, write_docx  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SignoffRebindTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = self.root / "old.docx"
        self.new = self.root / "new.docx"
        self.signoff = self.root / "signoff.json"
        write_docx(self.old, [paragraph(run("This is a small typo teh in the text."))])
        self.write_signoff()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_signoff(self, *, artifact: Path | None = None, artifact_hash: str | None = None) -> dict:
        artifact = artifact or self.old
        data = {
            "schema_version": "1.0", "matter_task_id": "MATTER-001",
            "artifact_path": str(artifact.resolve()), "artifact_sha256": artifact_hash or sha256(artifact),
            "risk_level": "R2", "reviewer": "审阅人", "reviewed_at": "2026-10-13T10:00:00+08:00",
            "status": "approved", "permitted_use": "internal-final",
            "checks": {key: True for key in ("facts", "authority", "strategy", "format", "privacy")},
            "contract_protection_review": {"artifact_sha256": artifact_hash or sha256(artifact)},
        }
        self.signoff.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def invoke(self, *, scope: str | None = None, semantic: str | None = None, reviewed_by: str | None = None, reviewed_at: str | None = None, signoff: Path | None = None, output: Path | None = None):
        output = output or self.root / "candidate.json"
        command = [sys.executable, str(REBINER), "--signoff", str(signoff or self.signoff), "--old-artifact", str(self.old), "--new-artifact", str(self.new), "--out-signoff", str(output)]
        for key, value in (("--scope", scope), ("--semantic-review", semantic), ("--reviewed-by", reviewed_by), ("--reviewed-at", reviewed_at)):
            if value is not None:
                command.extend([key, value])
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result, output

    def add_bold_visual_format_only(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo teh in the text."))])
        with zipfile.ZipFile(self.new, "r") as source:
            parts = {info.filename: (info, source.read(info.filename)) for info in source.infolist()}
        document = parts["word/document.xml"][1].decode("utf-8")
        document = document.replace("<w:r><w:t>", "<w:r><w:rPr><w:b/></w:rPr><w:t>", 1)
        parts["word/document.xml"] = (parts["word/document.xml"][0], document.encode("utf-8"))
        temp = self.new.with_suffix(".tmp.docx")
        with zipfile.ZipFile(temp, "w") as target:
            for name, (info, content) in parts.items():
                target.writestr(info, content)
        temp.replace(self.new)

    def test_strict_format_only_rebind_reuses_approval_and_passes_release_gate(self) -> None:
        self.add_bold_visual_format_only()
        result, candidate_path = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.assertEqual(candidate["status"], "approved")
        self.assertEqual(candidate["rebind_record"]["classification"], "format-only")
        self.assertFalse(candidate["rebind_record"]["requires_affected_review"])
        self.assertEqual(candidate["artifact_sha256"], sha256(self.new))
        self.assertEqual(candidate["contract_protection_review"]["artifact_sha256"], sha256(self.new))
        self.assertIn("direct w:b/w:bCs/w:i/w:iCs and w:jc", candidate["rebind_record"]["diff_summary"])
        self.assertTrue(candidate["rebind_record"]["visual_property_changes"])

        manifest_source = self.root / "source.txt"
        manifest_source.write_text("source facts", encoding="utf-8")
        manifest = self.root / "matter.json"
        manifest.write_text(json.dumps({
            "schema_version": "1.0", "matter_task_id": "MATTER-001", "owner": "使用者",
            "classification": "S2", "matter_root": str(self.root), "public_export_allowed": False,
            "retention_status": "active", "source_files": [{"path": manifest_source.name, "sha256": sha256(manifest_source), "role": "original"}],
        }, ensure_ascii=False), encoding="utf-8")
        output = self.root / "delivery.docx"
        release_report = self.root / "release.json"
        released = subprocess.run([
            sys.executable, str(GATE), "--artifact", str(self.new), "--output-path", str(output),
            "--intent", "internal-final", "--risk-level", "R2", "--matter-manifest", str(manifest),
            "--signoff", str(candidate_path), "--out-json", str(release_report),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(released.returncode, 0, released.stdout + released.stderr)
        self.assertEqual(json.loads(release_report.read_text(encoding="utf-8"))["decision"], "RELEASE")

    def test_light_signoff_may_inherit_omitted_nested_hash_through_rebind(self) -> None:
        original = self.root / "original.docx"
        write_docx(original, [paragraph(run("A typo teh exists."))])
        write_docx(self.old, [paragraph(run("A typo ") + deletion("teh") + insertion("the") + run(" exists."))], track=True)
        shutil.copyfile(self.old, self.new)

        self.write_signoff()
        signoff = self.signoff
        old_data = json.loads(signoff.read_text(encoding="utf-8"))
        old_data["artifact_path"] = str(self.old.resolve())
        old_data["artifact_sha256"] = sha256(self.old)
        old_data["risk_level"] = "R1"
        old_data["contract_protection_review"] = {
            "review_path": "light",
            "review_scope": "仅核对原件与一处拼写红线。",
            "core_risks_status": "none",
            "no_core_risks_rationale": "审阅人确认未改变句义、法律效果、适用范围或核心风险。",
        }
        signoff.write_text(json.dumps(old_data, ensure_ascii=False), encoding="utf-8")

        result, rebound_path = self.invoke(signoff=signoff)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rebound = json.loads(rebound_path.read_text(encoding="utf-8"))
        self.assertEqual(rebound["status"], "approved")
        self.assertNotIn("artifact_sha256", rebound["contract_protection_review"])
        self.assertEqual(rebound["artifact_sha256"], sha256(self.new))

        manifest_source = self.root / "matter.json"
        manifest_source.write_text(json.dumps({
            "schema_version": "1.0", "matter_task_id": "MATTER-001", "owner": "使用者",
            "classification": "S2", "matter_root": str(self.root), "public_export_allowed": False,
            "retention_status": "active", "source_files": [
                {"path": original.name, "sha256": sha256(original), "role": "original"},
            ],
        }, ensure_ascii=False), encoding="utf-8")
        redline_report = self.root / "redline.json"
        redline = subprocess.run([
            sys.executable, str(REDLINE_GATE), "--original", str(original), "--redline", str(self.new),
            "--out-json", str(redline_report),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(redline.returncode, 0, redline.stdout + redline.stderr)
        release_report = self.root / "release.json"
        released = subprocess.run([
            sys.executable, str(GATE), "--artifact", str(self.new), "--output-path", str(self.root / "delivery.docx"),
            "--intent", "internal-final", "--risk-level", "R1", "--matter-manifest", str(manifest_source),
            "--signoff", str(rebound_path), "--redline-report", str(redline_report), "--contract", "--out-json", str(release_report),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(released.returncode, 0, released.stdout + released.stderr)
        self.assertEqual(json.loads(release_report.read_text(encoding="utf-8"))["decision"], "RELEASE")

    def test_explicit_stale_light_nested_hash_is_not_inherited(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo teh in the text."))])
        data = self.write_signoff()
        data["contract_protection_review"] = {
            "review_path": "light", "artifact_sha256": "0" * 64,
        }
        self.signoff.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result, candidate_path = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("old contract_protection_review is stale", result.stdout)
        self.assertFalse(candidate_path.exists())

    def test_real_tracked_typo_creates_pending_candidate_and_preserves_nested_stale_hash(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo t") + deletion("eh") + insertion("he") + run(" in the text."))], track=True)
        result, candidate_path = self.invoke(
            scope="拼写更正，不改变定义、权利义务或保护范围。",
            semantic="已逐字比较原文与红线；仅更正拼写，不改变法律含义或核心风险。",
            reviewed_by="合同主审",
            reviewed_at="2026-10-13T11:00:00+08:00",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.assertEqual(candidate["status"], "pending")
        self.assertEqual(candidate["rebind_candidate"]["classification"], "content-change")
        self.assertTrue(candidate["rebind_candidate"]["requires_affected_review"])
        self.assertEqual(candidate["rebind_candidate"]["redline_gate_status"], "PASS")
        self.assertIn('"kind": "delete"', candidate["rebind_candidate"]["diff_summary"])
        self.assertEqual(candidate["contract_protection_review"]["artifact_sha256"], sha256(self.old))

    def test_old_signoff_hash_mismatch_is_blocked(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo teh in the text."))])
        self.write_signoff(artifact_hash="0" * 64)
        result, candidate_path = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("old signoff hash", result.stdout)
        self.assertFalse(candidate_path.exists())

    def test_relationship_change_is_never_auto_classified_as_format_only(self) -> None:
        rels_old = '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
        rels_new = '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.invalid" TargetMode="External"/></Relationships>'
        write_docx(self.old, [paragraph(run("Same visible text."))], extra_parts={"word/_rels/document.xml.rels": rels_old})
        self.write_signoff()
        write_docx(self.new, [paragraph(run("Same visible text."))], extra_parts={"word/_rels/document.xml.rels": rels_new})
        result, candidate_path = self.invoke(
            scope="检查新增超链接关系的目标及其法律含义。",
            semantic="新增关系可能影响内容来源，待人工核验，未批准交付。",
            reviewed_by="复核人",
            reviewed_at="2026-10-13T11:00:00+08:00",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        self.assertEqual(candidate["rebind_candidate"]["classification"], "manual-review-required")
        self.assertTrue(candidate["rebind_candidate"]["requires_affected_review"])
        self.assertEqual(candidate["rebind_candidate"]["redline_gate_status"], "FAIL")
        self.assertTrue(any("word/_rels/document.xml.rels" == item["part"] for item in candidate["rebind_candidate"]["changed_parts"]))

    def test_candidate_cannot_pass_release_gate_and_output_cannot_overwrite_input(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo t") + deletion("eh") + insertion("he") + run(" in the text."))], track=True)
        before = {path: sha256(path) for path in (self.old, self.new, self.signoff)}
        result, _ = self.invoke(output=self.old)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(before, {path: sha256(path) for path in before})

        result, candidate_path = self.invoke(
            scope="只核对一处拼写，不改变实体权利义务。",
            semantic="人工对照原件、实际红线和拒绝视图，确认语义、范围及法律影响均未改变。",
            reviewed_by="合同主审",
            reviewed_at="2026-10-13T11:00:00+08:00",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest_source = self.root / "source.txt"
        manifest_source.write_text("source facts", encoding="utf-8")
        manifest = self.root / "matter.json"
        manifest.write_text(json.dumps({
            "schema_version": "1.0", "matter_task_id": "MATTER-001", "owner": "使用者",
            "classification": "S2", "matter_root": str(self.root), "public_export_allowed": False,
            "retention_status": "active", "source_files": [{"path": manifest_source.name, "sha256": sha256(manifest_source), "role": "original"}],
        }, ensure_ascii=False), encoding="utf-8")
        output = self.root / "delivery.docx"
        release_report = self.root / "release.json"
        blocked = subprocess.run([
            sys.executable, str(GATE), "--artifact", str(self.new), "--output-path", str(output),
            "--intent", "internal-final", "--risk-level", "R2", "--matter-manifest", str(manifest),
            "--signoff", str(candidate_path), "--out-json", str(release_report),
        ], capture_output=True, text=True, check=False)
        self.assertNotEqual(blocked.returncode, 0)
        report = json.loads(release_report.read_text(encoding="utf-8"))
        self.assertTrue(any("rebind candidate is not releasable" in item for item in report["errors"]))

    def test_strike_color_and_font_size_changes_are_not_auto_approved(self) -> None:
        for prop in ("<w:strike/>", '<w:color w:val="FF0000"/>', '<w:sz w:val="4"/>'):
            with self.subTest(prop=prop):
                write_docx(self.new, [paragraph(run("This is a small typo teh in the text."))])
                with zipfile.ZipFile(self.new, "r") as source:
                    parts = {info.filename: (info, source.read(info.filename)) for info in source.infolist()}
                document = parts["word/document.xml"][1].decode("utf-8")
                document = document.replace("<w:r><w:t>", f"<w:r><w:rPr>{prop}</w:rPr><w:t>", 1)
                parts["word/document.xml"] = (parts["word/document.xml"][0], document.encode("utf-8"))
                temp = self.new.with_suffix(".tmp.docx")
                with zipfile.ZipFile(temp, "w") as target:
                    for name, (info, content) in parts.items():
                        target.writestr(info, content)
                temp.replace(self.new)
                result, candidate_path = self.invoke(
                    scope="格式差异需人工检查。", semantic="不按纯格式自动复用，等待受影响复核。",
                    reviewed_by="复核人", reviewed_at="2026-10-13T12:00:00+08:00",
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
                self.assertEqual(candidate["status"], "pending")
                self.assertEqual(candidate["rebind_candidate"]["classification"], "manual-review-required")
                self.assertEqual(candidate["contract_protection_review"]["artifact_sha256"], sha256(self.old))

    def test_tampered_or_stale_old_signoff_proof_blocks_rebound_signoff(self) -> None:
        self.add_bold_visual_format_only()
        result, output = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rebound = json.loads(output.read_text(encoding="utf-8"))
        rebound["rebind_record"]["old_signoff_sha256"] = "0" * 64
        output.write_text(json.dumps(rebound, ensure_ascii=False), encoding="utf-8")
        manifest_source = self.root / "source.txt"
        manifest_source.write_text("source facts", encoding="utf-8")
        manifest = self.root / "matter.json"
        manifest.write_text(json.dumps({
            "schema_version": "1.0", "matter_task_id": "MATTER-001", "owner": "使用者",
            "classification": "S2", "matter_root": str(self.root), "public_export_allowed": False,
            "retention_status": "active", "source_files": [{"path": manifest_source.name, "sha256": sha256(manifest_source), "role": "original"}],
        }, ensure_ascii=False), encoding="utf-8")
        report_path = self.root / "blocked.json"
        result = subprocess.run([
            sys.executable, str(GATE), "--artifact", str(self.new), "--output-path", str(self.root / "delivery.docx"),
            "--intent", "internal-final", "--risk-level", "R2", "--matter-manifest", str(manifest),
            "--signoff", str(output), "--out-json", str(report_path),
        ], capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertTrue(any("old sign-off hash mismatch" in item for item in report["errors"]))

    def test_output_symlink_to_input_signoff_is_protected(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo t") + deletion("eh") + insertion("he") + run(" in the text."))], track=True)
        alias = self.root / "signoff-alias.json"
        alias.symlink_to(self.signoff)
        result, _ = self.invoke(
            scope="拼写修正。", semantic="人工核对该修改不影响语义。",
            reviewed_by="复核人", reviewed_at="2026-10-13T13:00:00+08:00", output=alias,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not overwrite input signoff", result.stdout)

    def test_output_symlinks_to_old_or_new_artifact_are_protected(self) -> None:
        write_docx(self.new, [paragraph(run("This is a small typo teh in the text."))])
        before = {path: sha256(path) for path in (self.old, self.new, self.signoff)}
        for input_path, label in ((self.old, "old artifact"), (self.new, "new artifact")):
            with self.subTest(input=label):
                alias = self.root / f"{label.replace(' ', '-')}-alias.docx"
                alias.symlink_to(input_path)
                result, _ = self.invoke(output=alias)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"must not overwrite input {label}", result.stdout)
                self.assertEqual(before, {path: sha256(path) for path in before})


if __name__ == "__main__":
    unittest.main()
