import csv,sys,re; sys.path.insert(0,''+__import__('os').path.dirname(__file__)+''); from loc import *
EX={ # (cc,name_en): (tr name, in_phrase)
('DE','Munich'):('Münih',"Münih'te"),('DE','Cologne'):('Köln',"Köln'de"),('DE','Nuremberg'):('Nürnberg',"Nürnberg'de"),
('DE','Hanover'):('Hannover',"Hannover'de"),('DE','Frankfurt'):('Frankfurt',"Frankfurt'ta"),('DE','Berlin'):('Berlin',"Berlin'de"),
('AT','Vienna'):('Viyana',"Viyana'da"),('CZ','Prague'):('Prag',"Prag'da"),('PL','Warsaw'):('Varşova',"Varşova'da"),
('PL','Krakow'):('Krakov',"Krakov'da"),('PL','Kraków'):('Krakov',"Krakov'da"),('GR','Athens'):('Atina',"Atina'da"),('GR','Thessaloniki'):('Selanik',"Selanik'te"),
('GR','Rhodes'):('Rodos',"Rodos'ta"),('GR','Heraklion'):('Kandiye (Heraklion)',"Kandiye'de (Heraklion)"),('GR','Corfu'):('Korfu',"Korfu'da"),
('GR','Chania'):('Hanya',"Hanya'da"),('GR','Kos'):('İstanköy (Kos)',"İstanköy'de (Kos)"),('GR','Patras'):('Patras',"Patras'ta"),('GR','Larissa'):('Larissa',"Larissa'da"),
('GR','Ioannina'):('Yanya',"Yanya'da"),('GR','Corinth'):('Korint',"Korint'te"),('GR','Rethymno'):('Resmo',"Resmo'da"),('GR','Chalkida'):('Eğriboz (Halkida)',"Eğriboz'da (Halkida)"),
('GR','Kalamata'):('Kalamata',"Kalamata'da"),('GR','Preveza'):('Preveze',"Preveze'de"),
('RS','Belgrade'):('Belgrad',"Belgrad'da"),('RS','Novi Sad'):('Novi Sad',"Novi Sad'da"),('RS','Nis'):('Niş',"Niş'te"),('RS','Niš'):('Niş',"Niş'te"),
('BA','Sarajevo'):('Saraybosna',"Saraybosna'da"),('BA','Mostar'):('Mostar',"Mostar'da"),('MK','Skopje'):('Üsküp',"Üsküp'te"),('MK','Ohrid'):('Ohri',"Ohri'de"),('MK','Bitola'):('Manastır',"Manastır'da"),
('AL','Tirana'):('Tiran',"Tiran'da"),('AL','Durres'):('Dıraç',"Dıraç'ta"),('AL','Durrës'):('Dıraç',"Dıraç'ta"),('AL','Shkoder'):('İşkodra',"İşkodra'da"),('AL','Shkodër'):('İşkodra',"İşkodra'da"),
('XK','Pristina'):('Priştine',"Priştine'de"),('XK','Prizren'):('Prizren',"Prizren'de"),('ME','Podgorica'):('Podgorica',"Podgorica'da"),
('BG','Sofia'):('Sofya',"Sofya'da"),('BG','Plovdiv'):('Filibe (Plovdiv)',"Filibe'de (Plovdiv)"),('BG','Varna'):('Varna',"Varna'da"),('BG','Burgas'):('Burgaz',"Burgaz'da"),
('RO','Bucharest'):('Bükreş',"Bükreş'te"),('RO','Constanta'):('Köstence',"Köstence'de"),('RO','Constanța'):('Köstence',"Köstence'de"),('HU','Budapest'):('Budapeşte',"Budapeşte'de"),
('HR','Zagreb'):('Zagreb',"Zagreb'de"),('HR','Split'):('Split',"Split'te"),('HR','Rijeka'):('Rijeka',"Rijeka'da"),('HR','Dubrovnik'):('Dubrovnik',"Dubrovnik'te"),
('SI','Ljubljana'):('Ljubljana',"Ljubljana'da"),('SK','Bratislava'):('Bratislava',"Bratislava'da"),
('IT','Rome'):('Roma',"Roma'da"),('IT','Milan'):('Milano',"Milano'da"),('IT','Naples'):('Napoli',"Napoli'de"),('IT','Turin'):('Torino',"Torino'da"),
('IT','Florence'):('Floransa',"Floransa'da"),('IT','Venice'):('Venedik',"Venedik'te"),('IT','Genoa'):('Cenova',"Cenova'da"),('IT','Bologna'):('Bologna',"Bologna'da"),
('IT','Palermo'):('Palermo',"Palermo'da"),('IT','Trento'):('Trento',"Trento'da"),('IT','Brixen'):('Brixen',"Brixen'de"),('IT','Eppan'):('Eppan',"Eppan'da"),('IT','Merano'):('Merano',"Merano'da"),
('ES','Seville'):('Sevilla',"Sevilla'da"),('ES','Barcelona'):('Barselona',"Barselona'da"),('ES','Madrid'):('Madrid',"Madrid'de"),('ES','Valencia'):('Valensiya',"Valensiya'da"),
('ES','Malaga'):('Malaga',"Malaga'da"),('ES','Zaragoza'):('Zaragoza',"Zaragoza'da"),('ES','Palma'):('Palma',"Palma'da"),
('PT','Lisbon'):('Lizbon',"Lizbon'da"),('PT','Porto'):('Porto',"Porto'da"),
('FR','Paris'):('Paris',"Paris'te"),('FR','Lyon'):('Lyon',"Lyon'da"),('FR','Marseille'):('Marsilya',"Marsilya'da"),('FR','Nice'):('Nice',"Nice'te"),
('FR','Toulouse'):('Toulouse',"Toulouse'da"),('FR','Strasbourg'):('Strazburg',"Strazburg'da"),('FR','Bordeaux'):('Bordeaux',"Bordeaux'da"),('FR','Lille'):('Lille',"Lille'de"),
('FR','Nantes'):('Nantes',"Nantes'ta"),('FR','Montpellier'):('Montpellier',"Montpellier'de"),
('BE','Brussels'):('Brüksel',"Brüksel'de"),('BE','Antwerp'):('Anvers',"Anvers'te"),('BE','Bruges'):('Brugge',"Brugge'de"),('BE','Ghent'):('Gent',"Gent'te"),('BE','Liege'):('Liège',"Liège'de"),
('NL','Amsterdam'):('Amsterdam',"Amsterdam'da"),('NL','Rotterdam'):('Rotterdam',"Rotterdam'da"),('NL','The Hague'):('Lahey',"Lahey'de"),('NL','Utrecht'):('Utrecht',"Utrecht'te"),
('NL','Eindhoven'):('Eindhoven',"Eindhoven'da"),
('GB','London'):('Londra',"Londra'da"),('GB','Manchester'):('Manchester',"Manchester'da"),('GB','Edinburgh'):('Edinburgh',"Edinburgh'ta"),('GB','Birmingham'):('Birmingham',"Birmingham'da"),
('GB','Glasgow'):('Glasgow',"Glasgow'da"),('GB','Liverpool'):('Liverpool',"Liverpool'da"),('IE','Dublin'):('Dublin',"Dublin'de"),
('CH','Geneva'):('Cenevre',"Cenevre'de"),('CH','Zurich'):('Zürih',"Zürih'te"),('CH','Basel'):('Basel',"Basel'de"),('CH','Bern'):('Bern',"Bern'de"),('CH','Lausanne'):('Lozan',"Lozan'da"),('CH','Lugano'):('Lugano',"Lugano'da"),
('DK','Copenhagen'):('Kopenhag',"Kopenhag'da"),('SE','Stockholm'):('Stockholm',"Stockholm'de"),('SE','Gothenburg'):('Göteborg',"Göteborg'da"),('SE','Malmö'):('Malmö',"Malmö'de"),
('NO','Oslo'):('Oslo',"Oslo'da"),('NO','Bergen'):('Bergen',"Bergen'de"),('FI','Helsinki'):('Helsinki',"Helsinki'de"),('FI','Tampere'):('Tampere',"Tampere'de"),('FI','Turku'):('Turku',"Turku'da"),
('IS','Reykjavík'):('Reykjavik',"Reykjavik'te"),('EE','Tallinn'):('Tallinn',"Tallinn'de"),('LV','Riga'):('Riga',"Riga'da"),('LT','Vilnius'):('Vilnius',"Vilnius'ta"),('LT','Kaunas'):('Kaunas',"Kaunas'ta"),
('LU','Luxembourg'):('Lüksemburg',"Lüksemburg'da"),('RU','Moscow'):('Moskova',"Moskova'da"),('RU','Saint Petersburg'):('St. Petersburg',"St. Petersburg'da"),('RU','Ufa'):('Ufa',"Ufa'da"),('RU','Kazan'):('Kazan',"Kazan'da"),
('UA','Kyiv'):('Kiev',"Kiev'de"),('UA','Odesa'):('Odessa',"Odessa'da"),('UA','Lviv'):('Lviv',"Lviv'de"),('BY','Minsk'):('Minsk',"Minsk'te"),
('CY','Nicosia'):('Lefkoşa',"Lefkoşa'da"),('CY','Limassol'):('Limasol',"Limasol'da"),('CY','Larnaca'):('Larnaka',"Larnaka'da"),
('AZ','Baku'):('Bakü',"Bakü'de"),('GE','Tbilisi'):('Tiflis',"Tiflis'te"),('GE','Batumi'):('Batum',"Batum'da"),('AM','Yerevan'):('Erivan',"Erivan'da"),
('IL','Jerusalem'):('Kudüs',"Kudüs'te"),('IL','Tel Aviv'):('Tel Aviv',"Tel Aviv'de"),('EG','Cairo'):('Kahire',"Kahire'de"),('LB','Beirut'):('Beyrut',"Beyrut'ta"),
('AE','Dubai'):('Dubai',"Dubai'de"),('AE','Abu Dhabi'):('Abu Dabi',"Abu Dabi'de"),('SA','Riyadh'):('Riyad',"Riyad'da"),('QA','Doha'):('Doha',"Doha'da"),
('CN','Beijing'):('Pekin',"Pekin'de"),('CN','Shanghai'):('Şanghay',"Şanghay'da"),('JP','Tokyo'):('Tokyo',"Tokyo'da"),('KR','Seoul'):('Seul',"Seul'de"),
('IN','New Delhi'):('Yeni Delhi',"Yeni Delhi'de"),('IN','Mumbai'):('Mumbai',"Mumbai'de"),('IN','Bengaluru'):('Bengaluru',"Bengaluru'da"),('IN','Delhi'):('Delhi',"Delhi'de"),
('SG','Singapore'):('Singapur',"Singapur'da"),('TH','Bangkok'):('Bangkok',"Bangkok'ta"),
('US','New York City'):('New York',"New York'ta"),('US','New York'):('New York',"New York'ta"),('US','Los Angeles'):('Los Angeles',"Los Angeles'ta"),('US','San Francisco'):('San Francisco',"San Francisco'da"),
('US','Chicago'):('Chicago',"Chicago'da"),('US','Washington'):('Washington',"Washington'da"),('US','Seattle'):('Seattle',"Seattle'da"),('US','Boston'):('Boston',"Boston'da"),('US','Houston'):('Houston',"Houston'da"),
('CA','Toronto'):('Toronto',"Toronto'da"),('CA','Montreal'):('Montreal',"Montreal'de"),('CA','Vancouver'):('Vancouver',"Vancouver'da"),
('AU','Sydney'):('Sidney',"Sidney'de"),('AU','Melbourne'):('Melbourne',"Melbourne'da"),('MX','Mexico City'):('Meksiko',"Meksiko'da"),('BR','Sao Paulo'):('São Paulo',"São Paulo'da"),('BR','São Paulo'):('São Paulo',"São Paulo'da"),
}
SPECIAL_TR={'Kocaeli':"Kocaeli'nde"}
RULE_CC={'TR','DE','AT','IT','ES','HR','RS','BA','SI','ME','FI','CZ','SK','HU'}
LATIN=re.compile(r"^[A-Za-zÀ-ɏ .'\-]+$")
order={'month':1,'quarter':2,'balkan':1}
def loc_de(n):
    import loc as L
    w=lower_tr(n)
    w2=w.replace('ie','i').replace('ei','a').replace('ey','a').replace('ai','a').replace('eu','o').replace('äu','o').replace('ie','i').replace('ä','e')
    vs=[c for c in w2 if c in 'aıoueiöü']; back=vs[-1] in 'aıou'
    cons='t' if w[-1] in L.HARD else 'd'
    return f"{n}'{cons}{'a' if back else 'e'}"
