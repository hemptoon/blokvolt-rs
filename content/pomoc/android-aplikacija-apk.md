---
id: B11
title: Android aplikacija (APK): instalacija i provera fajla
h1: Android (APK): instalacija i provera
description: Kako da instalirate aplikaciju BlokVolt za Android iz APK fajla (1,2 MB, Android 5.0 ili noviji) i da proverite SHA-256 fajla na Windows-u, Mac-u i telefonu.
lead: Preuzmite APK sa stranice Aplikacija, dozvolite instalaciju iz pregledača i pritisnite „Instaliraj“. Pre instalacije SHA-256 fajla možete da uporedite sa brojem na sajtu.
kicker: Pomoć
section: aplikacija
order: 1
path: /pomoc/android-aplikacija-apk/
updated: 28.09.2026
related: /pomoc/azuriranja-i-instalacija/, /pomoc/iphone-i-racunar/, /pomoc/privatnost/
shots: apk-preuzimanje, android-dozvola-instalacije, android-instaliraj, apk-za-proveru-fajla
published: 2026-09-28
modified: 2026-09-28
---
## Korak po korak

1. Na telefonu otvorite stranicu [Aplikacija](/aplikacija/) i pritisnite „Preuzmi APK“ (1,2 MB). Ako ste na računaru, skenirajte QR kod sa te stranice kamerom telefona.
2. Ako telefon pita, dozvolite instalaciju iz pregledača kojim ste preuzeli fajl. To podešavanje posle možete da isključite.
3. Otvorite preuzeti fajl blokvolt.apk i pritisnite „Instaliraj“.
4. Ikonica BlokVolt pojavljuje se među aplikacijama. Dugim pritiskom na nju otvarate prečice za mapu, cene i vesti.

[[shot:apk-preuzimanje | Stranica Aplikacija na telefonu: dugme „Preuzmi APK 1,2 MB“ i oznake „Bez reklama“, „Bez dozvola“, „Android 5.0 ili noviji“]]

[[shot:android-dozvola-instalacije | Android podešavanje za instaliranje nepoznatih aplikacija, za Chrome, sa uključenom dozvolom]]

[[shot:android-instaliraj | Sistemski prozor Androida za instalaciju aplikacije BlokVolt, sa dugmetom „Instaliraj“]]

Potreban je Android 5.0 ili noviji i Chrome ili drugi pregledač koji podržava ovu vrstu aplikacija. Aplikacija ne traži nijednu dozvolu i otvara www.blokvolt.rs preko celog ekrana.

## Provera fajla (SHA-256)

Na stranici Aplikacija, u delu „Za proveru fajla“, stoje paket i verzija, „SHA-256 fajla“ i „SHA-256 sertifikata kojim je potpisan“. Na dan 28.09.2026 verzija je 1.0.0 (1). SHA-256 fajla menja se sa svakom verzijom, pa ga uvek uzmite sa te stranice.

Izračunajte SHA-256 preuzetog fajla:

- **Windows** (Command Prompt): `certutil -hashfile %USERPROFILE%\Downloads\blokvolt.apk SHA256`; u PowerShell-u: `Get-FileHash $HOME\Downloads\blokvolt.apk`.
- **Mac** (Terminal): `shasum -a 256 ~/Downloads/blokvolt.apk`.
- **Android:** instalirajte aplikaciju za proveru heš vrednosti fajla (u prodavnici aplikacija potražite „SHA-256“), izaberite algoritam SHA-256 i fajl blokvolt.apk iz fascikle Preuzimanja.

Ako je dobijeni broj isti kao „SHA-256 fajla“ na stranici, fajl je isti kao na sajtu. Velika i mala slova nisu bitna.

[[shot:apk-za-proveru-fajla | Otvoren deo „Za proveru fajla“ na stranici Aplikacija: paket i verzija, SHA-256 fajla i SHA-256 sertifikata]]

<details markdown="1">
<summary>Detalji: provera sertifikata</summary>

Sertifikat pokazuje ko je potpisao fajl i isti je za sve verzije, pa se nova verzija instalira preko postojeće. Na dan 28.09.2026 SHA-256 sertifikata je:

`AA:62:B4:08:E9:FA:69:4E:FB:89:57:99:8E:29:FF:93:4C:6F:DF:CA:71:CA:32:75:F8:B0:0D:82:EE:6A:17:21`

Sa alatom apksigner iz Android SDK: `apksigner verify --print-certs blokvolt.apk`. U redu „certificate SHA-256 digest“ treba da stoji isti broj, bez dvotačaka.

</details>

## Ako ne pomogne

- Broj se ne slaže: ne instalirajte fajl. Obrišite ga, preuzmite ponovo samo sa www.blokvolt.rs/aplikacija/ i proverite još jednom. Ako se i dalje ne slaže, javite na hello@blokvolt.com.
- Chrome ili Play Protect upozoravaju na fajl, ili instalacija ne uspeva: [Ažuriranja i problemi pri instalaciji](/pomoc/azuriranja-i-instalacija/).
- U Google Play aplikacije još nema; objava je u pripremi. Do tada je fajl sa sajta ista aplikacija.
