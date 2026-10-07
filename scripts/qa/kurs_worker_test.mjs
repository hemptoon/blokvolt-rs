// GET /api/kurs — the display currency's exchange rate (docs/RUNBOOK.md 3.29): the real worker/_worker.js in Miniflare
// (workerd) with an in-memory D1, the Cloudflare cache, and kurs.resenje.org answered by this script (nothing leaves the
// machine). Checks the answer's format and headers, the cache, the last good value in D1 (stale), the fallback constants,
// the sanity bounds, parity, CORS preflight and the worker without a database.
// Miniflare is not a dependency of the site: install it outside the repo and point MINIFLARE_DIR at it.
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/kurs_worker_test.mjs
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
async function loadMiniflare() {
  const dir = process.env.MINIFLARE_DIR;
  if (dir) return import(pathToFileURL(createRequire(path.join(path.resolve(dir), 'package.json')).resolve('miniflare')).href);
  try { return await import('miniflare'); } catch (e) {
    console.error('Miniflare not found: npm install --prefix /tmp/mf miniflare@4, then MINIFLARE_DIR=/tmp/mf node ' + process.argv[1]);
    process.exit(2);
  }
}
const { Miniflare } = await loadMiniflare();

const SITE = 'https://www.blokvolt.rs';
let fails = 0, oks = 0;
function check(cond, what, detail) {
  if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 400) : '')); }
}

// kurs.resenje.org as this test wants it: per currency an answer object, a status, or 'down' (connection fails)
const up = { EUR: null, USD: null };
const calls = [];
function plan(eur, usd) { up.EUR = eur; up.USD = usd; }
const rate = (code, mid, o = {}) => ({ code, date: o.date || '2026-10-06', date_from: o.date || '2026-10-06', number: 192, parity: o.parity || 1,
  cash_buy: mid * 0.98, cash_sell: mid * 1.02, exchange_buy: mid * 0.997, exchange_middle: mid, exchange_sell: mid * 1.003 });
async function outbound(req) {
  const u = new URL(req.url);
  if (u.hostname !== 'kurs.resenje.org') return new Response('blocked in tests', { status: 599 });
  const m = u.pathname.match(/^\/api\/v1\/currencies\/(eur|usd)\/rates\/today$/);
  if (!m) return new Response('not found', { status: 404 });
  const c = m[1].toUpperCase(), a = up[c];
  calls.push(c);
  if (a === 'down') throw new Error('connection refused');
  if (typeof a === 'number') return new Response('error', { status: a });
  return new Response(JSON.stringify(a), { headers: { 'content-type': 'application/json' } });
}
async function instance({ db = true, cache = true } = {}) {
  const mf = new Miniflare({
    modules: true, scriptPath: path.join(REPO, 'worker', '_worker.js'), compatibilityDate: '2025-09-01',
    ...(db ? { d1Databases: ['DB'] } : {}), cache,
    bindings: { SITE }, serviceBindings: { ASSETS: () => new Response('not found', { status: 404 }) }, outboundService: outbound,
  });
  const d1 = db ? await mf.getD1Database('DB') : null;
  async function call(method = 'GET', headers = {}) {
    const res = await mf.dispatchFetch(SITE + '/api/kurs', { method, headers });
    const txt = await res.text();
    let j = null;
    try { j = JSON.parse(txt); } catch (e) { j = null; }
    return { status: res.status, j, txt, headers: res.headers };
  }
  return { mf, d1, call };
}
const sleep = ms => new Promise(ok => setTimeout(ok, ms));
const KEYS = 'base,source,date,rates,fetchedAt,stale';

// ======================================================================= with the cache
console.log('— a good answer, then the cache');
const A = await instance();
plan(rate('EUR', 117.4948), rate('USD', 105.0468));
let r = await A.call();
check(r.status === 200 && Object.keys(r.j).join() === KEYS, 'format: exactly the fields of the spec, in its order', Object.keys(r.j || {}));
check(r.j.base === 'RSD' && r.j.source === 'NBS srednji kurs' && r.j.date === '2026-10-06' && r.j.rates.EUR === 117.4948 &&
  r.j.rates.USD === 105.0468 && r.j.stale === false && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(r.j.fetchedAt), 'values and stale:false', r.j);
check(Object.keys(r.j.rates).join() === 'EUR,USD', 'rates: EUR and USD only', r.j.rates);
check(r.headers.get('access-control-allow-origin') === '*', 'header: Access-Control-Allow-Origin *', r.headers.get('access-control-allow-origin'));
check(r.headers.get('cache-control') === 'public, max-age=3600', 'header: Cache-Control public, max-age=3600', r.headers.get('cache-control'));
check(/^application\/json/.test(r.headers.get('content-type')), 'header: JSON', r.headers.get('content-type'));
check(calls.length === 2, 'upstream asked once per currency', calls);
await sleep(100);                                                          // the cache and D1 are written after the answer
const row = await A.d1.prepare('SELECT * FROM kurs WHERE id = 1').first();
check(row && row.date === '2026-10-06' && row.eur === 117.4948 && row.usd === 105.0468 && row.fetched_at === r.j.fetchedAt,
  'last good value stored in D1 (table created on first use)', row);
