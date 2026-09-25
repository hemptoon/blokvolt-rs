# BlokVolt — news (/vesti/): what to publish, where to look, how to write

Written for the scheduled Claude sessions that publish news on www.blokvolt.rs, and for anyone checking them.
The procedure (build, translate, deploy, commit) is in `docs/RUNBOOK.md` §3.15; the general voice rules are in
`docs/CONTENT_STYLE.md`. Every rule of RUNBOOK §0 applies here too.

## 1. What a news item is

A short, checkable report that changes something for people who drive or plan to buy an electric car in Serbia:

- subsidies (deadlines, amounts, budget, procedure);
- public charging: new or closed chargers, networks entering or leaving, price changes, the state motorway chargers;
- electricity for home charging: EPS/AERS price or tariff changes, rules for meters and buildings;
- cars: a new model or brand with a Serbian importer, Serbian prices, new sales or service points;
- rules: laws and bylaws on charging, buildings (skupština), tolls, parking, customs and taxes — drafts clearly marked;
- statistics: fleet and registrations (MUP, SAUVD, RZS, ABS);
- the region and the EU, only when it clearly matters for drivers in Serbia (at most one such item per run).

Not news: a press release without facts, rumours, opinions, global tech stories without a Serbian angle, anything
about Evolako or about BlokVolt itself (site changes go to `content/podaci/izmene.md`), and anything that needs
contacting a company (the outreach ban of RUNBOOK §3.7 holds).

Volume follows reality: Serbia has roughly one or two relevant stories a week. A run publishes 0–3 items. When
nothing new and checkable happened, publish nothing and do not deploy.

## 2. Sources

Primary sources first; media for discovery and for statements made to journalists. Never work around a blocked
site (no mirrors, archives or other routes), and never take text from srb.guide or other guides whose terms forbid
rewriting — go to the primary source instead.

Official and primary (no RSS unless stated — open the page):

- Ministry of Environmental Protection (subsidies): https://www.ekologija.gov.rs/saopstenja/vesti
- Službeni glasnik (via Paragraf): https://www.paragraf.rs/glasila/rs/ — the proof that a decree or law was adopted
- Government: https://www.srbija.gov.rs · Ministry of Mining and Energy: https://www.mre.gov.rs
- Ministry of Construction, Transport and Infrastructure (charging-infrastructure law): https://www.mgsi.gov.rs
- EPS news and prices: https://www.eps.rs/lat/vesti · https://www.eps.rs/cir/snabdevanje/Pages/cene.aspx · AERS: https://www.aers.rs
- JP „Putevi Srbije“ chargers: https://www.putevi-srbije.rs/index.php/en/electric-chargers (see RUNBOOK 3.11)
- Statistics: RZS https://www.stat.gov.rs · SAUVD https://www.uvoznicivozila.rs · ABS https://www.abs.gov.rs
- Cities: https://www.beograd.rs/lat/ · https://novisad.rs
- Networks: https://chargego.rs · https://oriontelekom.rs/emobility/ · https://www.omv.rs/sr/mobilnost/elektricni-punjaci ·
  https://www.nisgazprom.rs · https://www.tesla.com/findus/list/superchargers/Serbia · https://edrive.co.rs
- Importers: https://byd-auto.rs/vesti/ · https://www.volkswagen.rs · https://www.renault.rs · https://www.hyundai.rs/vesti ·
  https://www.kia.rs · https://www.mgmotor.rs · https://www.toyota.rs

Media with a working RSS feed (checked 25.09.2026):

- B92 auto: https://www.b92.net/rss/b92/automobili and the EV section https://www.b92.net/rss/b92/automobili/visoki-napon
- Tanjug: https://www.tanjug.rs/rss/ekonomija · https://www.tanjug.rs/rss/srbija
- Nova ekonomija: https://novaekonomija.rs/feed · Danas: https://www.danas.rs/feed/
- Balkan Green Energy News: https://balkangreenenergynews.com/rs/feed/ (Serbian) · https://balkangreenenergynews.com/feed/
- Vrele gume: https://vrelegume.rs/feed/
- electrive (EU): https://www.electrive.com/feed/ · European Commission: https://ec.europa.eu/commission/presscorner/api/rss?language=en

Media without a confirmed feed (open the section page): Energetski portal https://energetskiportal.rs, 021.rs, N1,
RTS, Forbes Srbija, Biznis.rs, Telegraf auto, Mondo „EUpravo zato“ održiva mobilnost, AMSS https://www.amss.org.rs/aktuelnosti.

