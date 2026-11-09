# R-SK — korektúra slovenčiny (10.11.2026)

Nezávislá korektúra prekladu z vetvy `l-sk` (0a407ad). Vetva `r-sk`, jazyk stále nezapnutý (G8).

## Čo sa prešlo
- Reťazce: všetkých 403 (map 125, pages 120, shell 41, prices 117) + texts.json (97).
- Krajiny: všetkých 150 (`name`, `in_phrase`) — bez zmien, všetko správne (na/v/vo, ostrovy s „na“).
- Mestá: všetkých 18 SK a 63 CZ (správne) + prvých 500 miest `stage = month` v poradí súboru
  (places-2026-11-09.json nemá počty miest, len bbox — preto poradie súboru).
- Slugy: ASCII, prirodzené; prefix `/sk/` sa nekríži s `content/com/local/*` (al ba hr me mk xk) ani so svetovými EN/SR/RU.

## Opravy reťazcov — 41
- **Bez „my“:** `r_ok` „Ďakujeme.“ (1. osoba pl.) → „Vďaka za hlásenie.“
- **Pád pri meste (pool 4, `{city_u}`):** `t_city`, `t_city_cc`, `d_city` → „… {city_u}, {country}“ namiesto dvojbodky („Nabíjacie stanice pre elektromobily v Mníchove, Nemecko“). `t_near` „(pri {x})“ dávalo nominatív po „pri“ → „(v okolí: {x})“.
- **Zmysel:** `p_city_cmp` — {city}/{country} sú čísla; „priemer za krajinu ({country_name}) {country}“ → „celoštátny priemer ({country_name}) {country}“.
- **Jednotnosť:** `ch_home` „domov“ → „úvod“ (ako `home`); „O stránke“ → „O projekte“ (ako slug `o-projekte`); `h_chart` „Rýchlonabíjanie“ a texts `dc` → „rýchle nabíjanie“; `no_prices_n` „preverených“ → „overených“; `nav_download` → „Stiahnuť“ (ako `ft_download`).
- **Dĺžka tlačidiel/čipov (≤ EN × 1,4):** `h1` „Mapa nabíjania“, `c_unnamed` „Nabíjacia stanica“, `copied` „Skopírované“, `acc_*_notice_required` „…, s ohlásením vopred“.
- **Štýl:** `about_p` „prehľad“ → „informačný portál“; `p_hub` „s aspoň“ → „s najmenej“; `h_more` „Viac {country_u}“ → „Viac o nabíjaní {country_u}“; `lead_hub` kratšie zátvorky; `mini_alt` doplnené „body“; `odbl_note` „dostupné“.
- **Typografia:** spojovník s medzerami „ — “ → slovenská pomlčka „ – “ vo všetkých sk reťazcoch a texts.json; `pct` „{x} %“ s pevnou medzerou.

## Mestá — 28 opráv
- **Kolín (DE Köln) → „Kolín nad Rýnom“**: holé „Kolín“ koliduje s českým Kolínom v tom istom súbore.
- Doplnený lokál (decl_ok 0 → 1, poznámka `R-SK`): Braunschweig, Bochum, Paderborn, Heilbronn, Mönchengladbach, Landshut, Wuppertal, Koblenz, Trier, Gelsenkirchen, Schwerin, Tübingen, Fürth, Bayreuth, Groningen, Leiden, Perpignan, Brest, Besançon, Caen, Oviedo, Reading; nesklonné správne potvrdené: Tampere, Espoo, Oulu, Mulhouse, La Rochelle.
- decl_ok=1: 541 → 568. Ostatné „rule -burg/-heim/-dorf…“ v top 500 skontrolované, správne (vrátane „vo“ pred W/F/V: vo Wiesbadene, vo Würzburgu, vo Freiburgu).
- Exonymá Brémy, Cáchy, Mohuč, Norimberg, Pasov ponechané (spisovné, používané v slovenskej tlači). Ráb/Päťkostolie/Stoličný Belehrad mimo top 500 — nekontrolované.

## Spätný preklad
- 40 zmenených reťazcov naslepo späť do EN (druhý agent): významový posun 0. Na jeho podnet: „po ohlásení“ → „s ohlásením vopred“ (bolo dvojznačné), `th_home` ponechané „Domácnosť“ (stĺpec = cena elektriny domácností), `c_price_note` „Cena k {d}“, `p_city_cmp` „na každých 10“.

## check.py
- Doplnená ekvivalencia `{city_u}`≈`{city}` a `{country_u}`≈`{country}` (rozhodnutie pool 4, 00:12). Výsledok: 0 chýb, 0 varovaní.

## Sporné / na rozhodnutie
- `home_lead` „Na jednej mape: {n}, {c}, …“ — `pl_cc` nemá lokálový tvar, preto čiarka namiesto „v {c}“. Ak K8 pridá `pl_cc_in`, prepnúť na „{n} v {c}“.
- `p_hub_na`: EN „the Serbian pages cover Europe“ → sk „slovenské stránky pokrývajú Európu“ (logika: jazyk stránky = Európa). Ak má zostať doslovne „srbské“, zmeniť.
- `nav_open`/`k_hub` „Otvorené údaje“ (14 zn. vs 9) — kratší dobrý ekvivalent nie je; ponechané.
- Mestá mimo top 500 s „v meste X“ (decl_ok 0) sú gramaticky bezpečné, len menej prirodzené pri štvrtiach Londýna („v meste Camden Town“).
- glossary.csv stále bez stĺpca `sk` — termíny podľa NOTES.md (nabíjacia stanica / miesto / bod, sieť, prevádzkovateľ) sú konzistentné vo všetkých 403 reťazcoch.