plan('down', 'down');
const r2 = await A.call();
check(r2.status === 200 && r2.j.stale === false && r2.j.rates.EUR === 117.4948 && calls.length === 2, 'second request from the Cloudflare cache, upstream not asked', { calls, j: r2.j });
check(r2.headers.get('cache-control') === 'public, max-age=3600' && r2.headers.get('access-control-allow-origin') === '*', 'cached answer keeps the public headers', [...r2.headers]);
r = await A.call('OPTIONS', { origin: 'https://www.evolako.rs', 'access-control-request-method': 'GET' });
check(r.status === 204 && r.headers.get('access-control-allow-origin') === '*' && /GET/.test(r.headers.get('access-control-allow-methods') || ''), 'OPTIONS preflight: 204 with CORS', [...r.headers]);
r = await A.call('POST', { origin: SITE, 'content-type': 'application/json' });
check(r.status === 405, 'POST → 405', r.status);
r = await A.call('GET', { origin: 'https://www.evolako.rs' });
check(r.status === 200 && r.headers.get('access-control-allow-origin') === '*', 'cross-origin GET (evolako.rs) allowed', r.status);
await A.mf.dispose();

// ======================================================================= without the cache: upstream, D1, constants
console.log('— upstream down, last good value, constants');
const B = await instance({ cache: false });
calls.length = 0;
plan('down', 'down');
r = await B.call();
check(r.status === 200 && r.j.stale === true && r.j.date === '2026-10-05' && r.j.rates.EUR === 117.4948 && r.j.rates.USD === 105.0468 &&
  r.j.fetchedAt === null && Object.keys(r.j).join() === KEYS, 'nothing stored + upstream down → the spec constants, stale:true', r.j);
plan(503, rate('USD', 105.0468));
r = await B.call();
check(r.j.stale === true && r.j.date === '2026-10-05', 'one currency failing (503) counts as down', r.j);
plan(rate('EUR', 117.5521, { date: '2026-10-07' }), rate('USD', 101.2345, { date: '2026-10-07' }));
r = await B.call();
check(r.j.stale === false && r.j.date === '2026-10-07' && r.j.rates.EUR === 117.5521 && r.j.rates.USD === 101.2345, 'upstream back: fresh rate', r.j);
await sleep(100);
const fetched = r.j.fetchedAt;
plan('down', 'down');
r = await B.call();
check(r.j.stale === true && r.j.date === '2026-10-07' && r.j.rates.EUR === 117.5521 && r.j.fetchedAt === fetched,
  'upstream down → last good value from D1 with stale:true and its fetch time', r.j);
plan(rate('EUR', 5), rate('USD', 101));
r = await B.call();
check(r.j.stale === true && r.j.rates.EUR === 117.5521, 'nonsense EUR (5) not taken: last good value', r.j);
plan(rate('EUR', 117.6), rate('USD', 150));
r = await B.call();
check(r.j.stale === true && r.j.rates.USD === 101.2345, 'USD outside 80–140 not taken', r.j);
await sleep(100);
let row2 = await B.d1.prepare('SELECT eur, usd FROM kurs WHERE id = 1').first();
check(row2.eur === 117.5521 && row2.usd === 101.2345, 'a rejected rate is not stored', row2);
plan(rate('EUR', 11755.21, { parity: 100 }), rate('USD', 101.2399));
r = await B.call();
check(r.j.stale === false && r.j.rates.EUR === 117.5521, 'parity ≠ 1: exchange_middle divided by parity', r.j);
plan(rate('EUR', 117.6, { date: '2026-10-08' }), rate('USD', 101.3, { date: '2026-10-07' }));
r = await B.call();
check(r.j.date === '2026-10-07', 'lists of two dates: the older date is given', r.j);
plan({ code: 'EUR', date: 'juče', parity: 1, exchange_middle: 117.5 }, rate('USD', 101));
r = await B.call();
check(r.j.stale === true, 'a malformed date is not taken', r.j);
await B.mf.dispose();

console.log('— no database binding');
const C = await instance({ db: false, cache: false });
plan('down', 'down');
r = await C.call();
check(r.status === 200 && r.j.stale === true && r.j.rates.EUR === 117.4948, 'without D1 the endpoint still answers (constants)', r.j);
plan(rate('EUR', 117.4948), rate('USD', 105.0468));
r = await C.call();
check(r.status === 200 && r.j.stale === false, 'without D1: fresh rate, nothing stored', r.j);
await C.mf.dispose();

console.log(`\n${oks} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
