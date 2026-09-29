// Nedeljni pregled — the sender (docs/RUNBOOK.md 3.27, "Sending the issues"): the real worker/_worker.js in Miniflare
// (workerd) with an in-memory D1, the issue files behind env.ASSETS written by this script in the shape build.py writes
// them (scripts/pregled.py), and mail either in MAIL_MODE=log (to the D1 table mail_log) or through a fake Resend API
// answered here (nothing leaves the machine). The build side (the files themselves) is scripts/qa/pregled_build_test.py;
// the whole chain with the real build is scripts/qa/pregled_ui_test.py.
// Miniflare is not a dependency of the site: install it outside the repo and point MINIFLARE_DIR at it.
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/pregled_sender_test.mjs
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
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
const TEAM = 'hello@blokvolt.com';
const sha = s => createHash('sha256').update(s).digest('hex');
const H = s => sha('content:' + s);                 // a content hash of the issue files
let fails = 0, oks = 0;
function check(cond, what, detail) {
  if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 500) : '')); }
}
const sleep = ms => new Promise(ok => setTimeout(ok, ms));
const now = () => Math.floor(Date.now() / 1000);
const PAST = new Date(Date.now() - 3600e3).toISOString().replace(/\.\d+Z$/, 'Z');
const FUTURE = new Date(Date.now() + 86400e3).toISOString().replace(/\.\d+Z$/, 'Z');
const MONTH = new Date().toISOString().slice(0, 7);

// an issue file as build.py writes it: three languages, the intro and one section per topic, the reader's links as
// {{PREFS}} / {{UNSUB}}, every other link through the click counter
function issue(slug, o = {}) {
  const topics = o.topics || ['vesti', 'cene'], date = o.date || MONTH + '-02', langs = {};
  for (const l of ['sr', 'en', 'ru']) {
    langs[l] = {
      subject: `Broj ${slug} (${l})`, preheader: 'Uvod broja',
      head_html: `<!DOCTYPE html><html lang="${l}"><body><p>HEAD-${l}</p><a href="${SITE}/api/posta/klik?i=${slug}&amp;l=1">web</a><table>`,
      head_text: `HEAD-${l}\n`,
      sections: [{ topic: 'uvod', html: `<tr><td>UVOD-${l}</td></tr>`, text: `UVOD-${l}\n` }]
        .concat(topics.map(t => ({ topic: t, html: `<tr><td>SEC-${t}-${l}</td></tr>`, text: `SEC-${t}-${l}\n` }))),
      foot_html: '</table><a href="{{PREFS}}">teme</a> · <a href="{{UNSUB}}">odjava</a></body></html>',
      foot_text: 'teme: {{PREFS}}\nodjava: {{UNSUB}}\n',
    };
  }
  return { slug, date, month: date.slice(0, 7), title: 'Broj ' + slug, send_at: o.send_at || PAST, status: o.status || 'preview',
    approved_hash: o.approved_hash || '', hash: o.hash || H(slug), topics,
    links: o.links || { 1: SITE + '/pregled/' + slug + '/', 2: SITE + '/mapa/', 3: 'https://blokvolt.com/hr/', 4: 'https://evil.example/', 5: 'javascript:alert(1)' }, langs };
}

// the database as in production before the sender (the tables of worker/schema.sql the worker does not create itself)
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
let resendPlan = [];                 // statuses the fake Resend API answers with, one per call (then 200)
async function outbound(req) {
  const u = new URL(req.url);
  if (u.hostname !== 'api.resend.com') return new Response('blocked in tests', { status: 599 });
  const body = await req.json();
  resendCalls.push({ headers: Object.fromEntries(req.headers), body, t: Date.now() });
  const st = resendPlan.length ? resendPlan.shift() : 200;
  return new Response(JSON.stringify(st === 200 ? { id: 'em-' + resendCalls.length } : { name: 'error' }), { status: st, headers: { 'content-type': 'application/json' } });
}
const SOURCE = fs.readFileSync(path.join(REPO, 'worker', '_worker.js'), 'utf8');

