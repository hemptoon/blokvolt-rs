---
id: B2
title: Šta znači „Potvrđeno“ na mapi punjača — i šta ne znači
h1: Šta znači „Potvrđeno“ — i šta ne znači
description: „Potvrđeno“ na mapi BlokVolt znači da je punjač na spisku mreže ili ima skorašnje ocene vozača. Da li radi baš sada, pokazuje poslednja prijava vozača.
lead: Potvrđeno znači da punjač postoji. Ne znači da radi baš sada.
kicker: Pomoć
section: mapa-i-podaci
order: 2
path: /pomoc/sta-znaci-potvrdjeno/
updated: 28.09.2026
related: /pomoc/javite-da-li-punjac-radi/, /pomoc/odakle-su-podaci/, /pomoc/punjac-ne-radi/
shots: svg-potvrdjeno, mapa-kartica-potvrdjeno, mapa-kartica-nije-potvrdjeno, mapa-poslednja-prijava
published: 2026-09-28
modified: 2026-09-28
---
## Pravilo

Na [mapi](/mapa/), u delu „Odakle su podaci na mapi“, opisano je pravilo provere. Svaki punjač je proveren na spiskovima koje mreže same objavljuju: Charge&GO, roming mapa Charge&GO sa punjačima Orion eMobility, Tesla i JP „Putevi Srbije“. Punjači sa tih spiskova kojih nije bilo u otvorenim bazama dodati su na mapu. Ostali su traženi na Google mapama: ako postoje i imaju ocene vozača iz poslednjih godinu dana, računaju se kao potvrđeni. Nekoliko punjača potvrđeno je na sajtu vlasnika lokacije. Sve ostalo nosi oznaku „Nije potvrđeno“: takav punjač možda više ne postoji ili nije javan. Datum provere piše na kartici svakog punjača.

**Potvrđeno znači da punjač postoji. Ne znači da radi baš sada.** Spisak mreže i skorašnja ocena pokazuju da je punjač na tom mestu. Ne pokazuju da li je danas u kvaru, zauzet ili isključen.

<div class="flow" markdown="0">
<p class="fl-h">Kako punjač dobija oznaku</p>
<div class="fl-row">
<div class="fl-b"><b>Spiskovi mreža</b><span>Charge&amp;GO, Tesla, JP „Putevi Srbije“</span></div>
<div class="fl-b"><b>Google mape</b><span>ocena vozača iz poslednjih godinu dana</span></div>
<div class="fl-b"><b>Sajt vlasnika lokacije</b><span>za pojedine punjače</span></div>
</div>
<div class="fl-down" aria-hidden="true"></div>
<div class="fl-row">
<div class="fl-b ok"><b>Potvrđeno</b><span>punjač postoji na tom mestu</span></div>
<div class="fl-b warn"><b>Nije potvrđeno</b><span>samo u otvorenim bazama ili bez skorašnje ocene</span></div>
<div class="fl-b no"><b>Prijavljen kvar</b><span>u skorašnjim recenzijama piše da ne radi</span></div>
</div>
<p class="fl-note"><b>Odvojeno:</b> prijava vozača na kartici pokazuje kako je bilo pri poslednjem punjenju („Poslednja prijava“). Ne menja oznaku ni boju tačke.</p>
</div>

## Šta piše na kartici

- **Potvrđeno**, sa izvorom i datumom provere. Izvor je spisak mreže (Charge&GO, roming mapa Charge&GO, Tesla, JP „Putevi Srbije“), skorašnje ocene vozača na Google mapama ili sajt vlasnika lokacije.
- **Nije potvrđeno**, sa razlogom i datumom provere. Punjač je samo u otvorenim bazama, ili je na Google mapama bez ocene iz poslednjih godinu dana, ili je po spisku mreže u probnom radu.
- **Prijavljen kvar**: vozači u skorašnjim recenzijama pišu da punjač ne radi. Tačka je siva, a u listi stoji znak „!“.

Nepotvrđen punjač je na mapi bled, sa „?“ uz snagu, a u listi ima znak „?“. Prekidač „Potvrđeni“ iznad liste prikazuje samo potvrđene, a red iznad liste tada piše koliko ih je.

[[shot:mapa-kartica-potvrdjeno | Kartica potvrđenog punjača: zeleni okvir sa kvačicom „Potvrđeno na spisku lokacija mreže Charge&GO · 24.09.2026“]]

[[shot:mapa-kartica-nije-potvrdjeno | Kartica sa žutim okvirom „Nije potvrđeno“, razlogom i redom „Provereno 24.09.2026“]]

## Da li radi sada: prijave vozača

Drugi, odvojeni signal je deo „Iskustva vozača“ na kartici. Tu piše poslednja prijava, na primer „Poslednja prijava: Ne radi, pre 2 dana“, zatim prosečna ocena i poslednje prijave sa komentarima.

Vozač bira jedno od četiri stanja: „Radi“, „Radi, uz problem“, „Ne radi“ ili „Nema punjača“. Prijava se vidi odmah posle slanja ([kako se šalje](/pomoc/javite-da-li-punjac-radi/)).

Prijave vozača ne menjaju oznaku „Potvrđeno“ ni boju tačke. Oznaka kaže da punjač postoji, a prijava kako je bilo kad je neko poslednji put punio.

Za državne punjače na autoputevima kartica ima i deo „Stanje punjača“, po spisku JP „Putevi Srbije“ i sa datumom spiska.

[[shot:mapa-poslednja-prijava | Deo „Iskustva vozača“: prosečna ocena, „Poslednja prijava: Radi, pre 2 dana“ i četiri dugmeta stanja (primer)]]

## Korak po korak: pre polaska

1. Uključite „Potvrđeni“ ako vam treba punjač za koji se zna da postoji.
2. Otvorite karticu i pogledajte poslednju prijavu i njen datum.
3. Stanje punjača u trenutku polaska proverite u aplikaciji mreže.
4. Posle punjenja javite kako je bilo, da sledeći vozač ima svežu informaciju.
