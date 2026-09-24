---
title: Prijavite ispravku ili dodajte firmu
h1: Ispravka ili nova firma
description: Netačna cena, zastareo uslov, punjač koji ne postoji ili firma koje nema u registru: pošaljite ispravku kroz formu ili na hello@blokvolt.com. Greška se ispravlja u roku od nekoliko dana.
kicker: O sajtu · ispravke
lead: Grešku u podacima, punjač koji nedostaje ili firmu koje nema u registru prijavite kroz formu ili e-mailom.
updated: 24.09.2026
path: /ispravka/
published: 2026-09-22
modified: 2026-09-24
priority: 0.4
---
<div class="sum" markdown="1">
- Greška se ispravlja **u roku od nekoliko dana**
- Upis nove firme je **besplatan**
- Predstavljate firmu ili mrežu? Koristite [stranu za firme](/za-firme/)
</div>

<form class="bform" data-bv-form="ispravka" novalidate>
<div class="field"><label for="f-sta">Šta ispravljate</label><select class="select" id="f-sta" name="sta"><option value="firma">Podatak o firmi</option><option value="mreza">Mreža javnog punjenja ili cena punjenja</option><option value="stanica">Punjač na mapi (ne postoji, ne radi, pogrešno mesto)</option><option value="novi-punjac">Punjač koji nedostaje na mapi</option><option value="tekst">Tekst ili vodič</option><option value="drugo">Drugo</option></select></div>
<div class="field"><label for="f-gde">Stranica, firma ili punjač</label><input class="input" id="f-gde" name="gde" maxlength="300" placeholder="Link na stranicu ili naziv"></div>
<div class="field"><label for="f-poruka">Šta nije tačno ili šta se promenilo</label><textarea class="input" id="f-poruka" name="poruka" rows="5" maxlength="3000" required></textarea></div>
<div class="field"><label for="f-izvor">Izvor (link, nije obavezno)</label><input class="input" id="f-izvor" name="izvor" maxlength="500" placeholder="https://"><span class="hint">Podatak bez javnog izvora objavljujemo tek kad ga proverimo.</span></div>
<div class="field"><label for="f-mail">E-mail za odgovor (nije obavezno)</label><input class="input" id="f-mail" name="email" type="email" maxlength="120" autocomplete="email"></div>
<input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
<p class="bform-act"><button class="btn dark" type="submit">Pošalji ispravku</button></p>
<p class="f-msg f-ok" role="status" hidden>Hvala! Ispravka je primljena i biće proverena u roku od nekoliko dana.</p>
<p class="f-msg f-need" role="alert" hidden>Napišite šta nije tačno.</p>
<p class="f-msg f-err" role="alert" hidden>Slanje nije uspelo. Pokušajte ponovo ili pišite na hello@blokvolt.com.</p>
<p class="f-msg f-limit" role="alert" hidden>Previše poruka danas. Pišite na hello@blokvolt.com.</p>
</form>

## Šta napisati

1. Link na stranicu sa greškom, naziv firme ili punjača.
2. Šta nije tačno ili šta se promenilo.
3. Izvor: link na javnu stranicu sa novim podatkom, ako postoji.

Umesto forme možete pisati i na **hello@blokvolt.com**. Za punjač na mapi najbrže je da na kartici punjača javite da li radi — ta prijava se vidi odmah.

## Nova firma ili uklanjanje

Za upis u registar pošaljite naziv, sajt i grad firme. Pravila su ista za sve. Firma može da traži uklanjanje svog unosa bez objašnjenja.

Svaka ispravka se beleži u [dnevniku izmena](/izmene/).
