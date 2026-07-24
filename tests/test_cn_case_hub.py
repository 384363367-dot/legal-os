from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "cn-case-hub"
FIXTURE = ROOT / "tests" / "fixtures" / "cn-case-hub" / "competition_cases.json"


class CnCaseHubTests(unittest.TestCase):
    def run_script(self, script: str, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts" / script), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def test_official_case_fixture_validates(self) -> None:
        result = self.run_script("validate_case_records.py", str(FIXTURE))
        self.assertIn("4 case record(s) validated", result.stdout)

    def test_query_builder_generates_positive_and_adverse_queries(self) -> None:
        result = self.run_script(
            "build_official_queries.py",
            "竞业限制纠纷",
            "--fact",
            "新旧单位经营范围重合但实际产品不同",
        )
        payload = json.loads(result.stdout)
        self.assertGreaterEqual(len(payload["queries"]), 8)
        self.assertTrue(any("site:court.gov.cn" in item for item in payload["queries"]))
        self.assertTrue(any("不予支持" in item for item in payload["queries"]))

    def test_non_official_source_is_rejected(self) -> None:
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["cases"][0]["source_url"] = "https://example.com/not-official"
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_file = Path(temp_dir) / "invalid.json"
            invalid_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.run_script("validate_case_records.py", str(invalid_file), expected=1)
        self.assertIn("requires an official court URL", result.stderr)


if __name__ == "__main__":
    unittest.main()
