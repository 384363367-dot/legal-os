from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BOUNDARY = ROOT / "skills/legal-os-unified-intake/references/external-expression-boundary.md"


class ExternalExpressionBoundaryTests(unittest.TestCase):
    def test_boundary_is_public_and_audience_specific(self) -> None:
        text = BOUNDARY.read_text(encoding="utf-8")
        for marker in ("Counterparty", "Court", "Internal", "mandatory", "unverified"):
            self.assertIn(marker, text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("Registry", text)
        self.assertNotIn("receipt", text)

    def test_boundary_does_not_suppress_procedural_disclosure(self) -> None:
        text = BOUNDARY.read_text(encoding="utf-8")
        self.assertIn("required by law", text)
        self.assertIn("necessary logical link", text)
        self.assertIn("complete internal analysis", text)


if __name__ == "__main__":
    unittest.main()
