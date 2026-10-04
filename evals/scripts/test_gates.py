from pathlib import Path
import json,shutil,subprocess,tempfile
source=Path(__file__).resolve().parents[2]
label=json.loads((source/'evals/current.json').read_text())['candidate']
run_path='evals/runs/'+label
results=[]
with tempfile.TemporaryDirectory(prefix='v030-gates-') as tmp:
 root=Path(tmp)
 shutil.copytree(source/'skills',root/'skills')
 shutil.copytree(source/'evals/scripts',root/'evals/scripts',ignore=shutil.ignore_patterns('__pycache__'))
 shutil.copytree(source/'evals/fixtures',root/'evals/fixtures')
 shutil.copytree(source/run_path,root/run_path,symlinks=True,ignore=shutil.ignore_patterns('test-fixtures','__pycache__'))
 for name in ['AGENTS.md','evals/current.json']:shutil.copy2(source/name,root/name)
 def run(name,want):
  r=subprocess.run(['python3',str(root/'evals/scripts/verify_evidence.py')],text=True,capture_output=True)
  results.append({'case':name,'exit_code':r.returncode,'expected_pass':want,'pass':(r.returncode==0)==want,'output':r.stderr.splitlines()[-1] if r.returncode else r.stdout.strip()})
 run('complete-evidence',True)
 p=root/'skills/staged-project-delivery/SKILL.md';old=p.read_text();p.write_text(old+'\nstale test\n');run('reject-stale-skill',False);p.write_text(old)
 p=root/'AGENTS.md';old=p.read_text();p.write_text(old+'\nextra\nextra\n');run('reject-overlong-agents',False);p.write_text(old)
 p=root/run_path/'review.json';old=p.read_text();review=json.loads(old);review['cases']['lite']['v030_rules']['metrics']['pass']=False;p.write_text(json.dumps(review));run('reject-missing-metrics-evidence',False);p.write_text(old)
 p=root/'AGENTS.md';p.write_text(p.read_text().replace('0.3.0','0.3.1'));run('reject-changed-fallback-rules',False)
assert all(x['pass'] for x in results)
(source/('evals/gate-tests-'+label+'.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
