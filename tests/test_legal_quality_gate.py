from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class QualityGateCompatibilityTests(unittest.TestCase):
    def test_bundled_quality_suite_is_present(self):
        self.assertTrue((ROOT/"skills/legal-quality-gate/tests/test_quality_release_gate.py").is_file())
    def test_release_gate_script_is_present(self):
        self.assertTrue((ROOT/"skills/legal-quality-gate/scripts/release_gate.py").is_file())
if __name__=="__main__": unittest.main()
