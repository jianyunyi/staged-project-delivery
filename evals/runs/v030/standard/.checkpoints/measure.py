import pathlib,json,hashlib,difflib,sys
stage=sys.argv[1]
p=pathlib.Path('.')
files={str(x):x.read_text() for x in p.rglob('*') if x.is_file() and (x.parent==p or str(x).startswith('test/')) and x.name!='agent-output.md'}
before=json.loads(pathlib.Path(f'.checkpoints/{stage}-before.json').read_text())
rows=[]
for name in sorted(files.keys()|before.keys()):
 a=before.get(name,'').splitlines(); b=files.get(name,'').splitlines()
 if a==b: continue
 ops=difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes()
 plus=sum(j2-j1 for tag,i1,i2,j1,j2 in ops if tag in ('insert','replace'))
 minus=sum(i2-i1 for tag,i1,i2,j1,j2 in ops if tag in ('delete','replace'))
 category='测试' if name.startswith('test/') else '文档' if name.endswith('.md') else '实现'
 rows.append({'file':name,'category':category,'added':plus,'deleted':minus})
pathlib.Path(f'evidence/{stage}-diff.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
pathlib.Path(f'.checkpoints/{stage}-after.json').write_text(json.dumps(files,ensure_ascii=False,indent=2))
hashes={k:hashlib.sha256(v.encode()).hexdigest() for k,v in files.items()}
pathlib.Path(f'evidence/{stage}-sha256.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2))
for category in ['实现','测试','文档']:
 r=[x for x in rows if x['category']==category]
 print(category,len(r),sum(x['added'] for x in r),sum(x['deleted'] for x in r))
