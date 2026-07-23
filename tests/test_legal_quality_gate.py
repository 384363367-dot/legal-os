#!/usr/bin/env python3
"""Executable regression tests for the public legal quality gate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "skills" / "legal-quality-gate" / "scripts" / "release_gate.py"


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
                    "owner": "事项负责人",
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

    def write_signoff(self, *, risk: str, intent: str, artifact_hash: str | None = None) -> Path:
        path = self.root / "signoff.json"
        path.write_text(
            json.dumps(
                {
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
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

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

    def test_sensitive_matter_cannot_enter_declared_public_root(self) -> None:
        public_root = self.root / "public-export"
        output = public_root / "artifact.txt"
        completed, report = self.invoke(
            output=output,
            extra=["--public-root", str(public_root)],
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("declared public root" in item for item in report["errors"]))

    def test_public_s0_can_enter_declared_public_root(self) -> None:
        self.write_manifest(classification="S0", public_export_allowed=True)
        public_root = self.root / "public-export"
        output = public_root / "artifact.txt"
        completed, report = self.invoke(
            output=output,
            extra=["--public-root", str(public_root)],
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["decision"], "DRAFT_ONLY")

    def test_absolute_source_outside_matter_root_is_blocked(self) -> None:
        outside = self.root.parent / f"{self.root.name}-outside-source.txt"
        outside.write_text("outside", encoding="utf-8")
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        manifest["source_files"] = [
            {"path": str(outside), "sha256": sha256(outside), "role": "original"}
        ]
        self.manifest.write_text(json.dumps(manifest), encoding="utf-8")
        completed, report = self.invoke()
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(any("escapes matter root" in item for item in report["errors"]))
        outside.unlink()

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
