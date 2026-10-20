// "Dodaj punjač" (RUNBOOK 3.11d): the real worker/_worker.js in Miniflare (workerd) with an in-memory D1 that starts like
// the production database (tables of worker/schema.sql without `novi`), fake map files behind env.ASSETS.
// Checks: validation (point in Serbia, values, confirmation, power), honeypot and speed, the daily limit, nothing public
// before moderation, the moderation queue and decisions, the public list, the optional photo, drivers' reports on an
// approved charger, and that a rejected charger leaves the list.
// Miniflare is not a dependency of the site: install it outside the repo and point MINIFLARE_DIR at it.
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/novi_worker_test.mjs
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
const ADMIN = 'test-admin-key-0123456789';
let fails = 0, oks = 0;
function check(cond, what, detail) {
  if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 400) : '')); }
}
const ASSET_FILES = {
  '/assets/map/punjaci.json': { stations: [{ id: 'st-001' }, { id: 'st-002' }] },
  '/assets/map/mreze.json': { upd: {}, add: [{ id: 'cg-65' }] },
};
async function assets(req) {
  const f = ASSET_FILES[new URL(req.url).pathname];
  return f ? new Response(JSON.stringify(f), { headers: { 'content-type': 'application/json' } }) : new Response('not found', { status: 404 });
}
const LEGACY = [
  `CREATE TABLE checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, st TEXT NOT NULL, s TEXT NOT NULL, r INTEGER, c TEXT, n TEXT,
    cs TEXT NOT NULL DEFAULT 'none', at INTEGER NOT NULL, lang TEXT, ip TEXT, rep INTEGER NOT NULL DEFAULT 0)`,
  `CREATE TABLE photos (id TEXT PRIMARY KEY, st TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', at INTEGER NOT NULL, cap TEXT,
    w INTEGER, h INTEGER, mime TEXT NOT NULL, img BLOB NOT NULL, th BLOB, ip TEXT, rep INTEGER NOT NULL DEFAULT 0)`,
  `CREATE TABLE requests (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, slug TEXT, data TEXT NOT NULL, email TEXT,
    at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'new', ip TEXT)`,
  'CREATE TABLE rl (k TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (k, day))',
];
const mf = new Miniflare({
  modules: true, scriptPath: path.join(REPO, 'worker', '_worker.js'), compatibilityDate: '2025-09-01',
  d1Databases: ['DB'], bindings: { SITE, ADMIN_KEY: ADMIN },
  serviceBindings: { ASSETS: assets }, outboundService: () => new Response('blocked in tests', { status: 599 }),
});
const db = await mf.getD1Database('DB');
for (const s of LEGACY) await db.prepare(s).run();
let ipn = 1;
async function call(method, p, o = {}) {
  const headers = { 'cf-connecting-ip': o.ip || '10.1.' + Math.floor(ipn / 250) + '.' + (ipn++ % 250), ...(o.headers || {}) };
  if (o.bearer) headers.authorization = 'Bearer ' + o.bearer;
  let body;
  if (o.json !== undefined) { body = JSON.stringify(o.json); headers['content-type'] = 'application/json'; }
  else if (o.form) {
    // serialise the multipart body here: Miniflare's dispatchFetch does not add the boundary header for a FormData body
    const rq = new Request(SITE, { method: 'POST', body: o.form });
    headers['content-type'] = rq.headers.get('content-type');
    body = new Uint8Array(await rq.arrayBuffer());
  }
  if (method === 'POST' && !('origin' in headers)) headers.origin = SITE;
  const res = await mf.dispatchFetch(SITE + p, { method, headers, body });
  const txt = await res.text();
  let j = null;
  try { j = JSON.parse(txt); } catch (e) { j = null; }
  return { status: res.status, j };
}
function form(o) {
  const f = new FormData();
  const base = { lat: '44.81234', lon: '20.45678', n: 'Hotel Primer', k: 'ac', kw: '11', pl: 'type2,bogus', acc: 'gosti', fee: 'besplatno',
    c: 'Parking iza hotela', nick: 'Vozač', ja: '1', t: '9000', hp: '', lang: 'sr' };
  for (const [k, v] of Object.entries(Object.assign(base, o || {}))) if (v !== null) f.append(k, v);
  return f;
}
const jpeg = n => { const b = new Uint8Array(n); b[0] = 0xff; b[1] = 0xd8; b[2] = 0xff; return b; };

// --- validation
let r = await call('POST', '/api/novi-punjac', { form: form({ ja: null }) });
check(r.status === 400 && r.j.error === 'confirm', 'without the confirmation: refused', r);
r = await call('POST', '/api/novi-punjac', { form: form({ lat: '48.2', lon: '16.37' }) });
check(r.status === 400 && r.j.error === 'outside', 'a point outside Serbia: refused', r);
r = await call('POST', '/api/novi-punjac', { form: form({ k: 'plazma' }) });
check(r.status === 400 && r.j.error === 'value', 'an unknown kind: refused', r);
r = await call('POST', '/api/novi-punjac', { form: form({ kw: '9000' }) });
check(r.status === 400 && r.j.error === 'kw', 'power above 400 kW: refused', r);
r = await call('POST', '/api/novi-punjac', { form: form({ t: '900' }) });
check(r.status === 429 && r.j.error === 'too fast', 'sent within 4 s of opening: refused', r);
r = await call('POST', '/api/novi-punjac', { form: form({ hp: 'bot' }) });
check(r.status === 200 && r.j.ok, 'honeypot: answered ok', r);
let n = (await db.prepare(`SELECT COUNT(*) AS n FROM sqlite_master WHERE type = 'table' AND name = 'novi'`).first()).n
  ? (await db.prepare('SELECT COUNT(*) AS n FROM novi').first()).n : 0;
