from __future__ import annotations
import copy,hashlib,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.validate_manifest import validate_manifest
class ManifestValidationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.manifest=json.loads((ROOT/'legalos.manifest.json').read_text(encoding='utf-8'))
 def test_current_manifest_is_consistent(self):self.assertEqual(validate_manifest(ROOT),[])
 def test_has_fifteen_skills_and_twelve_routes(self):self.assertEqual(len(self.manifest['skills']),15);self.assertEqual(len(self.manifest['routes']),12)
 def test_t05_dispatches_case_and_current_law(self):
  r=next(x for x in self.manifest['routes'] if x['id']=='T-05');self.assertEqual(r['executor']['skill_by_intake_type'],{'current-law-research':'cn-legal-research','case-research':'cn-case-hub'})
 def test_cn_law_hub_is_compatibility_only(self):
  skill=next(x for x in self.manifest['skills'] if x['name']=='cn-law-hub');self.assertEqual(skill.get('status'),'compatibility');self.assertNotEqual(self.manifest['routes'][4]['executor']['skill_by_intake_type']['current-law-research'],'cn-law-hub')
 def test_t12_uses_learning_maintenance(self):
  r=next(x for x in self.manifest['routes'] if x['id']=='T-12');self.assertEqual(r['executor']['skill'],'legal-os-learning-maintenance')
 def test_missing_route_is_reported(self):
  m=copy.deepcopy(self.manifest);m['routes']=m['routes'][:-1];self.assertTrue(any('T-01 through T-12' in e for e in validate_manifest(ROOT,m)))
 def test_invocation_policy_must_cover_every_skill(self):
  m=copy.deepcopy(self.manifest);m['invocation_policy'].pop('cn-law-hub');self.assertTrue(any('every and only' in e for e in validate_manifest(ROOT,m)))
 def test_package_manifest_and_checksums_match_current_files(self):
  package=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
  files=package['files'];self.assertEqual(package['file_count'],len(files))
  expected={item['path'] for item in files}
  self.assertEqual(len(expected),len(files))
  if (ROOT/'.git').exists():
   listed=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
   self.assertEqual(expected,set(filter(None,listed)) - {'PACKAGE_MANIFEST.json','SHA256SUMS.txt'})
  for item in files:
   path=ROOT/item['path'];self.assertTrue(path.is_file(),item['path'])
   self.assertEqual(path.stat().st_size,item['size'],item['path'])
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),item['sha256'],item['path'])
  sums={}
  for line in (ROOT/'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
   if line.strip():
    digest,path=line.split('  ',1);self.assertNotIn(path,sums);sums[path]=digest
  self.assertEqual(set(sums),expected|{'PACKAGE_MANIFEST.json'})
  for path,digest in sums.items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
if __name__=='__main__':unittest.main()
