// Security basics of the worker (docs/RUNBOOK.md 3.33): the real worker/_worker.js called directly in node, with a D1
// look-alike on node:sqlite (worker/schema.sql loaded first) and the built dist/ behind env.ASSETS. Checks: the
// API on the production alias on pages.dev redirects, previews still answer; an IPv6 /64 is one fingerprint for the limits; the
// contact pattern is fast on hostile input; photos have a ceiling for everyone together and rejected photos give their
// bytes back; the admin key; the health check reads D1 at most once a minute.
// Run after a build: node --no-warnings scripts/qa/zastita_worker_test.mjs
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const DIST = path.join(REPO, 'dist');
if (!existsSync(path.join(DIST, 'assets', 'map', 'punjaci.json'))) { console.error('build first (python3 build.py)'); process.exit(2); }
const SRC = readFileSync(path.join(REPO, 'worker', '_worker.js'), 'utf8');
const W = (await import(pathToFileURL(path.join(REPO, 'worker', '_worker.js')).href)).default;
let fails = 0, oks = 0;
const check = (c, what, detail) => {
  if (c) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 300) : '')); }
};

// ---------------------------------------------------------------- D1 on node:sqlite (the part of the API the worker uses)
function d1(db) {
  const conv = v => (v === undefined ? null : typeof v === 'boolean' ? (v ? 1 : 0) : v);
  const stmt = (sql, args = []) => ({
    bind: (...a) => stmt(sql, a.map(conv)),
    first: async col => { const r = db.prepare(sql).get(...args); return r == null ? null : col ? r[col] : { ...r }; },
    all: async () => ({ results: db.prepare(sql).all(...args).map(r => ({ ...r })), success: true }),
    run: async () => {
      if (/\breturning\b/i.test(sql)) { const rows = db.prepare(sql).all(...args); return { success: true, results: rows, meta: { changes: rows.length } }; }
      const r = db.prepare(sql).run(...args); return { success: true, meta: { changes: Number(r.changes) } };
    },
    _exec: () => (/\breturning\b|^\s*select/i.test(sql) ? { results: db.prepare(sql).all(...args) } : db.prepare(sql).run(...args)),
  });
  return {
    prepare: sql => stmt(sql),
    batch: async list => { db.exec('BEGIN'); try { const out = list.map(s => s._exec()); db.exec('COMMIT'); return out; } catch (e) { db.exec('ROLLBACK'); throw e; } },
    exec: async sql => db.exec(sql),
  };
}
const sqlite = new DatabaseSync(':memory:');
sqlite.exec(readFileSync(path.join(REPO, 'worker', 'schema.sql'), 'utf8'));
const DB = d1(sqlite);
const ASSETS = {
  fetch: async req => {
    const u = new URL(typeof req === 'string' ? req : req.url);
    let f = path.join(DIST, decodeURIComponent(u.pathname));
    if (f.endsWith('/')) f += 'index.html';
    return existsSync(f) ? new Response(readFileSync(f), { headers: { 'content-type': f.endsWith('.json') ? 'application/json' : 'text/html' } }) : new Response('not found', { status: 404 });
  },
};
const ADMIN_KEY = 'test-admin-key-0123456789abcdef-zastita';
const env = { DB, ASSETS, ADMIN_KEY };
let pending = [];
const ctx = { waitUntil: p => pending.push(p), passThroughOnException() {} };
async function call(p, { method = 'GET', body, headers = {}, ip = '10.0.0.1', host = 'www.blokvolt.rs' } = {}) {
  const h = { 'cf-connecting-ip': ip, ...headers };
  if (method === 'POST' && !('origin' in h)) h.origin = 'https://www.blokvolt.rs';
  const res = await W.fetch(new Request('https://' + host + p, { method, headers: h, body, redirect: 'manual' }), env, ctx);
  await Promise.allSettled(pending); pending = [];
  const t = await res.text();
  let j = null; try { j = JSON.parse(t); } catch (e) {}
  return { status: res.status, j, loc: res.headers.get('location') };
}
const rows = (sql, ...a) => sqlite.prepare(sql).all(...a).map(r => ({ ...r }));

// ---------------------------------------------------------------- one public address
let r = await call('/api/stanice?x=1', { host: 'blokvolt.pages.dev' });
check(r.status === 301 && r.loc === 'https://www.blokvolt.rs/api/stanice?x=1', 'pages.dev: the API on the production alias redirects to www.blokvolt.rs with the path and query', r);
r = await call('/api/nalog/kod', { method: 'POST', body: '{}', host: 'blokvolt.pages.dev', headers: { 'content-type': 'application/json' } });
check(r.status === 301, 'pages.dev: a POST on the alias does not run either (no second door past the zone rules)', r);
r = await call('/api/zdravlje', { host: 'a1b2c3d4.blokvolt.pages.dev' });
check(r.status === 200 && r.j && r.j.ok === true, 'pages.dev: a preview deployment still answers (checks before a release)', r);

// ---------------------------------------------------------------- IPv6: one /64 is one fingerprint
const rep = ip => call('/api/prijavi', { method: 'POST', body: JSON.stringify({ t: 'c', id: 1 }), ip, headers: { 'content-type': 'application/json' } });
const six = [];
for (let i = 1; i <= 20; i++) six.push((await rep('2001:db8:1:2::' + i.toString(16))).status);
const same64 = await rep('2001:0db8:0001:0002:ffff:eeee:dddd:cccc');
const other64 = await rep('2001:db8:1:3::1');
check(six.every(x => x === 200) && same64.status === 429 && other64.status === 200,
  'IPv6: 20 reports a day from one /64, the 21st from another address of the same /64 → 429; the next /64 is someone else', [six.length, same64.status, other64.status]);
