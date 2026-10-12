---
title: Gubici pri punjenju: zašto kWh na punjaču nije kWh u bateriji
h1: Gubici pri punjenju
description: Deo struje sa brojila ili punjača ne stigne u bateriju. Koliko se gubi iz utičnice, na wallboxu i na brzom DC punjaču, i kako to uračunati u trošak.
lead: Plaćate struju koju izmeri brojilo ili punjač, a auto prikazuje samo ono što je stiglo u bateriju.
kicker: Vodič
updated: 11.10.2026
next_check: 11.11.2026
path: /gubici-pri-punjenju/
published: 2026-10-11
modified: 2026-10-11
priority: 0.7
sources: ADAC — gubici pri punjenju, AC i DC (izmenjeno 06.08.2026) :: https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/laden/ladeverluste-elektroauto-studie/ | ADAC — gubici na brzom punjaču, saopštenje :: https://presse.adac.de/meldungen/adac-ev/technik/e-auto-am-schnelllader-so-viel-energie-geht-zwischen-ladesaeule-und-akku-verloren.html | ACL Autotouring — AC gubici kod pet modela (ADAC, ACL, FDM) :: https://autotouring.acl.lu/de/laden-bis-zu-24-prozent-stromverlust/ | heise — ADAC studija o efikasnosti punjenja :: https://www.heise.de/hintergrund/ADAC-Studie-zur-Ladeeffizienz-An-der-Steckdose-geht-ueber-ein-Viertel-verloren-11401427.html | Auto Bild — ADAC test 2022, četiri modela :: https://www.autobild.de/artikel/adac-ermittelt-ladeverluste-beim-elektroauto-28135593.html | N1 — ÖAMTC: gubici u ugrađenom punjaču :: https://n1info.hr/magazin/auto/koliko-energije-pri-punjenju-gube-elektricni-automobili/ | Kurir — trošak punjenja u Srbiji i gubici kod kuće :: https://www.kurir.rs/zabava/auto/10026407/cena-punjenja-elektricnog-automobila-u-srbiji | EPS — cene za garantovano snabdevanje od 01.10.2025 :: https://www.eps.rs/lat/snabdevanje/Stranice/cene.aspx | EV Database — VW ID.3 Pro (MY24–26) :: https://ev-database.org/car/2213/Volkswagen-ID3-Pro
---
<div class="sum" markdown="1">
- Iz obične utičnice (2,3 kW) u bateriju ne stigne **12,7–24,2 %** struje sa brojila
- Wallbox na punoj snazi auta (11 ili 22 kW): gubici **5,1–7,0 %**
- Brzi DC punjač: ukupno **5–15 %**, najviše kad auto greje hladnu bateriju
- Putni računar pokazuje potrošnju iz baterije, bez gubitaka; vi plaćate kWh sa brojila ili punjača
- Za **50 kWh** u bateriji iz utičnice treba do oko **66 kWh**, a sa wallboxa oko **54 kWh**
</div>

## Gde se gubi struja

Pri AC punjenju auto sam pretvara naizmeničnu struju u jednosmernu. To radi ugrađeni punjač, koji se pri tome greje.

Dok traje punjenje, rade i elektronika i upravljačke jedinice auta. Što punjenje traje duže, one potroše više.

Deo struje se gubi u kablu i kućnoj instalaciji. Kod DC punjenja struju pretvara sam punjač, ali auto troši struju i na grejanje ili hlađenje baterije.

<details markdown="1">
<summary>Detalji: od čega se sastoje gubici</summary>

- **Ugrađeni punjač:** po ÖAMTC-u, pretvaranje struje gubi oko 7–9 %. Ceo lanac pri AC punjenju gubi oko 10 %.
- **Elektronika auta:** upravljački sistemi tokom punjenja troše do 300 W, po ADAC testu iz 2022.
- **Kućna instalacija:** nemačka norma DIN VDE 0100 dozvoljava do 4 % gubitka.
- **Kabl:** kabl do utičnice treba da bude što kraći, jer se i u njemu gubi struja.

