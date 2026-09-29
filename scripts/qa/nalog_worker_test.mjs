// Accounts ("Moj BlokVolt") and the newsletter (Nedeljni pregled): the real worker/_worker.js in Miniflare (workerd) with
// an in-memory D1 that starts like the production database (the tables of worker/schema.sql before accounts existed),
// fake map files behind env.ASSETS, and three instances: MAIL_MODE=log (mail goes to the D1 table mail_log, codes and
// links are read from there), RESEND_API_KEY with the Resend API answered in this script (nothing leaves the machine),
// and neither (mail off). docs/RUNBOOK.md 3.27.
// Miniflare is not a dependency of the site: install it outside the repo and point MINIFLARE_DIR at it.
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_worker_test.mjs
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash, createHmac, randomBytes } from 'node:crypto';
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
const WHSEC = 'whsec_' + randomBytes(24).toString('base64');     // the signing secret of Resend's webhook (Svix)
const sha = s => createHash('sha256').update(s).digest('hex');
let fails = 0, oks = 0;
function check(cond, what, detail) {
  if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 400) : '')); }
}

// the map files the worker reads through env.ASSETS: 320 Serbian stations (to test the limit of 300), one station from
// a network's own list (mreze.json) and one of the neighbouring countries (region.json)
const STATIONS = Array.from({ length: 320 }, (_, i) => ({ id: 'st-' + String(i + 1).padStart(3, '0') }));
const ASSET_FILES = {
  '/assets/map/punjaci.json': { stations: STATIONS },
  '/assets/map/mreze.json': { upd: {}, add: [{ id: 'cg-65' }] },
  '/assets/map/region.json': { stations: [{ id: 'osm-n777', cc: 'hr' }] },
};
async function assets(req) {
  const f = ASSET_FILES[new URL(req.url).pathname];
  return f ? new Response(JSON.stringify(f), { headers: { 'content-type': 'application/json' } }) : new Response('not found', { status: 404 });
}
// the D1 database as it is in production before this change (no uid columns, no account tables)
const LEGACY = [
  `CREATE TABLE checkins (id INTEGER PRIMARY KEY AUTOINCREMENT, st TEXT NOT NULL, s TEXT NOT NULL, r INTEGER, c TEXT, n TEXT,
    cs TEXT NOT NULL DEFAULT 'none', at INTEGER NOT NULL, lang TEXT, ip TEXT, rep INTEGER NOT NULL DEFAULT 0)`,
  `CREATE TABLE photos (id TEXT PRIMARY KEY, st TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', at INTEGER NOT NULL, cap TEXT,
    w INTEGER, h INTEGER, mime TEXT NOT NULL, img BLOB NOT NULL, th BLOB, ip TEXT, rep INTEGER NOT NULL DEFAULT 0)`,
  `CREATE TABLE requests (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, slug TEXT, data TEXT NOT NULL, email TEXT,
    at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'new', ip TEXT)`,
  'CREATE TABLE rl (k TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (k, day))',
];
const resendCalls = [];
let resendPlan = [];             // statuses the fake Resend API answers with, one per call (then 200)
let resendDelay = 0;             // ms the next call takes (a slow Resend)
async function outbound(req) {
  const u = new URL(req.url);
  if (u.hostname !== 'api.resend.com') return new Response('blocked in tests', { status: 599 });
  if (resendDelay) { const ms = resendDelay; resendDelay = 0; await new Promise(ok => setTimeout(ok, ms)); }
  const body = await req.json();
  resendCalls.push({ headers: Object.fromEntries(req.headers), body });
  const st = resendPlan.length ? resendPlan.shift() : 200;
  return new Response(JSON.stringify(st === 200 ? { id: 'test-' + resendCalls.length } : { name: 'error' }), { status: st, headers: { 'content-type': 'application/json' } });
}
async function instance(bindings, legacy = LEGACY) {
  const mf = new Miniflare({
    modules: true, scriptPath: path.join(REPO, 'worker', '_worker.js'), compatibilityDate: '2025-09-01',
    d1Databases: ['DB'], bindings: { SITE, ADMIN_KEY: ADMIN, ...bindings },
    serviceBindings: { ASSETS: assets }, outboundService: outbound,
  });
  const db = await mf.getD1Database('DB');
  for (const s of legacy) await db.prepare(s).run();
  let ipn = 1;
  // one request; the visitor's IP is new each time unless given (rate limits are per IP fingerprint and per address)
  async function call(method, p, o = {}) {
    const headers = { 'cf-connecting-ip': o.ip || '10.0.' + Math.floor(ipn / 250) + '.' + (ipn++ % 250), ...(o.headers || {}) };
    if (o.cookie) headers.cookie = o.cookie;
    if (o.bearer) headers.authorization = 'Bearer ' + o.bearer;
    let body;
    if (o.json !== undefined) { body = JSON.stringify(o.json); headers['content-type'] = headers['content-type'] || 'application/json'; }
    else if (o.raw !== undefined) body = o.raw;
    if (method === 'POST' && !('origin' in headers)) headers.origin = SITE;
    for (const k of Object.keys(headers)) if (headers[k] === undefined) delete headers[k];   // {origin: undefined} = no Origin (native app)
    const res = await mf.dispatchFetch(SITE + p, { method, headers, body, redirect: 'manual' });
    const txt = await res.text();
    let j = null;
    try { j = JSON.parse(txt); } catch (e) { j = null; }
    return { status: res.status, j, txt, headers: res.headers, cookies: res.headers.getSetCookie() };
  }
  return { mf, db, call };
}
const cookieJar = cookies => cookies.map(c => c.split(';')[0]).filter(c => !/=$/.test(c)).join('; ');
const now = () => Math.floor(Date.now() / 1000);
const sleep = ms => new Promise(ok => setTimeout(ok, ms));

// ======================================================================= MAIL_MODE=log
const A = await instance({ MAIL_MODE: 'log', RESEND_WEBHOOK_SECRET: WHSEC });
const { call, db } = A;
const lastMail = (to, kind) => db.prepare('SELECT * FROM mail_log WHERE to_addr = ?1' + (kind ? ' AND kind = ?2' : '') + ' ORDER BY id DESC LIMIT 1').bind(...(kind ? [to, kind] : [to])).first();
const mailCount = async (to, kind) => (await db.prepare('SELECT COUNT(*) AS n FROM mail_log WHERE to_addr = ?1' + (kind ? ' AND kind = ?2' : '')).bind(...(kind ? [to, kind] : [to])).first()).n;
// /nalog/kod and /posta/prijava answer before the mail is sent (ctx.waitUntil): wait for the next mail of this kind
async function nextMail(to, kind, before) {
  for (let i = 0; i < 150; i++) {
    if ((await mailCount(to, kind)) > before) return lastMail(to, kind);
    await sleep(20);
  }
  return null;
}
const codeOf = m => (m && m.subject.match(/^(\d{6}) — /) || [])[1];
const linkOf = m => (m && m.html.match(/\/nalog\/\?prijava=([0-9a-f]{64})/) || [])[1];
// a code asked for by one browser: the answer, its cookies (bv_n) as .jar, and the mail as .mail
async function askCode(email, extra = {}, o = {}) {
  const before = await mailCount(email, 'code');
  const r = await call('POST', '/api/nalog/kod', { json: { email, lang: 'sr', hp: '', t: 4000, ...extra }, ...o });
  r.jar = cookieJar(r.cookies);
  r.mail = r.status === 200 ? await nextMail(email, 'code', before) : null;
  return r;
}
// the code of that browser's mail, typed in that browser (the app: the nonce of the answer instead of the cookie)
const enterCode = (email, r0, code, o = {}) => call('POST', '/api/nalog/potvrdi', r0.j && r0.j.nonce
  ? { json: { email, code, app: true, nonce: r0.j.nonce }, ...o } : { json: { email, code }, cookie: r0.jar, ...o });
async function signIn(email, extra = {}) {
  const r0 = await askCode(email, extra);
  const r = await enterCode(email, r0, codeOf(r0.mail));
  return { r0, r, cookie: cookieJar(r.cookies.filter(c => !c.startsWith('bv_n='))), mail: r0.mail };
}
// a newsletter sign-up; its work runs after the answer, so wait for the confirmation mail (when one is expected)
async function prijava(to, json, o = {}) {
  const before = await mailCount(to, 'confirm');
  const r = await call('POST', '/api/posta/prijava', { json: { lang: 'sr', src: '/pregled/', t: 4000, ...json }, ...o });
  r.mail = r.status === 200 ? await nextMail(to, 'confirm', before) : null;
  return r;
}

