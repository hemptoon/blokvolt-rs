import csv, re, sys, unicodedata
from babel import Locale
W='/home/claude/blokvolt-rs/content/world/'
OUT=W+'i18n/mk/'
L=Locale('mk')
# ---------- translit helpers
LAT=[('dž','џ'),('Dž','Џ'),('DŽ','Џ'),('lj','љ'),('Lj','Љ'),('LJ','Љ'),('nj','њ'),('Nj','Њ'),('NJ','Њ')]
M=dict(zip('abcčćdđefghijklmnoprsštuvzž','абцчќдѓефгхијклмнопрсштувзж'))
def sr2mk(s):
    for a,b in LAT: s=s.replace(a,b)
    o=''
    for ch in s:
        lo=ch.lower()
        if lo in M:
            t=M[lo]; o+= t.upper() if ch!=lo else t
        else: o+=ch
    return o
VOW='аеиоуяюёэыАЕИОУЯЮЁЭЫ'
def ru2mk(s,en,cc=''):
    s=s.replace('Дж','Џ').replace('дж','џ')
    o=[];i=0
    uml='ü' in en.lower() or 'ue' in en.lower()
    while i<len(s):
        ch=s[i]; lo=ch.lower(); up=ch!=lo
        nx=s[i+1].lower() if i+1<len(s) else ''
        prev=o[-1] if o else ''
        prevcons= bool(prev) and prev.lower() in 'бвгдѓжзѕјклљмнњпрстќфхцчџш'
        def U(t): return (t[0].upper()+t[1:]) if up else t
        if lo in 'нл' and nx=='ь':
            nn=s[i+2].lower() if i+2<len(s) else ''
            if nn and nn in 'яюеёио':
                o.append(U('њ' if lo=='н' else 'љ'))
                m={'я':'а','ю':'у','е':'е','ё':'о','и':'и','о':'о'}[nn]
                o.append(m); i+=3; continue
            o.append(U(lo)); i+=2; continue
        if lo=='ь':
            if nx and nx in 'ео': o.append('ј')
            i+=1; continue
        if lo=='ъ': i+=1; continue
        if lo=='я': o.append(U('ја')); i+=1; continue
        if lo=='ю':
            o.append(U('и' if (prevcons and (uml or cc not in ('GB','US','CA','AU','NZ','IE'))) else 'ју')); i+=1; continue
        if lo=='ё':
            o.append(U('е' if prevcons else 'јо')); i+=1; continue
        rep={'э':'е','ы':'и','й':'ј','щ':'шч'}
        o.append(U(rep.get(lo,lo))); i+=1
    r=''.join(o).replace('јј','ј').replace('Јј','Ј')
    if '-' not in en: r=r.replace('-',' ')
    # collapse doubled consonants
    r=re.sub(r'([бвгдѓжзѕклљмнњпрстќфхцчџшБВГДЖЗКЛМНПРСТФХЦЧШ])\1',r'\1',r,flags=re.I)
    return r
def mk2lat(s):
    m={'а':'a','б':'b','в':'v','г':'g','д':'d','ѓ':'gj','е':'e','ж':'zh','з':'z','ѕ':'dz','и':'i','ј':'j','к':'k','л':'l','љ':'lj','м':'m','н':'n','њ':'nj','о':'o','п':'p','р':'r','с':'s','т':'t','ќ':'kj','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','џ':'dzh','ш':'sh'}
    o=''.join(m.get(c,c) for c in s.lower())
    o=unicodedata.normalize('NFKD',o).encode('ascii','ignore').decode()
    return re.sub(r'[^a-z0-9]+','-',o).strip('-')
# ---------- countries
NA={'CY','MT','MU','BB','JM','KY','IS','FO','AX','IM','JE','GG','RE','TT','FJ','TO','WS','LC','MF','VC','AW','PR','CU','HT','DO','SJ'}
FIX={'MM':'Мјанмар','HK':'Хонгконг','MO':'Макао','SZ':'Есватини','PS':'Палестина','CZ':'Чешка','NL':'Холандија'}
rows=[];slugs=set()
for r in csv.DictReader(open(W+'names/countries.csv')):
    cc=r['cc']; note=''
    name=r['name_mk'].strip()
    if not name: name=L.territories.get(cc,r['name_en']); note='babel'
    if cc in FIX and FIX[cc]!=name: note=(note+'; ' if note else '')+f'CLDR: {name}'; name=FIX[cc]
    slug=mk2lat(name)
    assert slug not in slugs, slug; slugs.add(slug)
    prep='на' if cc in NA else 'во'
    if prep=='на': note=(note+'; ' if note else '')+'предлог «на» (остров)'
    rows.append([cc,name,slug,f'{prep} {name}',note])
