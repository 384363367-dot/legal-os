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


if __name__ == "__main__":
    unittest.main()