console.log('— status, validation, methods');
let r = await call('GET', '/api/nalog/status');
check(r.status === 200 && r.j.mail === true && /max-age=60/.test(r.headers.get('cache-control')), 'status: mail on in log mode, cached 60 s', r.j);
r = await call('POST', '/api/nalog/kod', { json: { email: 'not-an-address', t: 4000 } });
check(r.status === 400 && r.j.error === 'email', 'kod: bad address → 400 email', r);
for (const bad of [' a@b.c ', 'a@b', 'a..b@example.com', '.a@example.com', 'a@exa mple.com', 'x'.repeat(115) + '@a.rs', 'a@b.rs\u0007']) {
  r = await call('POST', '/api/nalog/kod', { json: { email: bad, t: 4000 } });
  check(r.status === 400, 'kod: rejects ' + JSON.stringify(bad).slice(0, 40), r.j);
}
r = await call('POST', '/api/nalog/kod', { json: { email: '  Mixed.Case+tag@Example.COM ', t: 4000 } });
check(r.status === 200 && (await nextMail('mixed.case+tag@example.com', 'code', 0)), 'kod: address trimmed and lower-cased', r.j);
r = await call('GET', '/api/nalog/kod');
check(r.status === 405 && r.headers.get('allow') === 'POST', 'GET on a POST path → 405 with Allow', r.status);
r = await call('POST', '/api/nalog/ja', { json: {} });
check(r.status === 405, 'POST on a GET path → 405', r.status);
r = await call('POST', '/api/nalog/kod', { raw: 'email=a@b.rs', headers: { 'content-type': 'application/x-www-form-urlencoded' } });
check(r.status === 415, 'kod: form body → 415', r.status);
r = await call('POST', '/api/nalog/kod', { json: { email: 'x@example.com', t: 4000 }, headers: { origin: 'https://evil.example' } });
check(r.status === 403, 'kod: foreign origin → 403', r.status);
r = await call('POST', '/api/nalog/kod', { json: { email: 'fast@example.com', t: 300 } });
check(r.status === 429 && r.j.error === 'too fast', 'kod: typed in 0,3 s → 429 too fast', r.j);
r = await call('POST', '/api/nalog/kod', { json: { email: 'bot@example.com', hp: 'x', t: 4000 } });
await sleep(300);
check(r.status === 200 && !(await lastMail('bot@example.com')), 'kod: honeypot → ok, nothing sent', r.j);
r = await call('GET', '/api/nalog/nepostoji');
check(r.status === 404, 'unknown path → 404', r.status);
for (const p of ['/api/nalog/ja', '/api/nalog/doprinosi', '/api/nalog/izvoz']) {
  r = await call('GET', p);
  check(r.status === 401 && r.j.error === 'auth' && r.headers.get('cache-control') === 'no-store', p + ' without a session → 401, no-store', r.status);
}
r = await call('GET', '/api/nalog/ja', { cookie: 'bv_s=' + 'a'.repeat(64) });
check(r.status === 401, 'ja: unknown token → 401', r.status);

console.log('— sign-in by code');
const E1 = 'vozac@example.com';
let s = await signIn(E1);
check(s.r0.status === 200 && s.r0.j.ok === true && !('nonce' in s.r0.j), 'kod: ok (the nonce only in the cookie)', s.r0.j);
const bvN = s.r0.cookies.find(c => c.startsWith('bv_n='));
check(bvN && /^bv_n=[0-9a-f]{32}; Path=\/api\/nalog; HttpOnly; SameSite=Lax; Max-Age=900$/.test(bvN), 'cookie bv_n: this browser\'s nonce, HttpOnly, Path=/api/nalog, Lax, 15 minutes (no Secure in log mode)', bvN);
check(s.r.cookies.some(c => /^bv_n=; Path=\/api\/nalog; HttpOnly; SameSite=Lax; Max-Age=0$/.test(c)), 'sign-in clears bv_n', s.r.cookies);
check(/^\d{6} — vaš kod za BlokVolt$/.test(s.mail.subject) && s.mail.text.includes(codeOf(s.mail)) && !/[<>]/.test(s.mail.text), 'code mail: subject, plain-text part', s.mail.subject);
check(s.mail.html.includes('/nalog/?prijava=') && s.mail.html.includes('Važi 15 minuta.') && !/<img|<link|<script/i.test(s.mail.html), 'code mail: link, preheader, no remote images', null);
const ac = await db.prepare('SELECT * FROM auth_codes').all();
check(ac.results.every(x => /^[0-9a-f]{64}$/.test(x.code_hash) && /^[0-9a-f]{64}$/.test(x.link_hash) && !JSON.stringify(x).includes(codeOf(s.mail))), 'auth_codes: only hashes stored', null);
check(s.r.status === 200 && s.r.j.ok && s.r.j.user.email === E1 && Array.isArray(s.r.j.favs) && s.r.j.sub === null, 'potvrdi: signed in, /ja shape', s.r.j);
const bvS = s.r.cookies.find(c => c.startsWith('bv_s=')), bvIn = s.r.cookies.find(c => c.startsWith('bv_in='));
check(bvS && /; Path=\/api; HttpOnly; SameSite=Lax; Max-Age=7776000$/.test(bvS) && !/Secure/.test(bvS), 'cookie bv_s: HttpOnly, Path=/api, Lax, 90 days (no Secure in log mode)', bvS);
check(bvIn && /^bv_in=1; Path=\/; SameSite=Lax; Max-Age=7776000$/.test(bvIn), 'cookie bv_in=1: Path=/, not HttpOnly', bvIn);
const C1 = s.cookie;
r = await call('GET', '/api/nalog/ja', { cookie: C1 });
check(r.status === 200 && r.j.user.email === E1 && r.j.user.tesla === false && !r.cookies.length, '/ja with the cookie; no new cookie within the hour', r.j);
const sess = await db.prepare('SELECT * FROM sessions').all();
check(sess.results.length === 1 && /^[0-9a-f]{64}$/.test(sess.results[0].h) && !C1.includes(sess.results[0].h) && sess.results[0].kind === 'web', 'sessions: only the hash of the token', sess.results);
await db.prepare('UPDATE sessions SET seen = seen - 7200, exp = exp - 7200').run();
r = await call('GET', '/api/nalog/ja', { cookie: C1 });
const ss = await db.prepare('SELECT seen, exp FROM sessions').first();
check(r.status === 200 && r.cookies.length === 2 && Math.abs(ss.exp - (now() + 90 * 86400)) < 5 && Math.abs(ss.seen - now()) < 5, 'sliding expiry: seen after an hour → exp now + 90 days, cookies renewed', ss);
r = await enterCode(E1, s.r0, codeOf(s.mail));
check(r.status === 400 && r.j.error === 'code', 'the same code again → 400 code (used once)', r.j);

console.log('— wrong code ×5, codes bound to the browser, expired code, link');
const E2 = 'pogresno@example.com';
const own = await askCode(E2);                                   // the owner's browser
const good = codeOf(own.mail);
const wrongCode = good === '000000' ? '111111' : '000000';
const answers = [];
for (let i = 0; i < 5; i++) answers.push(await enterCode(E2, own, wrongCode));
check(answers.slice(0, 4).every(x => x.status === 400 && x.j.error === 'code') && answers[4].status === 429 && answers[4].j.error === 'tries', 'four wrong → 400 code, fifth → 429 tries', answers.map(x => x.status));
r = await enterCode(E2, own, good);
check(r.status === 400 && !(await db.prepare('SELECT 1 FROM auth_codes WHERE email = ?1').bind(E2).first()), 'after five wrong the right code no longer works (code deleted)', r.j);
const EV = 'zrtva@example.com';
const victim = await askCode(EV), stranger = await askCode(EV);  // two browsers, two codes for one address
check(victim.jar !== stranger.jar && (await db.prepare('SELECT COUNT(*) AS n FROM auth_codes WHERE email = ?1').bind(EV).first()).n === 2, 'two browsers asking for one address: two codes, one each', null);
r = await enterCode(EV, victim, codeOf(stranger.mail));
check(r.status === 400 && r.j.error === 'code', "the other browser's code does not work here", r.j);
r = await call('POST', '/api/nalog/potvrdi', { json: { email: EV, code: codeOf(victim.mail) } });
check(r.status === 400 && r.j.error === 'code', 'no bv_n cookie: even the right code → 400', r.j);
const tries = [];
for (let i = 0; i < 5; i++) tries.push((await enterCode(EV, stranger, wrongCode)).status);
check(tries[4] === 429 && (await db.prepare('SELECT COUNT(*) AS n FROM auth_codes WHERE email = ?1').bind(EV).first()).n === 1, "a stranger's five wrong codes end only the stranger's code", tries);
r = await enterCode(EV, victim, codeOf(victim.mail));
check(r.status === 200 && r.j.user.email === EV, "the owner's code still works (no lock-out)", r.j);
const E3 = 'istekao@example.com';
const ex = await askCode(E3);
await db.prepare('UPDATE auth_codes SET exp = ?1 WHERE email = ?2').bind(now() - 1, E3).run();
r = await enterCode(E3, ex, codeOf(ex.mail));
check(r.status === 400 && r.j.error === 'code', 'expired code → 400 code', r.j);
const E4 = 'link@example.com';
let lr = await askCode(E4, { lang: 'en' });
let lm = lr.mail;
check(lm.subject.endsWith('— your BlokVolt code') && lm.html.includes(SITE + '/en/nalog/?prijava='), 'code mail in English links to /en/nalog/', lm.subject);
r = await call('POST', '/api/nalog/link', { json: { token: linkOf(lm), peek: true } });
check(r.status === 200 && r.j.email_masked === 'l***@example.com' && !r.j.user && !r.cookies.length, 'link {peek}: the masked address, no session', r.j);
r = await call('POST', '/api/nalog/link', { json: { token: linkOf(lm), peek: true } });
check(r.status === 200 && (await db.prepare('SELECT 1 FROM auth_codes WHERE email = ?1').bind(E4).first()), 'link {peek} twice: nothing spent', r.j);
r = await call('POST', '/api/nalog/link', { json: { token: 'f'.repeat(64), peek: true } });
check(r.status === 400 && r.j.error === 'code', 'link {peek} with an unknown token → 400', r.j);
r = await call('POST', '/api/nalog/link', { json: { token: linkOf(lm) } });
check(r.status === 200 && r.j.user.email === E4 && r.j.user.lang === 'en' && r.cookies.some(c => c.startsWith('bv_s=')), 'link token (the button), in a browser without bv_n: signed in (lang en)', r.j);
r = await call('POST', '/api/nalog/link', { json: { token: linkOf(lm), peek: true } });
check(r.status === 400, 'link {peek} after the sign-in → 400 (spent)', r.j);
r = await call('POST', '/api/nalog/link', { json: { token: linkOf(lm) } });
check(r.status === 400, 'link token used twice → 400', r.j);
r = await call('POST', '/api/nalog/link', { json: { token: 'f'.repeat(64) } });
check(r.status === 400, 'unknown link token → 400', r.j);
lr = await askCode(E4);
await call('POST', '/api/nalog/link', { json: { token: linkOf(lr.mail) } });
r = await enterCode(E4, lr, codeOf(lr.mail));
check(r.status === 400, 'the code of a mail whose link was used → 400 (one sign-in per mail)', r.j);
const first = await askCode(E4);
const again = await askCode(E4, {}, { cookie: first.jar });      // "Pošaljite ponovo" in the same browser
r = await enterCode(E4, first, codeOf(first.mail));
check(again.jar === first.jar && (r.status === 400 || codeOf(first.mail) === codeOf(again.mail)), 'a new code in the same browser replaces its previous one', r.j);
r = await enterCode(E4, first, codeOf(again.mail));
check(r.status === 200, '… and the new one works', r.j);

