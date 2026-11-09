import csv,sys,json; sys.path.insert(0,''+__import__('os').path.dirname(__file__)+''); from loc import *
from babel import Locale
tr=Locale('tr')
OV={'HK':('Hong Kong',"Hong Kong'da",'hong-kong','CLDR: Çin Hong Kong ÖİB — kısaltıldı'),
    'MO':('Makao',"Makao'da",'makao','CLDR: Çin Makao ÖİB — kısaltıldı'),
    'MM':('Myanmar',"Myanmar'da",'myanmar','CLDR: Myanmar (Burma) — kısaltıldı'),
    'NP':(None,"Nepal'de",None,'ünlü uyumu istisnası (Nepal\'de)'),
    'LI':(None,"Liechtenstein'da",None,'okunuşa göre (lihtenştayn)'),
    'RE':('Réunion',"Réunion'da",'reunion','')}
rows=[]
for x in csv.DictReader(open(__import__('os').path.dirname(__file__)+'/../../../names/countries.csv')):
    cc=x['cc']; name=x['name_tr'] or tr.territories.get(cc); note=''
    ip=loc(name); sl=slug(name)
    if cc in OV:
        n2,ip2,sl2,nt=OV[cc]; name=n2 or name; ip=ip2 or ip; sl=sl2 or sl; note=nt
    if tr.territories.get(cc)!=x['name_tr'] and not note: note='babel: '+str(tr.territories.get(cc))
    rows.append([cc,name,sl,ip,note])
w=csv.writer(open(__import__('os').path.dirname(__file__)+'/../countries.csv','w',newline=''))
w.writerow(['cc','name','slug','in_phrase','note']); w.writerows(rows)
print(len(rows), len({r[2] for r in rows}), [r for r in rows if r[4]])
