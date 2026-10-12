```markdown
---
title: Provera baterije polovnog EV: SoH, test i garancija
h1: Kako proveriti bateriju polovnog EV
description: SoH pokazuje koliko je kapaciteta baterije ostalo. Normalne vrednosti po kilometraži, test u Srbiji i garancija od 8 godina i 70 %.
lead: Kod polovnog električnog auta stanje baterije govori više od kilometraže i godišta.
kicker: Vodič
updated: 11.10.2026
next_check: 11.11.2026
path: /provera-baterije-polovnog-ev/
published: 2026-10-11
modified: 2026-10-11
priority: 0.7
sources: SuperTest — SOH polovnog električnog auta :: https://supertest.rs/polovni-elektricni-automobili-da-li-se-kupovina-isplati-ili-je-rizik-prevelik/ | ADAC — kupovina polovnog električnog auta, preporučene SoH vrednosti :: https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/elektroauto/elektroautos-gebraucht-kaufen-2026/ | Kurir — ADAC pravilo za kapacitet baterije :: https://biznis.kurir.rs/novcanik/10127763/kako-proveriti-stanje-polovnog-elektricnog-automobila | Geotab — studija zdravlja baterija, 22.700 vozila :: https://www.geotab.com/blog/ev-battery-health/ | Geotab — saopštenje, brzo punjenje i degradacija :: https://www.geotab.com/press-release/ev-battery-health-degradation-fast-charging-study/ | Mobilni mali servis — pregled pre kupovine i AVILOO test (12.000 RSD) :: https://mobilnimaliservis.rs/provera-automobila-pre-kupovine | Volkswagen Srbija — garantni list :: https://www.volkswagen.rs/servis-i-oprema/servis/garancija/garantni-list | Porsche Finder Srbija — garancija HV baterije :: https://finder.porsche.com/rs/sr-RS/details/porsche-taycan-4-cross-turismo-polovan-EPEE0E | Bloomberg Adria — garancije na baterije :: https://rs.bloombergadria.com/politika/opste/64271/baterije-za-elektricna-vozila-koliko-traju-i-imaju-li-garanciju/news | AutoInfo — provere pre kupovine električnog polovnjaka :: https://autoinfo.rs/voznja-na-struju/sta-sve-moze-da-se-pokvari-na-elektricnom-vozilu/
---
<div class="sum" markdown="1">
- **SoH** je procenat preostalog kapaciteta baterije u odnosu na novu. Nije isto što i procenat napunjenosti na instrument tabli
- Orijentir ADAC-a: najmanje **88 %** na **100.000 km** i **80 %** na **200.000 km**
- Prosečan gubitak: **2,3 %** godišnje, oko **81,6 %** kapaciteta posle **8 godina**
- Nezavisni AVILOO test u Beogradu: **12.000 RSD**, rezultat za nekoliko minuta
- Garancija je obično **8 godina ili 160.000 km**, uz najmanje **70 %** kapaciteta
</div>

## Šta pokazuje SoH

SoH od 90 % znači da baterija ima približno 90 % prvobitnog kapaciteta. Domet pada u istoj meri. Auto koji je kao nov imao realnih 200 km, sa 80 % kapaciteta prelazi oko 160 km.

Mnogi električni auti ne prikazuju tačan SoH. Stariji Nissan Leaf, na primer, ima posebne crtice na instrument tabli.

<details markdown="1">
<summary>Detalji: odakle dolazi broj</summary>

- SoH u autu je procena sistema za upravljanje baterijom (BMS). Specijalizovani servis može da očita BMS, a često i greške i odstupanja između ćelija.
- U servisnoj knjižici ne mora da postoji podatak o trenutnom kapacitetu baterije.
- **Tesla:** od softvera 2025.8.3 test se pokreće preko Controls > Service > Battery Health. Auto mora da bude priključen na AC punjač do 16 sati. Ažuriranje 2025.26 uklonilo je test na delu vozila.
- AVILOO samostalno računa SoH, umesto da preuzme vrednost iz auta.

</details>

## Koji SoH je normalan

Preporuka ADAC-a za polovne aute:

- **50.000 km:** najmanje **92 %**
- **100.000 km:** najmanje **88 %**
- **150.000 km:** najmanje **84 %**
- **200.000 km:** najmanje **80 %**

Vrednost znatno ispod ove može da ukaže na prekomerno starenje ili problem sa ćelijama. SoH nije jedini pokazatelj: važne su i greške, rad pod opterećenjem i normalno punjenje.

<details markdown="1">
<summary>Detalji: koliko baterije gube u praksi</summary>

- Geotab je analizirao više od 22.700 vozila, 21 model: prosečan gubitak je 2,3 % godišnje.
- Uz često DC punjenje iznad 100 kW gubitak je do 3,0 % godišnje, a uz AC i slabije punjenje oko 1,5 %. Kako se puni jeftinije: [javno punjenje](/javno-punjenje/kako-jeftinije-puniti/).
- U toplijim krajevima baterije gube oko 0,4 % godišnje više nego u blažoj klimi.
- Oko 10.000 testova u Švedskoj, 2022–2026: Kia e-Niro 64 kWh posle više od 100.000 km ima prosečno 97,25 %, VW ID.3 58 kWh 91,79 %.
- SoH od 90 do 95 % uglavnom je veoma dobar. Od 80 do 90 % ne mora da bude problem, naročito za kraće gradske vožnje.

</details>

## Kako izmeriti pre kupovine

- **Meni auta:** besplatno, ali to je procena samog auta.
- **Dijagnostika u servisu:** čitanje BMS-a, grešaka i odstupanja između ćelija.
- **AVILOO Flash test:** uređaj se priključuje na OBD priključak, a rezultat stiže za 3 minuta. U Beogradu samostalan test košta 12.000 RSD.


![Uređaj za test baterije priključen na OBD priključak polovnog VW ID.3 u servisu u Beogradu](https://d8j0ntlcm91z4.cloudfront.net/user_3FM7Qei6HMfZNdHxGMvPdz3BwTf/hf_20261011_230522_e0e7000a-e67e-4322-9f62-8c3ec58dffab.png)

Test zakažite pre kapare, uz saglasnost prodavca.

<details markdown="1">
<summary>Detalji: kako teče test</summary>

- Za Flash test baterija treba da bude napunjena na 50 %. Rezultat je gotov za tri do pet minuta.
- Sertifikat daje rezultat u kWh i procentima SoH, nezavisno od proizvođača.
- Kod Premium testa baterija se tokom sedam dana vozi od pune do oko 10 %.
- Pre testa se proverava da li je vozilo podržano.
- Pregled vozila pre kupovine u Beogradu, 120+ tačaka sa dijagnostikom, košta od 6.000 RSD.

</details>

## Garancija na bateriju

Većina proizvođača daje osam godina ili 160.000 km. Za VW u Srbiji rok teče od isporuke. Postepen pad kapaciteta nije kvar, dok ne padne ispod 70 % korisnog kapaciteta.

Proverite da li garancija na bateriju još važi i da li prelazi na novog vlasnika.

<details markdown="1">
<summary>Detalji: razlike po markama</summary>

- **Volkswagen:** garancija ne važi kod nepravilnog korišćenja, rukovanja ili održavanja, posebno punjenja.
- **Porsche:** najmanje 80 % neto kapaciteta do 3 godine ili 60.000 km, zatim 70 % do kraja garancije.
- **Tesla:** ulazni modeli sa zadnjim pogonom 8 godina ili 160.000 km, verzije Long Range i Performance 192.000 km.
- **Hyundai Ioniq EV:** stariji model imao je garanciju od osam godina ili 200.000 km.
- **EU, Euro 7:** za automobile najmanje 80 % do pet godina ili 100.000 km i 72 % do osam godina ili 160.000 km.

</details>

## Pre nego što platite

- Pitajte da li je baterija menjana ili popravljana i koliko često je auto punjen na DC punjačima.
- Pregledajte podvozje i kućište baterije. Posle jačeg udara oštećenje ćelija, kablova ili hlađenja može da se javi tek posle više nedelja ili meseci.
- Kod redovno servisiranog auta tražite izveštaje ovlašćenog servisa o stanju baterije.
- Nalaz testa je argument za nižu cenu ili za odustajanje.


![Pregled kućišta baterije sa donje strane polovnog Hyundai Kona Electric na dizalici u servisu](https://d8j0ntlcm91z4.cloudfront.net/user_3FM7Qei6HMfZNdHxGMvPdz3BwTf/hf_20261011_230523_0cb4bde1-d798-4863-a59e-aaef1f3c6939.png)

## NOTES (za proveru)

Datum pristupa za sve: 11.10.2026.

- SoH definicija, 90 % = ~90 % kapaciteta, nije % napunjenosti, primer 200 → 160 km, Leaf crtice, mnogi auti ne prikazuju SoH, servisna knjižica, tumačenje 90–95 % / 80–90 % → https://supertest.rs/polovni-elektricni-automobili-da-li-se-kupovina-isplati-ili-je-rizik-prevelik/
- ADAC 92/88/84/80 % na 50/100/150/200 hiljada km → https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/elektroauto/elektroautos-gebraucht-kaufen-2026/ (isto na srpskom: https://biznis.kurir.rs/novcanik/10127763/kako-proveriti-stanje-polovnog-elektricnog-automobila); „znatno ispod = prekomerno starenje ili problem ćelija" → https://www.auto-motor-und-sport.de/tech-zukunft/alternative-antriebe/adac-test-so-stark-altern-die-phev-batterien-von-mercedes-vw-bmw-co/ (Napomena: tamo je reč o testu PHEV baterija, a preporuka se odnosi na polovne aute uopšte. Proveriti da li formulacija važi i za BEV.)
- Geotab 2,3 %/god, 81,6 % posle 8 god → https://www.geotab.com/blog/ev-battery-health/ ; 22.700 vozila, 21 model → https://www.act-news.com/news/real-world-data-ev-batteries/ ; DC >100 kW do 3,0 % naspram ~1,5 % i klima +0,4 % → https://finance.yahoo.com/news/geotab-data-points-modest-rise-141059571.html (prenosi Geotabovo saopštenje: https://www.geotab.com/press-release/ev-battery-health-degradation-fast-charging-study/)
- Carla, Švedska: ~10.000 testova, e-Niro 97,25 %, ID.3 58 kWh 91,79 % → https://www.sparneuwagen.de/news/e-auto-akku-nach-100-000-km-diese-modelle-haben-noch-bis-zu-97-prozent (sekundarni izvor, original Carla nije proveren)
- AVILOO u Beogradu 12.000 RSD, provera podrške vozila, pregled od 6.000 RSD → https://mobilnimaliservis.rs/provera-automobila-pre-kupovine — **NIJE PROVERENO da li je cena sa PDV-om ili bez.** Proveriti i da li u Srbiji još neko nudi AVILOO.
- AVILOO: OBD, 3 minuta, kWh i % SoH → https://www.emilfrey.si/storitve/test-baterije-elektricnih-vozil/ ; baterija na 50 %, 3–5 minuta → https://www.delo.si/magazin/avtomobilno/hitri-test-ki-vam-pove-resnico-o-bateriji ; Premium 7 dana, od punog do ~10 % → https://www.futurez.fi/en/shop/devices-accessories/electric-car-accessories/aviloo-premium-ev-electric-car-battery-test/ ; nezavisni proračun SoH → https://www.am-online.com/r/dg36kxg8
- Dijagnostika BMS-a u servisu → supertest.rs (isti URL kao gore)
- Tesla test: 2025.8.3, Controls > Service > Battery Health, do 16 h na AC → https://www.shop4tesla.com/en/blogs/news/tesla-battery-health-test-update ; uklonjen na delu vozila u 2025.26 → https://www.notateslaapp.com/news/2988/tesla-quietly-removes-battery-health-test-for-many-in-update-202526 (Nema zvaničnog izvora Tesle. Trenutno stanje funkcije posle 2025.26 nije provereno.)
- Garancija 8 god / 160.000 km / 70 % (većina) → https://autoklub.net/baterije-elektricna-vozila-savjeti-trajanje-zamjena/ i https://rs.bloombergadria.com/politika/opste/64271/baterije-za-elektricna-vozila-koliko-traju-i-imaju-li-garanciju/news
- VW Srbija: 8 god od isporuke ili 160.000 km, 70 % korisnog kapaciteta, izuzeci (punjenje) → https://www.volkswagen.rs/servis-i-oprema/servis/garancija/garantni-list (Garantni list se odnosi na vozila kupljena kod ovlašćenih prodavaca Porsche SCG. **Nije provereno da li važi za polovne aute iz uvoza.**)
- Porsche 80 % do 3 god / 60.000 km, zatim 70 % → https://finder.porsche.com/rs/sr-RS/details/porsche-taycan-4-cross-turismo-polovan-EPEE0E
- Tesla 160.000 / 192.000 km, Hyundai Ioniq EV 8 god / 200.000 km → Bloomberg Adria (isti URL kao gore). **Članak je iz 2024. Proveriti aktuelne uslove kod Tesle.**
- Euro 7: 80 % do 5 god / 100.000 km, 72 % do 8 god / 160.000 km → https://esgnews.com/euro-7-agreement-stricter-emission-rules-for-eu-road-transport/ (Uredba (EU) 2024/1257. **Nisu provereni datumi primene, a ni da li i kako važi u Srbiji.** Zato u tekstu stoji samo „EU".)
- Prenosivost garancije → https://emobilnost.rs/vodic-za-kupovinu-polovnih-elektricnih-automobila-u-srbiji/
- Pitanja prodavcu (zamena baterije, DC punjenje) → https://deloovi.com/kupovina-polovnog-elektricnog-vozila-sta-treba-proveriti/ ; oštećenje posle udara → https://autoinfo.rs/voznja-na-struju/sta-sve-moze-da-se-pokvari-na-elektricnom-vozilu/ ; izveštaji ovlašćenog servisa → Kurir (isti URL kao gore); nalaz kao argument za cenu → mobilnimaliservis.rs (isti URL kao gore)
- Nije uneto, jer nije potvrđeno izvorom za Srbiju: cena OBD adaptera i aplikacija (Car Scanner, LeafSpy), cena dijagnostike u ovlašćenim servisima u Srbiji, cena zamene baterije u Srbiji, DEKRA/TÜV testovi u Srbiji.
- Ključ `image` je izostavljen jer nije poznat odgovarajući naziv slike. Dodati ručno.
- Nije uneto, jer je izvor slab (speedme.ru/hr): švedski uzorak od 8.200 AVILOO testova sa prosekom 93,7 %.
```
