from __future__ import annotations
import sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.validate_repo import validate_repository
class RepositoryValidationTests(unittest.TestCase):
 def test_current_repository_is_consistent(self):self.assertEqual(validate_repository(ROOT),[])
 def test_every_skill_has_agent_metadata(self):
  for d in (ROOT/'skills').iterdir():
   if d.is_dir():self.assertTrue((d/'agents/openai.yaml').is_file(),d.name)
 def test_no_legacy_cn_law_crawlers(self):
  banned={'court_law_crawler.py','tax_law_crawler.py','moj_law_crawler.py','treaty_crawler.py','mod_law_crawler.py','mee_law_crawler.py','party_law_crawler.py'}
  self.assertEqual([p for p in (ROOT/'skills/cn-law-hub').rglob('*.py') if p.name in banned],[])
 def test_public_tree_has_no_runtime_snapshot_folder(self):self.assertFalse((ROOT/'runtime').exists())
if __name__=='__main__':unittest.main()
