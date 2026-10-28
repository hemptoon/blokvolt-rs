// Site search regression test (docs/RUNBOOK.md 3.8): the engine of /assets/pretraga.js with MiniSearch and the built indexes
// of dist/ answers ~80 real queries — typos, Cyrillic, towns of the map, synonyms, stop words, the three languages.
// Run after a build: node scripts/qa/pretraga_test.mjs [--show]. Exit 1 on a failed case. No network, no browser.
import { createRequire } from 'module';
import { readFileSync } from 'fs';
const require = createRequire(import.meta.url);
const ROOT = new URL('../../', import.meta.url).pathname;
const MiniSearch = require(ROOT + 'static/assets/vendor/minisearch-7.2.0.min.js');
const B = require(ROOT + 'static/assets/pretraga.js');
const CFG = JSON.parse(readFileSync(ROOT + 'content/data/pretraga.json', 'utf8'));
const SHOW = process.argv.includes('--show');
const idx = {};
for (const l of ['sr', 'en', 'ru']) {
  const docs = JSON.parse(readFileSync(ROOT + 'dist/assets/' + (l === 'sr' ? 'search.json' : `search-${l}.json`), 'utf8'));
  idx[l] = B.create(MiniSearch, docs, { lang: l, syn: CFG.syn, stop: CFG.stop });
}
// [lang, query, expected url (or several: any of them), within the first N results, extra checks]
const CASES = [
  ['sr', 'evolnako', '/firme/evolako/', 1],
  ['sr', 'evolako', '/firme/evolako/', 1],
  ['sr', 'Evolako', '/firme/evolako/', 1],
  ['sr', 'statanet', '/firme/stasanet/', 2],
  ['sr', 'stasanet', '/firme/stasanet/', 1],
  ['sr', 'volbox', ['/wallbox-cena-srbija', '/podaci/wallbox-modeli/'], 3],
  ['sr', 'volboks cena', ['/wallbox-cena-srbija', '/podaci/wallbox-modeli/', '/cena-punjaca-za-elektricni-auto'], 3],
  ['sr', 'tesla', '/javno-punjenje/tesla/', 3, { notTop: '/bezbednost-punjenja-atest' }],
  ['sr', 'teslla', '/javno-punjenje/tesla/', 3],
  ['sr', 'subvencije za auto', '/podaci/subvencije-2026/', 2],
  ['sr', 'subvencija', '/podaci/subvencije-2026/', 2],
  ['sr', 'subvencje', '/podaci/subvencije-2026/', 3],
  ['sr', 'punjač za stan', ['/punjenje-elektricnog-auta-u-zgradi', '/punjac-u-zgradi-skupstina', '/ko-placa-struju-za-punjenje'], 3],
  ['sr', 'punjac u zgradi', ['/punjenje-elektricnog-auta-u-zgradi', '/punjac-u-zgradi-skupstina'], 2],
  ['sr', 'kraljevo', '/gradovi/kraljevo/', 1],   // towns with 3+ chargers have a page since 26.10.2026 (RUNBOOK 3.35)
  ['sr', 'Kraljevo punjač', '/gradovi/kraljevo/', 3],
  ['sr', 'Paraćin', '/gradovi/paracin/', 1],
  ['sr', 'paracin', '/gradovi/paracin/', 1],
  ['sr', 'Нови Сад', '/gradovi/novi-sad/', 1],
  ['sr', 'Novi Sad', '/gradovi/novi-sad/', 1],
  ['sr', 'Beograd', '/gradovi/beograd/', 1],
  ['sr', 'cacak', '/gradovi/cacak/', 1],
  ['sr', 'nis', '/gradovi/nis/', 3],
  ['sr', 'пуњач за стан', ['/punjenje-elektricnog-auta-u-zgradi', '/punjac-u-zgradi-skupstina', '/ko-placa-struju-za-punjenje'], 3],
  ['sr', 'субвенција', '/podaci/subvencije-2026/', 3],
  ['sr', 'chargego', ['/javno-punjenje/chargego/', '/firme/chargego/'], 2],
  ['sr', 'charge&go', '/javno-punjenje/chargego/', 3],
  ['sr', 'charge go', '/javno-punjenje/chargego/', 3],
  ['sr', 'nocna tarifa', '/podaci/tarife-eps/', 2],
  ['sr', 'noćna tarifa', '/podaci/tarife-eps/', 2],
  ['sr', 'brojlo', ['/ko-placa-struju-za-punjenje', '/alati/racun-u-zgradi/', '/punjenje-elektricnog-auta-u-zgradi'], 4],
  ['sr', 'kalkultor', '/alati/kalkulator-troskova/', 2],
  ['sr', 'skupstina stanara', '/punjac-u-zgradi-skupstina', 2],
  ['sr', 'besplatno punjenje', '/javno-punjenje/besplatni-punjaci/', 2],
  ['sr', 'besplatni punjaci', '/javno-punjenje/besplatni-punjaci/', 1],
  ['sr', 'kako da punim auto bez garaže', '/elektricni-auto-bez-garaze', 3],
  ['sr', 'gde da napunim ako parkiram na ulici', '/elektricni-auto-bez-garaze', 3],
  ['sr', 'nemam garažu gde da punim', '/elektricni-auto-bez-garaze', 3],
  ['sr', 'wallbox cena', ['/wallbox-cena-srbija', '/cena-punjaca-za-elektricni-auto'], 2],
  ['sr', 'uvoz auta', '/podaci/uvoz-i-carina/', 2],
  ['sr', 'carina', '/podaci/uvoz-i-carina/', 2],
  ['sr', 'registracija', '/podaci/registracija-i-porezi/', 2],
  ['sr', 'putarina', '/podaci/putarina-i-parking/', 2],
  ['sr', 'osiguranje', '/podaci/osiguranje-elektricnog-automobila/', 2],
  ['sr', 'kredit', '/podaci/krediti-i-lizing/', 2],
  ['sr', 'apk', ['/aplikacija/', '/pomoc/android-aplikacija-apk/'], 2],
  ['sr', 'punjač ne radi', '/pomoc/punjac-ne-radi/', 3],   // 26.10.2026: the motorway network page ("punjači … stanje", which work) is a fair #2
  ['sr', 'orion', '/javno-punjenje/orion-emobility/', 2],
  ['sr', 'lidl', '/javno-punjenje/lidl-echarge/', 1],
  ['sr', 'yesla', '/javno-punjenje/yesla/', 1],
  ['sr', 'xyzqwv', null, 0],
  ['ru', 'эволако', '/ru/firme/evolako/', 1],
  ['ru', 'стасанет', '/ru/firme/stasanet/', 1],
  ['ru', 'тесла', '/ru/javno-punjenje/tesla/', 3, { notTop: '/ru/bezbednost-punjenja-atest' }],
  ['ru', 'зарядка в доме', ['/ru/punjenje-elektricnog-auta-u-zgradi', '/ru/punjac-u-zgradi-skupstina'], 3],
  ['ru', 'субсидии', '/ru/podaci/subvencije-2026/', 2],
  ['ru', 'кралево', '/ru/gradovi/kraljevo/', 3],
  ['ru', 'Нови Сад', '/ru/gradovi/novi-sad/', 2],
  ['ru', 'ночной тариф', '/ru/podaci/tarife-eps/', 4],   // the Russian page says „низкий тариф“; the city pages, „ночной“,
  ['ru', 'evolnako', '/ru/firme/evolako/', 1],
  ['en', 'evolnako', '/en/firme/evolako/', 1],
  ['en', 'home charger apartment', ['/en/punjenje-elektricnog-auta-u-zgradi', '/en/punjac-u-zgradi-skupstina'], 3],
  ['en', 'subsidies', '/en/podaci/subvencije-2026/', 2],
  ['en', 'free charging', '/en/javno-punjenje/besplatni-punjaci/', 2],
  ['en', 'night tariff', '/en/podaci/tarife-eps/', 2],
  ['en', 'kraljevo', '/en/gradovi/kraljevo/', 1],
  // electric cars section (docs/RUNBOOK.md 3.31, 24.10.2026)
  ['sr', 'električni automobili', '/elektricni-automobili/', 1],
  ['sr', 'gde kupiti električni auto', ['/elektricni-automobili/', '/elektricni-automobili/polovni/'], 2],
  ['sr', 'polovni električni automobili', '/elektricni-automobili/polovni/', 1],
  ['sr', 'kupujemprodajem', '/elektricni-automobili/polovni/', 2],
  ['sr', 'byd srbija', '/elektricni-automobili/byd/', 1],
  ['sr', 'tesla srbija', ['/elektricni-automobili/tesla/', '/javno-punjenje/tesla/'], 2],
  ['sr', 'deepal', '/elektricni-automobili/changan/', 2],   // the Deepal S05 model page (29.10.2026) may come first
  ['sr', 'lynk', '/elektricni-automobili/lynk-co/', 1],
  ['sr', 'dolphin surf', '/elektricni-automobili/byd/dolphin-surf/', 1],   // model pages since 29.10.2026 (RUNBOOK 3.32)
  ['sr', 'renault 5 cena', '/elektricni-automobili/renault/renault-5-e-tech/', 1],
  ['sr', 'bmw i5', '/elektricni-automobili/bmw/i5/', 1],
  ['sr', 'byd', '/elektricni-automobili/byd/', 1],   // a brand name still finds the brand page first
  ['en', 'kia ev3 price', '/en/elektricni-automobili/kia/ev3/', 1],
  ['en', 'used electric car', '/en/elektricni-automobili/polovni/', 2],
  ['en', 'electric cars serbia', '/en/elektricni-automobili/', 2],
  ['ru', 'купить электромобиль', ['/ru/elektricni-automobili/', '/ru/elektricni-automobili/polovni/'], 2],
  ['ru', 'подержанный электромобиль', '/ru/elektricni-automobili/polovni/', 2],
  // fuel and electricity (docs/RUNBOOK.md 3.36, 29.10.2026)
  ['sr', 'cena goriva', '/podaci/cena-goriva-i-struje/', 2],
  ['sr', 'cena goriva danas', '/podaci/cena-goriva-i-struje/', 2],
  ['sr', 'cena dizela', '/podaci/cena-goriva-i-struje/', 3],
  ['sr', 'koliko kosta 100 km', ['/podaci/cena-goriva-i-struje/', '/alati/kalkulator-troskova/'], 3],
  ['en', 'fuel prices', '/en/podaci/cena-goriva-i-struje/', 3],
  ['ru', 'цены на бензин', '/ru/podaci/cena-goriva-i-struje/', 3],
];
let bad = 0;
for (const [l, q, want, n, x = {}] of CASES) {
  const t0 = performance.now();
  const r = idx[l].search(q);
  const ms = performance.now() - t0;
  const urls = r.hits.map(h => h.doc.u);
  const wants = want == null ? [] : [].concat(want);
  let ok = want == null ? urls.length === 0 : urls.slice(0, n).some(u => wants.includes(u));
  if (ok && x.fixed && !r.fixed) ok = false;
  if (ok && x.notTop && urls[0] === x.notTop) ok = false;
  if (!ok) bad++;
  if (!ok || SHOW) console.log(`${ok ? 'ok ' : 'BAD'} [${l}] ${q}${r.fixed ? ' → ' + r.fixed.to : ''}${r.maybe ? ' (maybe ' + r.maybe + ')' : ''}: ` +
    urls.slice(0, 4).join(', ') + ` (${urls.length}, ${ms.toFixed(0)} ms)`);
}
const sug = idx.sr.search('evol', { suggest: true }).hits.slice(0, 3).map(h => h.doc.u);
if (!sug.includes('/firme/evolako/')) { bad++; console.log('BAD suggest „evol“:', sug.join(', ')); }
const sug2 = idx.sr.search('kragu', { suggest: true }).hits.slice(0, 3).map(h => h.doc.u);
if (!sug2.includes('/gradovi/kragujevac/')) { bad++; console.log('BAD suggest „kragu“:', sug2.join(', ')); }
console.log(`search: ${CASES.length + 2 - bad}/${CASES.length + 2} cases pass`);
process.exit(bad ? 1 : 0);
