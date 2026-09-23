---
title: Bezbedno punjenje u garaži: zašto ne produžni kabl i šta je atest
h1: Bezbednost punjenja i atest
description: Zašto šuko utičnica i produžni kabl nisu za punjenje auta, šta mora da ima namenska linija (FID tip A + DC, SRPS HD 60364-7-722) i šta se meri u atestu.
lead: Auto se bezbedno puni na namenskoj liniji sa FID zaštitom i atestom, a ne na običnoj utičnici.
kicker: Vodič
updated: 07.09.2026
published: 2026-09-08
modified: 2026-09-08
priority: 0.8
path: /bezbednost-punjenja-atest.html
sources: SRPS HD 60364-7-722 — Električne instalacije niskog napona, posebni zahtevi za napajanje električnih vozila (Institut za standardizaciju Srbije) :: https://iss.rs/ | SRPS HD 60364-6 — Električne instalacije niskog napona, verifikacija (ispitivanje) (iss.rs) :: https://iss.rs/ | Pravilnik o tehničkim normativima bezbednosti garaža od požara, „Sl. glasnik RS“ 31/2024 i 59/2025 :: https://pravno-informacioni-sistem.rs/eli/rep/sgrs/ministarstva/pravilnik/2024/31/2 | Zagrevanje šuko utičnica pri dugotrajnom punjenju (emobilitysimplified.com) :: https://www.emobilitysimplified.com/2019/10/ev-charging-basics-can-you-charge-your-electric-car-using-a-household-socket.html | Vodič profesionalnog upravnika: zasebna linija, ovlašćeni izvođač, atest (aleksic.xyz) :: https://www.aleksic.xyz/odrzavanje-zgrade/investiciono-odrzavanje/punjaci-elektricna-vozila-garazi/
---
<div class="sum" markdown="1">
- Opasno nije punjenje, nego **obična šuko utičnica**: na 16 A, posle pola sata neprekidnog punjenja, zagreje se do **~100 °C**
- Bezbedna instalacija: **zaseban krug**, pravi presek kabla, **FID tip A sa DC detekcijom od 6 mA** ili tip B i industrijska utičnica ili wallbox
- **Atest** je izveštaj o ispitivanju instalacije; tražite ga od svakog ko vam ugrađuje punjač
</div>

## Zašto ne obična utičnica

Šuko utičnica od 16 A pravljena je za kratka opterećenja: usisivač, grejalicu, alat. Punjač vuče 10–16 A neprekidno, satima. Kontakti se greju, opruge popuštaju, kontakt slabi i greje se još više.

Punjač u autu može da propusti jednosmernu (DC) struju curenja. Obična FID sklopka tip AC tu struju ne vidi. Veća DC komponenta može i da je „zaslepi“, pa ne štiti ni ostatak kruga.

Mobilni punjač iz auta nije problem, nego utičnica iza njega. Na industrijskoj utičnici i namenskoj liniji sa ispravnom zaštitom isti kabl radi bezbedno svake noći.

<details markdown="1">
<summary>Detalji: produžni kabl i kabl kroz hodnik</summary>

- Produžni kabl, naročito namotan na kalem, greje se sam od sebe.
- Na dugom kablu pada napon, pa punjač radi na ivici.
- Kabl kroz hodnik smeta u prolazu, stoji na vratima i vuče struju sa brojila za koje niko ne zna čije je.

</details>

## Šta mora da ima namenska linija

Spisak propisuje standard SRPS HD 60364-7-722 i važi za svaki punjač, ma od koga ga kupili.

- **Zaseban strujni krug** od razvodne table, samo za punjač.
- **Kabl odgovarajućeg preseka** za snagu i dužinu.
- **Automatski osigurač** prema snazi punjača.
- **FID tip A od 30 mA sa DC detekcijom od 6 mA** (RDC-DD) ili **FID tip B**. Tip AC nije prihvatljiv.
- **Uzemljenje** i provera petlje kvara.
- **Industrijska utičnica (CEE) ili fiksni wallbox**, IP44 ili više. Ne šuko i ne „pojačana šuko“.

<details markdown="1">
<summary>Detalji: preseci, osigurači i dodatna oprema</summary>

