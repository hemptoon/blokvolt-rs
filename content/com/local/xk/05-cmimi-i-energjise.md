---
key: electricity
slug: cmimi-i-energjise/
order: 5
nav: Çmimi i rrymës
icon: bolt
priority: 0.85
title: Çmimi i rrymës në Kosovë 2026 – kWh ditën dhe natën (ZRRE, KESCO) | BlokVolt
description: Kilovat-ora për familjet me TVSH 8 %: natën 4,2 centë dhe ditën 9,8 centë deri në 800 kWh në muaj, më shtrenjtë mbi 800 kWh. Orët e tarifës së ulët dhe karikimi i veturës.
kicker: Rryma për familjet
h1: Çmimi i rrymës në Kosovë në vitin 2026 për familjet
lead: Sa paguan një familje për një kilovat-orë rrymë te KESCO, furnizuesi me shërbim universal, sipas tarifave të ZRRE-së — ditën dhe natën, deri dhe mbi 800 kWh në muaj, me TVSH — dhe sa kushton karikimi i veturës elektrike në shtëpi.
card: Kilovat-ora ditën dhe natën deri dhe mbi 800 kWh, orët e tarifës së ulët dhe karikimi i veturës natën.
checked: 10.11.2026
checked_iso: 2026-11-10
related: home, prices, map
---
{% set P = C.power %}
{% set E = C.electricity %}
{% set tu = P.tariffs|selectattr('id', 'equalto', 'tu800')|first %}
{% set tl = P.tariffs|selectattr('id', 'equalto', 'tl800')|first %}
{% set tu2 = P.tariffs|selectattr('id', 'equalto', 'tu_mbi800')|first %}
{% set tl2 = P.tariffs|selectattr('id', 'equalto', 'tl_mbi800')|first %}
<div class="sum" markdown="1">
- **{{ num(tu.allin * 100, 2) }} centë** për kWh natën (tarifa e ulët) deri në 800 kWh në muaj, me TVSH {{ P.vat }} %
- **{{ num(tl.allin * 100, 2) }} centë** ditën (tarifa e lartë), pra ditën rryma është mbi **dy herë më e shtrenjtë**
- Mbi 800 kWh në muaj: **{{ num(tu2.allin * 100, 2) }}** natën dhe **{{ num(tl2.allin * 100, 2) }} centë** ditën
- **{{ money(tu.allin * 18.7) }}** rrymë për 100 km natën, deri në 800 kWh
</div>

## Çmimi i kilovat-orës për familjet

| Tarifa | Pa TVSH | Me TVSH |
|---|---|---|
{% for t in P.tariffs %}
| {{ t.name }} | {{ num(t.price, 2) }} | **{{ num(t.allin * 100, 2) }}** |
{% endfor %}

Çmimet janë në centë euro për kWh. {{ P.note }}

- **Blloqet.** {{ P.blocks }} {{ P.night_conflict }}
- **Tarifa fikse.** Mbi çmimin e kWh, fatura ka edhe një tarifë fikse mujore, sipas medias {{ money(P.fixed.v) }} në muaj (më parë {{ money(P.fixed.prev) }}). Ajo paguhet edhe pa veturë, prandaj nuk hyn në çmimin e kWh. Shuma nuk është konfirmuar në faqet e ZRRE-së ose të KESCO-s.
- **Viti 2026.** ZRRE-ja i miratoi në maj 2026 të hyrat e KOSTT-it, KEDS-it dhe KESCO-s pa ndryshuar çmimet për konsumatorët, kështu që vlejnë ende tarifat nga 01.05.2025.

## Kur është rryma më e lirë

{{ P.nt_hours }}

Dallimi mes ditës dhe natës vlen për matësit që i regjistrojnë veçmas orët e tarifës së lartë dhe të ulët. Karikimi i veturës mund të vendoset me kohëmatës në veturë ose në karikues, që të nisë kur fillon tarifa e ulët.

## Sa kushtojnë 100 kWh

| Konsumi në muaj | Natën | Ditën |
|---|---|---|
| Deri në 800 kWh | {{ money(tu.allin * 100) }} | {{ money(tl.allin * 100) }} |
| Mbi 800 kWh | {{ money(tu2.allin * 100) }} | {{ money(tl2.allin * 100) }} |