rows=[]
for x in csv.DictReader(open(__import__('os').path.dirname(__file__)+'/../../../../../content/world/names/cities.csv')):
    cc=x['cc']; key=(cc,x['name_en'])
    if key in EX:
        n,ip=EX[key]; ok=1; note='egzonim/yaygın Türkçe ad' if n!=x['name_local'] else ''
    else:
        n = x['name_local'] if LATIN.match(x['name_local'] or '') else (x['name_en'] or x['name_local'])
        if cc=='TR': n=x['name_local']
        simple = re.match(r"^[A-Za-zÀ-ɏ\-]+( [A-Za-zÀ-ɏ\-]+)?$", n) and not re.search(r'[()/.,0-9]',n)
        if n in SPECIAL_TR: ip=SPECIAL_TR[n]; ok=1; note=''
        elif cc in RULE_CC and simple and ' ' not in n and loc(n):
            ip=loc(n) if cc=='TR' else loc_x(n,cc); ok=1; note='kural (ünlü uyumu)' if cc!='TR' else ''
        else:
            ip=f"{n} şehrinde"; ok=0; note='güvenli yapı'
    rows.append((0 if cc=='TR' else order.get(x['stage'],3), x['geonameid'], n, ip, ok, note))
rows.sort(key=lambda r:r[0])
w=csv.writer(open(__import__('os').path.dirname(__file__)+'/../../../../../content/world/i18n/tr/cities.csv','w',newline=''))
w.writerow(['geonameid','name','in_phrase','decl_ok','note'])
for r in rows: w.writerow(r[1:])
import collections
print(len(rows), collections.Counter(r[4] for r in rows), sum(1 for r in rows if r[5].startswith('egz')))
