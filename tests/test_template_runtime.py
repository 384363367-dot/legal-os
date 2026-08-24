from __future__ import annotations
import hashlib,json,subprocess,sys,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SKILLS=ROOT/'skills';CAT=SKILLS/'legal-os-template-runtime/references/template-catalog.json';RUN=SKILLS/'legal-os-template-runtime/scripts/template_runtime.py'
class TemplateRuntimeTests(unittest.TestCase):
 def test_catalog_has_24_hash_bound_assets(self):
  c=json.loads(CAT.read_text(encoding='utf-8'));self.assertEqual(len(c['templates']),24)
  for x in c['templates']:
   p=SKILLS/x['skill']/x['relative_path'];self.assertTrue(p.is_file(),x['id']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'],x['id'])
 def test_all_office_assets_are_valid_zip_packages(self):
  for p in SKILLS.glob('*/assets/templates/*'):
   if p.suffix.lower() in {'.docx','.xlsx'}:
    self.assertTrue(zipfile.is_zipfile(p),str(p))
 def test_memory_candidate_diff_resolves(self):
  r=subprocess.run([sys.executable,str(RUN),'resolve','--document-type','memory-update-candidate-diff','--skills-root',str(SKILLS)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);d=json.loads(r.stdout);self.assertEqual(d['template_id'],'MEMORY-CANDIDATE-DIFF-V1.12')
 def test_civil_complaint_has_paired_evidence_catalog(self):
  r=subprocess.run([sys.executable,str(RUN),'resolve','--document-type','civil-complaint','--skills-root',str(SKILLS)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);d=json.loads(r.stdout);self.assertEqual(d['paired_document_type'],'evidence-catalog');self.assertTrue(Path(d['paired_path']).is_file())
 def test_unknown_template_stops(self):
  r=subprocess.run([sys.executable,str(RUN),'resolve','--document-type','unknown-form','--skills-root',str(SKILLS)],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stdout)['status'],'TEMPLATE_REQUIRED')
if __name__=='__main__':unittest.main()
