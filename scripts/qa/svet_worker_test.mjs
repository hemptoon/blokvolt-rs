// World map „Prijavi grešku“ (K6, P1 §2.4–2.5): the real worker/_worker.js in Miniflare (workerd) with an in-memory D1 that
// starts like the production database (no world_reports table yet). Checks: the field checks (also as a unit through
// globalThis.SVET_TEST), the honeypot, CORS and the preflight for blokvolt.com and localhost, a foreign origin, the daily
// limit and one report per place a day, silent spam, the admin key, the queue grouped by place, human decisions
// (accept with the default action, move by the median point, access, reject, postpone, answered, undo of an automatic
// decision), the script's automatic decisions that never overwrite a human one, the export (no e-mail), the counts,
// and the e-mail clean-up.
// Miniflare is not a dependency of the site: install it outside the repo and point MINIFLARE_DIR at it.
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/svet_worker_test.mjs
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
const { parse, majority } = globalThis.SVET_TEST;
const P = o => parse(Object.assign({ pid: 123, type: 'ne_radi', hp: '', lang: 'sr' }, o));
check(P({}).pid === 123 && !P({}).error, 'unit: a minimal report passes');
check(P({ pid: '456' }).pid === 456, 'unit: pid as digit string');
for (const [o, e] of [[{ pid: 0 }, 'pid'], [{ pid: -1 }, 'pid'], [{ pid: 1.5 }, 'pid'], [{ pid: 'x1' }, 'pid'], [{ pid: 3000000000 }, 'pid'],
  [{ type: 'bogus' }, 'type'], [{ type: 'lokacija' }, 'point'], [{ type: 'lokacija', lat: 91, lon: 1 }, 'point'],
  [{ type: 'lokacija', lat: 1, lon: 'x' }, 'point'], [{ text: 'a'.repeat(301) }, 'text'], [{ text: 5 }, 'text'],
  [{ email: 'not-an-address' }, 'email'], [{ lang: 'de' }, 'lang']]) {
  check(P(o).error === e, 'unit: ' + JSON.stringify(o).slice(0, 50) + ' → ' + e, P(o));
}
check(P({ text: 'a'.repeat(300) }).text.length === 300, 'unit: 300 characters pass');
check(P({ lang: undefined }).lang === 'en', 'unit: missing lang → en');
check(P({ hp: 'x' }).trap === true, 'unit: honeypot');
check(P({ type: 'lokacija', lat: 48.1371234567, lon: '11.5753' }).lat === 48.137123, 'unit: point rounded to 6 decimals');
check(P({ type: 'ne_radi', lat: 1, lon: 2 }).lat === null, 'unit: lat/lon ignored for other types');
check(P({ cc: 'DE', g: 'u281z' }).cc === 'DE' && P({ cc: 'DE', g: 'u281z' }).g === 'u281z', 'unit: cc and g hints kept');
check(P({ cc: 'de', g: 'u2a<' }).cc === null && P({ cc: 'de', g: 'u2a<' }).g === null, 'unit: bad cc and g hints dropped');
check(P({ text: 'vidi www.example.com' }).spam && P({ text: 'jebem ti' }).spam && !P({ text: 'Punjač je uklonjen 2025.' }).spam, 'unit: spam flags');
check(P({ email: ' Ana@Example.COM ' }).email === 'ana@example.com', 'unit: e-mail normalised');
check(majority([{ type: 'ne_radi' }, { type: 'drugo' }]) === 'hide' && majority([{ type: 'lokacija' }, { type: 'lokacija' }, { type: 'ne_radi' }]) === 'move' &&
  majority([{ type: 'snaga' }]) === 'none', 'unit: default action by majority (tie → the one that changes the map)');

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
const rep = (o, c = {}) => call('POST', '/api/svet/prijava', { json: Object.assign({ pid: 1001, type: 'ne_radi', lang: 'sr', hp: '' }, o), ...c });
const rows = async (where = '1') => (await db.prepare('SELECT * FROM world_reports WHERE ' + where + ' ORDER BY id').all()).results;