The site's own data is a source too: when the monthly update changes the price index, the state-charger status or
new-car prices, a short item may report the change and link to the page with the data.

## 3. Checking

- Every number, name and date in the item must be on a page you opened in this run. The page goes into `sources`
  with its date (`Label, DD.MM.YYYY — what it says :: URL`).
- An official announcement on the primary source is enough on its own. A claim found only in the media: prefer two
  independent outlets; with one, say so in the text („prema pisanju portala …“).
- Proposals, drafts, plans and forecasts are named as such („predlog“, „nacrt“, „najava“) and never written as rules.
- Company figures are attributed („po podacima kompanije“).
- Before writing, check `content/vesti/` for an item on the same event. A follow-up is a new item only when there is
  a material new fact; it links to the earlier one.
- If the news changes a fact the site states elsewhere (a subsidy deadline, EPS prices, a charger count, a price),
  update that page in the same run following RUNBOOK §3 — or list it in the report if it cannot be done.

## 4. Writing

Serbian, Latin script, ekavica, addressing the reader as „vi“, impersonal about the site (never „mi“, „redakcija“,
„proverili smo“). Natural, plain, specific.

- **Title**: the fact itself, up to ~75 characters, sentence case, no question, no exclamation, no clickbait.
- **Lead**: one sentence with the main fact, up to ~25 words.
- **Body**: two to four short paragraphs, 120–300 words in all — what happened, who says so, the numbers; then the
  detail a reader needs. Then `## Šta to znači`: one to three sentences on what it means for a driver or buyer in
  Serbia, without speculation. Up to three links to the relevant site pages (map, subsidies, prices), relative paths.
- Numbers exactly as in the source, in Serbian format: 5.000 €, 7,4 kW, 21,7 %, 1.641.333. Prices say „sa PDV-om“ or
  „bez PDV-a“ when the source does. Dates in running text: „9. septembra“ (the year only when it is not obvious).
- Quotes only when the exact words matter: one short sentence, in „…“, with the speaker.
- Vary sentence length. Say a thing once. No announcements of what the item will say, no closing moral.
- Do not use: clichés and PR words (the list in `scripts/lint_sr.py`: „važno je napomenuti“, „ključnu ulogu“,
  „značajan korak“, „revolucija“, „budućnost mobilnosti“, „ostaje da se vidi“ …), „ne samo … već i“, decorative
  lists of three adjectives, rhetorical questions, exclamation marks, emoji, Croatian or ijekavian forms.
- No images from media. No names of the team. No Evolako (neutrality, RUNBOOK §0).

Good (from 09.09.2026):

> Vlada je izmenila uredbu o subvencionisanoj kupovini novih električnih vozila. Izmena je objavljena u Službenom
> glasniku RS broj 86/2026, 9. septembra. Prethodni rok bio je 30. septembar.

Bad — the same news written as filler:

> U današnjem svetu električna vozila igraju ključnu ulogu, a država čini značajan korak ka zelenoj budućnosti:
> rok za subvencije je produžen!

## 5. File format

One file per item: `content/vesti/YYYY-MM-DD-<slug>.md`, the date being the day of the news, the slug short ASCII
Serbian (`rok-za-subvencije-produzen-do-1-decembra`). The URL is `/vesti/<slug>/` — never change a published slug.

```
---
title: Rok za subvencije za električna vozila produžen do 1. decembra
lead: Zahtev za 5.000 € za nov električni automobil može da se podnese do 1. decembra 2026, umesto do 30. septembra.
description: (optional, up to 155 characters; otherwise the lead is used)
date: 09.09.2026            # the day of the news, shown on the site
published: 2026-09-25       # the day the item goes online (JSON-LD, RSS) — today
modified: 2026-09-26        # only after a correction
tag: subvencije             # subvencije | punjaci | cene | modeli | propisi | struja | statistika | region
sources: Label, DD.MM.YYYY — what :: https://… | Label :: https://…
related: /podaci/subvencije-2026/ | /podaci/cene-elektricnih-automobila/
---
Body in Markdown, ending with "## Šta to znači".
```

`related` accepts article paths and the pages listed in `PAGE_NAMES` in `build.py` (add a page there if needed).
A correction to a published item: fix it, set `modified`, add a line to `izmene.md`. An item is never deleted.

`python3 scripts/lint_sr.py content/vesti/<file>.md` must report 0 errors; read the warnings and fix what is real.

## 6. Transparency

`/metodologija/#vesti` says that news texts are prepared with the help of AI tools, under the same rules as the
rest of the site, and that every number is checked in its source before publishing. Keep that true: never publish
a number that was not seen in a source during the run.