const v4a = await rep('192.0.2.1'), v4b = await rep('192.0.2.2');
check(v4a.status === 200 && v4b.status === 200, 'IPv4: every address is its own fingerprint, as before', [v4a.status, v4b.status]);

// ---------------------------------------------------------------- the contact pattern: linear on hostile input
const m = /const CONTACTY = (\/.*\/);/.exec(SRC);
const CONTACTY = m ? eval(m[1]) : null;
let ms = Infinity;
if (CONTACTY) {
  const t0 = performance.now();
  for (const s of ['@'.repeat(500), 'a@'.repeat(250), ('x@y.' ).repeat(125), ' @.'.repeat(166)]) CONTACTY.test(s);
  ms = performance.now() - t0;
}
check(CONTACTY && ms < 5, 'contact pattern: 500 hostile characters in under 5 ms (a Free worker has 10 ms of CPU)', ms);
check(CONTACTY && CONTACTY.test('pišite na pera.peric@gmail.com') && CONTACTY.test('zovite 064/123-4567') && !CONTACTY.test('Punjač radi, 22 kW.'),
  'contact pattern: still finds an e-mail address and a phone number, and leaves a normal comment alone');

// ---------------------------------------------------------------- photos
const ids = JSON.parse(readFileSync(path.join(DIST, 'assets', 'map', 'punjaci.json'), 'utf8')).stations.map(s => s.id);
const st = ids[0];
const jpeg = n => { const b = new Uint8Array(n); b[0] = 0xff; b[1] = 0xd8; b[2] = 0xff; return b; };
async function upload(stId, ip) {
  const fd = new FormData();
  fd.append('foto', new Blob([jpeg(5000)], { type: 'image/jpeg' }), 'a.jpg');
  fd.append('t', '5000');
  return call('/api/stanica/' + stId + '/foto', { method: 'POST', body: fd, ip });
}
r = await upload(st, '198.51.100.1');
check(r.status === 200 && r.j && r.j.pending === true, 'photos: an upload goes to the queue', r);
const ins = sqlite.prepare("INSERT INTO photos (id, st, status, at, mime, img) VALUES (?, ?, 'pending', 0, 'image/jpeg', ?)");
for (let i = 0; i < 149; i++) ins.run(i.toString(16).padStart(32, '0'), 'fake-' + (i % 50), jpeg(3000));
r = await upload(ids[1], '198.51.100.2');
check(r.status === 429 && r.j && r.j.error === 'queue full', 'photos: 150 waiting photos from everyone together → the next upload waits (429 queue full)', r);
sqlite.exec("DELETE FROM photos WHERE st LIKE 'fake-%'");
sqlite.exec("INSERT INTO rl (k, day, n) VALUES ('ph:all', '" + new Date().toISOString().slice(0, 10) + "', 40) ON CONFLICT (k, day) DO UPDATE SET n = 40");
r = await upload(ids[2], '198.51.100.3');
check(r.status === 429, 'photos: 40 new photos a day from everyone together → the 41st waits for tomorrow', r);
sqlite.exec("DELETE FROM rl WHERE k = 'ph:all'");

const auth = { authorization: 'Bearer ' + ADMIN_KEY, 'content-type': 'application/json' };
const pid = rows("SELECT id FROM photos WHERE status = 'pending' AND st = ?", st)[0].id;
r = await call('/api/admin/odluka', { method: 'POST', body: JSON.stringify({ t: 'f', id: pid, a: 'no' }), headers: auth });
const after = rows('SELECT status, length(img) AS n, th FROM photos WHERE id = ?', pid)[0];
check(r.status === 200 && after.status === 'no' && after.n === 0 && after.th === null, 'photos: a rejected photo keeps its row but gives its bytes back', after);
r = await call('/api/foto/' + pid + '.jpg');
check(r.status === 404, 'photos: a rejected photo is not served', r.status);
ins.run('ab'.repeat(16), st, jpeg(4000));
sqlite.exec("UPDATE photos SET status = 'no' WHERE id = '" + 'ab'.repeat(16) + "'");
r = await call('/api/admin/red', { headers: auth });
check(r.status === 200 && rows("SELECT length(img) AS n FROM photos WHERE id = ?", 'ab'.repeat(16))[0].n === 0, 'photos: opening the queue frees the bytes of photos rejected earlier', r.status);

// ---------------------------------------------------------------- admin key
r = await call('/api/admin/red', { headers: { authorization: 'Bearer ' + ADMIN_KEY.slice(0, -1) + 'x' } });
check(r.status === 404, 'admin: a wrong key looks like a missing page', r.status);
r = await call('/api/admin/red', { headers: { authorization: 'Bearer ' + ADMIN_KEY } });
check(r.status === 200 && r.j && r.j.ok, 'admin: the right key opens the queue', r.status);

// ---------------------------------------------------------------- the health check: one count a minute
const h1 = await call('/api/zdravlje');
sqlite.exec("INSERT INTO checkins (st, s, at, ip) VALUES ('" + st + "', 'radi', 1, 'x')");
const h2 = await call('/api/zdravlje');
check(h1.status === 200 && h2.status === 200 && h1.j.checkins === h2.j.checkins, 'health: the count is read from D1 at most once a minute per isolate', [h1.j, h2.j]);

console.log(`\nsecurity worker: ${oks} ok, ${fails} failed`);
process.exit(fails ? 1 : 0);
