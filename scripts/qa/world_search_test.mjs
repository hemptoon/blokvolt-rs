// SEARCH (12.11.2026): the query set of the search of blokvolt.com (scripts/qa/world_search_queries.json) (static/com/world-search.js over the built index
// dist-com/assets/world/search-<code>.json + -2.json). Step of .github/workflows/preview.yml.
//   node scripts/qa/world_search_test.mjs [dist-com] [--verbose]
// Each line: [language of the page, query, expected, rank] — expected: c:<cc> country, t:<geonameid> city, n:<slug> network,
// p:<key> page (scripts/world_search.py), r:<cc>:<region> region, u:<text> the address of a result contains it, cities>=8:<gid,…>;<name,…> at least
// 8 cities among the results, those gids among the first 12 cities and those names among the first 20. rank 1 = must be the first result (exact names), 3 = in the first three.
// Pass: ≥ 95 % of all queries in the top 3 and 100 % of the rank-1 queries first; the fold of the browser equals the
// fold of the build (the "chk" pairs of the index); the time per query (node, this machine) is printed.
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
const require = createRequire(import.meta.url);
const S = require('../../static/com/world-search.js');
const args = process.argv.slice(2);
const dist = args.find(a => !a.startsWith('--')) || 'dist-com';
const verbose = args.includes('--verbose');
const Q = JSON.parse(fs.readFileSync(new URL('./world_search_queries.json', import.meta.url), 'utf8'));
const cache = {};
function index(l) {
  if (cache[l]) return cache[l];
  const dir = path.join(dist, 'assets', 'world');
  const doc = JSON.parse(fs.readFileSync(path.join(dir, `search-${l}.json`), 'utf8'));
  const I = S.load(doc);
  for (const t of [].concat(doc.tail || [])) S.addTail(I, JSON.parse(fs.readFileSync(path.join(dir, t), 'utf8')));
  I.region = 'eu';
  return (cache[l] = I);
}
function ok(x, e) {
  const r = x.r, [k, v] = [e.slice(0, e.indexOf(':')), e.slice(e.indexOf(':') + 1)];
  if (k === 'u') return (x.url || '').includes(v);
  if (k === 'c') return r[0] === 'c' && r[1] === v;
  if (k === 't') return r[0] === 't' && String(r[1]) === v;
  if (k === 'n') return r[0] === 'n' && !r[7] && String(r[1]).split(',')[0] === v;
  if (k === 'p') return r[0] === 'p' && r[1] === v;
  if (k === 'r') return r[0] === 'r' && r[1] === v;
  return false;
}
let fails = 0, f1 = 0, n1 = 0, top3 = 0, foldBad = 0, worst = 0, total = 0;
for (const l of [...new Set(Q.map(q => q[0]))]) {
  const I = index(l);
  for (const [raw, a, b] of I.doc.chk || []) {
    if (S.words(raw).join(' ') !== a || S.words(raw, true).join(' ') !== b) { foldBad++; console.log('FOLD', l, raw, S.words(raw), a); }
  }
}
for (const [l, q, e, rank] of Q) {
  const I = index(l);
  const t0 = performance.now();
  const res = S.search(I, q).list;
  const dt = performance.now() - t0;
  worst = Math.max(worst, dt); total += dt;
  let pass, pos = -1;
  if (e.startsWith('cities>=8:')) {
    const cities = res.filter(x => x.r[0] === 't');
    const [gids, labels] = e.slice(10).split(';');
    pass = cities.length >= 8 && gids.split(',').every(g => cities.slice(0, 12).some(x => String(x.r[1]) === g)) &&
      (labels || '').split(',').filter(Boolean).every(n => cities.slice(0, 20).some(x => x.r[2] === n));
    pos = pass ? 0 : -1;
  } else {
    pos = res.findIndex(x => ok(x, e));
    pass = pos >= 0 && pos < rank;
  }
  if (rank === 1) { n1++; if (!pass) f1++; }
  if (pos >= 0 && pos < 3) top3++;
  if (!pass) {
    fails++;
    console.log(`FAIL [${l}] "${q}" → want ${e} (rank ${rank}), at ${pos}; got: ` + res.slice(0, 5).map(x => `${x.r[0]}:${x.r[1]} ${x.r[2]}`).join(' | '));
  } else if (verbose) console.log(`ok   [${l}] "${q}" → ${res[0].r[2]}`);
}
const share = top3 / Q.length;
console.log(`world_search_test: ${Q.length} queries, ${Q.length - fails} pass; expected in top 3: ${(100 * share).toFixed(1)} %; ` +
  `exact names first: ${n1 - f1}/${n1}; fold differences: ${foldBad}; time per query avg ${(total / Q.length).toFixed(1)} ms, worst ${worst.toFixed(1)} ms`);
process.exit(share >= 0.95 && f1 === 0 && foldBad === 0 ? 0 : 1);
