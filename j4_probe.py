import urllib.request,urllib.error,json,hashlib,time,sys,pathlib
routes=[('GET','/api/tags',None),('GET','/api/articles',None),('GET','/api/user',None),('GET','/j4-missing',None),('POST','/api/users/login',{})]
if pathlib.Path('package.json').exists():routes.insert(0,('GET','/',None))
for i in range(60):
 try:urllib.request.urlopen('http://127.0.0.1:3000/j4-missing',timeout=2)
 except urllib.error.HTTPError:break
 except Exception:time.sleep(1);continue
 else:break
else:raise SystemExit('BOOT FAILED')
def normalize(v):
 if isinstance(v,dict):return {k:normalize(x) for k,x in v.items() if k not in ('createdAt','updatedAt','created_at','updated_at','requestId')}
 if isinstance(v,list):return [normalize(x) for x in v]
 return v
out=[]
for method,path,body in routes:
 req=urllib.request.Request('http://127.0.0.1:3000'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Content-Type':'application/json','Accept':'application/json'})
 try:r=urllib.request.urlopen(req,timeout=10)
 except urllib.error.HTTPError as e:r=e
 raw=r.read().decode();ct=r.headers.get('Content-Type','').split(';')[0]
 try:raw=json.dumps(normalize(json.loads(raw)),sort_keys=True,separators=(',',':'))
 except ValueError:pass
 out.append(dict(method=method,path=path,status=r.code,content_type=ct,sha256=hashlib.sha256(raw.encode()).hexdigest(),body=raw))
pathlib.Path('surface.actual.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
assert all(x['status']<500 for x in out),'server error in measured surface'
expected=pathlib.Path('surface.json')
if expected.exists():assert json.loads(expected.read_text())==out,'CHARACTERIZATION DRIFT'
print('BOOT + CHARACTERIZATION PASS')