</details>

## Kod kuće: utičnica ili wallbox

Iz obične utičnice auto puni sporo, pa elektronika radi dugo. Zato su tu gubici najveći.


![Dva električna auta u garaži kuće: jedan se puni iz obične šuko utičnice, drugi sa crnog wallboxa](https://d8j0ntlcm91z4.cloudfront.net/user_3FM7Qei6HMfZNdHxGMvPdz3BwTf/hf_20261011_230324_22266e41-2890-4c7e-aea4-139d2077fb76.png)

| Način punjenja | Snaga | Ne stigne u bateriju |
|---|---|---|
| Obična (šuko) utičnica | 2,3 kW | 12,7–24,2 % |
| Wallbox, smanjena snaga | oko 4 kW | 8,0–12,8 % |
| Wallbox, puna snaga auta | 11 ili 22 kW | 5,1–7,0 % |

Utičnicu koristite kao rezervu. Za redovno punjenje wallbox je bezbedniji i troši manje struje za isti kWh u bateriji.

<details markdown="1">
<summary>Detalji: rezultati po modelu</summary>

- **Utičnica:** Mercedes CLA 350 EQ 24,2 %, VW ID.7 15,3 %, Volvo EX30 14,2 %, Renault 5 E-Tech 13,7 %, Tesla Model Y 12,7 %.
- **Mercedes CLA 350 EQ:** 24,2 % iz utičnice, 12,8 % na oko 4 kW i 6,9 % na wallboxu od 11 kW. Iz utičnice puni sa 8 A umesto 10 A.
- **Uslovi merenja:** punjenje od 10 do 90 %, temperatura baterije na početku 20–30 °C.
- **Smanjena snaga** simulira punjenje viškom struje sa solarnih panela. Izvori navode 4,1 ili 4,2 kW.
- **Razlika u izvorima:** heise za wallbox od 11 kW navodi 5,1–10,6 %, a za 22 kW 5,1–7,0 %.
- **Test iz 2022, utičnica → wallbox 11 kW:** Renault Zoe 24,2 → 9,7 %, Tesla Model 3 15,2 → 7,7 %, VW ID.3 13,6 → 9,0 %, Fiat 500e 12,7 → 6,3 %.
- **Procena za Srbiju (Kurir):** kod kućnog punjenja gubici su najčešće oko 8–15 %. Pri veoma sporom punjenju i na hladnoći mogu da budu i veći.

</details>

## Na brzom DC punjaču

Na DC punjaču struju pretvara sam punjač. U proseku se pri tome gubi oko 3 %. Ukupni gubici su 5–15 %.


![VW ID.3 na brzom DC punjaču na odmorištu uz auto-put po hladnom zimskom jutru, sa injem na autu](https://d8j0ntlcm91z4.cloudfront.net/user_3FM7Qei6HMfZNdHxGMvPdz3BwTf/hf_20261011_230323_f842bfce-27e6-4a3d-92d0-883163a847df.png)

Najviše zavisi od temperature baterije. Topla baterija gubi 1–4 %, a hladna 6–10 %, jer je auto prvo greje strujom sa punjača. Tu struju plaćate.

Uključite predgrevanje baterije navigacijom do punjača. Tada se deo energije za grejanje potroši iz baterije još u vožnji. Kako se plaća javno punjenje: [jeftinije javno punjenje](/javno-punjenje/kako-jeftinije-puniti/).

<details markdown="1">
<summary>Detalji: gubici u autu po modelu</summary>

| Model | 23 °C, predgrejano | 0 °C, predgrejano | 0 °C, bez predgrevanja |
|---|---|---|---|
| Hyundai Ioniq 6 | 1 % | 1 % | 6 % |
| Renault Mégane E-Tech | 4 % | 6 % | 8 % |
| Tesla Model Y | 3 % | 4 % | 10 % |
| VW ID.3 | 3 % | 5 % | 7 % |

- Svaki auto je napunjen sa 30 kWh. Grejanje baterije na punjaču dodaje 2–8 % gubitaka.
- Baterija se greje na početku punjenja, snagom od više kilovata.

</details>

## Kako to uračunati u trošak

Putni računar prikazuje samo potrošnju za vožnju. Gubitke pri punjenju ne vidi, a vi ih plaćate.

Računica: kWh sa brojila = kWh u bateriji ÷ (1 − gubitak). Za 50 kWh u bateriji:

| Način | Gubitak | Sa brojila |
|---|---|---|
| Utičnica, najlošiji model | 24,2 % | oko 66 kWh |
| Utičnica, najbolji model | 12,7 % | oko 57,3 kWh |
| Wallbox, puna snaga | 7,0 % | oko 53,8 kWh |

Zimi punite odmah posle vožnje, dok je baterija još topla. Trošak na 100 km: [kalkulator troškova](/alati/kalkulator-troskova/).

<details markdown="1">
<summary>Detalji: cena struje i kapacitet baterije</summary>

- **EPS, zelena zona, niža tarifa:** 2,4034 RSD/kWh, bez akcize i PDV-a. Cenovnik važi od 1. oktobra 2025.
- **Po toj ceni:** 66 kWh košta oko 159 RSD, a 53,8 kWh oko 129 RSD. To je samo aktivna energija, a na račun se dodaju pristup mreži, naknade i porezi.
- **Kapacitet:** ukupni i upotrebljivi kapacitet se razlikuju. VW ID.3 Pro (2024–2026) ima 63 kWh ukupno i 59 kWh upotrebljivo. Za računicu koristite upotrebljivi kapacitet.
- **ADAC, 15 modela:** potrošnja na putnom računaru i struja na punjaču razlikovale su se za 10–25 %.

</details>

## NOTES (za proveru)

Datum pristupa za sve izvore: 11.10.2026.

**Kućno AC punjenje (ADAC 2026)**
- 12,7–24,2 % iz utičnice: Je nach Modell verschwinden zwischen 12,7 und 24,2 Prozent der Energie, die am Zähler gemessen wurde, bevor sie die Batterie erreicht. → https://autotouring.acl.lu/de/laden-bis-zu-24-prozent-stromverlust/; CLA na primarnoj stranici: Die höchsten Ladeverluste an der Steckdose weist der Mercedes CLA EQ mit 24,2 Prozent auf. → https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/laden/ladeverluste-elektroauto-studie/
- 5,1–7,0 % na wallboxu najveće snage: Beim Laden mit der maximal möglichen AC-Leistung von 11 oder 22 kW lagen die Ladeverluste der untersuchten Fahrzeuge zwischen 5,1 und 7,0 Prozent. → https://www.e-mobileo.de/ladeverluste-wallbox/ (sekundarni). **Neslaganje:** An einer 11-kW-Wallbox lagen die Verluste bei den getesteten Fahrzeugen zwischen 5,1 und 10,6 Prozent, an einer 22-kW-Wallbox bei 5,1 bis 7,0 Prozent. → heise. Tabelu na adac.de proveriti ručno.
- 8,0–12,8 % pri smanjenoj snazi: liegen die Verluste zwischen 8 und 12,8 Prozent → ACL. Snaga: ACL navodi einer Wallbox mit einer reduzierten Leistung von 4,1 kW, a autoflotte Selbst wenn die Ladeleistung auf 4,2 kW begrenzt wird. Zato u tekstu stoji „oko 4 kW“.
- Rezultati po modelu: Der Tesla Model Y kam auf 12,7 Prozent, der Renault R5 E-Tech auf 13,7 Prozent, der Volvo EX30 auf 14,2 Prozent und der VW ID.7 auf 15,3 Prozent. → heise. CLA 24,2 / 12,8 / 6,9 % i „22 kW nije moguće“ → adac.de (tabela).
- CLA, 8 A: das Bordladegerät des CLA lädt nur mit 8 Ampere statt mit den sowieso schon geringen 10 Ampere → adac.de
- Uslovi merenja: Die Messungen erfolgten jeweils im SoC-Fenster von 10 bis 90 Prozent bei einer Starttemperatur der Batterie zwischen 20 und 30 Grad Celsius. → heise
- Utičnica kao rezerva, wallbox bezbedniji: Die Haushaltssteckdose sollte eine Behelfs- oder Notfalllösung bleiben. Für den regelmäßigen Gebrauch ist die Wallbox nicht nur sicherer, sondern auch deutlich effizienter. → ACL

**Test iz 2022. i uzroci gubitaka**
- Vrednosti iz 2022. i norma za instalaciju: Zulässig sind in der Hausinstallation laut ADAC bis zu vier Prozent Ladeverluste, so die Norm DIN VDE 0100. Tabele za utičnicu i wallbox → https://www.autobild.de/artikel/adac-ermittelt-ladeverluste-beim-elektroauto-28135593.html
- 300 W: Samo pri punjenju kontrolni sustavi troše do 300 W. → https://www.index.hr/auto/clanak/punjenje-automobila-na-kucnoj-uticnici-donosi-velike-gubitke-evo-i-zasto/2396416.aspx (sekundarni izvor, 2022; nije provereno na adac.de)
- Kabl: Erhebliche Verluste messen die Techniker auch im Kabel, das daher möglichst kurz sein sollte. → https://www.heise.de/news/E-Auto-Untersuchung-des-ADAC-zeigt-grosse-Unterschiede-bei-Ladestromverlusten-10418882.html
- ÖAMTC: ti gubici pretvorbe u OBC-u iznosili su oko sedam do devet posto, ovisno o kvaliteti i učinkovitosti punjača vozila. Kada bi uzeli u obzir cijeli lanac gubitaka u procesu, studija pokazuje da postoje gubici punjenja od oko deset posto kada se puni izmjeničnom strujom. → https://n1info.hr/magazin/auto/koliko-energije-pri-punjenju-gube-elektricni-automobili/ (2022)
- Srbija, Kurir: Kod kućnog punjenja gubici se najčešće kreću približno od 8 do 15 odsto → https://www.kurir.rs/zabava/auto/10026407/cena-punjenja-elektricnog-automobila-u-srbiji (procena, ne merenje)

**DC punjenje (ADAC)**
- 3 % u punjaču, 2–8 % na grejanje: Die Umwandlungsverluste in der Schnellladesäule betrugen durchschnittlich 3 Prozent. Das Heizen der Batterien an der Ladesäule hatte zusätzliche Energieverluste von 2 bis 8 Prozent zur Folge. → adac.de
- 30 kWh po autu: Jedes Auto wurde während des Tests mit 30 kWh geladen → adac.de
- Tabela po modelu i ukupno 5–15 %: Alles zusammen genommen betragen die Energieverluste beim DC-Laden zwischen 5 und 15 Prozent. → adac.de
- Topla i hladna baterija, plaća kupac, predgrevanje: So sind bei warmer Batterie die Ladeverluste mit einem bis vier Prozent recht gering. Bei niedrigen Temperaturen und kalter Batterie steigen die Ladeverluste im Fahrzeug jedoch auf sechs bis zehn Prozent, da die kalte Batterie aufgeheizt werden muss. Diese Energie stammt aus der Ladesäule, landet aber nicht in der Batterie – der Kunde bezahlt sie dennoch. Wird die Batteriekonditionierung bereits während der Fahrt zur Ladesäule durchgeführt, fallen zwar beim Ladevorgang weniger Verluste an, da die benötigte Energie schon vorher aus der Batterie entnommen wurde. → https://presse.adac.de/meldungen/adac-ev/technik/e-auto-am-schnelllader-so-viel-energie-geht-zwischen-ladesaeule-und-akku-verloren.html

**Trošak i kapacitet**
- Putni računar: Sie zeigen lediglich den Verbrauch für den Antrieb an – Verluste beim Ladevorgang bleiben unberücksichtigt, müssen aber mitbezahlt werden → https://ecomento.de/2020/07/23/adac-ermittelt-elektroauto-ladeverluste/; 15 modela, 10–25 %: Ergebnis: Je nach Fahrzeug weichen die Angaben zehn bis 25 Prozent voneinander ab. → https://www.electrive.net/2020/07/23/ladeverluste-laut-adac-oft-hoeher-als-angegeben/ (2020)
- Zimi puniti odmah posle vožnje: Im Winter sollte möglichst gleich nach Fahrtende aufgeladen werden, solange die Batterie noch warm ist. → https://www.notebookcheck.com/ADAC-untersucht-Ladeverluste-bei-E-Autos-So-viel-Energie-geht-beim-Laden-verloren.653666.0.html (2022, prenosi ADAC)
- EPS cena: cenovnik koji se primenjuje od 01.10.2025. godine (cene su iskazane bez akcize i PDV) → https://www.eps.rs/lat/snabdevanje/Stranice/cene.aspx. Iznos 2,4034 RSD/kWh preuzet je iz sekundarnog izvora: 2,4034 RSD/kWh u nižoj tarifi zelene zone → https://ceneizakon.rs/cena-struje-u-srbiji-2026/. **Iznos proveriti u PDF odluci na eps.rs.** Dodatne stavke: Na to se dodaju pristup mreži, naknade i PDV. → https://www.ozon.rs/vestisrbija/2025/detaljan-cenovnik-struje-po-tarifama-i-zonama-od-1-oktobra/
- ID.3 Pro: Nominal Capacity · 63.0 kWh, upotrebljivo 59,0 kWh → https://ev-database.org/car/2213/Volkswagen-ID3-Pro
- Računica (moja, nije iz izvora): 50 ÷ (1 − 0,242) = 65,96 kWh; 50 ÷ 0,873 = 57,27 kWh; 50 ÷ 0,93 = 53,76 kWh. Cena: 65,96 × 2,4034 ≈ 158,5 RSD i 53,8 × 2,4034 ≈ 129,3 RSD. ADAC računa gubitak kao procenat struje sa brojila, pa je formula „÷ (1 − gubitak)“ ispravna.

**Nije provereno ili nije uneto**
- Nije pronađen srpski primarni izvor sa merenjem gubitaka. Jedini domaći izvor je procena Kurira.
- Nije potvrđeno gde stoji brojilo na srpskim DC punjačima i da li kWh na računu Charge&GO znači energiju na izlazu iz punjača. Zato o tome u tekstu nema ničega. Charge&GO naplaćuje po minutu prema postojećoj BlokVolt vesti: Charge&GO, the largest network of public chargers in Serbia, bills charging by the minute, according to the charger's power. → https://www.blokvolt.rs/en/vesti/cena-brzog-punjenja-43-79-rsd-po-kwh/
- Da li 22 kW donosi manje gubitke od 11 kW (Volvo EX30): odlomak ACL-a je prekinut, pa podatak nije unet.
- Stranicu adac.de video sam samo delimično. Pre objave proveriti celu tabelu AC gubitaka (kolone za 11 kW i 22 kW).
- `path: /gubici-pri-punjenju/` je izveden iz zadatog sluga. Proveriti da li stranica treba da stoji pod /vodici/ ili /javno-punjenje/. Ključ `image` je izostavljen jer naziv slike nije zadat.
- Interni linkovi /javno-punjenje/kako-jeftinije-puniti/ i /alati/kalkulator-troskova/ preuzeti su iz uzorka vodiča. Proveriti da li postoje.
