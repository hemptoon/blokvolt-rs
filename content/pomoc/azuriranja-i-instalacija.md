---
id: B13
title: Ažuriranja i problemi pri instalaciji aplikacije
h1: Ažuriranja i problemi pri instalaciji
description: Kako se ažurira aplikacija BlokVolt i šta da uradite kad Android blokira APK, Chrome ili Play Protect upozore, instalacija ne uspe ili se vidi adresna traka.
lead: Cene, mapa i vesti ažuriraju se same, zajedno sa sajtom. Nova verzija APK fajla retko treba; kad je bude, pojaviće se na stranici Aplikacija i instalira se preko postojeće.
kicker: Pomoć
section: aplikacija
scope: web
order: 3
path: /pomoc/azuriranja-i-instalacija/
updated: 28.09.2026
related: /pomoc/android-aplikacija-apk/, /pomoc/iphone-i-racunar/, /pomoc/kontakt/
shots: aplikacija-verzija, android-upozorenje-chrome, android-play-protect, offline-stranica
published: 2026-09-28
modified: 2026-09-28
---
## Kako stižu ažuriranja

Aplikacija prikazuje sajt, pa se nove cene, punjači i vesti vide odmah, bez ažuriranja. Isto važi za ikonicu na iPhone-u i računaru.

Novu verziju samog APK fajla retko treba instalirati. Kad je bude, pojaviće se na stranici [Aplikacija](/aplikacija/), sa brojem verzije i datumom u dnu stranice. Na dan 28.09.2026 tu piše „Verzija 1.0.0 · objavljena 25.09.2026“.

Aplikacija ne šalje obaveštenja, pa za novu verziju ne stiže poruka.

Za ažuriranje preuzmite novi fajl i instalirajte ga preko postojećeg; staru verziju ne treba brisati. Svaka verzija je potpisana istim sertifikatom. Omiljeni punjači su u memoriji pregledača, a ne u samoj aplikaciji.

[[shot:aplikacija-verzija | Dno stranice Aplikacija: „Verzija 1.0.0 · objavljena 25.09.2026 · Prijavite grešku“]]

## Česti problemi

**Telefon ne dozvoljava instalaciju.** Android traži dozvolu za instaliranje aplikacija iz pregledača. Otvorite Podešavanja → Aplikacije → pregledač kojim ste preuzeli fajl, na primer Chrome → Instaliranje nepoznatih aplikacija, i uključite dozvolu. Nazivi se razlikuju od telefona do telefona; na Androidu 5–7 opcija se zove „Nepoznati izvori“ i nalazi se u bezbednosnim podešavanjima.

**Chrome upozorava da fajl može da ošteti uređaj.** Chrome tako upozorava za svaki APK fajl. Proverite SHA-256 ([kako](/pomoc/android-aplikacija-apk/)) i izaberite da ipak zadržite fajl.

**Play Protect upozorava na nepoznatu aplikaciju.** Aplikacija nije iz Google Play, pa je Play Protect ne poznaje. Ako se SHA-256 slaže, otvorite detalje upozorenja i izaberite instalaciju; aplikacija ne traži nijednu dozvolu.

[[shot:android-upozorenje-chrome | Upozorenje Chrome-a pri preuzimanju APK fajla, sa dugmetom za zadržavanje fajla]]

[[shot:android-play-protect | Upozorenje Play Protect-a pri instalaciji, sa otvorenim detaljima i opcijom za instalaciju]]

**„Aplikacija nije instalirana“.** Najčešće je fajl preuzet samo delimično ili je Android stariji od 5.0. Preuzmite fajl ponovo. Ako piše da je paket u konfliktu sa postojećim, na telefonu je aplikacija istog imena potpisana drugim ključem: obrišite je i instalirajte fajl sa sajta.

**Gore se vidi adresna traka.** Aplikacija tada radi kao obična kartica pregledača. Ažurirajte Chrome ili instalirajte pregledač koji podržava ovu vrstu aplikacija.

**Nema interneta.** Stranice koje ste nedavno otvorili rade i bez veze, a za ostale se prikazuje „Nema internet veze“. Prijave vozača i fotografije šalju se samo uz vezu.

[[shot:offline-stranica | Stranica „Nema internet veze“ u aplikaciji, na srpskom, engleskom i ruskom]]

## Google Play

Objava u Google Play je u pripremi; do tada je fajl sa sajta ista aplikacija.

## Šta da pošaljete

Ako problem ostane, pišite na hello@blokvolt.com:

- model telefona i verziju Androida;
- pregledač i njegovu verziju;
- tačan tekst poruke ili snimak ekrana;
- da li se SHA-256 fajla slaže sa brojem na stranici Aplikacija.
