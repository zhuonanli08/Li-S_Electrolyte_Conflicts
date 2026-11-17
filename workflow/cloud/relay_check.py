"""Offline relay acceptance only. No scientific/model/network calls."""
import hashlib, importlib, json, platform, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
def main():
    manifest=json.loads((ROOT/'workflow/cloud/sync_manifest.json').read_text(encoding='utf-8'))
    checks=[]
    for f in manifest['files']:
        p=ROOT/f['path']
        checks.append({'path':f['path'],'matches':p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']})
    versions={n:importlib.import_module(n).VERSION for n in ('progressive_discovery','inspiration_design','evidence_first_design','experiment_design_workflow')}
    suite=unittest.defaultTestLoader.loadTestsFromName('test_evidence_claims')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    receipt={'protocol':'relay-20261117-v1','python':platform.python_version(),'platform':platform.system(),
             'file_checks':checks,'versions':versions,'tests_run':result.testsRun,
             'tests_passed':result.wasSuccessful(),'hashes_passed':all(c['matches'] for c in checks),
             'scientific_calls':0,'simulation_runs':0,'data_scope':'code_rules_only_no_fulltext_or_extraction',
             'success':result.wasSuccessful() and all(c['matches'] for c in checks)}
    target=ROOT/'workflow/cloud/relay_receipt.json'
    target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    return 0 if receipt['success'] else 1
if __name__=='__main__':raise SystemExit(main())