## Karikimi i veturës elektrike natën

Shembull: në bateri hyjnë 40 kWh, rreth 235 km me konsum prej 17 kWh për 100 km. Për shkak të humbjeve gjatë karikimit (rreth 10 %), nga matësi merren 44 kWh. Kjo kushton:

- natën, deri në 800 kWh: **{{ money(tu.allin * 44) }}** (ditën {{ money(tl.allin * 44) }});
- natën, mbi 800 kWh: **{{ money(tu2.allin * 44) }}** (ditën {{ money(tl2.allin * 44) }}).

Për {{ num(1200) }} km në muaj vetura merr nga matësi rreth 224 kWh: natën kjo kushton {{ money(tu.allin * 224.4) }} deri në 800 kWh dhe {{ money(tu2.allin * 224.4) }} mbi 800 kWh.

Këto 224 kWh i shtohen konsumit të shtëpisë dhe mund ta çojnë familjen mbi 800 kWh në muaj. Natën kilovat-ora mbi 800 kWh është rreth {{ ((tu2.allin / tu.allin - 1) * 100)|round|int }} % më e shtrenjtë, prandaj ia vlen të ndiqet konsumi i zakonshëm i shtëpisë në faturat e KESCO-s. Llogaritja për veturën tuaj: [kalkulatori i karikimit në shtëpi]({{ PAGES.home.path }}).

<details markdown="1"><summary>Si është llogaritur</summary>

- **Çmimi me TVSH:** çmimi pa TVSH × 1,08. Natën deri në 800 kWh: {{ num(tu.price, 2) }} × 1,08 = {{ num(tu.allin * 100, 4) }} centë.
- **Çmimet pa TVSH** janë marrë nga mediat, sepse tabela e vendimit V_2703_2025 të ZRRE-së është publikuar si imazh; orët e tarifave dhe TVSH-ja 8 % janë nga faqja e KESCO-s.
- **Blloku mbi 800 kWh:** nuk është sqaruar zyrtarisht nëse çmimi i bllokut të dytë vlen vetëm për kWh mbi 800; llogaritjet më lart e marrin çmimin e bllokut për të gjitha kWh e veturës.
- **Tarifa fikse mujore** nuk hyn në çmimin e kWh.
- **Vetura:** 17 kWh për 100 km dhe 10 % humbje gjatë karikimit, pra 18,7 kWh nga matësi për 100 km.

</details>

## Pyetje të shpeshta

<details markdown="1">
<summary>Sa kushton një kilovat-orë rrymë në Kosovë në vitin 2026?</summary>

Me TVSH 8 %, deri në 800 kWh në muaj: {{ num(tu.allin * 100, 2) }} centë natën dhe {{ num(tl.allin * 100, 2) }} centë ditën. Mbi 800 kWh: {{ num(tu2.allin * 100, 2) }} centë natën dhe {{ num(tl2.allin * 100, 2) }} centë ditën. Fatura ka edhe tarifë fikse mujore.

</details>

<details markdown="1">
<summary>Në cilat orë është rryma më e lirë?</summary>

Nga 1 tetori deri më 31 mars prej orës 22:00 deri në 07:00, kurse nga 1 prilli deri më 30 shtator prej orës 23:00 deri në 08:00.

</details>

<details markdown="1">
<summary>A ndryshuan çmimet e rrymës në vitin 2026?</summary>

Jo. Në maj 2026 ZRRE-ja i la të pandryshuara tarifat e KESCO-s për familjet, kështu që vlejnë çmimet nga 01.05.2025.

</details>

<details markdown="1">
<summary>Sa kushton karikimi i veturës elektrike në shtëpi?</summary>

Për 100 km duhen rreth 18,7 kWh nga matësi. Natën kjo kushton {{ money(tu.allin * 18.7) }} deri në 800 kWh në muaj dhe {{ money(tu2.allin * 18.7) }} mbi 800 kWh; ditën {{ money(tl.allin * 18.7) }} dhe {{ money(tl2.allin * 18.7) }}.

</details>

## Burimet dhe kontrolli

Çmimet u kontrolluan më {{ E.checked }} në faqet e ZRRE-së dhe të KESCO-s; çmimet pa TVSH janë nga mediat. Kontrolli i radhës: {{ E.next_check }}.

{{ w.sources(E.sources) }}
