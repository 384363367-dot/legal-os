from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAW = ROOT / "skills/cn-law-hub"
RESEARCH = ROOT / "skills/cn-legal-research"


class PublicLawResearchAdaptationTests(unittest.TestCase):
    def run_script(self, script: str, *args: str, expected: int = 0):
        result = subprocess.run(
            [sys.executable, str(LAW / "scripts" / script), *args],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_query_plan_covers_ten_registered_sources(self):
        output = self.run_script(
            "build_authority_queries.py",
            "合同违约金调整",
            "--name",
            "民法典",
            "--article",
            "第五百八十五条",
        )
        data = json.loads(output.stdout)
        self.assertEqual(data["source_count"], 10)
        self.assertEqual(len(data["official_sources"]), 10)
        self.assertTrue(any(item["source_id"] == "spc-publications" for item in data["official_sources"]))
        self.assertIn("不自动抓取", data["verification_note"])

    def test_missing_authority_metadata_is_rejected(self):
        record = {
            "title": "示例规范",
            "authority_type": "law",
            "issuing_body": "全国人民代表大会",
            "status": "effective",
            "proposition": "示例命题",
            "source_url": "https://flk.npc.gov.cn/",
            "accessed_at": "2026-08-25",
            "verification_status": "verified-source",
            "limitations": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            path.write_text(json.dumps({"authorities": [record]}, ensure_ascii=False), encoding="utf-8")
            result = self.run_script("validate_authority_records.py", str(path), expected=1)
        self.assertIn("document_number", result.stderr)
        self.assertIn("promulgated_date", result.stderr)
        self.assertIn("effective_date", result.stderr)

    def test_official_host_and_authority_type_must_match(self):
        record = {
            "title": "示例条约",
            "authority_type": "treaty",
            "issuing_body": "外交部",
            "document_number": None,
            "promulgated_date": None,
            "effective_date": None,
            "status": "effective",
            "proposition": "示例命题",
            "source_url": "https://flk.npc.gov.cn/",
            "accessed_at": "2026-08-25",
            "verification_status": "verified-source",
            "limitations": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            path.write_text(json.dumps({"authorities": [record]}, ensure_ascii=False), encoding="utf-8")
            result = self.run_script("validate_authority_records.py", str(path), expected=1)
        self.assertIn("authority type 'treaty'", result.stderr)

    def test_duplicate_record_links_are_rejected(self):
        record = {
            "title": "示例规范",
            "authority_type": "law",
            "issuing_body": "全国人民代表大会",
            "document_number": None,
            "promulgated_date": None,
            "effective_date": None,
            "status": "effective",
            "proposition": "示例命题",
            "source_url": "https://flk.npc.gov.cn/",
            "accessed_at": "2026-08-25",
            "verification_status": "verified-source",
            "limitations": [],
            "supersedes": ["A", "A"],
            "superseded_by": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            path.write_text(json.dumps({"authorities": [record]}, ensure_ascii=False), encoding="utf-8")
            result = self.run_script("validate_authority_records.py", str(path), expected=1)
        self.assertIn("duplicate IDs", result.stderr)

    def test_public_boundary_stays_first_party_and_private_free(self):
        result = self.run_script("check_first_party_boundary.py")
        self.assertIn("PASS", result.stdout)

    def run_research_script(self, script: str, *args: str, expected: int = 0):
        result = subprocess.run(
            [sys.executable, str(RESEARCH / "scripts" / script), *args],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_current_law_default_is_the_full_adapter(self):
        manifest = json.loads((ROOT / "legalos.manifest.json").read_text(encoding="utf-8"))
        route = next(item for item in manifest["routes"] if item["id"] == "T-05")
        self.assertEqual(route["executor"]["skill_by_intake_type"]["current-law-research"], "cn-legal-research")
        self.assertEqual(next(item for item in manifest["skills"] if item["name"] == "cn-law-hub")["status"], "compatibility")

    def test_public_adapter_boundary_and_registry(self):
        result = self.run_research_script("check_first_party_boundary.py")
        self.assertIn("PASS", result.stdout)
        result = subprocess.run(
            [sys.executable, "-c", "from source_registry import OFFICIAL_SOURCES; print(len(OFFICIAL_SOURCES)); assert all(s.official_url.startswith('https://') for s in OFFICIAL_SOURCES)"],
            cwd=str(RESEARCH / "scripts"),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "10")

    def test_public_adapter_mcp_protocol_is_offline(self):
        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}) + "\n"
        result = subprocess.run(
            [sys.executable, str(RESEARCH / "scripts/mcp_server.py"), "--once"],
            input=request,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(any(tool["name"] == "search_official_source" for tool in payload["result"]["tools"]))


if __name__ == "__main__":
    unittest.main()
