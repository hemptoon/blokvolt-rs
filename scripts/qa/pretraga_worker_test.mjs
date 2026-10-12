// Site search on the server (docs/RUNBOOK.md 3.8, 3.8b): the real worker/_worker.js called directly in node, with a D1
// look-alike on node:sqlite (worker/schema.sql loaded first), the built dist/ behind env.ASSETS, and a fake Workers AI
// binding (a word-hashing "embedding"). Checks: the search log (folding, cleaning, no IP, the owner's view), „Niste
// našli“ as a request, search by meaning switched off without the binding, and with it: the vector store in D1 filled
// step by step from the build's pieces, answers, a deploy that changes pages (the isolate reloads), the background step.
// Run after a build: node --no-warnings scripts/qa/pretraga_worker_test.mjs
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const DIST = path.join(REPO, 'dist');
if (!existsSync(path.join(DIST, 'assets', 'smisao', 'meta.json'))) { console.error('build first (python3 build.py)'); process.exit(2); }
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
sqlite.exec(readFileSync(path.join(REPO, 'worker', 'schema.sql'), 'utf8').replace(/CREATE TABLE IF NOT EXISTS (pretraga|sm_vec|sm_meta)[\s\S]*?\);\n/g, ''));
const DB = d1(sqlite);

// ---------------------------------------------------------------- the built site behind ASSETS (with a hook to fake a new deploy)
let assetHook = null;
const ASSETS = {
  fetch: async req => {
    const u = new URL(typeof req === 'string' ? req : req.url);
    if (assetHook) { const r = assetHook(u.pathname); if (r) return r; }
    let f = path.join(DIST, decodeURIComponent(u.pathname));
    if (f.endsWith('/')) f += 'index.html';
    return existsSync(f) ? new Response(readFileSync(f), { headers: { 'content-type': f.endsWith('.json') ? 'application/json' : 'text/html' } }) : new Response('not found', { status: 404 });
  },
};

// ---------------------------------------------------------------- fake Workers AI (bge-m3 shape)
const DIM = 1024;
let aiCalls = 0, aiTexts = 0;
function embed(text) {
  const v = new Array(DIM).fill(0);
  for (const w of String(text).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[^a-z0-9]+/).filter(x => x.length > 2)) {
    const h = createHash('md5').update(w.slice(0, 6)).digest();
    v[h.readUInt16BE(0) % DIM] += 1; v[h.readUInt16BE(2) % DIM] += 0.5;
  }
  const n = Math.hypot(...v) || 1;
  return v.map(x => x / n);
}
const AI = { run: async (model, inp) => { aiCalls++; aiTexts += inp.text.length; if (model !== '@cf/baai/bge-m3') throw new Error('model ' + model); return { shape: [inp.text.length, DIM], data: inp.text.map(embed) }; } };
const ADMIN_KEY = 'test-admin-key-0123456789abc';
const base = { DB, ASSETS, ADMIN_KEY };
let pending = [];
const ctx = { waitUntil: p => pending.push(p), passThroughOnException() {} };
async function call(env, p, { method = 'GET', body, headers = {}, ip = '10.0.0.1' } = {}) {
  const h = { 'cf-connecting-ip': ip, ...headers };
  if (method === 'POST' && !('origin' in h)) h.origin = 'https://www.blokvolt.rs';
  const res = await W.fetch(new Request('https://www.blokvolt.rs' + p, { method, headers: h, body }), env, ctx);
  await Promise.allSettled(pending); pending = [];
  const t = await res.text();
  let j = null; try { j = JSON.parse(t); } catch (e) {}
  return { status: res.status, j };
}
const rows = sql => sqlite.prepare(sql).all().map(r => ({ ...r }));
const stored = () => { try { return new Set(rows('SELECT id FROM sm_vec').map(r => r.id)); } catch (e) { return new Set(); } };