// one worker with its own files behind env.ASSETS ({path: object}); pregled: false rewrites the CFG line as build.py does
async function instance(bindings, o = {}) {
  const files = {};
  const script = o.pregled === false ? SOURCE.replace(/^(const CFG = \{.*)pregled: true(.*\};)$/m, '$1pregled: false$2') : SOURCE;
  if (o.pregled === false && script === SOURCE) throw new Error('CFG line not found');
  const mf = new Miniflare({
    modules: true, script, compatibilityDate: '2025-09-01', d1Databases: ['DB'], bindings: { SITE, ADMIN_KEY: ADMIN, ...bindings },
    serviceBindings: { ASSETS: async req => {
      const f = files[new URL(req.url).pathname];
      return f ? new Response(JSON.stringify(f), { headers: { 'content-type': 'application/json' } }) : new Response('not found', { status: 404 });
    } }, outboundService: outbound,
  });
  const db = await mf.getD1Database('DB');
  for (const s of LEGACY) await db.prepare(s).run();
  async function call(method, p, x = {}) {
    const headers = { 'cf-connecting-ip': '10.9.' + Math.floor(Math.random() * 250) + '.' + Math.floor(Math.random() * 250), ...(x.headers || {}) };
    let body;
    if (x.json !== undefined) { body = JSON.stringify(x.json); headers['content-type'] = 'application/json'; }
    if (method === 'POST' && !('origin' in headers) && x.origin !== false) headers.origin = SITE;
    for (const k of Object.keys(headers)) if (headers[k] === undefined) delete headers[k];
    const res = await mf.dispatchFetch(SITE + p, { method, headers, body, redirect: 'manual' });
    const txt = await res.text();
    let j = null;
    try { j = JSON.parse(txt); } catch (e) { j = null; }
    return { status: res.status, j, txt, headers: res.headers };
  }
  // the issues the "deploy" has: index.json and one file each
  function publish(...list) {
    for (const k of Object.keys(files)) if (k.startsWith('/pregled-mail/')) delete files[k];
    files['/pregled-mail/index.json'] = { about: 'test', issues: list.map(i => ({ slug: i.slug, date: i.date, month: i.month, title: i.title,
      send_at: i.send_at, status: i.status, approved_hash: i.approved_hash, hash: i.hash, topics: i.topics })) };
    for (const i of list) files['/pregled-mail/' + i.slug + '.json'] = i;
  }
  // a tick right now: the lock of the previous one is set back (a real tick waits a minute)
  async function tick(x = {}) {
    await db.prepare('UPDATE pg_lock SET at = 0, until = 0').run().catch(() => {});
    return call('POST', '/api/posta/tick', { origin: false, ...x });
  }
  // a subscriber as the sign-up flows leave it
  async function sub(email, o2 = {}) {
    const token = o2.token || sha('token:' + email).slice(0, 32);
    await db.prepare(`INSERT INTO subs (email, lang, topics, freq, status, token, src, consent_v, created_at, confirmed_at)
      VALUES (?1, ?2, ?3, ?4, ?5, ?6, '/pregled/', 'pregled-v1', ?7, ?7)`)
      .bind(email, o2.lang || 'sr', o2.topics === undefined ? 'vesti,cene,punjaci' : o2.topics, o2.freq || 'w', o2.status || 'on', token, now()).run();
    return token;
  }
  const mails = (kind, to) => db.prepare('SELECT * FROM mail_log WHERE kind = ?1' + (to ? ' AND to_addr = ?2' : '') + ' ORDER BY id').bind(...(to ? [kind, to] : [kind])).all().then(r => r.results);
  const rows = slug => db.prepare('SELECT * FROM pg_queue WHERE slug = ?1 ORDER BY id').bind(slug).all().then(r => r.results);
  // the first /api request of an instance starts the background tick: let it finish before the tests take over
  async function settle() {
    await call('GET', '/api/zdravlje');
    for (let i = 0; i < 100; i++) {
      const l = await db.prepare('SELECT at, until FROM pg_lock').first().catch(() => null);
      if (l && l.at && !l.until) return;
      await sleep(20);
    }
  }
  return { mf, db, call, publish, tick, sub, mails, rows, settle };
}
const issueOf = (r, slug) => ((r.j && r.j.issues) || []).find(x => x.slug === slug) || {};

// ======================================================================= MAIL_MODE=log
console.log('— previews');
const A = await instance({ MAIL_MODE: 'log' });
await A.settle();
let r = await A.tick();
check(r.status === 503 && r.j.ok === false && r.j.error === 'no_index', 'no index file (a broken deploy) → 503 no_index', r.j);
r = await A.call('GET', '/api/posta/tick');
check(r.status === 405, 'GET on the tick → 405 (only POST works)', r.status);
const P = issue('probni', { status: 'preview', hash: H('probni-1') });
A.publish(P);
r = await A.tick();
let pv = await A.mails('preview');
check(r.status === 200 && issueOf(r, 'probni').action === 'preview_sent' && pv.length === 3, 'preview: three mails in one tick', { j: r.j, n: pv.length });
check(pv.every(m => m.to_addr === TEAM) && pv.map(m => m.subject).join('|') === ['sr', 'en', 'ru'].map(l => `[PREVIEW ${P.hash.slice(0, 8)}] Broj probni (${l})`).join('|'),
  'preview: sr, en, ru to the team address only, subject "[PREVIEW <8 hex>] …"', pv.map(m => [m.to_addr, m.subject]));
