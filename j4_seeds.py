"""Execute preregistered independent faults; original files restored in finally."""
import pathlib,subprocess,json,sys,xml.etree.ElementTree as ET,shutil
from j4_stage import run_http,NAME
config=json.loads(pathlib.Path('j4_config.json').read_text())
results=[]
for name,file,old,new in json.loads(pathlib.Path('j4_mutations.json').read_text()):
 p=pathlib.Path(file);original=p.read_text();assert old in original,(name,'mutation source missing')
 dest=pathlib.Path('seed-evidence')/name;dest.mkdir(parents=True,exist_ok=True)
 try:
  changed=original.replace(old,new,1)
  if NAME=='nest' and name=='tags-status':changed=changed.replace('Controller, Get','Controller, Get, HttpCode')
  p.write_text(changed)
  if NAME=='symfony':shutil.rmtree('var/cache/test',ignore_errors=True)
  if NAME=='nest':cmd=['yarn','test','--runInBand','--json','--outputFile='+str(dest/'tests.json')]
  elif NAME=='fastapi':cmd=['poetry','run','python','-m','pytest','-n','2','--junitxml='+str(dest/'tests.xml')]
  else:cmd=['vendor/bin/phpunit','--log-junit',str(dest/'tests.xml')]
  with (dest/'tests.log').open('w') as log:test=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=150)
  if NAME=='nest':
   d=json.loads((dest/'tests.json').read_text());assert d['numTotalTests']==config['test_count'] and d['numRuntimeErrorTestSuites']==0,'test inventory/infra failure'
   failures=d['numFailedTests'];errors=0
  else:
   tree=ET.parse(dest/'tests.xml');assert len(tree.findall('.//testcase'))==config['test_count'],'test inventory changed'
   failures=len(tree.findall('.//failure'));errors=len(tree.findall('.//error'));assert errors==0,'test infrastructure/runtime error; do not score as detection'
  assert test.returncode==0 or failures>0,'non-assertion test failure; do not score as detection'
  http=run_http(dest,NAME=='nest')
  assert http['harness_detected'],'mutation must change measured HTTP surface'
  results.append({'fault':name,'project_detected':failures>0 or http['e2e_detected'],'project_test_failures':failures,**http})
  pathlib.Path('seed-results.json').write_text(json.dumps(results,indent=2))
 finally:
  p.write_text(original)
  if NAME=='symfony':shutil.rmtree('var/cache/test',ignore_errors=True)
a=sum(r['project_detected'] for r in results);b=sum(r['project_detected'] or r['harness_detected'] for r in results)
print(json.dumps(results,indent=2));assert b>=4 and 5-b<=(5-a)/2