// ---------------------------------------------------------------- the search log
let r = await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: '  Evolnako ', l: 'sr', n: 7, w: 'home', f: 'Evolako' }) });
check(r.status === 200 && r.j.ok, 'log: a query is accepted', r);
await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'evolnako', l: 'sr', n: 7, w: 'page' }) });
await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'evolnako', l: 'sr', n: 7, c: 1 }) });
let lg = rows("SELECT * FROM pretraga WHERE q = 'evolnako'");
check(lg.length === 1 && lg[0].cnt === 2 && lg[0].clk === 1 && lg[0].home === 1 && lg[0].fix === 'evolako' && lg[0].n === 7, 'log: folded per day and query (2 searches, 1 from home, 1 opened, the correction)', lg);
await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'Zovite me 064/123-4567 ili pera.peric@gmail.com', l: 'sr', n: 0 }) });
lg = rows("SELECT q FROM pretraga WHERE q LIKE 'zovite%'");
check(lg.length === 1 && lg[0].q === 'zovite me # ili [e-mail]', 'log: phone numbers and e-mail addresses are cut out before writing', lg);
await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'субсидии', l: 'ru', n: 3 }) });
await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'x', l: 'sr', n: 0 }) });
const cols = rows('PRAGMA table_info(pretraga)').map(c => c.name);
check(!cols.some(c => /ip|fp|uid|ua/.test(c)) && cols.join(',') === 'day,l,q,n,cnt,clk,home,fix', 'log: no column for IP, fingerprint, account or browser', cols);
check(rows("SELECT q FROM pretraga WHERE q = 'x'").length === 0, 'log: one-letter queries are not kept');
r = await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'spam' }), headers: { origin: 'https://evil.example' } });
check(r.status === 403, 'log: another site cannot write to it', r.status);
r = await call(base, '/api/admin/pretraga');
check(r.status === 404, 'owner view: hidden without the key', r.status);
r = await call(base, '/api/admin/pretraga?d=30', { headers: { authorization: 'Bearer ' + ADMIN_KEY } });
const z = r.j && r.j.by_day && r.j.by_day[0];
check(r.j && r.j.ok && r.j.rows.length === 3 && z && z.cnt === 4 && z.zero === 1 && z.clk === 1, 'owner view: queries, searches per day, without results, opened', r.j);
// old rows go: the worker deletes rows older than 90 days now and then (2 % of the calls) — force it with many calls
sqlite.exec("INSERT INTO pretraga (day, l, q, n, cnt) VALUES ('2026-01-01', 'sr', 'stari upit', 1, 1)");
for (let i = 0; i < 400 && rows("SELECT q FROM pretraga WHERE day = '2026-01-01'").length; i++) {
  await call(base, '/api/pretraga', { method: 'POST', body: JSON.stringify({ q: 'tesla ' + (i % 3), l: 'en', n: 4 }), ip: '10.1.' + (i % 200) + '.' + Math.floor(i / 200) });
}
check(rows("SELECT q FROM pretraga WHERE day = '2026-01-01'").length === 0, 'log: rows older than 90 days are deleted');

// ---------------------------------------------------------------- „Niste našli šta tražite?“
r = await call(base, '/api/zahtev', { method: 'POST', body: JSON.stringify({ kind: 'pretraga', slug: '/pretraga/', data: { poruka: 'Tražim punjač za kamp prikolicu', upit: 'kamp prikolica', jezik: 'sr' }, hp: '', t: 4000 }) });
const rq = rows("SELECT kind, slug, data FROM requests WHERE kind = 'pretraga'");
check(r.j && r.j.ok && rq.length === 1 && JSON.parse(rq[0].data).upit === 'kamp prikolica', 'question box: stored as a request of kind pretraga (the bot shows it)', rq);

// ---------------------------------------------------------------- search by meaning, off
r = await call(base, '/api/smisao?q=gde+da+punim&l=sr');
check(r.status === 200 && r.j && r.j.ok === false && r.j.error === 'off', 'by meaning: off without the bindings', r);
r = await call(base, '/api/smisao/stanje');
check(r.j && r.j.on === false && r.j.need.join() === 'AI', 'by meaning: the state says which binding is missing', r.j);
check(rows("SELECT name FROM sqlite_master WHERE name LIKE 'sm_%'").length === 0, 'by meaning: nothing is created while it is off');

