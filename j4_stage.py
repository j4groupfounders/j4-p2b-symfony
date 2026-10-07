"""Scoped real-server replay with owned process cleanup; no model/API calls."""
import pathlib,subprocess,os,signal,json,sys
NAME=json.loads(pathlib.Path('j4_config.json').read_text())['name']
def reset():
 if NAME=='nest':
  subprocess.run(['mysql','--protocol=tcp','-h127.0.0.1','-P3307','-uroot','-e','DROP DATABASE IF EXISTS nestjsrealworld; CREATE DATABASE nestjsrealworld;'],check=True,stdout=subprocess.DEVNULL)
 if NAME=='symfony':
  for cmd in ['doctrine:schema:drop --force','doctrine:schema:create']:
   subprocess.run(['php','bin/console',*cmd.split()],check=True,stdout=subprocess.DEVNULL)
def run_http(dest, e2e=False):
 dest=pathlib.Path(dest);dest.mkdir(parents=True,exist_ok=True)
 reset()
 cmd={'nest':['yarn','start'],'fastapi':['poetry','run','uvicorn','app.main:app','--host','127.0.0.1','--port','3000'],'symfony':['php','-d','variables_order=EGPCS','-S','127.0.0.1:3000','-t','public']}[NAME]
 server=None
 try:
  with (dest/'boot.log').open('w') as log:
   server=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   with (dest/'probe.log').open('w') as log2:
    probe=subprocess.run([sys.executable,'j4_probe.py'],stdout=log2,stderr=subprocess.STDOUT,timeout=95)
   output=(dest/'probe.log').read_text()
   assert 'BOOT FAILED' not in output and pathlib.Path('surface.actual.json').exists(),'server failed to boot or probe failed'
   (dest/'surface.json').write_text(pathlib.Path('surface.actual.json').read_text())
   ee=None
   if e2e:
    with (dest/'e2e.log').open('w') as log3:
     subprocess.run(['npx','--yes','newman@6.2.2','run','e2e/Conduit.postman_collection.json','--delay-request','0','--global-var','APIURL=http://localhost:3000/api','--global-var','USERNAME=j4fixture','--global-var','EMAIL=j4fixture@example.test','--global-var','PASSWORD=practice-password','--reporters','json','--reporter-json-export',str(dest/'e2e.json')],stdout=log3,stderr=subprocess.STDOUT,timeout=120)
    ee=json.loads((dest/'e2e.json').read_text())['run']
    assert ee['stats']['assertions']['total']==280,'E2E assertion inventory changed'
   return {'harness_detected':probe.returncode!=0,'e2e_detected':bool(ee and ee['failures']),'e2e_assertions':ee['stats']['assertions'] if ee else None}
 finally:
  if server:
   try:os.killpg(server.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   server.wait(timeout=20)
if __name__=='__main__':
 result=run_http('http-evidence',NAME=='nest')
 print(json.dumps(result))
 assert not result['harness_detected'] and not result['e2e_detected'],'baseline/upgrade HTTP or API collection failure'