// CORS and the preflight
let r = await call('OPTIONS', '/api/svet/prijava', { headers: { origin: 'https://blokvolt.com', 'access-control-request-method': 'POST' } });
check(r.status === 204 && r.h.get('access-control-allow-origin') === 'https://blokvolt.com' && /POST/.test(r.h.get('access-control-allow-methods') || ''),
  'preflight from blokvolt.com', [r.status, r.h.get('access-control-allow-origin')]);
r = await call('OPTIONS', '/api/svet/prijava', { headers: { origin: 'http://localhost:8790' } });
check(r.status === 204 && r.h.get('access-control-allow-origin') === 'http://localhost:8790', 'preflight from localhost');
r = await call('OPTIONS', '/api/svet/prijava', { headers: { origin: 'https://evil.example' } });
check(r.status === 403 && !r.h.get('access-control-allow-origin'), 'preflight from a foreign origin refused');
r = await rep({}, { headers: { origin: 'https://evil.example' } });
check(r.status === 403 && r.j && r.j.error === 'origin', 'POST from a foreign origin → 403 origin');
r = await rep({}, { headers: { origin: 'http://blokvolt.com' } });
check(r.status === 403, 'POST from http://blokvolt.com (not https) refused');
r = await call('GET', '/api/svet/prijava', { headers: { origin: 'https://blokvolt.com' } });
check(r.status === 405, 'GET → 405');

// the first report creates the table; answers carry CORS
r = await rep({ text: 'Stanica je uklonjena.', email: 'vozac@example.com', cc: 'DE', g: 'u281zbcd' });
check(r.status === 200 && r.j.ok === true && r.h.get('access-control-allow-origin') === 'https://blokvolt.com', 'valid report → 200 with CORS', r);
let all = await rows();
check(all.length === 1 && all[0].status === 'new' && all[0].pid === 1001 && all[0].email === 'vozac@example.com' && all[0].lang === 'sr' &&
  /^[0-9a-f]{24}$/.test(all[0].ip_hash) && all[0].cc === 'DE' && all[0].g === 'u281zbcd' && all[0].created_at > 1.7e9, 'row stored as specified', all[0]);
r = await rep({ type: 'lokacija' });
check(r.status === 400 && r.j.error === 'point' && r.h.get('access-control-allow-origin'), '400 point, with CORS (the page can read the error)');
r = await call('POST', '/api/svet/prijava', { raw: '{bad json' });
check(r.status === 400 && r.j.error === 'json', '400 json');
r = await rep({ hp: 'bot' });
check(r.status === 200 && (await rows()).length === 1, 'honeypot: 200, nothing stored');
r = await rep({}, { headers: {} , ip: '10.0.0.1' });
check(r.status === 200, 'no Origin header (server-side test) → allowed');

// limits: 5 a day per fingerprint, one per place and fingerprint a day
const IP = '10.77.0.1';
let st = [];
for (let i = 0; i < 6; i++) st.push((await rep({ pid: 2000 + i }, { ip: IP })).status);
check(st.slice(0, 5).every(s => s === 200) && st[5] === 429, 'sixth report of the day → 429', st);
r = await rep({ pid: 2000 }, { ip: '10.77.0.2' });
const before = (await rows('pid = 3000')).length;
await rep({ pid: 3000 }, { ip: '10.77.0.3' });
r = await rep({ pid: 3000, type: 'drugo' }, { ip: '10.77.0.3' });
check(r.status === 200 && (await rows('pid = 3000')).length === before + 1, 'same place twice a day: 200, stored once');

// silent spam
r = await rep({ pid: 4000, text: 'Najbolje cene na www.spam-shop.com' });
let sp = await rows('pid = 4000');
check(r.status === 200 && sp.length === 1 && sp[0].status === 'rejected' && sp[0].rule === 'spam_insert' && sp[0].decided_by === 'auto', 'link in text → stored as rejected, answer 200', sp);

