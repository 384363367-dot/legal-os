from __future__ import annotations
import os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INSTALL=ROOT/'install.sh'
class InstallerTests(unittest.TestCase):
 def test_dry_run_lists_fourteen_skills(self):
  with tempfile.TemporaryDirectory() as td:
   r=subprocess.run([str(INSTALL),'--dry-run','--target',td],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('14 Skill(s) processed',r.stdout);self.assertEqual(list(Path(td).iterdir()),[])
 def test_clean_install_copies_all_skills(self):
  with tempfile.TemporaryDirectory() as td:
   r=subprocess.run([str(INSTALL),'--target',td],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(len([p for p in Path(td).iterdir() if p.is_dir() and p.name!='.backup']),14)
 def test_replace_backs_up_existing_skill(self):
  with tempfile.TemporaryDirectory() as td:
   t=Path(td);(t/'cn-case-hub').mkdir();(t/'cn-case-hub/old.txt').write_text('old')
   r=subprocess.run([str(INSTALL),'--replace','--target',td],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertTrue((t/'.backup').exists());self.assertTrue((t/'cn-case-hub/SKILL.md').exists())
if __name__=='__main__':unittest.main()