- Presek za 11 kW je tipično 5×2,5 do 5×6 mm², a za monofaznu utičnicu 3×2,5 do 3×4 mm². Presek raste sa dužinom, jer se računa pad napona, a ne samo struja.
- Osigurač je 16 A za 11 kW trofazno ili 3,7 kW monofazno, a 32 A za 22 kW ili 7,4 kW.
- Prenaponska zaštita je preporučena, naročito uz stariju instalaciju. Štiti i punjač i auto.

</details>

<details markdown="1">
<summary>Čeklista pre ugradnje</summary>

Pitajte izvođača:

- ime i licencu;
- da li u ponudi piše zaseban krug, FID zaštita (u tabli ili u punjaču), presek i dužina kabla;
- šta je na kraju linije: industrijska utičnica ili wallbox, ne šuko;
- da li je atest u ceni i da li ga dobijate na dan ugradnje;
- ima li garancije na radove, ne samo na uređaj, i ko dolazi kad ne radi, za koliko dana;
- gde je MID brojilo, ako struja nije vaša: [ko plaća struju](/ko-placa-struju-za-punjenje).

</details>

## Atest

Atest je uobičajen naziv za **izveštaj o ispitivanju električne instalacije**. Njime ovlašćeni izvođač, uz kalibrisane instrumente, potvrđuje da je instalacija izvedena i izmerena po propisima. Ako firma ne može da izda atest, to je već odgovor.

Atest je dokaz za zgradu i vlasnika garaže, osnov za osiguranje u slučaju štete i uslov garancije proizvođača punjača.

<details markdown="1">
<summary>Detalji: šta se meri i kako izgleda</summary>

Ispitivanje ide po SRPS HD 60364-6. Za liniju punjača meri se i proverava:

- neprekidnost zaštitnog provodnika, od table do utičnice;
- otpor izolacije provodnika;
- impedansa petlje kvara, da osigurač u kvaru isključi dovoljno brzo;
- FID sklopka: struja i vreme isključenja;
- otpor uzemljenja, polaritet i funkcionalni test punjača.

Merenja traju 30–60 minuta i rade se odmah po ugradnji, a dokument dobijate isti dan. U njemu piše ko je ispitivao, šta, gde, kada i kojim instrumentima, sa rezultatima, zaključkom i potpisom. Bez toga nije atest, nego papir.

</details>

## Propisi i zima

Mesta za punjenje u garažama uređuje i Pravilnik o tehničkim normativima bezbednosti garaža od požara („Sl. glasnik RS“ 31/2024 i 59/2025). Punjenje je uređeno, ne zabranjeno: traži namensku instalaciju i zaštitu. Paušalne zabrane nemaju uporište, a nemaju ga ni produžni kablovi kroz hodnik.

Zimi deo energije ide na grejanje baterije, pa je punjenje na maloj snazi (utičnica 2,3–3,7 kW) osetno sporije. Wallbox od 11 kW te gubitke svodi na minimum.

<details markdown="1">
<summary>Detalji: provera pred zimu</summary>

Zimi punjač radi najviše, a kontakti se termički najviše naprežu. Zato jednom godišnje, pred sezonu, ima smisla proveriti dotegnutost spojeva u tabli i na utičnici, testirati FID sklopku dugmetom „T“ i pregledati kabl i utikač.

</details>

## Česta pitanja

<details markdown="1"><summary>Šta je FID tip B i da li mi treba?</summary>FID tip B detektuje jednosmerne struje curenja bilo koje veličine. Treba samo ako punjač nema ugrađenu DC detekciju od 6 mA (RDC-DD). Većina savremenih wallbox uređaja je ima, pa je dovoljan FID tip A, a tip B je nekoliko puta skuplji.</details>

<details markdown="1"><summary>Hoće li wallbox od 11 kW da izbija osigurače u stanu?</summary>Ne, ako ima dinamičko upravljanje snagom: senzor na priključku vidi koliko domaćinstvo troši i smanji punjenje kad se uključe šporet, bojler i drugi veliki potrošači. Koliko snage priključka ostaje za auto, vidi se na proceni.</details>

<details markdown="1"><summary>Treba li mi osiguranje od odgovornosti?</summary>Nije obaveza, ali je razuman odgovor na pitanje skupštine „ko odgovara“: [procedura sa skupštinom](/punjac-u-zgradi-skupstina). Polisa odgovornosti za štetu trećim licima košta manje nego što se misli.</details>