// ---------------------------------------------------------------- search by meaning, on
const on = { ...base, AI };
const man = JSON.parse(readFileSync(path.join(DIST, 'assets', 'smisao', 'meta.json'), 'utf8'));
// the background step: right after the bindings appear, any /api request starts filling the index (at most once a minute
// per isolate, so this is the only background step of this run)
r = await call(on, '/api/zdravlje');
check(r.status === 200 && stored().size === 20, 'by meaning: a plain /api request starts filling the store in the background', stored().size);
let st, steps = 0;
do { st = (await call(on, '/api/smisao/stanje', { ip: '10.9.0.' + (steps % 250) })).j; steps++; } while (st.state && st.state.done !== st.state.total && steps < 80);
check(st.on && st.state.done === man.n && st.state.total === man.n && stored().size === man.n && !st.state.err, `by meaning: all ${man.n} pieces embedded in ${steps} more steps (${aiCalls} AI calls)`, st);
check(aiTexts === man.n, 'by meaning: every piece embedded exactly once', aiTexts);
const piece = JSON.parse(readFileSync(path.join(DIST, 'assets', 'smisao', man.parts[0].f), 'utf8'))[3];
r = await call(on, '/api/smisao?l=sr&q=' + encodeURIComponent(piece.x.slice(0, 150)));
check(r.j && r.j.ok && r.j.hits.length >= 1 && r.j.hits[0].u === piece.u && r.j.hits.every(h => typeof h.s === 'number' && Object.keys(h).join() === 'u,s'), `by meaning: a page's own words find it first (${piece.u}); the answer is addresses and scores only`, r.j);
const before = aiTexts;
r = await call(on, '/api/smisao/stanje');
check(r.j.step === 'up to date' && aiTexts === before, 'by meaning: a step with nothing to do embeds nothing', r.j);
// a new deploy: the first part's pieces changed (new ids), one part removed
const man2 = JSON.parse(JSON.stringify(man));
const p0 = JSON.parse(readFileSync(path.join(DIST, 'assets', 'smisao', man.parts[0].f), 'utf8')).map(x => ({ ...x, id: 'n' + x.id.slice(1), x: x.x + ' (izmenjeno)' }));
man2.parts[0] = { f: 'p0-new.json', ids: p0.map(x => x.id) };
const dropped = man2.parts.pop();
man2.v = 'deploy2'; man2.n = man2.parts.reduce((s, p) => s + p.ids.length, 0);
assetHook = p => (p === '/assets/smisao/meta.json' ? Response.json(man2) : p === '/assets/smisao/p0-new.json' ? Response.json(p0) : null);
const before2 = aiTexts;
steps = 0;
do { st = (await call(on, '/api/smisao/stanje', { ip: '10.8.0.' + steps })).j; steps++; } while ((st.state.done !== st.state.total || st.state.v !== 'deploy2') && steps < 40);
check(st.state.v === 'deploy2' && st.state.done === man2.n && stored().size === man2.n && aiTexts - before2 === p0.length,
  `by meaning: after a deploy only the ${p0.length} changed pieces are embedded, ${dropped.ids.length + p0.length} old ones deleted`, { st: st.state, size: stored().size, emb: aiTexts - before2 });
check(!dropped.ids.some(id => stored().has(id)) && p0.every(x => stored().has(x.id)), 'by meaning: the store holds exactly the new build');
const q8 = rows('SELECT q FROM sm_vec LIMIT 1')[0].q;
check(Buffer.from(q8, 'base64').length === 1024 && q8.length < 1400, 'by meaning: a vector is 1024 bytes (base64 under 1,4 KB)', q8.length);
r = await call(on, '/api/smisao?l=sr&q=' + encodeURIComponent(p0[3].x.slice(0, 150)));
check(r.j && r.j.ok && r.j.hits.length && r.j.hits[0].u === p0[3].u, 'by meaning: after the change the search sees the new pieces (vectors reloaded)', r.j);
assetHook = null;
// errors are kept in the state and back off
const brokenAI = { run: async () => ({ shape: [1, 384], data: [new Array(384).fill(0.1)] }) };
sqlite.exec('UPDATE sm_meta SET lock_until = 0');
r = await call({ ...base, AI: brokenAI }, '/api/smisao/stanje');
check(/384 dimensions/.test(r.j.state.err || '') && r.j.state.lock_until > Date.now() / 1000 + 200, 'by meaning: a wrong embedding size is reported and the steps pause 5 minutes', r.j.state);
r = await call({ ...base, AI: brokenAI }, '/api/smisao?q=test&l=sr');
check(r.status === 502 && r.j.error === 'ai', 'by meaning: a wrong answer of the model is an error, not a result', r);

console.log(`\nsearch worker: ${oks} ok, ${fails} failed`);
process.exit(fails ? 1 : 0);