// admin key
r = await call('GET', '/api/admin/svet');
check(r.status === 404, 'admin without key → 404');
r = await call('GET', '/api/admin/svet', { bearer: 'wrong-key-0123456789' });
check(r.status === 404, 'admin with a wrong key → 404');

// a set of reports for the queue
await rep({ pid: 5000, type: 'lokacija', lat: 48.1, lon: 11.5 });
await rep({ pid: 5000, type: 'lokacija', lat: 48.1002, lon: 11.5004 });
await rep({ pid: 5000, type: 'lokacija', lat: 48.2, lon: 11.6 });
await rep({ pid: 6000, type: 'nije_javni', cc: 'FR' });
await rep({ pid: 7000, type: 'snaga', text: 'Samo 50 kW, ne 150.' });
await rep({ pid: 8000, type: 'ne_postoji' });
await rep({ pid: 8000, type: 'ne_postoji' });
r = await call('GET', '/api/admin/svet', { bearer: ADMIN });
const g5 = r.j && r.j.groups.find(g => g.pid === 5000);
check(r.status === 200 && r.j.ok && g5 && g5.n === 3 && g5.types.lokacija === 3 && g5.reports.length === 3 && !r.j.groups.some(g => g.pid === 4000),
  'queue: grouped by pid, spam not in it', r.j && r.j.groups.map(g => [g.pid, g.n]));
check(r.j.groups[0].n >= r.j.groups[r.j.groups.length - 1].n, 'queue: sorted by number of reports');
const g1 = r.j.groups.find(g => g.pid === 1001);
check(g1 && g1.reports.some(x => x.email === 'vozac@example.com') && g1.cc === 'DE' && g1.g === 'u281zbcd', 'queue shows the e-mail and the hints to the owner');

// human decisions
const post = b => call('POST', '/api/admin/svet', { bearer: ADMIN, json: b, headers: {} });
r = await post({ pid: 5000, a: 'accept' });
let d5 = await rows('pid = 5000');
check(r.j.ok && r.j.n === 3 && d5.every(x => x.status === 'accepted' && x.action === 'move' && x.decided_by === 'admin') &&
  d5[0].alat === 48.1002 && d5[0].alon === 11.5004, 'accept lokacija → move to the median point', d5.map(x => [x.status, x.action, x.alat, x.alon]));
r = await post({ pid: 6000, a: 'accept' });
let d6 = await rows('pid = 6000');
check(d6[0].action === 'access' && d6[0].access === 'restricted_reported', 'accept nije_javni → access restricted_reported', d6[0]);
r = await post({ pid: 7000, a: 'postpone' });
check((await rows('pid = 7000'))[0].status === 'postponed', 'postpone');
r = await call('GET', '/api/admin/svet', { bearer: ADMIN });
check(r.j.groups.some(g => g.pid === 7000 && g.reports[0].status === 'postponed'), 'a postponed place stays in the queue');
r = await post({ pid: 7000, a: 'reject' });
check((await rows('pid = 7000'))[0].status === 'rejected', 'reject (also a postponed one)');
r = await post({ pid: 1001, a: 'answered' });
check((await rows('pid = 1001')).every(x => x.email === null), 'answered → e-mail erased');
r = await post({ pid: 1001, a: 'accept', action: 'teleport' });
check(r.status === 400 && r.j.error === 'action', 'unknown action → 400');
r = await post({ pid: 1001, a: 'accept', action: 'move' });
check(r.status === 400 && r.j.error === 'point', 'move without any point → 400 point');
r = await post({ pid: 1001, a: 'accept', action: 'move', lat: 45.25, lon: 19.84 });
check((await rows('pid = 1001'))[0].alat === 45.25, 'move with a point the owner gives');
r = await post({ pid: 1001, a: 'fly' });
check(r.status === 400 && r.j.error === 'what', 'unknown decision → 400');

