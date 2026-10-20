from __future__ import annotations
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.validate_manifest import validate_manifest
from scripts.profile_inventory import profile_payload
class ManifestValidationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.manifest=json.loads((ROOT/'legalos.manifest.json').read_text(encoding='utf-8'))
 def test_current_manifest_is_consistent(self):self.assertEqual(validate_manifest(ROOT),[])
 def test_release_identity_and_public_profile_are_current(self):
  self.assertEqual(self.manifest['release'],{'release_id':'legalos-v0.8.6','version':'0.8.6'})
  self.assertEqual(self.manifest['profile']['profile_id'],'public-generic')
  self.assertEqual(self.manifest['profile']['payload'],profile_payload(ROOT/'skills'))
  self.assertEqual(self.manifest['product']['public_version'],self.manifest['release']['version'])
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
 def test_release_version_must_match_product_version(self):
  m=copy.deepcopy(self.manifest);m['release']['version']='9.9.9';self.assertTrue(any('must match product.public_version' in e for e in validate_manifest(ROOT,m)))
 def test_product_release_status_has_no_candidate_wait_state(self):
  m=copy.deepcopy(self.manifest);m['product']['release_status']='candidate';self.assertTrue(any('release_status must be released or superseded' in e for e in validate_manifest(ROOT,m)))
 def test_public_profile_hash_must_match_skills_payload(self):
  m=copy.deepcopy(self.manifest);m['profile']['payload']['tree_sha256']='0'*64;self.assertTrue(any('profile.payload' in e for e in validate_manifest(ROOT,m)))
 def test_generated_runtime_artifacts_do_not_change_profile_hash(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'skills';skill=root/'sample-skill';skill.mkdir(parents=True);(skill/'SKILL.md').write_text('payload',encoding='utf-8')
   expected=profile_payload(root);self.assertEqual(expected['skill_count'],1);self.assertEqual(expected['file_count'],1)
   (skill/'__pycache__').mkdir();(skill/'__pycache__'/'generated.pyc').write_bytes(b'cache')
   (skill/'generated.pyc').write_bytes(b'cache')
   (skill/'.venv'/'lib').mkdir(parents=True);(skill/'.venv'/'lib'/'generated.py').write_text('runtime',encoding='utf-8')
   (skill/'.git'/'objects').mkdir(parents=True);(skill/'.git'/'objects'/'generated').write_text('metadata',encoding='utf-8')
   (root/'__pycache__').mkdir();(root/'__pycache__'/'generated.pyc').write_bytes(b'cache')
   self.assertEqual(profile_payload(root),expected)
 def test_skill_maturity_and_cn_law_compatibility_remain_independent(self):
  skills={item['name']:item for item in self.manifest['skills']}
  self.assertEqual(skills['legal-os-unified-intake']['maturity'],'candidate')
  self.assertEqual(skills['cn-law-hub']['status'],'compatibility')
 def test_package_manifest_and_checksums_match_current_files(self):
  package=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
  self.assertEqual(package['package_version'],'0.8.6')
  self.assertEqual(package['release'],self.manifest['release'])
  self.assertEqual(package['profile'],self.manifest['profile'])
  files=package['files'];self.assertEqual(package['file_count'],len(files))
  expected={item['path'] for item in files}
  self.assertEqual(len(expected),len(files))
  if (ROOT/'.git').exists():
   listed=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
   checkout_files={path for path in filter(None,listed) if (ROOT/path).is_file()}
   self.assertEqual(expected,checkout_files - {'PACKAGE_MANIFEST.json','SHA256SUMS.txt'})
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
