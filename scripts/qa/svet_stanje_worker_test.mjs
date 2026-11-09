// World map check-ins „Radi / Ne radi / Zauzeto“ and „Koliko si platio“ (G6): the real worker/_worker.js in Miniflare (workerd)
// with an in-memory D1 that starts like the production database (no world_checkins table yet). Checks: the field checks
// (also as a unit through globalThis.SVET_TEST), the honeypot, CORS, Balkan pids, both limits, the card summary (distinct
// drivers), the admin key, the export, the script's decisions that never overwrite a human one, accept / hide.
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/svet_stanje_worker_test.mjs
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
let fails = 0, oks = 0;
function check(cond, what, detail) {
  if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 400) : '')); }
}

// ---- unit: the field checks, in plain Node
globalThis.SVET_TEST = {};
await import(pathToFileURL(path.join(REPO, 'worker', '_worker.js')).href);
const { scParse, scSummary, scMonthOk } = globalThis.SVET_TEST;
const T0 = Date.UTC(2026, 10, 9, 12) / 1000;   // 09.11.2026
const P = o => scParse(Object.assign({ pid: 123, s: 'radi', hp: '', lang: 'en' }, o), T0);
check(!P({}).error && P({}).s === 'radi' && P({}).amt === null, 'unit: a state alone passes');
check(!P({ s: '', amt: 0.59, unit: 'kwh', cur: 'eur', ym: '2026-10' }).error && P({ s: '', amt: 0.59, unit: 'kwh', cur: 'eur', ym: '2026-10' }).cur === 'EUR',
  'unit: a price alone passes, currency upper-cased');
for (const [o, e] of [[{ pid: 0 }, 'pid'], [{ pid: 'x' }, 'pid'], [{ pid: 900000001 }, 'balkan'], [{ s: 'bogus' }, 'state'],
  [{ s: null }, 'empty'], [{ amt: -1, unit: 'kwh', cur: 'EUR', ym: '2026-10' }, 'amount'], [{ amt: 'x', unit: 'kwh', cur: 'EUR', ym: '2026-10' }, 'amount'],
  [{ amt: 200000, unit: 'kwh', cur: 'EUR', ym: '2026-10' }, 'amount'], [{ amt: 1, unit: 'litre', cur: 'EUR', ym: '2026-10' }, 'unit'],
  [{ amt: 1, unit: 'kwh', cur: 'EURO', ym: '2026-10' }, 'currency'], [{ amt: 1, unit: 'kwh', cur: 'EUR', ym: '2026-12' }, 'month'],
  [{ amt: 1, unit: 'kwh', cur: 'EUR', ym: '2025-10' }, 'month'], [{ amt: 1, unit: 'kwh', cur: 'EUR', ym: '2026-13' }, 'month'], [{ lang: 'de' }, 'lang']]) {
  check(P(o).error === e, 'unit: ' + JSON.stringify(o).slice(0, 60) + ' → ' + e, P(o));
}
check(scMonthOk('2025-11', T0) && !scMonthOk('2025-10', T0), 'unit: 12 months back is the limit');
check(P({ hp: 'x' }).trap === true, 'unit: honeypot');
check(P({ cls: 'dc', cc: 'DE', g: 'u281z', net: 'EnBW' }).cls === 'dc' && P({ cls: 'xx' }).cls === null && P({ cc: 'de' }).cc === null, 'unit: hints kept or dropped');
check(P({ net: 'see www.spam.com' }).net === null, 'unit: a link as network name dropped');
const S = scSummary([{ s: 'radi', created_at: T0 - 86400 * 3, ip_hash: 'a' }, { s: 'radi', created_at: T0 - 86400 * 40, ip_hash: 'b' },
  { s: 'ne_radi', created_at: T0 - 3600, ip_hash: 'c' }, { s: 'radi', created_at: T0 - 86400 * 5, ip_hash: 'a' }], T0);
check(S.last_ok === T0 - 86400 * 3 && S.last.s === 'ne_radi' && S.d30.radi === 1 && S.d30.ne_radi === 1 && S.d30.zauzeto === 0,
  'unit: summary — last radi, last state, distinct drivers in 30 days', S);