// the script's automatic decisions
const ids8 = (await rows('pid = 8000')).map(x => x.id);
r = await post({ auto: ids8.map(id => ({ id, status: 'auto_hidden', rule: 'hide_2_reports', action: 'hide' })).concat([{ id: d5[0].id, status: 'auto_hidden', rule: 'x', action: 'hide' }]) });
const d8 = await rows('pid = 8000');
check(r.j.ok && r.j.n === 2 && d8.every(x => x.status === 'auto_hidden' && x.decided_by === 'auto' && x.rule === 'hide_2_reports'),
  'auto decisions applied to new reports only', [r.j, d8.map(x => x.status)]);
check((await rows('id = ' + d5[0].id))[0].status === 'accepted', 'auto never overwrites a human decision');
r = await post({ auto: [{ id: ids8[0], status: 'new' }] });
check(r.status === 400, 'auto with a status the script may not set → 400');
r = await post({ auto: [{ id: 999999, status: 'auto_moved', action: 'move' }] });
check(r.status === 400 && r.j.error === 'point', 'auto move without a point → 400');
r = await call('GET', '/api/admin/svet', { bearer: ADMIN });
check(r.j.auto.some(g => g.pid === 8000 && g.reports.every(x => x.rule === 'hide_2_reports')), 'queue lists recent automatic decisions');
r = await post({ pid: 8000, a: 'undo' });
const u8 = await rows('pid = 8000');
check(r.j.n === 2 && u8.every(x => x.status === 'rejected' && x.action === 'unhide' && x.rule === 'undo' && x.decided_by === 'admin'), 'undo of a hide → unhide', u8.map(x => [x.status, x.action]));

// export (for the script) and counts
r = await call('GET', '/api/admin/svet?view=export&since=0', { bearer: ADMIN });
check(r.j.ok && r.j.reports.length === (await rows()).length && r.j.reports.every(x => !('email' in x)) && 'ip_hash' in r.j.reports[0] && r.j.now > 0,
  'export: every row, no e-mail, with fingerprints');
r = await call('GET', '/api/admin/svet?view=export&since=' + (Math.floor(Date.now() / 1000) + 3600), { bearer: ADMIN });
check(r.j.reports.length === 0, 'export since the future → empty');
r = await call('GET', '/api/admin/svet?view=stats&days=7', { bearer: ADMIN });
check(r.j.ok && r.j.total === (await rows()).length && r.j.by_type.lokacija === 3 && r.j.by_country.some(c => c.cc === 'FR' && c.n === 1) &&
  r.j.decided_by.admin > 0 && r.j.decided_by.auto > 0 && r.j.by_lang.sr > 0, 'stats: by type, country, decided_by', r.j);
r = await call('GET', '/api/admin/svet?view=bogus', { bearer: ADMIN });
check(r.status === 400, 'unknown view → 400');

// e-mail clean-up: older than 90 days, or 30 days after the decision
await rep({ pid: 9000, email: 'a@example.com' });
await rep({ pid: 9001, email: 'b@example.com' });
await rep({ pid: 9002, email: 'c@example.com' });
const T = Math.floor(Date.now() / 1000);
await db.prepare('UPDATE world_reports SET created_at = ?1 WHERE pid = 9000').bind(T - 91 * 86400).run();
await db.prepare(`UPDATE world_reports SET status = 'rejected', decided_at = ?1 WHERE pid = 9001`).bind(T - 31 * 86400).run();
await call('GET', '/api/admin/svet', { bearer: ADMIN });
const e = Object.fromEntries((await rows('pid >= 9000')).map(x => [x.pid, x.email]));
check(e[9000] === null && e[9001] === null && e[9002] === 'c@example.com', 'e-mail clean-up', e);

// a full queue answers 429 limit
await db.prepare(`INSERT INTO world_reports (pid, type, lang, ip_hash, created_at) SELECT 1, 'drugo', 'en', 'x', 1 FROM
  (WITH RECURSIVE c(i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM c WHERE i < 5000) SELECT i FROM c)`).run();
r = await rep({ pid: 9100 });
check(r.status === 429 && r.j.error === 'limit', 'more than 5000 open reports → 429 limit');

await mf.dispose();
console.log(`\n${oks} ok, ${fails} FAIL`);
process.exit(fails ? 1 : 0);