console.log('— app sign-in (bearer token)');
const E5 = 'app@example.com';
r = await askCode(E5, { app: true });
check(r.status === 200 && /^[0-9a-f]{32}$/.test(r.j.nonce) && !r.cookies.length, 'kod {app:true}: the nonce in the answer, no cookie', r.j);
const appNo = await call('POST', '/api/nalog/potvrdi', { json: { email: E5, code: codeOf(r.mail), app: true } });
check(appNo.status === 400, 'potvrdi {app:true} without the nonce → 400', appNo.j);
s = await signIn(E5, { app: true });
check(s.r.status === 200 && /^[0-9a-f]{64}$/.test(s.r.j.token) && !s.r.cookies.length, 'potvrdi {app:true, nonce}: token in the answer, no cookies', s.r.j);
r = await call('GET', '/api/nalog/ja', { bearer: s.r.j.token });
check(r.status === 200 && r.j.user.email === E5, '/ja with Authorization: Bearer', r.j);
const TOKEN5 = s.r.j.token;
r = await call('POST', '/api/nalog/omiljeni', { bearer: TOKEN5, json: { add: ['st-001'] }, headers: { origin: undefined } });
check(r.status === 200 && r.j.favs.join() === 'st-001', 'the app (no Origin header) can use the account', r.j);
const appSess = await db.prepare('SELECT kind FROM sessions WHERE uid = (SELECT id FROM users WHERE email = ?1)').bind(E5).first();
check(appSess.kind === 'app', 'sessions.kind = app', appSess);

console.log('— favourites');
r = await call('POST', '/api/nalog/omiljeni', { cookie: C1, json: { add: ['st-002', 'st-003', 'cg-65', 'osm-n777', 'nema-ga-1', '<script>'] } });
check(r.status === 200 && r.j.favs.length === 4 && r.j.dropped.includes('nema-ga-1') && r.j.dropped.includes('<script>'), 'add: map, network-list and region ids kept; unknown ids dropped', r.j);
r = await call('POST', '/api/nalog/omiljeni', { cookie: C1, json: { remove: ['st-003', 'osm-n777'] } });
check(r.j.favs.slice().sort().join() === 'cg-65,st-002', 'remove', r.j.favs);
r = await call('POST', '/api/nalog/omiljeni', { cookie: C1, json: { replace: STATIONS.map(x => x.id) } });
check(r.status === 200 && r.j.favs.length === 300 && r.j.full === true, 'replace with 320 → 300 kept, full', { n: r.j.favs.length, full: r.j.full });
r = await call('POST', '/api/nalog/omiljeni', { cookie: C1, json: { add: ['cg-65'] } });
check(r.j.favs.length === 300 && r.j.full === true && !r.j.favs.includes('cg-65'), 'add over 300 → not added, full', { n: r.j.favs.length });
r = await call('POST', '/api/nalog/omiljeni', { cookie: C1, json: { replace: ['st-010', 'st-011', 'st-012', 'st-010'] } });
check(r.j.favs.length === 3 && r.j.full === false, 'replace with 3 (duplicate ignored)', r.j.favs);
r = await call('GET', '/api/nalog/ja', { cookie: C1 });
check(r.j.favs.slice().sort().join() === 'st-010,st-011,st-012', '/ja lists the favourites', r.j.favs);
r = await call('POST', '/api/nalog/omiljeni', { json: { add: ['st-001'] } });
check(r.status === 401, 'favourites without a session → 401', r.status);

console.log('— settings');
for (const [b, err] of [[{ car: 'x'.repeat(81) }, 'car'], [{ dc: 'type2' }, 'dc'], [{ tesla: 'da' }, 'tesla'], [{ city: 'pariz' }, 'city'], [{ lang: 'de' }, 'lang']]) {
  r = await call('POST', '/api/nalog/podesavanja', { cookie: C1, json: b });
  check(r.status === 400 && r.j.error === err, 'settings: invalid ' + err + ' → 400', r.j);
}
r = await call('POST', '/api/nalog/podesavanja', { cookie: C1, json: { car: ' BYD  Dolphin Surf ', dc: 'ccs2', tesla: true, city: 'novi-sad', lang: 'ru' } });
check(r.status === 200 && r.j.user.car === 'BYD Dolphin Surf' && r.j.user.dc === 'ccs2' && r.j.user.tesla === true && r.j.user.city === 'novi-sad' && r.j.user.lang === 'ru', 'settings saved', r.j.user);
r = await call('POST', '/api/nalog/podesavanja', { cookie: C1, json: { car: '', dc: 'none', city: 'drugo', tesla: false } });
check(r.j.user.car === null && r.j.user.dc === 'none' && r.j.user.city === 'drugo' && r.j.user.tesla === false, 'settings: empty car, "drugo", no DC', r.j.user);
r = await call('POST', '/api/nalog/podesavanja', { cookie: C1, json: { car: 'x'.repeat(80) } });
check(r.status === 200 && r.j.user.car.length === 80, 'settings: car of 80 characters is fine', r.status);

console.log('— reports from the map');
const cols = (await db.prepare("SELECT name FROM pragma_table_info('checkins')").all()).results.map(x => x.name);
check(cols.includes('uid'), 'checkins got the uid column (ALTER TABLE on the old database)', cols);
r = await call('POST', '/api/stanica/st-005/prijava', { cookie: C1, json: { s: 'ok', r: 5, c: 'Radi', t: 4000, lang: 'sr' } });
check(r.status === 200, 'check-in while signed in', r.j);
r = await call('POST', '/api/stanica/st-006/prijava', { json: { s: 'broken', t: 4000 } });
check(r.status === 200, 'check-in without an account still works', r.j);
const jpeg = new Uint8Array(3000); jpeg.set([0xff, 0xd8, 0xff, 0xe0]);
const fd = new FormData();
fd.append('foto', new Blob([jpeg], { type: 'image/jpeg' }), 'f.jpg'); fd.append('t', '4000'); fd.append('w', '1600'); fd.append('h', '1200');
const mp = new Request('http://x/', { method: 'POST', body: fd });   // multipart bytes + boundary, as a browser sends them
r = await call('POST', '/api/stanica/st-005/foto', { cookie: C1, raw: new Uint8Array(await mp.arrayBuffer()), headers: { 'content-type': mp.headers.get('content-type') } });
check(r.status === 200 && r.j.pending === true, 'photo while signed in', r.j);
const ci = await db.prepare('SELECT st, uid FROM checkins ORDER BY id').all();
check(ci.results.length === 2 && ci.results[0].uid && ci.results[1].uid === null, 'check-in uid: set with a session, NULL without', ci.results);
r = await call('GET', '/api/nalog/doprinosi', { cookie: C1 });
check(r.status === 200 && r.j.checkins.length === 1 && r.j.checkins[0].st === 'st-005' && r.j.checkins[0].cs === 'ok' && r.j.photos.length === 1 && r.j.photos[0].status === 'pending' && !('img' in r.j.photos[0]),
  'doprinosi: own check-in (st, s, r, cs, at) and photo (st, status, at)', r.j);