check(pv.every(m => !JSON.parse(m.hdr)['List-Unsubscribe'] && JSON.parse(m.hdr)['Idempotency-Key'].startsWith('pregled-preview-probni-')), 'preview: no List-Unsubscribe, an Idempotency-Key per issue, hash and language', pv.map(m => m.hdr));
check(pv.every(m => ['UVOD-', 'SEC-vesti-', 'SEC-cene-'].every(x => m.html.includes(x)) && !m.html.includes('{{') && !m.text.includes('{{') && /\/pregled\/"/.test(m.html)),
  'preview: every section, the reader links replaced by /pregled/', pv[0].html.slice(-200));
check(pv[1].html.includes('HEAD-en') && pv[1].html.includes(SITE + '/en/pregled/') && pv[2].text.includes(SITE + '/ru/pregled/'), 'preview: each language its own text and links', null);
check((await A.db.prepare('SELECT hash FROM pg_previews WHERE slug = ?1').bind('probni').all()).results.map(x => x.hash).join() === P.hash, 'pg_previews: (slug, hash) recorded', null);
r = await A.tick();
check(issueOf(r, 'probni').action === 'previewed' && (await A.mails('preview')).length === 3, 'the same hash again: nothing sent (a preview once per hash)', r.j);
P.hash = H('probni-2');
A.publish(P);
r = await A.tick();
pv = await A.mails('preview');
check(issueOf(r, 'probni').action === 'preview_sent' && pv.length === 6 && pv[5].subject.startsWith('[PREVIEW ' + P.hash.slice(0, 8) + ']'), 'the text changed (new hash): a new preview', pv.map(m => m.subject));
r = await A.tick();
check(r.j && r.j.ok && !(await A.rows('probni')).length, 'a preview never queues a reader', r.j);

console.log('— approval checks');
await A.sub('citalac@example.com');
const B1 = issue('nije-previewed', { status: 'approved', hash: H('b1'), approved_hash: H('b1') });
A.publish(P, B1);
r = await A.tick();
let notes = await A.mails('notice');
check(issueOf(r, 'nije-previewed').action === 'blocked' && issueOf(r, 'nije-previewed').reason === 'not_previewed' && !(await A.rows('nije-previewed')).length,
  'approved, but that hash was never previewed: nothing queued', issueOf(r, 'nije-previewed'));
check(notes.length === 1 && notes[0].to_addr === TEAM && notes[0].text.includes('Выпуск nije-previewed не отправлен: хэш одобрения не совпадает с превью'),
  'one notice to the team (Russian): «Выпуск … не отправлен: хэш одобрения не совпадает с превью»', notes.map(m => m.text));
r = await A.tick();
check(issueOf(r, 'nije-previewed').action === 'blocked' && (await A.mails('notice')).length === 1, 'the next tick: still nothing, no second notice the same day', null);
// previewed, approved, then the text changed
const B2 = issue('promenjen', { status: 'preview', hash: H('b2-a') });
A.publish(P, B2);
await A.tick();
B2.status = 'approved'; B2.approved_hash = H('b2-a'); B2.hash = H('b2-b');
A.publish(P, B2);
r = await A.tick();
notes = await A.mails('notice');
check(issueOf(r, 'promenjen').action === 'blocked' && issueOf(r, 'promenjen').reason === 'hash_changed' && !(await A.rows('promenjen')).length &&
  notes.length === 2 && notes[1].text.includes('текст изменился после одобрения'), 'approved hash previewed, but the file changed since: nothing queued, one notice', { i: issueOf(r, 'promenjen'), t: notes.map(m => m.text.slice(0, 80)) });
// approved and previewed, send_at still ahead
const B3 = issue('kasnije', { status: 'preview', hash: H('b3'), send_at: FUTURE });
A.publish(B3);
await A.tick();
B3.status = 'approved'; B3.approved_hash = B3.hash;
A.publish(B3);
r = await A.tick();
check(issueOf(r, 'kasnije').action === 'waiting' && issueOf(r, 'kasnije').send_at === FUTURE && !(await A.rows('kasnije')).length, 'approved before send_at: waiting, nothing queued', issueOf(r, 'kasnije'));

console.log('— queueing and sending');
const TOK = {};
TOK.s1 = await A.sub('s1@example.com', { lang: 'sr' });
TOK.s2 = await A.sub('s2@example.com', { lang: 'en', topics: 'cene' });
TOK.s3 = await A.sub('s3@example.com', { lang: 'ru', topics: 'moji' });
TOK.s4 = await A.sub('s4@example.com', { status: 'pending' });
TOK.s5 = await A.sub('s5@example.com', { status: 'off' });
TOK.s6 = await A.sub('s6@example.com');
await A.db.prepare('INSERT INTO suppressions (email_hash, reason, at) VALUES (?1, ?2, ?3)').bind(sha('s6@example.com'), 'bounce', now()).run();
TOK.s7 = await A.sub('s7@example.com', { freq: 'm' });
await A.db.prepare(`INSERT INTO pg_queue (slug, email, lang, month, status, attempts, at, sent_at) VALUES ('ranije', 's7@example.com', 'sr', ?1, 'sent', 1, ?2, ?2)`).bind(MONTH, now()).run();
TOK.s8 = await A.sub('s8@example.com', { freq: 'm', lang: 'ru' });
TOK.s9 = await A.sub('s9@example.com', { topics: null });
TOK.s10 = await A.sub('s10@example.com', { topics: 'punjaci' });
const C1 = issue('broj-1', { status: 'preview', hash: H('c1') });
A.publish(C1);
await A.tick();
C1.status = 'approved'; C1.approved_hash = C1.hash;
A.publish(C1);
r = await A.tick();
const q1 = await A.rows('broj-1');
const who = q1.map(x => x.email).sort().join();
check(issueOf(r, 'broj-1').action === 'enqueued' && who === ['citalac', 's1', 's2', 's6', 's8', 's9'].map(x => x + '@example.com').sort().join(),
  'enqueue: readers who are on, with a topic of the issue (vesti, cene); not pending, off, "moji" only, "punjaci" only, or monthly with an issue this month', who);
check(q1.find(x => x.email === 's2@example.com').lang === 'en' && q1.find(x => x.email === 's8@example.com').lang === 'ru' && q1.every(x => x.month === MONTH),
  'rows carry the language and the issue month', q1.map(x => [x.email, x.lang, x.month]));
check(!r.txt.includes('@') && r.j.sent === 5 && issueOf(r, 'broj-1').sent === 5 && issueOf(r, 'broj-1').cancelled === 1 && issueOf(r, 'broj-1').queued === 0,
  'the same tick sends: 5 sent, the suppressed one cancelled, the answer has no address', r.j);
let sent = await A.mails('pregled');
const m1 = sent.find(m => m.to_addr === 's1@example.com'), m2 = sent.find(m => m.to_addr === 's2@example.com'), m8 = sent.find(m => m.to_addr === 's8@example.com');
check(sent.length === 5 && !sent.some(m => m.to_addr === 's6@example.com'), 'suppressed address: no mail (checked again at sending)', sent.map(m => m.to_addr));
const h1 = JSON.parse(m1.hdr);
check(h1['List-Unsubscribe'] === `<${SITE}/api/posta/odjava?t=${TOK.s1}>, <mailto:${TEAM}?subject=odjava>` && h1['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click' &&
  h1['Idempotency-Key'] === 'pregled-broj-1-' + sha('s1@example.com').slice(0, 16), 'newsletter mail: List-Unsubscribe one-click + mailto, Idempotency-Key pregled-<slug>-<sha256(address)[0..16]>', h1);
check(m1.subject === 'Broj broj-1 (sr)' && ['UVOD-sr', 'SEC-vesti-sr', 'SEC-cene-sr'].every(x => m1.html.includes(x)) &&
  m1.html.includes(`${SITE}/pregled/odjava/?t=${TOK.s1}&amp;teme=1`) && m1.html.includes(`${SITE}/pregled/odjava/?t=${TOK.s1}"`) && m1.text.includes(`/pregled/odjava/?t=${TOK.s1}&teme=1`),
  'sr reader: every section, the own settings and unsubscribe links (HTML escaped, text plain)', m1.html.slice(-260));
check(m2.subject === 'Broj broj-1 (en)' && m2.html.includes('UVOD-en') && m2.html.includes('SEC-cene-en') && !m2.html.includes('SEC-vesti') && m2.html.includes(`${SITE}/en/pregled/odjava/?t=${TOK.s2}`),
  'en reader with topic cene: the intro and the cene section only, English links', m2.html);
check(m8 && m8.html.includes('HEAD-ru') && m8.html.includes('/ru/pregled/odjava/'), 'monthly reader, first issue of the month: sent, in Russian', m8 && m8.subject);
check(!sent.some(m => /\{\{|\}\}/.test(m.html + m.text)), 'no placeholder left in any mail', null);
const st1 = Object.fromEntries((await A.db.prepare(`SELECT email, status, note, attempts, provider_id, sent_at FROM pg_queue WHERE slug = 'broj-1'`).all()).results.map(x => [x.email, x]));
check(st1['s1@example.com'].status === 'sent' && st1['s1@example.com'].attempts === 1 && /^log-\d+$/.test(st1['s1@example.com'].provider_id) && st1['s1@example.com'].sent_at &&
  st1['s6@example.com'].status === 'cancelled' && st1['s6@example.com'].note === 'suppressed', 'rows: sent (attempts, provider id, time), suppressed → cancelled', st1);
r = await A.tick();
check(issueOf(r, 'broj-1').action === 'done' && (await A.rows('broj-1')).length === 6 && (await A.mails('pregled')).length === 5, 'repeated ticks: no new rows, no second mail', r.j);
// a second issue of the month: monthly readers skip it, weekly ones get it
const C2 = issue('broj-2', { status: 'preview', hash: H('c2'), topics: ['vesti'] });
A.publish(C1, C2);
await A.tick();
C2.status = 'approved'; C2.approved_hash = C2.hash;
A.publish(C1, C2);
r = await A.tick();
const q2 = (await A.rows('broj-2')).map(x => x.email).sort();
check(!q2.includes('s8@example.com') && q2.includes('s1@example.com') && !q2.includes('s2@example.com'), 'second issue of the month: the monthly reader is not queued again; topic vesti only for readers of vesti', q2);

console.log('— the click counter');
r = await A.call('GET', '/api/posta/klik?i=broj-1&l=2');
check(r.status === 302 && r.headers.get('location') === SITE + '/mapa/' && r.headers.get('cache-control') === 'no-store', 'klik: 302 to the link of the table, no-store', [r.status, r.headers.get('location')]);
await A.call('GET', '/api/posta/klik?i=broj-1&l=2');
r = await A.call('GET', '/api/posta/klik?i=broj-1&l=3');
check(r.headers.get('location') === 'https://blokvolt.com/hr/', 'klik: blokvolt.com links too', r.headers.get('location'));
for (const [q, what] of [['i=broj-1&l=4', 'a link to another site in the table'], ['i=broj-1&l=5', 'a javascript: link'], ['i=broj-1&l=99', 'an unknown link number'],
  ['i=nema-ga&l=1', 'an unknown issue'], ['i=../x&l=1', 'a bad slug'], ['i=broj-1&l=0', 'link 0'], ['i=broj-1', 'no link number']]) {
  r = await A.call('GET', '/api/posta/klik?' + q);
  check(r.status === 302 && r.headers.get('location') === SITE + '/pregled/', 'klik: ' + what + ' → /pregled/', r.headers.get('location'));
}
r = await A.call('HEAD', '/api/posta/klik?i=broj-1&l=1');
check(r.status === 302 && r.headers.get('location') === SITE + '/pregled/broj-1/', 'klik: HEAD (link checkers) redirects too', r.status);
await sleep(300);
const clicks = (await A.db.prepare('SELECT slug, l, day, n FROM pg_clicks ORDER BY l').all()).results;
check(clicks.length === 2 && clicks[0].l === 2 && clicks[0].n === 2 && clicks[1].l === 3 && clicks[1].n === 1 && clicks[0].day === new Date().toISOString().slice(0, 10),
  'clicks: per issue, link and day; not for refused links or HEAD', clicks);
check(Object.keys((await A.db.prepare('SELECT * FROM pg_clicks LIMIT 1').first()) || {}).sort().join() === 'day,l,n,slug', 'pg_clicks holds nothing about the reader', null);

console.log('— admin: stats and stop');
r = await A.call('GET', '/api/admin/posta');
check(r.status === 404, 'admin/posta without the key → 404', r.status);
r = await A.call('GET', '/api/admin/posta', { headers: { authorization: 'Bearer ' + ADMIN } });
const a1 = r.j && r.j.pregled && r.j.pregled.issues.find(x => x.slug === 'broj-1');
check(r.status === 200 && a1 && a1.rows.sent === 5 && a1.rows.cancelled === 1 && a1.rows.queued === 0 && a1.previews.length === 1 && a1.enqueued_at &&
  a1.clicks.find(c => c.l === 2).n === 2 && a1.clicks.find(c => c.l === 2).url === SITE + '/mapa/', 'admin/posta: per issue rows by status, previews, clicks per link with the URL', a1);
check(r.j.pregled.on === true && r.j.pregled.cap === 30 && r.j.pregled.sent_today >= 5 && typeof r.j.subs_on === 'number', 'admin/posta: cap, sent today, and the old counts', r.j.pregled);
const D1i = issue('za-stop', { status: 'preview', hash: H('d1'), send_at: FUTURE });
A.publish(D1i);
await A.tick();
D1i.status = 'approved'; D1i.approved_hash = D1i.hash;
A.publish(D1i);
r = await A.call('POST', '/api/admin/posta', { json: { stop: 'za-stop' } });
check(r.status === 404, 'admin stop without the key → 404', r.status);
r = await A.call('POST', '/api/admin/posta', { json: { stop: 'za-stop' }, headers: { authorization: 'Bearer ' + ADMIN, origin: 'https://evil.example' } });
check(r.status === 403, 'admin stop from another origin → 403', r.status);
r = await A.call('POST', '/api/admin/posta', { json: { stop: '../x' }, headers: { authorization: 'Bearer ' + ADMIN } });
check(r.status === 400 && r.j.error === 'stop', 'admin stop with a bad slug → 400', r.j);
r = await A.call('POST', '/api/admin/posta', { json: { stop: 'za-stop' }, headers: { authorization: 'Bearer ' + ADMIN } });
check(r.status === 200 && r.j.ok && r.j.cancelled === 0 && r.j.stopped_at, 'admin stop before the send: ok (nothing queued yet)', r.j);
D1i.send_at = PAST;
A.publish(D1i);
r = await A.tick();
check(issueOf(r, 'za-stop').action === 'stopped' && !(await A.rows('za-stop')).length, 'an issue stopped by the admin is never queued, even after send_at', issueOf(r, 'za-stop'));

console.log('— stopped in the Markdown');
// a full day's cap leaves rows queued; status stopped cancels them
await A.db.prepare(`UPDATE pg_queue SET sent_at = ?1 WHERE status = 'sent'`).bind(now()).run();
for (let i = 0; i < 30; i++) await A.db.prepare(`INSERT INTO pg_queue (slug, email, lang, month, status, attempts, at, sent_at) VALUES ('stari', ?1, 'sr', '2020-01', 'sent', 1, ?2, ?2)`).bind('x' + i + '@example.com', now()).run();
const E1 = issue('zaustavi', { status: 'preview', hash: H('e1') });
A.publish(E1);
await A.tick();
E1.status = 'approved'; E1.approved_hash = E1.hash;
A.publish(E1);
r = await A.tick();
check(issueOf(r, 'zaustavi').action === 'enqueued' && issueOf(r, 'zaustavi').queued > 0 && r.j.stop === 'cap' && r.j.sent === 0, 'the day\'s cap is used up: queued, nothing sent (stop: cap)', r.j);
E1.status = 'stopped';
A.publish(E1);
r = await A.tick();
const zs = await A.rows('zaustavi');
check(issueOf(r, 'zaustavi').action === 'stopped' && issueOf(r, 'zaustavi').cancelled === zs.length && zs.every(x => x.status === 'cancelled' && x.note === 'stopped'),
  'status stopped: every queued row cancelled', zs.map(x => [x.status, x.note]));

console.log('— privacy: account deletion, export, the 60 days');
const E = 's1@example.com', stoken = 'f'.repeat(64);
await A.db.prepare(`INSERT INTO users (id, email, lang, created_at, verified_at, last_login_at) VALUES ('u1', ?1, 'sr', ?2, ?2, ?2)`).bind(E, now()).run();
await A.db.prepare(`INSERT INTO sessions (h, uid, at, seen, exp, kind) VALUES (?1, 'u1', ?2, ?2, ?3, 'web')`).bind(sha(stoken), now(), now() + 86400).run();
await A.db.prepare(`INSERT INTO pg_queue (slug, email, lang, month, status, attempts, at) VALUES ('buduci', ?1, 'sr', ?2, 'queued', 0, ?3)`).bind(E, MONTH, now()).run();
r = await A.call('GET', '/api/nalog/izvoz', { headers: { cookie: 'bv_s=' + stoken } });
check(r.status === 200 && r.j.newsletter_issues.length >= 2 && r.j.newsletter_issues.some(x => x.slug === 'broj-1' && x.status === 'sent') && !('email' in r.j.newsletter_issues[0]),
  'izvoz: the issues sent to the account\'s address', r.j && r.j.newsletter_issues);
r = await A.call('POST', '/api/nalog/obrisi', { json: { confirm: 'OBRISI' }, headers: { cookie: 'bv_s=' + stoken } });
const left = (await A.db.prepare('SELECT COUNT(*) AS n FROM pg_queue WHERE email = ?1').bind(E).first()).n;
const fut = await A.db.prepare(`SELECT email, status, note FROM pg_queue WHERE slug = 'buduci'`).first();
check(r.status === 200 && left === 0 && fut.email === null && fut.status === 'cancelled' && fut.note === 'obrisan', 'account deleted: no issue row keeps the address, a queued one is cancelled', { left, fut });
await A.db.prepare(`UPDATE pg_queue SET sent_at = ?1 WHERE slug = 'broj-1' AND email = 's2@example.com'`).bind(now() - 61 * 86400).run();
await A.call('GET', '/api/admin/posta', { headers: { authorization: 'Bearer ' + ADMIN } });            // runs the cleanup first
const old = await A.db.prepare(`SELECT email, status FROM pg_queue WHERE slug = 'broj-1' AND sent_at < ?1`).bind(now() - 60 * 86400).first();
check(old && old.email === null && old.status === 'sent', 'housekeeping: 60 days after sending the row keeps the status, not the address', old);

console.log('— the budget of one tick: many new previews');
const many9 = Array.from({ length: 9 }, (_, i) => issue('mnogo-' + i, { status: 'preview', hash: H('mnogo-' + i) }));
A.publish(...many9);
r = await A.tick();
const later = r.j.issues.filter(x => x.action === 'later').length, sentPv = r.j.issues.filter(x => x.action === 'preview_sent').length;
r = await A.tick();
check(sentPv === 7 && later === 2 && r.j.issues.filter(x => x.action === 'preview_sent').length === 2 && r.j.issues.filter(x => x.action === 'previewed').length === 7,
  'nine new previews: seven fit the D1/fetch budget of a tick, two go out on the next one ("later")', { sentPv, later });

console.log('— the lock');
A.publish(P);
r = await A.tick();
const r2 = await A.call('POST', '/api/posta/tick', { origin: false });
check(r.j.ok && !r.j.skipped && r2.status === 200 && r2.j.skipped === 'busy', 'a second tick within a minute: {ok: true, skipped: "busy"}', r2.j);
await A.db.prepare('UPDATE pg_lock SET at = 0, until = 0').run();
const many = await Promise.all([1, 2, 3, 4].map(() => A.call('POST', '/api/posta/tick', { origin: false })));
check(many.filter(x => x.j && !x.j.skipped).length === 1 && many.filter(x => x.j && x.j.skipped === 'busy').length === 3, 'four ticks at once: one runs, three are busy', many.map(x => x.j));
await A.db.prepare('UPDATE pg_lock SET at = ?1, until = ?2').bind(now() - 3600, now() + 500).run();   // started long ago, still running
r = await A.call('POST', '/api/posta/tick', { origin: false });
await A.db.prepare('UPDATE pg_lock SET at = ?1, until = ?1').bind(now() - 3600).run();
const r3 = await A.call('POST', '/api/posta/tick', { origin: false });
check(r.j.skipped === 'busy' && !r3.j.skipped, 'a running tick holds the lock; a stale one (its time passed) does not', [r.j, r3.j]);
check(!(await A.mails('pregled')).some(m => m.to_addr === 's6@example.com') && (await A.mails('pregled')).every(m => m.kind === 'pregled'), 'mail_log: nothing to the suppressed address', null);
await A.mf.dispose();

console.log('— the budget: a day and a tick');
const B = await instance({ MAIL_MODE: 'log', PREGLED_DAILY_CAP: '3' });
await B.settle();
for (let i = 0; i < 5; i++) await B.sub(`d${i}@example.com`);
const F1 = issue('dnevni', { status: 'preview', hash: H('f1') });
B.publish(F1);
await B.tick();
F1.status = 'approved'; F1.approved_hash = F1.hash;
B.publish(F1);
r = await B.tick();
check(r.j.sent === 3 && r.j.cap === 3 && r.j.sent_today === 3 && issueOf(r, 'dnevni').queued === 2, 'PREGLED_DAILY_CAP=3: three sent, two wait', r.j);
r = await B.tick();
check(r.j.sent === 0 && r.j.stop === 'cap' && issueOf(r, 'dnevni').action === 'sending', 'the same day: nothing more (stop: cap)', r.j);
await B.db.prepare(`UPDATE pg_queue SET sent_at = sent_at - 86400 WHERE status = 'sent'`).run();       // the next UTC day
await B.sub('d5@example.com');
await B.call('POST', '/api/posta/odjava?t=' + sha('token:d3@example.com').slice(0, 32), { origin: false });
await B.db.prepare(`UPDATE subs SET lang = 'en' WHERE email = 'd4@example.com'`).run();
r = await B.tick();
const bRows = Object.fromEntries((await B.rows('dnevni')).map(x => [x.email, x]));
const d4 = (await B.mails('pregled', 'd4@example.com'))[0];
check(r.j.sent === 1 && bRows['d3@example.com'].status === 'cancelled' && bRows['d3@example.com'].note === 'off' && !bRows['d5@example.com'],
  'next day: the one who unsubscribed meanwhile is skipped (cancelled, off); a reader who signed up after the enqueue is not added', r.j);
check(d4 && d4.subject.endsWith('(en)') && bRows['d4@example.com'].lang === 'en', 'a reader who changed the language meanwhile gets it in the new language', d4 && d4.subject);
await B.mf.dispose();
const C = await instance({ MAIL_MODE: 'log', PREGLED_DAILY_CAP: '100' });
await C.settle();
for (let i = 0; i < 30; i++) await C.sub(`t${String(i).padStart(2, '0')}@example.com`);
const G1 = issue('tick', { status: 'preview', hash: H('g1') });
C.publish(G1);
await C.tick();
G1.status = 'approved'; G1.approved_hash = G1.hash;
C.publish(G1);
r = await C.tick();
const r4 = await C.tick();
check(r.j.sent === 25 && issueOf(r, 'tick').queued === 5 && r4.j.sent === 5 && issueOf(r4, 'tick').queued === 0, 'at most 25 a tick: 25, then 5', [r.j.sent, r4.j.sent]);
const order = (await C.mails('pregled')).map(m => m.to_addr);
check(order.join() === order.slice().sort().join(), 'oldest rows first', order.slice(0, 4));
await C.mf.dispose();

console.log('— the background tick');
const D = await instance({ MAIL_MODE: 'log' });
D.publish(issue('pozadina', { status: 'preview', hash: H('bg') }));
r = await D.call('GET', '/api/zdravlje');
let bg = [];
for (let i = 0; i < 100 && bg.length < 3; i++) { await sleep(30); bg = await D.mails('preview').catch(() => []); }
check(r.status === 200 && bg.length === 3, 'a normal /api request starts a tick after its answer (the three previews)', bg.length);
await D.db.prepare('UPDATE pg_lock SET at = 0, until = 0').run();
await D.call('GET', '/api/zdravlje');
await D.call('GET', '/api/nalog/status');
await sleep(400);
check((await D.db.prepare('SELECT at FROM pg_lock').first()).at === 0, 'the next requests within 10 minutes start none (checked in memory first, no D1)', null);
await D.mf.dispose();

console.log('— the newsletter switched off, mail off');
const O = await instance({ MAIL_MODE: 'log' }, { pregled: false });
O.publish(issue('iskljuceno', { status: 'preview', hash: H('off') }));
r = await O.call('POST', '/api/posta/tick', { origin: false });
await O.call('GET', '/api/zdravlje');
await sleep(300);
const oLog = await O.db.prepare("SELECT COUNT(*) AS n FROM sqlite_master WHERE name = 'mail_log'").first();
check(r.status === 200 && r.j.ok === true && r.j.skipped === 'off' && (!oLog.n || !(await O.mails('preview')).length), 'pregled off: the tick does nothing ({skipped: "off"}), no background tick', r.j);
r = await O.call('GET', '/api/posta/klik?i=iskljuceno&l=2');
check(r.status === 302 && r.headers.get('location') === SITE + '/mapa/', 'pregled off: the links of mails already sent still work', r.headers.get('location'));
await O.mf.dispose();
const N = await instance({});
N.publish(issue('bez-poste', { status: 'preview', hash: H('nomail') }));
r = await N.call('POST', '/api/posta/tick', { origin: false });
check(r.status === 503 && r.j.ok === false && r.j.error === 'mail_off', 'no RESEND_API_KEY: the tick answers 503 {ok: false, error: "mail_off"}', r.j);
r = await N.call('GET', '/api/posta/klik?i=bez-poste&l=3');
check(r.status === 302 && r.headers.get('location') === 'https://blokvolt.com/hr/', 'mail off: klik still works', r.headers.get('location'));
r = await N.call('GET', '/api/admin/posta', { headers: { authorization: 'Bearer ' + ADMIN } });
check(r.status === 200 && r.j.pregled && Array.isArray(r.j.pregled.issues), 'mail off: admin/posta still works', r.j && r.j.pregled);
await N.mf.dispose();

// ======================================================================= Resend (fake API in this script)
console.log('— Resend: payload, 429, 5xx, 401, 422');
const R = await instance({ RESEND_API_KEY: 're_test_123' });
await R.settle();
for (let i = 0; i < 4; i++) await R.sub(`r${i}@example.com`, { lang: i === 1 ? 'ru' : 'sr' });
const K1 = issue('resend', { status: 'preview', hash: H('k1') });
R.publish(K1);
let n0 = resendCalls.length;
r = await R.tick();
const pc = resendCalls.slice(n0);
check(issueOf(r, 'resend').action === 'preview_sent' && pc.length === 3 && pc.every(c => c.body.to.join() === TEAM && !c.body.headers && c.body.tags[0].value === 'preview'),
  'Resend: three previews to the team address, without List-Unsubscribe', pc.map(c => c.body.subject));
check(pc[1].t - pc[0].t >= 500 && pc[2].t - pc[1].t >= 500, 'Resend: at most 2 requests a second', [pc[1].t - pc[0].t, pc[2].t - pc[1].t]);
K1.status = 'approved'; K1.approved_hash = K1.hash;
R.publish(K1);
resendPlan = [429];
n0 = resendCalls.length;
r = await R.tick();
let rr = await R.rows('resend');
check(r.j.stop === 'resend_429' && r.j.sent === 0 && resendCalls.length === n0 + 1 && rr[0].status === 'queued' && rr[0].attempts === 1 && rr[0].note === 'resend 429' && rr.slice(1).every(x => x.attempts === 0),
  '429: the tick stops, the row stays queued (attempts 1), the others untouched', { j: r.j, rr: rr.map(x => [x.status, x.attempts]) });
n0 = resendCalls.length;
r = await R.tick();
const nc = resendCalls.slice(n0);
rr = await R.rows('resend');
check(r.j.sent === 4 && rr.every(x => x.status === 'sent' && /^em-\d+$/.test(x.provider_id)), 'next tick: all four sent, with the provider id', rr.map(x => [x.status, x.provider_id]));
const c0 = nc[0];
check(c0.headers.authorization === 'Bearer re_test_123' && c0.headers['idempotency-key'] === 'pregled-resend-' + sha('r0@example.com').slice(0, 16) &&
  c0.body.from === 'BlokVolt <obavestenja@mail.blokvolt.com>' && c0.body.reply_to === TEAM && c0.body.to.join() === 'r0@example.com' &&
  c0.body.headers['List-Unsubscribe'] === `<${SITE}/api/posta/odjava?t=${sha('token:r0@example.com').slice(0, 32)}>, <mailto:${TEAM}?subject=odjava>` &&
  c0.body.headers['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click' && c0.body.tags.map(t => t.name + ':' + t.value).join() === 'kind:pregled,issue:resend' &&
  c0.body.html.includes('UVOD-sr') && c0.body.text.includes('odjava: ' + SITE + '/pregled/odjava/?t='), 'payload: key, Idempotency-Key, from, reply_to, List-Unsubscribe, tags, html and text', c0);
check(nc.find(c => c.body.to[0] === 'r1@example.com').body.subject.endsWith('(ru)') && nc.every((c, i) => !i || c.t - nc[i - 1].t >= 500), 'each in its language; paced', null);
// 5xx on the fifth attempt → failed; 422 → failed at once, the tick goes on; 401 → stops without counting, one notice
for (let i = 0; i < 3; i++) await R.sub(`z${i}@example.com`);
const K2 = issue('greske', { status: 'preview', hash: H('k2') });
R.publish(K2);
await R.tick();
K2.status = 'approved'; K2.approved_hash = K2.hash;
R.publish(K2);
resendPlan = [401];
n0 = resendCalls.length;
r = await R.tick();
rr = await R.rows('greske');
const note401 = resendCalls.slice(n0).find(c => c.body.tags[0].value === 'notice');
check(r.j.stop === 'resend_401' && r.j.sent === 0 && rr.every(x => x.status === 'queued' && x.attempts === 0) && note401 && note401.body.to.join() === TEAM && /Resend отвечает 401/.test(note401.body.text),
  '401 (the key): stop, no attempt counted, one notice to the team', { j: r.j, rr: rr.map(x => [x.status, x.attempts]) });
await R.db.prepare(`UPDATE pg_queue SET attempts = 4 WHERE slug = 'greske' AND id = (SELECT MIN(id) FROM pg_queue WHERE slug = 'greske')`).run();
resendPlan = [503];
r = await R.tick();
rr = await R.rows('greske');
check(r.j.stop === 'resend_503' && rr[0].status === 'failed' && rr[0].attempts === 5 && issueOf(r, 'greske').failed === 1, '5xx on the fifth attempt: the row is failed', rr.map(x => [x.status, x.attempts]));
resendPlan = [422];
r = await R.tick();
rr = await R.rows('greske');
check(!r.j.stop && r.j.sent === rr.filter(x => x.status === 'sent').length && rr.filter(x => x.status === 'failed').length === 2 && rr.find(x => x.note === 'resend 422'),
  '422 (this address refused): failed at once, the others sent in the same tick', rr.map(x => [x.status, x.note]));
resendPlan = [];
await R.mf.dispose();

console.log(`\n${oks} passed, ${fails} failed`);
process.exit(fails ? 1 : 0);
