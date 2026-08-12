from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NativeOfficePolicyTests(unittest.TestCase):
    def test_office_policy_has_no_retired_renderer_path(self) -> None:
        prohibited = [
            "".join(("Libre", "Office")),
            "".join(("render_", "docx.py")),
            "".join(("render", " → inspect")),
            "".join(("Render and inspect", " every")),
        ]
        hits: list[str] = []
        for base in (ROOT / "docs", ROOT / "skills"):
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in {".md", ".py", ".yaml", ".yml", ".json"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for token in prohibited:
                    if token.lower() in text.lower():
                        hits.append(f"{path.relative_to(ROOT)}: {token}")
        self.assertEqual(hits, [])

    def test_native_office_policy_is_complete(self) -> None:
        policy = (ROOT / "docs" / "native-office-quality-gate.md").read_text(encoding="utf-8")
        required = [
            "structured file inspection",
            "concrete objective pagination/layout risk",
            "Quick Look",
            "WPS Office",
            "explicit user authorization",
            "Draft/Hold",
        ]
        self.assertEqual([token for token in required if token not in policy], [])

    def test_render_failure_is_not_a_standalone_blocker(self) -> None:
        policy = (ROOT / "docs" / "native-office-quality-gate.md").read_text(encoding="utf-8")
        required = [
            "DOCX source as the formal Office deliverable",
            "OOXML/package structure",
            "PDF/PNG",
            "at most one final render",
            "120-second",
            "300-second",
            "one corrective retry",
            "ENVIRONMENT_LIMITATION",
            "while structural checks pass",
            "not set Draft/Hold solely",
            "source-content, source-structure, privacy or authorization blocker",
        ]
        self.assertEqual([token for token in required if token not in policy], [])
        self.assertNotIn("keep the output at Draft/Hold", policy)


if __name__ == "__main__":
    unittest.main()