// ---- the worker in workerd
const { Miniflare } = await loadMiniflare();
const SITE = 'https://www.blokvolt.rs';
const ADMIN = 'test-admin-key-0123456789';
const LEGACY = ['CREATE TABLE rl (k TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (k, day))'];
const mf = new Miniflare({
  modules: true, scriptPath: path.join(REPO, 'worker', '_worker.js'), compatibilityDate: '2025-09-01',
  d1Databases: ['DB'], bindings: { SITE, ADMIN_KEY: ADMIN },
  serviceBindings: { ASSETS: () => new Response('not found', { status: 404 }) }, outboundService: () => new Response('blocked in tests', { status: 599 }),
});
const db = await mf.getD1Database('DB');
for (const s of LEGACY) await db.prepare(s).run();
let ipn = 1;
async function call(method, p, o = {}) {
  const headers = { 'cf-connecting-ip': o.ip || '10.9.' + Math.floor(ipn / 250) + '.' + (ipn++ % 250), ...(o.headers || {}) };
  if (o.bearer) headers.authorization = 'Bearer ' + o.bearer;
  let body;
  if (o.json !== undefined) { body = JSON.stringify(o.json); headers['content-type'] = 'application/json'; }
  if (o.raw !== undefined) { body = o.raw; headers['content-type'] = 'application/json'; }
  if (method === 'POST' && !('origin' in headers)) headers.origin = 'https://blokvolt.com';
  const res = await mf.dispatchFetch(SITE + p, { method, headers, body });
  const txt = await res.text();
  let j = null;
  try { j = JSON.parse(txt); } catch (e) { j = null; }
  return { status: res.status, j, h: res.headers };
}
const ci = (o, c = {}) => call('POST', '/api/svet/stanje', { json: Object.assign({ pid: 1001, s: 'radi', lang: 'en', hp: '' }, o), ...c });
const rows = async (where = '1') => (await db.prepare('SELECT * FROM world_checkins WHERE ' + where + ' ORDER BY id').all()).results;
const ymNow = new Date().toISOString().slice(0, 7);

// CORS
let r = await call('OPTIONS', '/api/svet/stanje', { headers: { origin: 'https://blokvolt.com', 'access-control-request-method': 'POST' } });
check(r.status === 204 && r.h.get('access-control-allow-origin') === 'https://blokvolt.com' && /GET/.test(r.h.get('access-control-allow-methods') || ''),
  'preflight from blokvolt.com', [r.status]);
r = await call('OPTIONS', '/api/svet/stanje', { headers: { origin: 'https://evil.example' } });
check(r.status === 403, 'preflight from a foreign origin refused');
r = await ci({}, { headers: { origin: 'https://evil.example' } });
check(r.status === 403 && r.j.error === 'origin', 'POST from a foreign origin → 403');
r = await call('PUT', '/api/svet/stanje', { headers: { origin: 'https://blokvolt.com' } });
check(r.status === 405, 'PUT → 405');

// GET before any check-in creates the table and answers an empty summary
r = await call('GET', '/api/svet/stanje?pid=1001', { headers: { origin: 'https://blokvolt.com' } });
check(r.status === 200 && r.j.ok && r.j.last_ok === null && r.j.last === null && r.h.get('access-control-allow-origin') === 'https://blokvolt.com' &&
  /max-age=60/.test(r.h.get('cache-control') || ''), 'GET on a new place: empty summary, CORS, short cache', r.j);
r = await call('GET', '/api/svet/stanje?pid=abc', { headers: { origin: 'https://blokvolt.com' } });
check(r.status === 400 && r.j.error === 'pid', 'GET with a bad pid → 400');

// a state, a price, both
r = await ci({ cls: 'dc', cc: 'DE', g: 'u281zbcd', net: 'EnBW' });
check(r.status === 200 && r.j.ok, 'state check-in → 200', r);
r = await ci({ pid: 1002, s: '', amt: 0.59, unit: 'kwh', cur: 'EUR', ym: ymNow, cls: 'dc', cc: 'DE', net: 'EnBW' });
check(r.status === 200, 'price check-in → 200', r);
let all = await rows();
check(all.length === 2 && all[0].s === 'radi' && all[0].price_status === null && all[0].cc === 'DE' && /^[0-9a-f]{24}$/.test(all[0].ip_hash) &&
  all[1].s === null && all[1].amt === 0.59 && all[1].price_status === 'new' && all[1].ym === ymNow, 'rows stored as specified', all);