with open(OUT+'countries.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['cc','name','slug','in_phrase','note']); w.writerows(rows)
# ---------- cities
OV={('AT','Vienna'):'Виена',('CZ','Prague'):'Прага',('IT','Naples'):'Неапол',('IT','Genoa'):'Џенова',('IT','Venice'):'Венеција',
('IT','Florence'):'Фиренца',('IT','Rome'):'Рим',('IT','Milan'):'Милано',('IT','Turin'):'Торино',('DE','Munich'):'Минхен',('DE','Cologne'):'Келн',
('CH','Zurich'):'Цирих',('CH','Geneva'):'Женева',('BE','Brussels'):'Брисел',('NL','The Hague'):'Хаг',('BE','Antwerpen'):'Антверпен',('BE','Antwerp'):'Антверпен',
('PT','Lisbon'):'Лисабон',('PL','Warsaw'):'Варшава',('DK','Copenhagen'):'Копенхаген',('SE','Stockholm'):'Стокхолм',('GR','Athens'):'Атина',
('GR','Thessaloniki'):'Солун',('GR','Ioannina'):'Јанина',('GR','Piraeus'):'Пиреј',('TR','Istanbul'):'Истанбул',('UA','Kyiv'):'Киев',('UA','Lviv'):'Лавов',
('RU','Moscow'):'Москва',('RU','Saint Petersburg'):'Санкт Петербург',('GB','London'):'Лондон',('FR','Paris'):'Париз',('DE','Berlin'):'Берлин',
('DE','Hamburg'):'Хамбург',('DE','Frankfurt am Main'):'Франкфурт',('DE','Nuremberg'):'Нирнберг',('DE','Düsseldorf'):'Дизелдорф',('DE','Dresden'):'Дрезден',
('DE','Leipzig'):'Лајпциг',('DE','Stuttgart'):'Штутгарт',('DE','Hanover'):'Хановер',('DE','Hannover'):'Хановер',('DE','Bremen'):'Бремен',
('US','New York City'):'Њујорк',('US','Los Angeles'):'Лос Анџелес',('US','Washington'):'Вашингтон',('US','Chicago'):'Чикаго',('US','San Francisco'):'Сан Франциско',
('HU','Budapest'):'Будимпешта',('RO','Bucharest'):'Букурешт',('BG','Sofia'):'Софија',('RS','Belgrade'):'Белград',('SI','Ljubljana'):'Љубљана',
('SK','Bratislava'):'Братислава',('LU','Luxembourg'):'Луксембург',('GB','Edinburgh'):'Единбург',('ES','Barcelona'):'Барселона',('ES','Madrid'):'Мадрид',
('ES','Seville'):'Севиља',('ES','Valencia'):'Валенсија',('FR','Marseille'):'Марсеј',('FR','Lyon'):'Лион',('FR','Nice'):'Ница',('FR','Strasbourg'):'Стразбур',
('FR','Toulouse'):'Тулуза',('FR','Bordeaux'):'Бордо',('NL','Amsterdam'):'Амстердам',('NL','Rotterdam'):'Ротердам',('NL','Utrecht'):'Утрехт',
('AL','Tirana'):'Тирана',('AL','Durrës'):'Драч',('AL','Shkodër'):'Скадар',('AL','Korçë'):'Корча',('XK','Pristina'):'Приштина',('XK','Prizren'):'Призрен',
('PL','Krakow'):'Краков',('PL','Kraków'):'Краков',('PL','Gdańsk'):'Гдањск',('PL','Wrocław'):'Вроцлав',('PL','Poznań'):'Познањ',('IE','Dublin'):'Даблин',
('NO','Oslo'):'Осло',('FI','Helsinki'):'Хелсинки',('PT','Porto'):'Порто',('HR','Zagreb'):'Загреб',('BA','Sarajevo'):'Сарајево',('ME','Podgorica'):'Подгорица',
('GR','Kerkyra'):'Крф',('GR','Corfu'):'Крф',('AT','Salzburg'):'Салцбург',('AT','Graz'):'Грац',('BE','Ghent'):'Гент',('BE','Bruges'):'Бриж',
('DE','Aachen'):'Ахен',('DE','Mainz'):'Мајнц',('DE','Freiburg'):'Фрајбург',('CH','Basel'):'Базел',('CH','Bern'):'Берн',('CH','Lausanne'):'Лозана',
('US','Houston'):'Хјустон',('US','Seattle'):'Сиетл',('US','Boston'):'Бостон',('CA','Montreal'):'Монтреал',('CA','Toronto'):'Торонто',('CA','Vancouver'):'Ванкувер'}
SRCC={'RS','BA','HR','ME','SI','XK','AL','BG','RU','UA','BY','GR','MK'}
c=list(csv.DictReader(open(W+'names/cities.csv')))
pri=lambda x:(0 if x['cc']=='MK' else 1 if x['stage']=='month' else 2)
c.sort(key=pri)  # stable
bad=re.compile(r'[^A-Za-zČčĆćŠšŽžĐđ \-\.\'’]|[wxyqWXYQ]')
stats={'ov':0,'ru':0,'sr':0,'local':0,'auto':0}
out=[]
for x in c:
    en=x['name_en'];sr=x['name_sr'];note=''
    k=(x['cc'],en)
    if x['cc']=='MK':
        name=x['name_local']; stats['local']+=1
    elif k in OV:
        name=OV[k]; note='exonym'; stats['ov']+=1
    elif (x['cc'] in SRCC or (sr!=en and sr!=x['name_local'])) and not bad.search(sr):
        name=sr2mk(sr); stats['sr']+=1
    elif x['name_ru']:
        name=ru2mk(x['name_ru'],en,x['cc']); note='auto: ru'; stats['ru']+=1
    else:
        name=sr2mk(en); note='auto: en'; stats['auto']+=1
    out.append([x['geonameid'],name,f'во {name}',1,note])
with open(OUT+'cities.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['geonameid','name','in_phrase','decl_ok','note']); w.writerows(out)
print(len(rows),len(out),stats)
