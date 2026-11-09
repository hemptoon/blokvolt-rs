# K8-i18n: hreflang reciprocity of a built dist-com: python3 scripts/qa/world_hreflang_check.py dist-com [/de/]
import re,glob,os,collections,sys,json
root=sys.argv[1]
alt_re=re.compile(r'<link rel="alternate" hreflang="([^"]+)" href="https://blokvolt\.com([^"]+)"')
pages={}
for f in glob.glob(root+'/**/index.html',recursive=True):
    h=open(f,encoding='utf-8').read()
    a=alt_re.findall(h)
    if not a: continue
    url=('/'+os.path.relpath(os.path.dirname(f),root)+'/').replace('/./','/').replace('//','/')
    pages[url]=(dict(a),h)
bad=collections.Counter(); ex={}
for u,(a,h) in pages.items():
    for hl,t in a.items():
        if hl=='x-default': continue
        if t not in pages: bad['target missing']+=1; ex.setdefault('target missing',(u,t)); continue
        if set(pages[t][0].items())!=set(a.items()):
            k='not reciprocal (world)' if not re.match(r'/(ba|hr|me|mk|al|xk|si)/',u) else 'not reciprocal (regional, pre-existing scope)'
            bad[k]+=1; ex.setdefault(k,(u,t))
pref=sys.argv[2] if len(sys.argv)>2 else None
n=sum(1 for u in pages if pref and u.startswith(pref))
print(json.dumps({'pages_with_hreflang':len(pages),'pages_'+str(pref):n,'problems':bad,'examples':ex},ensure_ascii=False))