r = await ci({ pid: 1003, amt: 9, unit: 'kwh', cur: 'EUR', ym: '2001-01' });
check(r.status === 400 && r.j.error === 'month' && r.h.get('access-control-allow-origin'), '400 month, with CORS');
r = await ci({ pid: 950000000 });
check(r.status === 400 && r.j.error === 'balkan', 'Balkan pid → 400 balkan (they use /mapa/)');
r = await ci({ hp: 'bot', pid: 1004 });
check(r.status === 200 && (await rows('pid = 1004')).length === 0, 'honeypot: 200, nothing stored');

// limits: one per place and fingerprint a day (silent), 20 a day per fingerprint
const IP = '10.88.0.1';
await ci({ pid: 3000 }, { ip: IP });
r = await ci({ pid: 3000, s: 'ne_radi' }, { ip: IP });
check(r.status === 200 && (await rows('pid = 3000')).length === 1, 'same place twice a day: 200, stored once');
let st = [];
for (let i = 0; i < 21; i++) st.push((await ci({ pid: 3100 + i }, { ip: '10.88.0.9' })).status);
check(st.slice(0, 20).every(s => s === 200) && st[20] === 429, '21st check-in of the day → 429', st);

// the card's summary counts different drivers
await ci({ pid: 4000, s: 'radi' }, { ip: '10.88.1.1' });
await ci({ pid: 4000, s: 'radi' }, { ip: '10.88.1.2' });
await ci({ pid: 4000, s: 'zauzeto' }, { ip: '10.88.1.3' });
r = await call('GET', '/api/svet/stanje?pid=4000', { headers: { origin: 'https://blokvolt.com' } });
check(r.j.d30.radi === 2 && r.j.d30.zauzeto === 1 && r.j.last.s === 'zauzeto' && r.j.last_ok > 1.7e9, 'summary: 2 radi, 1 zauzeto, last state', r.j);

// admin
r = await call('GET', '/api/admin/svet/stanje');
check(r.status === 404, 'admin without key → 404');
r = await call('GET', '/api/admin/svet/stanje?view=export', { bearer: ADMIN });
check(r.status === 200 && r.j.checkins.length === (await rows()).length && 'ip_hash' in r.j.checkins[0], 'export has every row and the fingerprint');
const pr = (await rows('pid = 1002'))[0];
r = await call('POST', '/api/admin/svet/stanje', { bearer: ADMIN, json: { auto: [{ id: pr.id, price_status: 'off', rule: 'tariff_off' }] } });
check(r.j.ok && r.j.n === 1 && (await rows('pid = 1002'))[0].price_status === 'off', 'script decision stored');
r = await call('GET', '/api/admin/svet/stanje?view=queue', { bearer: ADMIN });
check(r.j.off.length === 1 && r.j.off[0].id === pr.id, 'queue lists the price far from the tariff', r.j);
r = await call('POST', '/api/admin/svet/stanje', { bearer: ADMIN, json: { id: pr.id, a: 'accept' } });
check(r.j.n === 1 && (await rows('pid = 1002'))[0].price_status === 'accepted', 'owner accepts the price');
r = await call('POST', '/api/admin/svet/stanje', { bearer: ADMIN, json: { auto: [{ id: pr.id, price_status: 'auto_hidden', rule: 'x' }] } });
check(r.j.n === 0 && (await rows('pid = 1002'))[0].price_status === 'accepted', 'the script never overwrites a human decision');
r = await call('POST', '/api/admin/svet/stanje', { bearer: ADMIN, json: { auto: [{ id: pr.id, price_status: 'bogus' }] } });
check(r.status === 400, 'bad automatic status → 400');
const one = (await rows('pid = 4000'))[2];
r = await call('POST', '/api/admin/svet/stanje', { bearer: ADMIN, json: { id: one.id, a: 'hide' } });
r = await call('GET', '/api/svet/stanje?pid=4000', { headers: { origin: 'https://blokvolt.com' } });
check(r.j.d30.zauzeto === 0 && r.j.last.s === 'radi', 'a hidden check-in leaves the card');
r = await call('POST', '/api/admin/svet/stanje', { bearer: ADMIN, json: { id: one.id, a: 'nope' } });
check(r.status === 400, 'unknown admin action → 400');

// the K6 reports still answer next to it
r = await call('POST', '/api/svet/prijava', { json: { pid: 1001, type: 'ne_radi', lang: 'en', hp: '' } });
check(r.status === 200 && r.j.ok, 'K6 /api/svet/prijava unchanged');

await mf.dispose();
console.log(`\n${oks} ok, ${fails} failed`);
process.exit(fails ? 1 : 0);
