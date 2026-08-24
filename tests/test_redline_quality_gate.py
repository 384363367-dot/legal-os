from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class RedlineGateCompatibilityTests(unittest.TestCase):
    def test_bundled_contract_suites_present(self):
        t=ROOT/"skills/legal-os-contract/tests"
        self.assertTrue((t/"test_contract_redline_quality_gate.py").is_file())
        self.assertTrue((t/"test_contract_release_gate.py").is_file())
    def test_redline_gate_script_is_present(self):
        self.assertTrue((ROOT/"skills/legal-os-contract/scripts/redline_quality_gate.py").is_file())
if __name__=="__main__": unittest.main()