check(!('id' in r.j.photos[0]) && Object.keys(r.j.photos[0]).sort().join() === 'at,st,status', 'doprinosi: a photo waiting for review has no id (its id alone would open it)', r.j.photos[0]);
const photoId = (await db.prepare("SELECT id FROM photos WHERE st = 'st-005'").first()).id;
await db.prepare("UPDATE photos SET status = 'ok' WHERE id = ?1").bind(photoId).run();
r = await call('GET', '/api/nalog/doprinosi', { cookie: C1 });
check(r.j.photos[0].id === photoId && r.j.photos[0].status === 'ok', 'doprinosi: an approved photo keeps its id', r.j.photos[0]);
await db.prepare("UPDATE photos SET status = 'pending' WHERE id = ?1").bind(photoId).run();
r = await call('GET', '/api/nalog/ja', { cookie: C1 });
const owner1 = r.j.user.owner;
check(/^[0-9a-f]{16}$/.test(owner1) && !JSON.stringify(r.j).includes((await db.prepare('SELECT id FROM users WHERE email = ?1').bind(E1).first()).id), '/ja: user.owner, a short hash (not the account id) for bv:fav-owner', owner1);

console.log('— newsletter without an account');
const N1 = 'citalac@example.com';
r = await prijava(N1, { email: N1, hp: '' });
let sub = await db.prepare('SELECT * FROM subs WHERE email = ?1').bind(N1).first();
check(r.status === 200 && sub.status === 'pending' && sub.topics === 'vesti,cene,punjaci' && sub.freq === 'w' && /^[0-9a-f]{32}$/.test(sub.token) && sub.src === '/pregled/' && sub.consent_v === 'pregled-v1', 'prijava: pending, default topics, token', sub);
let cons = await db.prepare('SELECT * FROM consents WHERE email = ?1 ORDER BY id').bind(N1).all();
check(cons.results.length === 1 && cons.results[0].granted === 1 && cons.results[0].src === '/pregled/' && cons.results[0].text_v === 'pregled-v1' && /^[0-9a-f]{24}$/.test(cons.results[0].ip), 'consent row: granted 1, source, text version, IP fingerprint', cons.results);
let cm = r.mail;
const TOK = (cm.html.match(/\/pregled\/potvrda\/\?t=([0-9a-f]{32})/) || [])[1];
check(cm.subject === 'Potvrdite prijavu na Nedeljni pregled' && TOK === sub.token && cm.html.includes('<b style="color:#0D111A">' + N1 + '</b>') && cm.html.includes('u petak'), 'confirmation mail: subject, address, link, day', cm.subject);
check(!JSON.parse(cm.hdr)['List-Unsubscribe'], 'confirmation mail has no List-Unsubscribe (nothing subscribed yet)', cm.hdr);
r = await prijava(N1, { email: N1, src: '/vesti/' });
sub = await db.prepare('SELECT * FROM subs WHERE email = ?1').bind(N1).first();
check(r.status === 200 && sub.token === TOK && sub.status === 'pending' && sub.src === '/vesti/', 'signing up again keeps the token, stays pending', sub);
r = await call('GET', '/api/posta/stanje?t=' + TOK);
check(r.status === 200 && r.j.status === 'pending' && r.j.email_masked === 'c***@example.com', 'stanje: pending, masked address', r.j);
r = await call('POST', '/api/posta/potvrdi', { json: { token: 'a'.repeat(32) } });
check(r.status === 400 && r.j.error === 'token', 'potvrdi: unknown token → 400', r.j);
r = await call('POST', '/api/posta/potvrdi', { json: { token: TOK } });
sub = await db.prepare('SELECT * FROM subs WHERE email = ?1').bind(N1).first();
check(r.status === 200 && r.j.status === 'on' && r.j.email_masked === 'c***@example.com' && sub.status === 'on' && sub.confirmed_at, 'potvrdi: pending → on', r.j);
cons = await db.prepare('SELECT * FROM consents WHERE email = ?1 ORDER BY id').bind(N1).all();
check(cons.results.at(-1).src === 'confirm-click' && cons.results.at(-1).granted === 1, 'consent row src confirm-click (only the button confirms)', cons.results.at(-1));
let wm = await lastMail(N1, 'welcome');
const wh = JSON.parse(wm.hdr);
check(wm.subject === 'Prijava je potvrđena — Nedeljni pregled' && wh['List-Unsubscribe'] === '<' + SITE + '/api/posta/odjava?t=' + TOK + '>, <mailto:hello@blokvolt.com?subject=odjava>' &&
  wh['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click' && wh['Idempotency-Key'] === 'welcome-' + TOK, 'welcome mail: subject, List-Unsubscribe one-click + mailto, Idempotency-Key', wh);
check(wm.html.includes('/pregled/odjava/?t=' + TOK + '&amp;teme=1') && wm.html.includes('obavestenja@mail.blokvolt.com') && wm.text.includes('/pregled/odjava/?t=' + TOK), 'welcome mail: preferences link, sender to add, text part', null);
const nWelcome = (await db.prepare("SELECT COUNT(*) AS n FROM mail_log WHERE to_addr = ?1 AND kind = 'welcome'").bind(N1).first()).n;
r = await call('POST', '/api/posta/potvrdi', { json: { token: TOK } });
const nWelcome2 = (await db.prepare("SELECT COUNT(*) AS n FROM mail_log WHERE to_addr = ?1 AND kind = 'welcome'").bind(N1).first()).n;
check(r.status === 200 && r.j.status === 'on' && nWelcome === 1 && nWelcome2 === 1, 'second confirmation click: ok, no second welcome mail', { nWelcome, nWelcome2 });
const nMail = (await db.prepare('SELECT COUNT(*) AS n FROM mail_log WHERE to_addr = ?1').bind(N1).first()).n;
r = await call('POST', '/api/posta/prijava', { json: { email: N1, lang: 'sr', src: '/pregled/', t: 4000 } });
await sleep(300);
const nMail2 = (await db.prepare('SELECT COUNT(*) AS n FROM mail_log WHERE to_addr = ?1').bind(N1).first()).n;
check(r.status === 200 && r.j.ok && nMail2 === nMail, 'sign-up of an address that is already on: same answer, nothing sent', { nMail, nMail2 });
// the source of a consent: a page path, or 'nepoznato'; the values the server writes itself cannot be sent
for (const [src, want] of [['confirm-click', 'nepoznato'], ['nalog', 'nepoznato'], ['https://evil.example/x', 'nepoznato'], ['/Pregled/', 'nepoznato'],
  [undefined, 'nepoznato'], ['/vesti/2026-09-24-eu-svaki-peti/', '/vesti/2026-09-24-eu-svaki-peti/']]) {
  const who = 'izvor' + Math.random().toString(36).slice(2, 8) + '@example.com';
  r = await prijava(who, { email: who, src });
  const c0 = await db.prepare('SELECT src FROM consents WHERE email = ?1').bind(who).first();
  const s0 = await db.prepare('SELECT src FROM subs WHERE email = ?1').bind(who).first();
  check(r.status === 200 && c0.src === want && s0.src === want, 'consent source ' + JSON.stringify(src) + ' → ' + want, { c0, s0 });
}

console.log('— preferences and unsubscribing');
r = await call('POST', '/api/posta/podesavanja', { json: { token: TOK, topics: ['cene', 'nesto'], freq: 'm', lang: 'en' } });
check(r.status === 200 && r.j.topics.join() === 'cene' && r.j.freq === 'm' && r.j.lang === 'en', 'podesavanja by token', r.j);
for (const [b, err] of [[{ token: TOK, topics: [] }, 'topics'], [{ token: TOK, freq: 'd' }, 'freq'], [{ token: TOK, lang: 'xx' }, 'lang']]) {
  r = await call('POST', '/api/posta/podesavanja', { json: b });
  check(r.status === 400 && r.j.error === err, 'podesavanja: invalid ' + err, r.j);
}
r = await call('POST', '/api/posta/podesavanja', { json: { token: 'b'.repeat(32), freq: 'w' } });
check(r.status === 404, 'podesavanja: unknown token → 404', r.status);
r = await call('GET', '/api/posta/odjava?t=' + TOK);
check(r.status === 303 && r.headers.get('location') === '/pregled/odjava/?t=' + TOK && (await db.prepare('SELECT status FROM subs WHERE token = ?1').bind(TOK).first()).status === 'on',
  'GET on the one-click address: 303 to the page, still subscribed', r.headers.get('location'));
r = await call('POST', '/api/posta/odjava?t=' + TOK, { raw: 'List-Unsubscribe=One-Click', headers: { 'content-type': 'application/x-www-form-urlencoded', origin: 'https://mail.google.com' } });
sub = await db.prepare('SELECT * FROM subs WHERE token = ?1').bind(TOK).first();
check(r.status === 200 && r.j.status === 'off' && sub.status === 'off' && sub.off_reason === 'link' && sub.off_at, 'one-click (RFC 8058 form body, foreign origin) → off', r.j);
cons = await db.prepare('SELECT * FROM consents WHERE email = ?1 ORDER BY id').bind(N1).all();
check(cons.results.at(-1).granted === 0 && cons.results.at(-1).src === 'one-click', 'withdrawal row granted 0', cons.results.at(-1));
r = await call('POST', '/api/posta/odjava?t=' + TOK, { raw: '' , headers: { origin: 'https://mail.google.com' } });
const nCons = (await db.prepare('SELECT COUNT(*) AS n FROM consents WHERE email = ?1').bind(N1).first()).n;
check(r.status === 200 && r.j.status === 'off' && nCons === cons.results.length, 'one-click again, empty body: 200, idempotent (no new row)', { status: r.status, nCons });
r = await call('POST', '/api/posta/odjava?t=' + 'c'.repeat(32), { raw: '' });
check(r.status === 404, 'one-click with an unknown token → 404', r.status);
r = await call('POST', '/api/posta/potvrdi', { json: { token: TOK } });
check(r.status === 400 && r.j.error === 'token', 'an old confirmation link after unsubscribing does not switch it on again', r.j);
r = await call('POST', '/api/posta/prijava', { json: { token: TOK, src: '/pregled/odjava/', t: 4000 } });
check(r.status === 429 && r.j.error === 'limit', 'a 4th sign-up of one address on one day → 429 (also by token)', r.j);
const N2 = 'odjava2@example.com';
await prijava(N2, { email: N2, lang: 'ru', src: '/ru/pregled/' });
const T2 = (await db.prepare('SELECT token FROM subs WHERE email = ?1').bind(N2).first()).token;
r = await call('POST', '/api/posta/odjava?t=' + T2, { raw: '', headers: { origin: 'https://outlook.live.com' } });
check(r.status === 200 && r.j.status === 'off', 'one-click with an empty body → off (also from pending)', r.j);
const N3 = 'stranica@example.com';
await prijava(N3, { email: N3 });
const T3 = (await db.prepare('SELECT token FROM subs WHERE email = ?1').bind(N3).first()).token;
await call('POST', '/api/posta/potvrdi', { json: { token: T3 } });
r = await call('POST', '/api/posta/odjava', { json: { token: T3 } });
cons = await db.prepare('SELECT src FROM consents WHERE email = ?1 ORDER BY id DESC LIMIT 1').bind(N3).first();
check(r.status === 200 && r.j.status === 'off' && cons.src === 'odjava', 'unsubscribe button on the page (JSON {token})', r.j);
await call('POST', '/api/posta/podesavanja', { json: { token: T3, topics: 'cene,punjaci' } });
r = await prijava(N3, { token: T3, lang: 'en', src: '/pregled/odjava/' });
sub = await db.prepare('SELECT * FROM subs WHERE token = ?1').bind(T3).first();
cm = r.mail;
check(r.status === 200 && sub.status === 'pending' && sub.topics === 'cene,punjaci' && sub.lang === 'en' && cm.subject === 'Confirm your subscription to the Weekly Digest' && cm.html.includes('/en/pregled/potvrda/?t=' + T3),
  '"Prijavite se ponovo" by token: pending again, new confirmation mail (English), topics kept', sub);

console.log('— newsletter in the account, opt-in at sign-in');
r = await call('POST', '/api/nalog/pregled', { cookie: C1, json: { on: true, topics: ['vesti', 'moji'], freq: 'w', lang: 'sr' } });
sub = await db.prepare('SELECT * FROM subs WHERE email = ?1').bind(E1).first();
check(r.status === 200 && r.j.sub.status === 'on' && sub.status === 'on' && sub.src === 'nalog' && sub.topics === 'vesti,moji' && sub.uid, 'account: on at once (address proved by the sign-in)', r.j);
cons = await db.prepare('SELECT * FROM consents WHERE email = ?1 ORDER BY id').bind(E1).all();
check(cons.results.length === 1 && cons.results[0].src === 'nalog' && cons.results[0].granted === 1, 'account: consent row src nalog', cons.results);
r = await call('POST', '/api/nalog/pregled', { cookie: C1, json: { on: true, freq: 'm' } });
cons = await db.prepare('SELECT COUNT(*) AS n FROM consents WHERE email = ?1').bind(E1).first();
check(r.j.sub.freq === 'm' && r.j.sub.topics.join() === 'vesti,moji' && cons.n === 1, 'account: changing settings while on writes no new consent', r.j.sub);
r = await call('POST', '/api/nalog/pregled', { cookie: C1, json: { on: false } });
cons = await db.prepare('SELECT * FROM consents WHERE email = ?1 ORDER BY id').bind(E1).all();
check(r.j.sub.status === 'off' && cons.results.at(-1).granted === 0 && cons.results.at(-1).src === 'nalog', 'account: off, withdrawal row', r.j.sub);
r = await call('POST', '/api/nalog/pregled', { cookie: C1, json: { on: 'da' } });
check(r.status === 400, 'account newsletter: on must be a boolean', r.j);
r = await call('POST', '/api/nalog/pregled', { cookie: C1, json: { on: true } });
check(r.j.sub.status === 'on', 'account: on again', r.j.sub);
r = await call('GET', '/api/nalog/ja', { cookie: C1 });
check(r.j.sub && r.j.sub.status === 'on' && r.j.sub.freq === 'm', '/ja shows the newsletter', r.j.sub);
r = await call('POST', '/api/posta/podesavanja', { cookie: C1, json: { freq: 'w' } });
check(r.status === 200 && r.j.freq === 'w', 'posta/podesavanja by session', r.j);
const E6 = 'optin@example.com';
s = await signIn(E6, { opt_in: true });
sub = await db.prepare('SELECT * FROM subs WHERE email = ?1').bind(E6).first();
cm = await lastMail(E6, 'confirm');
check(s.r.status === 200 && sub && sub.status === 'pending' && sub.src === 'nalog-prijava' && cm && s.r.j.sub.status === 'pending', 'opt-in at sign-in: pending + confirmation mail, never on without the click', sub);

console.log('— export and delete');
r = await call('GET', '/api/nalog/izvoz', { cookie: C1 });
check(r.status === 200 && /attachment; filename="blokvolt-nalog-\d{4}-\d{2}-\d{2}\.json"/.test(r.headers.get('content-disposition')) && r.headers.get('cache-control') === 'no-store', 'izvoz: JSON download', r.headers.get('content-disposition'));
check(r.j.user.email === E1 && r.j.favourites.length === 3 && r.j.newsletter.status === 'on' && r.j.consents.length >= 3 && r.j.checkins.length === 1 && r.j.photos.length === 1 &&
  !('img' in r.j.photos[0]) && !('th' in r.j.photos[0]) && r.j.sessions.some(x => x.this_device), 'izvoz: user, favourites, newsletter, consents, check-ins, photo metadata, sessions', Object.keys(r.j));
check(r.j.photos[0].status === 'pending' && !('id' in r.j.photos[0]), 'izvoz: no id of a photo waiting for review either', r.j.photos[0]);
const uid1 = (await db.prepare('SELECT id FROM users WHERE email = ?1').bind(E1).first()).id;
s = await signIn(E1);
const C1b = s.cookie;
r = await call('POST', '/api/nalog/obrisi', { cookie: C1, json: { confirm: 'da' } });
check(r.status === 400 && r.j.error === 'confirm', 'obrisi without confirm OBRISI → 400', r.j);
r = await call('POST', '/api/nalog/obrisi', { cookie: C1, json: { confirm: 'OBRISI' } });
check(r.status === 200 && r.cookies.some(c => /^bv_s=; .*Max-Age=0/.test(c)) && r.cookies.some(c => /^bv_in=; .*Max-Age=0/.test(c)), 'obrisi: ok, both cookies cleared', r.cookies);
const left = {
  users: (await db.prepare('SELECT COUNT(*) AS n FROM users WHERE id = ?1').bind(uid1).first()).n,
  sessions: (await db.prepare('SELECT COUNT(*) AS n FROM sessions WHERE uid = ?1').bind(uid1).first()).n,
  favs: (await db.prepare('SELECT COUNT(*) AS n FROM favs WHERE uid = ?1').bind(uid1).first()).n,
  subs: (await db.prepare('SELECT COUNT(*) AS n FROM subs WHERE email = ?1').bind(E1).first()).n,
  plain: (await db.prepare('SELECT COUNT(*) AS n FROM consents WHERE email = ?1').bind(E1).first()).n,
};
const hashed = await db.prepare("SELECT * FROM consents WHERE email LIKE 'sha256:%' ORDER BY id").all();
check(!left.users && !left.sessions && !left.favs && !left.subs && !left.plain, 'obrisi: user, sessions (all devices), favourites, newsletter gone; no consent row keeps the address', left);
check(hashed.results.length >= 4 && hashed.results.every(x => /^sha256:[0-9a-f]{64}$/.test(x.email)) && hashed.results.at(-1).src === 'brisanje-naloga' && hashed.results.at(-1).granted === 0,
  'consent history kept with sha256 of the address, ending with a withdrawal', hashed.results.map(x => [x.src, x.granted]));
const ci2 = await db.prepare("SELECT uid, c FROM checkins WHERE st = 'st-005'").first();
const ph2 = await db.prepare("SELECT uid FROM photos WHERE st = 'st-005'").first();
check(ci2.uid === null && ci2.c === 'Radi' && ph2.uid === null, 'check-in and photo stay, uid set to NULL', { ci2, ph2 });
r = await call('GET', '/api/nalog/ja', { cookie: C1b });
check(r.status === 401, 'the other device of the deleted account is signed out too', r.status);

console.log('— sign out');
const E7 = 'odjava@example.com';
const d1 = (await signIn(E7)).cookie, d2 = (await signIn(E7)).cookie, d3 = (await signIn(E7)).cookie;
r = await call('POST', '/api/nalog/odjava', { cookie: d1, json: {} });
check(r.status === 200 && r.cookies.length === 2 && (await call('GET', '/api/nalog/ja', { cookie: d1 })).status === 401 && (await call('GET', '/api/nalog/ja', { cookie: d2 })).status === 200, 'odjava: this device only', r.cookies);
r = await call('POST', '/api/nalog/odjava', { cookie: d2, json: { all: true } });
check((await call('GET', '/api/nalog/ja', { cookie: d3 })).status === 401, 'odjava {all:true}: every device', r.j);

console.log('— rate limits');
const RL = 'limit@example.com', mkOf = e => sha('rl:' + e).slice(0, 24);
const hourIp = [];
for (let i = 0; i < 6; i++) hourIp.push((await askCode(RL, {}, { ip: '192.0.2.10' })).status);
check(hourIp.slice(0, 5).every(x => x === 200) && hourIp[5] === 429, 'kod: 5 an hour per address from one IP, the 6th → 429', hourIp);
r = await askCode(RL, {}, { ip: '192.0.2.11' });
check(r.status === 200, 'kod: the same address from another IP still gets a code (nobody can use up the limit of an address)', r.j);
await db.prepare('UPDATE rl SET n = 10 WHERE k LIKE ?1').bind('nd:' + mkOf(RL) + ':%').run();
r = await askCode(RL, {}, { ip: '192.0.2.11' });
const r12 = await askCode(RL, {}, { ip: '192.0.2.12' });
check(r.status === 429 && r12.status === 200, 'kod: 10 a day per address from one IP, then 429 there only', [r.status, r12.status]);
await db.prepare('UPDATE rl SET n = 30 WHERE k = ?1').bind('na:' + mkOf(RL)).run();
r = await askCode(RL, {}, { ip: '192.0.2.13' });
check(r.status === 429 && r.j.error === 'limit', 'kod: 30 a day per address from everywhere, then 429', r.j);
const sameIp = [];
for (let i = 0; i < 31; i++) sameIp.push((await call('POST', '/api/nalog/kod', { ip: '192.0.2.77', json: { email: 'ip' + i + '@example.com', t: 4000 } })).status);
check(sameIp.slice(0, 30).every(x => x === 200) && sameIp[30] === 429, 'kod: 30 a day per IP, the 31st → 429', sameIp);
const guesses = [];
for (let i = 0; i < 31; i++) guesses.push((await call('POST', '/api/nalog/potvrdi', { ip: '203.0.113.5', json: { email: 'guess' + i + '@example.com', code: '123456' } })).status);
check(guesses.slice(0, 30).every(x => x === 400) && guesses[30] === 429, 'potvrdi: 30 failed attempts a day per IP, the 31st → 429', guesses);
const later = await askCode('posle@example.com', {}, { ip: '203.0.113.5' });
r = await enterCode('posle@example.com', later, codeOf(later.mail), { ip: '203.0.113.5' });
const r6 = await enterCode('posle@example.com', later, codeOf(later.mail), { ip: '203.0.113.6' });
check(r.status === 429 && r.j.error === 'limit' && r6.status === 200, 'potvrdi: after that even the right code from that IP → 429 for the day; from another IP it works', [r.status, r6.status]);
const perMail = [];
for (let i = 0; i < 4; i++) perMail.push((await call('POST', '/api/posta/prijava', { json: { email: 'pl@example.com', src: '/pregled/', t: 4000 } })).status);
check(perMail.slice(0, 3).every(x => x === 200) && perMail[3] === 429 && (await call('POST', '/api/posta/prijava', { json: { email: 'pl@example.com', t: 4000 } })).j.error === 'limit', 'posta/prijava: 3 a day per address, the 4th → 429 limit', perMail);
const perIp = [];
for (let i = 0; i < 21; i++) perIp.push((await call('POST', '/api/posta/prijava', { ip: '198.51.100.9', json: { email: 'pi' + i + '@example.com', t: 4000 } })).status);
check(perIp.slice(0, 20).every(x => x === 200) && perIp[20] === 429, 'posta/prijava: 20 a day per IP, the 21st → 429', perIp);
const rl = await db.prepare("SELECT k FROM rl WHERE k LIKE 'n%' OR k LIKE 'p%'").all();
check(rl.results.every(x => !x.k.includes('@')), 'rate-limit keys do not contain the address', rl.results.slice(0, 3));

console.log("— Resend's webhook: signature, bounces, complaints, suppression");
// a request as Svix sends it: "v1,<base64 HMAC-SHA256 of id.timestamp.body>" with the base64 key after "whsec_"
function svix(ev, o = {}) {
  const body = JSON.stringify(ev), id = o.id || 'msg_' + randomBytes(8).toString('hex'), ts = String(o.ts ?? now());
  const sig = createHmac('sha256', Buffer.from((o.secret || WHSEC).slice(6), 'base64')).update(id + '.' + ts + '.' + body).digest('base64');
  return { raw: body, headers: { 'content-type': 'application/json', origin: undefined, 'svix-id': id, 'svix-timestamp': ts,
    'svix-signature': o.sig !== undefined ? o.sig : (o.extra ? o.extra + ' ' : '') + 'v1,' + sig } };
}
const bounced = (to, type = 'Permanent') => ({ type: 'email.bounced', created_at: new Date().toISOString(),
  data: { email_id: 'em_1', from: 'BlokVolt <obavestenja@mail.blokvolt.com>', to: [to], subject: 'x', bounce: { message: 'm', subType: 'General', type } } });
const complained = (to, from = 'BlokVolt <obavestenja@mail.blokvolt.com>') => ({ type: 'email.complained', created_at: new Date().toISOString(),
  data: { email_id: 'em_2', from, to: [to], subject: 'x' } });
async function onSub(email) {
  await prijava(email, { email });
  const tok = (await db.prepare('SELECT token FROM subs WHERE email = ?1').bind(email).first()).token;
  await call('POST', '/api/posta/potvrdi', { json: { token: tok } });
  return tok;
}
const W1 = 'odbijen@example.com', W2 = 'zalba@example.com', W3 = 'bez-prijave@example.com';
await onSub(W1);
await onSub(W2);
r = await call('POST', '/api/posta/resend', { raw: JSON.stringify(bounced(W1)), headers: { 'content-type': 'application/json', origin: undefined } });
check(r.status === 401 && r.j.error === 'signature', 'webhook without the Svix headers → 401', r.j);
r = await call('POST', '/api/posta/resend', svix(bounced(W1), { sig: 'v1,' + Buffer.from('x'.repeat(32)).toString('base64') }));
check(r.status === 401, 'webhook with a wrong signature → 401', r.j);
r = await call('POST', '/api/posta/resend', svix(bounced(W1), { secret: 'whsec_' + randomBytes(24).toString('base64') }));
check(r.status === 401, 'webhook signed with another secret → 401', r.j);
r = await call('POST', '/api/posta/resend', svix(bounced(W1), { ts: now() - 6 * 60 }));
check(r.status === 401, 'webhook with a timestamp 6 minutes old → 401 (replay)', r.j);
r = await call('POST', '/api/posta/resend', svix(bounced(W1), { ts: now() + 6 * 60 }));
check(r.status === 401, 'webhook with a timestamp 6 minutes ahead → 401', r.j);
const w1 = await db.prepare('SELECT status FROM subs WHERE email = ?1').bind(W1).first();
check(w1.status === 'on' && !(await db.prepare('SELECT 1 FROM suppressions').first()), 'refused webhooks changed nothing', w1);
r = await call('POST', '/api/posta/resend', svix(bounced(W1, 'Transient'), { ts: now() - 4 * 60 }));
check(r.status === 200 && r.j.ignored === true && (await db.prepare('SELECT status FROM subs WHERE email = ?1').bind(W1).first()).status === 'on',
  'a soft bounce (Transient), signed 4 minutes ago: 200, ignored', r.j);
const evB = svix(bounced(W1), { extra: 'v1,' + Buffer.from('y'.repeat(32)).toString('base64') });
r = await call('POST', '/api/posta/resend', evB);
let wsub = await db.prepare('SELECT status, off_reason, off_at FROM subs WHERE email = ?1').bind(W1).first();
let wsup = await db.prepare('SELECT * FROM suppressions WHERE email_hash = ?1').bind(sha(W1)).first();
let wcons = await db.prepare('SELECT src, granted FROM consents WHERE email = ?1 ORDER BY id DESC LIMIT 1').bind(W1).first();
check(r.status === 200 && wsub.status === 'off' && wsub.off_reason === 'bounce' && wsub.off_at && wsup && wsup.reason === 'bounce' && wcons.src === 'bounce' && wcons.granted === 0,
  'hard bounce (one of two signatures valid): newsletter off (bounce), address suppressed (SHA-256 only), closing consent row', { wsub, wsup, wcons });
const nC1 = (await db.prepare('SELECT COUNT(*) AS n FROM consents WHERE email = ?1').bind(W1).first()).n;
r = await call('POST', '/api/posta/resend', svix(bounced(W1)));
const nC2 = (await db.prepare('SELECT COUNT(*) AS n FROM consents WHERE email = ?1').bind(W1).first()).n;
check(r.status === 200 && nC1 === nC2, 'the same event again: 200, nothing new', { nC1, nC2 });
r = await call('POST', '/api/posta/resend', svix(complained(W2)));
wsub = await db.prepare('SELECT status, off_reason FROM subs WHERE email = ?1').bind(W2).first();
wsup = await db.prepare('SELECT reason FROM suppressions WHERE email_hash = ?1').bind(sha(W2)).first();
check(r.status === 200 && wsub.status === 'off' && wsub.off_reason === 'complaint' && wsup.reason === 'complaint', 'complaint: newsletter off (complaint), address suppressed', { wsub, wsup });
r = await call('POST', '/api/posta/resend', svix(complained(W3)));
check(r.status === 200 && (await db.prepare('SELECT 1 FROM suppressions WHERE email_hash = ?1').bind(sha(W3)).first()), 'complaint for an address without a sign-up: suppressed', r.j);
r = await call('POST', '/api/posta/resend', svix({ type: 'email.delivered', data: { from: 'BlokVolt <obavestenja@mail.blokvolt.com>', to: ['ok@example.com'] } }));
check(r.status === 200 && r.j.ignored === true && !r.j.other_sender, 'other events: 200, ignored', r.j);
// one Resend team sends for both brands: events of mail sent by Evolako reach this endpoint too and must change nothing
const W5 = 'evolako-klijent@example.com';
await onSub(W5);
const evo = { ...bounced(W5), data: { ...bounced(W5).data, from: 'Evolako <obavestenja@mail.evolako.com>' } };
r = await call('POST', '/api/posta/resend', svix(evo));
const w5 = await db.prepare('SELECT status FROM subs WHERE email = ?1').bind(W5).first();
check(r.status === 200 && r.j.ignored === true && r.j.other_sender === true && w5.status === 'on' && !(await db.prepare('SELECT 1 FROM suppressions WHERE email_hash = ?1').bind(sha(W5)).first()),
  "a hard bounce of Evolako's mail (same Resend team): 200, ignored, the subscription stays on, nothing suppressed", { j: r.j, w5 });
r = await call('POST', '/api/posta/resend', svix(complained(W5, 'obavestenja@mail.evolako.com')));
check(r.status === 200 && r.j.other_sender === true && (await db.prepare('SELECT status FROM subs WHERE email = ?1').bind(W5).first()).status === 'on',
  "a complaint about Evolako's mail (bare address): ignored", r.j);
r = await call('POST', '/api/posta/resend', svix({ type: 'email.complained', data: { to: [W5] } }));
check(r.status === 200 && r.j.other_sender === true && (await db.prepare('SELECT status FROM subs WHERE email = ?1').bind(W5).first()).status === 'on',
  'an event without a sender: ignored', r.j);
r = await call('POST', '/api/posta/resend', svix(complained(W5, 'BlokVolt <OBAVESTENJA@Mail.BlokVolt.com>')));
check(r.status === 200 && r.j.suppressed === 1 && (await db.prepare('SELECT status FROM subs WHERE email = ?1').bind(W5).first()).status === 'off',
  'our own sender in another letter case: counted (complaint → off)', r.j);
check(!(await db.prepare("SELECT 1 FROM suppressions WHERE email_hash LIKE '%@%' OR length(email_hash) != 64").first()), 'suppressions hold no addresses', null);
// user-initiated mail still goes to a suppressed address (sign-in code, confirmation link); the rest is held,
// a successful sign-in lifts 'bounce', a confirmed sign-up lifts 'bounce' and 'complaint'
const cnt = async (to, kind) => (await db.prepare('SELECT COUNT(*) AS n FROM mail_log WHERE to_addr = ?1 AND kind = ?2').bind(to, kind).first()).n;
const supOf = async e => db.prepare('SELECT reason FROM suppressions WHERE email_hash = ?1').bind(sha(e)).first();
const c1 = await cnt(W1, 'code');
const kW1 = await askCode(W1);
check(kW1.status === 200 && kW1.j.ok && kW1.mail && (await cnt(W1, 'code')) === c1 + 1 && (await supOf(W1)), 'bounce-suppressed address: the requested sign-in code is still sent, the row stays until sign-in', { c1 });
r = await enterCode(W1, kW1, codeOf(kW1.mail));
check(r.status === 200 && r.j.ok && !(await supOf(W1)), 'successful sign-in lifts the bounce suppression', r.j);
const cf2 = await cnt(W2, 'confirm'), wl2 = await cnt(W2, 'welcome');
const r2 = await prijava(W2, { email: W2 });
const cmW2 = r2.mail;
check(r2.status === 200 && r2.j.ok && (await cnt(W2, 'confirm')) === cf2 + 1 && (await supOf(W2)), 'complaint-suppressed address: a new sign-up still gets the confirmation link', { cf2 });
const TW2 = (cmW2.html.match(/\/pregled\/potvrda\/\?t=([0-9a-f]{32})/) || [])[1];
r = await call('POST', '/api/posta/potvrdi', { json: { token: TW2 } });
check(r.status === 200 && r.j.status === 'on' && !(await supOf(W2)) && (await cnt(W2, 'welcome')) === wl2 + 1, 'the confirmation click lifts the complaint and the welcome goes out', r.j);
check(!!(await supOf(W3)), 'an address that did nothing stays suppressed', null);
// switching the newsletter on in the account (a proved address, an explicit act) lifts a complaint too
const W4 = 'nalog-zalba@example.com';
const sW4 = await signIn(W4);
await call('POST', '/api/posta/resend', svix(complained(W4)));
const wl4 = await cnt(W4, 'welcome');
check((await supOf(W4)).reason === 'complaint', 'an account holder marked a mail as spam: suppressed (complaint)', null);
r = await call('POST', '/api/nalog/pregled', { cookie: sW4.cookie, json: { on: true } });
const cW4 = await db.prepare('SELECT src, granted FROM consents WHERE email = ?1 ORDER BY id DESC LIMIT 1').bind(W4).first();
check(r.status === 200 && r.j.sub.status === 'on' && !(await supOf(W4)) && cW4.src === 'nalog' && cW4.granted === 1 && (await cnt(W4, 'welcome')) === wl4 + 1,
  'the account switch "on" lifts the complaint, writes the consent row and the welcome goes out (never "on" but blocked)', { cW4 });

console.log('— housekeeping and admin counts');
await db.prepare("INSERT INTO subs (email, lang, topics, freq, status, token, src, consent_v, created_at) VALUES ('staro@example.com', 'sr', 'vesti', 'w', 'pending', ?1, '/pregled/', 'pregled-v1', ?2)").bind('d'.repeat(32), now() - 31 * 86400).run();
await db.prepare("INSERT INTO consents (email, kind, granted, text_v, src, at) VALUES ('staro@example.com', 'pregled', 1, 'pregled-v1', '/pregled/', ?1)").bind(now() - 31 * 86400).run();
await db.prepare("INSERT INTO consents (email, kind, granted, text_v, src, at) VALUES ('davno@example.com', 'pregled', 1, 'pregled-v1', '/pregled/', ?1), ('davno@example.com', 'pregled', 0, 'pregled-v1', 'one-click', ?2)").bind(now() - 1200 * 86400, now() - 1100 * 86400).run();
await db.prepare('INSERT INTO sessions (h, uid, at, seen, exp, kind) VALUES (?1, ?2, 1, 1, 2, ?3)').bind('e'.repeat(64), 'nobody', 'web').run();
await prijava('brojanje@example.com', { email: 'brojanje@example.com' });
await call('POST', '/api/posta/potvrdi', { json: { token: (await db.prepare("SELECT token FROM subs WHERE email = 'brojanje@example.com'").first()).token } });
r = await call('GET', '/api/admin/posta');
check(r.status === 404, 'admin/posta without the key → 404', r.status);
r = await call('GET', '/api/admin/posta', { headers: { authorization: 'Bearer ' + ADMIN } });
check(r.status === 200 && typeof r.j.users === 'number' && r.j.subs_on === 3 && r.j.subs_pending >= 1 && r.j.subs_off >= 1 && r.j.by_lang.sr === 3 && r.j.suppressed === 2,
  'admin/posta: users, subs on / pending / off, subscribers by language, suppressed addresses', r.j);
const hk = {
  stale: await db.prepare("SELECT COUNT(*) AS n FROM subs WHERE email = 'staro@example.com'").first(),
  plain: await db.prepare("SELECT COUNT(*) AS n FROM consents WHERE email = 'staro@example.com'").first(),
  staleCons: await db.prepare('SELECT src, granted FROM consents WHERE email = ?1 ORDER BY id').bind('sha256:' + sha('staro@example.com')).all(),
  old: await db.prepare("SELECT COUNT(*) AS n FROM consents WHERE email = 'davno@example.com'").first(),
  sess: await db.prepare("SELECT COUNT(*) AS n FROM sessions WHERE uid = 'nobody'").first(),
};
check(hk.stale.n === 0 && hk.plain.n === 0 && hk.staleCons.results.length === 2 && hk.staleCons.results[1].src === 'isteklo' && hk.staleCons.results[1].granted === 0 && hk.old.n === 0 && hk.sess.n === 0,
  'housekeeping: pending > 30 days deleted, its consent rows keep only sha256 of the address (+ "isteklo"); history 3 years after withdrawal and expired sessions deleted', hk);
const nLog = (await db.prepare('SELECT COUNT(*) AS n FROM mail_log').first()).n;
check(nLog > 20 && !(await db.prepare("SELECT 1 FROM mail_log WHERE kind NOT IN ('code', 'confirm', 'welcome')").first()), 'mail_log: ' + nLog + ' mails, three kinds', nLog);
await A.mf.dispose();

// ======================================================================= Resend (fake API in this script)
console.log('— Resend: production mode');
const B = await instance({ RESEND_API_KEY: 're_test_123' });
// the mail work runs after the answer: wait until the fake API has had n more calls
async function resendAfter(n0, n = 1, ms = 4000) {
  for (let t = 0; t < ms; t += 20) { if (resendCalls.length >= n0 + n) return resendCalls.slice(n0); await sleep(20); }
  return resendCalls.slice(n0);
}
let n0 = resendCalls.length;
resendDelay = 1500;
let t0 = Date.now();
r = await B.call('POST', '/api/nalog/kod', { json: { email: 'prod@example.com', lang: 'ru', t: 4000 } });
const tKod = Date.now() - t0;
const bvNp = r.cookies.find(c => c.startsWith('bv_n='));
check(r.status === 200 && tKod < 1000 && resendCalls.length === n0, 'kod answers before the mail is sent (Resend taking 1,5 s: answer in ' + tKod + ' ms)', tKod);
check(bvNp && /; HttpOnly; Secure; SameSite=Lax; Max-Age=900$/.test(bvNp), 'production cookie bv_n carries Secure', bvNp);
let rc = (await resendAfter(n0)).at(-1);
check(r.status === 200 && rc && rc.headers.authorization === 'Bearer re_test_123' && /^code-[0-9a-f]{40}$/.test(rc.headers['idempotency-key'] || ''), 'code mail sent to Resend with the key and an Idempotency-Key', rc && rc.headers);
check(rc.body.from === 'BlokVolt <obavestenja@mail.blokvolt.com>' && rc.body.to.join() === 'prod@example.com' && rc.body.reply_to === 'hello@blokvolt.com' &&
  /^\d{6} — ваш код для BlokVolt$/.test(rc.body.subject) && rc.body.html.includes('/ru/nalog/?prijava=') && rc.body.text && rc.body.tags[0].value === 'code' && !rc.body.headers,
  'payload: from, to, reply_to, subject (ru), html, text, tags; no List-Unsubscribe on a code mail', rc.body.subject);
const pcode = rc.body.subject.slice(0, 6);
r = await B.call('POST', '/api/nalog/potvrdi', { json: { email: 'prod@example.com', code: pcode }, cookie: bvNp.split(';')[0] });
check(r.status === 200 && r.cookies.every(c => /; Secure;/.test(c)), 'production cookies carry Secure', r.cookies);
n0 = resendCalls.length;
resendDelay = 1500;
t0 = Date.now();
r = await B.call('POST', '/api/posta/prijava', { json: { email: 'spor@example.com', lang: 'sr', src: '/vesti/', t: 4000 } });
const tPr = Date.now() - t0;
check(r.status === 200 && tPr < 1000 && (await resendAfter(n0)).length === 1, 'posta/prijava answers before the sign-up mail is sent (' + tPr + ' ms)', tPr);
resendPlan = [500];
const before = resendCalls.length;
r = await B.call('POST', '/api/posta/prijava', { json: { email: 'retry@example.com', lang: 'sr', src: '/vesti/', t: 4000 } });
const two = await resendAfter(before, 2);
check(r.status === 200 && two.length === 2 && two[0].headers['idempotency-key'] === two[1].headers['idempotency-key'] && /^confirm-/.test(two[0].headers['idempotency-key']), 'a 5xx from Resend is retried once with the same Idempotency-Key', two.map(x => x.headers['idempotency-key']));
const ptok = (two[1].body.html.match(/potvrda\/\?t=([0-9a-f]{32})/) || [])[1];
r = await B.call('POST', '/api/posta/potvrdi', { json: { token: ptok } });
rc = resendCalls.at(-1);
check(r.status === 200 && rc.body.headers && rc.body.headers['List-Unsubscribe'] === '<' + SITE + '/api/posta/odjava?t=' + ptok + '>, <mailto:hello@blokvolt.com?subject=odjava>' &&
  rc.body.headers['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click' && rc.headers['idempotency-key'] === 'welcome-' + ptok && rc.body.tags[0].value === 'welcome', 'welcome mail through Resend: List-Unsubscribe headers', rc.body.headers);
resendPlan = [422];
n0 = resendCalls.length;
r = await B.call('POST', '/api/nalog/kod', { json: { email: 'refused@example.com', t: 4000 } });
const one = await resendAfter(n0, 1);
await sleep(1200);
check(r.status === 200 && one.length === 1 && resendCalls.length === n0 + 1, 'Resend refuses the mail: the answer is the same (the failure is only logged), no retry', r.j);
await B.mf.dispose();

console.log('— mail off');
const C = await instance({});
r = await C.call('GET', '/api/nalog/status');
check(r.j.mail === false, 'status: mail false without RESEND_API_KEY', r.j);
r = await C.call('POST', '/api/nalog/kod', { json: { email: 'x@example.com', t: 4000 } });
check(r.status === 503 && r.j.error === 'mail_off', 'kod → 503 mail_off', r.j);
r = await C.call('POST', '/api/posta/prijava', { json: { email: 'x@example.com', t: 4000 } });
check(r.status === 503 && r.j.error === 'mail_off', 'posta/prijava → 503 mail_off', r.j);
r = await C.call('POST', '/api/posta/resend', svix(complained('x@example.com')));
check(r.status === 503 && r.j.error === 'webhook_off', 'webhook without RESEND_WEBHOOK_SECRET → 503 webhook_off', r.j);
r = await C.call('GET', '/api/zdravlje');
check(r.status === 200 && r.j.ok === true, '/api/zdravlje unchanged', r.j);
await C.mf.dispose();

console.log('— lazy migration');
// a database with auth_codes of the older shape (one code per address) and without the photos table
const OLD_CODES = `CREATE TABLE auth_codes (email TEXT PRIMARY KEY, code_hash TEXT, link_hash TEXT, salt TEXT, exp INTEGER,
  tries INTEGER DEFAULT 0, at INTEGER, lang TEXT, opt_in INTEGER DEFAULT 0)`;
const D = await instance({ MAIL_MODE: 'log' }, [LEGACY[0], LEGACY[2], LEGACY[3], OLD_CODES]);
const colsOf = async t => (await D.db.prepare(`SELECT name FROM pragma_table_info('${t}')`).all()).results.map(x => x.name);
r = await D.call('POST', '/api/nalog/kod', { json: { email: 'mig@example.com', t: 4000 } });
check(r.status === 200 && (await colsOf('auth_codes')).includes('nonce') && (await colsOf('checkins')).includes('uid'),
  'migration: auth_codes of the older shape replaced (nonce), checkins got uid', await colsOf('auth_codes'));
await D.db.prepare(LEGACY[1]).run();                                     // the missing table appears
r = await D.call('POST', '/api/nalog/kod', { json: { email: 'mig2@example.com', t: 4000 } });
check(r.status === 200 && (await colsOf('photos')).includes('uid'), 'migration: a step that failed (no photos table) is tried again on the next request', await colsOf('photos'));
await D.mf.dispose();

console.log(`\n${oks} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