check(n === 0, 'honeypot and refused sends stored nothing', n);
r = await call('POST', '/api/novi-punjac', { form: form(), headers: { origin: 'https://evil.example' } });
check(r.status === 403, 'another origin: refused', r.status);

// --- a good one, with a photo
const f1 = form({ n: 'Hotel Primer', kw: '11,5' });
f1.append('foto', new Blob([jpeg(5000)], { type: 'image/jpeg' }), 'foto.jpg');
f1.append('thumb', new Blob([jpeg(800)], { type: 'image/jpeg' }), 'thumb.jpg');
r = await call('POST', '/api/novi-punjac', { form: f1, ip: '10.9.9.9' });
check(r.status === 200 && r.j.ok && r.j.pending, 'a charger with a photo: accepted, pending', r);
const row = await db.prepare('SELECT * FROM novi ORDER BY id DESC LIMIT 1').first();
check(row && row.status === 'pending' && row.kw === 11.5 && row.pl === 'type2' && row.acc === 'gosti' && row.fee === 'besplatno' && row.nick === 'Vozač' && row.ip && row.ip.length === 24,
  'stored: values cleaned (11,5 kW, unknown plug dropped), fingerprint, nickname', row);
const ph = await db.prepare('SELECT id, st, status FROM photos WHERE st = ?1').bind('vz-' + row.id).first();
check(ph && ph.status === 'pending' && ph.id === row.foto, 'the photo waits in the photo queue under vz-<id>', ph);
r = await call('GET', '/api/novi-punjaci');
check(r.status === 200 && r.j.ok && r.j.st.length === 0, 'nothing public before moderation', r.j);

// --- the daily limit: 5 a day per fingerprint
for (let i = 0; i < 4; i++) await call('POST', '/api/novi-punjac', { form: form({ n: 'Isti ' + i }), ip: '10.9.9.9' });
r = await call('POST', '/api/novi-punjac', { form: form({ n: 'Šesti' }), ip: '10.9.9.9' });
check(r.status === 429 && r.j.error === 'limit', 'the 6th charger from one fingerprint in a day: limit', r);

// --- moderation
r = await call('GET', '/api/admin/red');
check(r.status === 404, 'the queue without the key: 404', r.status);
r = await call('GET', '/api/admin/red', { bearer: ADMIN });
check(r.status === 200 && r.j.novi.length === 5 && r.j.novi[0].lat === 44.81234 && !('ip' in r.j.novi[0]), 'the queue lists the 5 new chargers, without the fingerprint', r.j.novi && r.j.novi.length);
r = await call('POST', '/api/admin/odluka', { json: { t: 'n', id: row.id, a: 'ok' } });
check(r.status === 404, 'a decision without the key: 404', r.status);
r = await call('POST', '/api/admin/odluka', { json: { t: 'n', id: row.id, a: 'ok' }, bearer: ADMIN });
check(r.status === 200 && r.j.ok, 'approve', r);
r = await call('POST', '/api/admin/odluka', { json: { t: 'n', id: row.id + 1, a: 'no' }, bearer: ADMIN });
check(r.status === 200 && r.j.ok, 'reject another one', r);

// the public list (cached per minute: a fresh minute key is not guaranteed, so read the rows directly as well)
const pub = await db.prepare(`SELECT COUNT(*) AS n FROM novi WHERE status = 'ok'`).first();
check(pub.n === 1, 'one approved charger', pub);
r = await call('GET', '/api/novi-punjaci');
const vz = r.j && r.j.st.find(x => x.id === 'vz-' + row.id);
check(vz && vz.n === 'Hotel Primer' && vz.k === 'ac' && vz.kw === 11.5 && vz.pl.join() === 'type2' && vz.c === 'Parking iza hotela' && !('nick' in vz) && !('ip' in vz) && vz.ok > 0,
  'the public list has the approved charger, without nickname or fingerprint', r.j);
check(!r.j.st.some(x => x.id === 'vz-' + (row.id + 1)), 'the rejected one is not public');

// drivers' reports and photos work on an approved charger, not on a pending one
r = await call('POST', '/api/stanica/vz-' + row.id + '/prijava', { json: { s: 'ok', r: 5, t: 9000 } });
check(r.status === 200 && r.j.ok, 'a report on the approved charger', r);
r = await call('POST', '/api/stanica/vz-' + (row.id + 2) + '/prijava', { json: { s: 'ok', t: 9000 } });
check(r.status === 404, 'a report on a pending charger: 404', r);
r = await call('GET', '/api/stanica/vz-' + row.id);
check(r.status === 200 && r.j && r.j.n === 1, 'its summary counts the report', r.j);

// taking an approved charger off again: 'no' later, and its waiting photo goes with it
r = await call('POST', '/api/admin/odluka', { json: { t: 'n', id: row.id, a: 'no' }, bearer: ADMIN });
const after = await db.prepare('SELECT status FROM novi WHERE id = ?1').bind(row.id).first();
const phAfter = await db.prepare('SELECT status FROM photos WHERE id = ?1').bind(row.foto).first();
check(after.status === 'no' && phAfter.status === 'no', 'rejecting it later takes it off and rejects its waiting photo', [after, phAfter]);

await mf.dispose();
console.log(`\n${oks} ok, ${fails} FAIL`);
process.exit(fails ? 1 : 0);
