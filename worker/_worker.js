// BlokVolt API — Cloudflare Pages "advanced mode" worker (copied to dist/_worker.js by build.py).
// Only /api/* reaches it (dist/_routes.json); everything else is served as static files.
// Binding: DB = D1 database "blokvolt" (schema: worker/schema.sql; the one-row table dk and the tables of the accounts
// and the newsletter are also created here on first use). Optional secret: ADMIN_KEY (set by the owner in Pages →
// Settings → Variables and Secrets; without it the /api/admin/* endpoints answer 404).
// Accounts ("Moj BlokVolt", /api/nalog/*) and the newsletter (Nedeljni pregled, /api/posta/*): see the section
// "accounts and the newsletter" below and docs/RUNBOOK.md 3.27. They need the secret RESEND_API_KEY to send mail;
// optional: the secret RESEND_WEBHOOK_SECRET (bounces and spam complaints from Resend), the variables MAIL_FROM,
// MAIL_REPLY_TO, SITE, PREGLED_DAILY_CAP (newsletter mails a day, see "sending the issues"), and MAIL_MODE=log for
// local tests only.

const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8' };
const STATUSES = new Set(['ok', 'problem', 'broken', 'missing']);
// drivers' short answers on the map card (map.js: WHY, FACTS): field -> allowed values
const FACT_VALUES = { why: new Set(['busy', 'broken', 'app', 'cable', 'closed', 'short']), cab: new Set(['att', 'own']),
  park: new Set(['free', 'paid']), oh: new Set(['24', 'lim']) };
const KINDS = new Set(['firma', 'mreza', 'ispravka', 'stanica', 'pomoc']);
const MAX_IMG = 950 * 1024, MAX_TH = 90 * 1024;
const LINKY = /(https?:\/\/|www\.|\b[a-z0-9-]+\.(com|rs|net|org|info|me|io)\b)/i;
const CONTACTY = /(\S+@\S+\.\S+|(\+?\d[\d\s\/.-]{7,}\d))/;
// dates and times are not phone numbers: "28.09.2026", "28. 9. 2026.", "28/09", "2026-09-28", "15.30", "15h30"
const DATEY = /\b(\d{4}-\d{2}-\d{2}|\d{1,2}[./]\s?\d{1,2}[./]?(\s?\d{4}\.?|\s?\d{2}\b)?|\d{1,2}[:.h]\d{2}\b)/g;
const contacty = t => CONTACTY.test(String(t).replace(DATEY, ' '));
const RUDE = /\b(jebem|jebo|jebi|pi[čc]k|kurac|kurc|govno|sranje|peder|kreten|idiot|debil|stoka|fuck|shit)/i;

const json = (obj, status = 200, extra = {}) =>
  new Response(JSON.stringify(obj), { status, headers: { ...JSON_HEADERS, 'cache-control': 'no-store', ...extra } });
const bad = (msg, status = 400) => json({ ok: false, error: msg }, status);
const now = () => Math.floor(Date.now() / 1000);
const today = () => new Date().toISOString().slice(0, 10);
const clean = (s, max) => String(s == null ? '' : s).replace(/[\u0000-\u001f\u007f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, max);

function rid() {
  const a = new Uint8Array(16);
  crypto.getRandomValues(a);
  return [...a].map(b => b.toString(16).padStart(2, '0')).join('');
}

// A short daily fingerprint of the visitor's IP address, for rate limits and moderation. It is an HMAC with a random
// key that lives in D1 for one day (UTC) and is then overwritten by a new one: a plain hash of the address could be
// reversed by trying every IPv4 address, while an old fingerprint without its key cannot. Cached per isolate.
let DAYKEY = null;
async function dayKey(env) {
  const d = today();
  if (DAYKEY && DAYKEY.day === d) return DAYKEY.key;
  let row = null;
  try {
    row = await env.DB.prepare('SELECT day, k FROM dk WHERE id = 1').first();
  } catch (e) {
    await env.DB.prepare('CREATE TABLE IF NOT EXISTS dk (id INTEGER PRIMARY KEY CHECK (id = 1), day TEXT NOT NULL, k TEXT NOT NULL)').run();
  }
  if (!row || row.day < d) {
    const fresh = rid() + rid();
    if (!row) await env.DB.prepare('INSERT OR IGNORE INTO dk (id, day, k) VALUES (1, ?1, ?2)').bind(d, fresh).run();
    else await env.DB.prepare('UPDATE dk SET day = ?1, k = ?2 WHERE id = 1 AND day = ?3').bind(d, fresh, row.day).run();
    row = await env.DB.prepare('SELECT day, k FROM dk WHERE id = 1').first();   // another request may have won the race
  }
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(row.k), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  DAYKEY = { day: row.day, key };
  return key;
}

async function ipHash(request, env) {
  const ip = request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || '0';
  const sig = await crypto.subtle.sign('HMAC', await dayKey(env), new TextEncoder().encode(ip));
  return [...new Uint8Array(sig)].slice(0, 12).map(b => b.toString(16).padStart(2, '0')).join('');
}

// true while the key is under `max` uses today
async function allow(env, key, max) {
  const row = await env.DB.prepare(
    'INSERT INTO rl (k, day, n) VALUES (?1, ?2, 1) ON CONFLICT (k, day) DO UPDATE SET n = n + 1 RETURNING n'
  ).bind(key, today()).first();
  if (Math.random() < 0.02) await env.DB.prepare('DELETE FROM rl WHERE day < ?1').bind(today()).run();
  return !row || row.n <= max;
}

function sameOrigin(request) {
  const o = request.headers.get('origin');
  if (!o) return true; // some browsers omit Origin on same-origin POST
  try {
    const h = new URL(o).hostname;
    return h === 'www.blokvolt.rs' || h === 'blokvolt.rs' || h === 'blokvolt.pages.dev' || h.endsWith('.blokvolt.pages.dev') || h === 'localhost' || h === '127.0.0.1';
  } catch (e) { return false; }
}

// station ids that exist on the map (the static map files: open data + the networks' own lists), cached per isolate for 10 minutes
let STATIONS = null, STATIONS_AT = 0;
async function stationIds(env, request) {
  if (STATIONS && Date.now() - STATIONS_AT < 600000) return STATIONS;
  try {
    const [a, m] = await Promise.all(['/assets/map/punjaci.json', '/assets/map/mreze.json'].map(u =>
      env.ASSETS.fetch(new Request(new URL(u, request.url))).then(r => r.json()).catch(() => ({}))));
    STATIONS = new Set((a.stations || []).map(s => s.id).concat((m.add || []).map(s => s.id)));
    STATIONS_AT = Date.now();
  } catch (e) { STATIONS = STATIONS || new Set(); }
  return STATIONS;
}

// ---------------------------------------------------------------- summaries
async function summaryAll(env) {
  const rows = await env.DB.prepare(
    `SELECT st, ROUND(AVG(r), 1) AS avg, COUNT(r) AS nr, COUNT(*) AS n, MAX(at) AS last
       FROM checkins WHERE cs != 'hidden' GROUP BY st`
  ).all();
  const lastS = await env.DB.prepare(
    `SELECT st, s, at FROM (SELECT st, s, at, ROW_NUMBER() OVER (PARTITION BY st ORDER BY at DESC) AS rn
       FROM checkins WHERE cs != 'hidden') WHERE rn = 1`
  ).all();
  const photos = await env.DB.prepare(`SELECT st, COUNT(*) AS n FROM photos WHERE status = 'ok' GROUP BY st`).all();
  const out = {};
  for (const r of rows.results) out[r.st] = { a: r.avg, nr: r.nr, n: r.n };
  for (const r of lastS.results) if (out[r.st]) { out[r.st].s = r.s; out[r.st].t = r.at; }
  for (const p of photos.results) (out[p.st] = out[p.st] || { a: null, nr: 0, n: 0 }).f = p.n;
  return out;
}

// the drivers' short answers (cable, parking, hours, what went wrong): one table, created on first use
let FACTS_OK = false;
async function ensureFacts(env) {
  if (FACTS_OK) return;
  await env.DB.batch([
    env.DB.prepare(`CREATE TABLE IF NOT EXISTS facts (id INTEGER PRIMARY KEY AUTOINCREMENT, st TEXT NOT NULL, f TEXT NOT NULL, v TEXT NOT NULL,
      at INTEGER NOT NULL, ip TEXT, uid TEXT)`),
    env.DB.prepare('CREATE INDEX IF NOT EXISTS facts_st ON facts (st, at)'),
  ]);
  FACTS_OK = true;
}
async function addFact(env, st, f, v, ip, uid) {
  await ensureFacts(env);
  await env.DB.prepare('INSERT INTO facts (st, f, v, at, ip, uid) VALUES (?1, ?2, ?3, ?4, ?5, ?6)').bind(st, f, v, now(), ip, uid || null).run();
}
// answers of the last 60 days: distinct drivers (day fingerprints) per field and value
async function factsOf(env, st) {
  try {
    await ensureFacts(env);
    const r = await env.DB.prepare(`SELECT f, v, COUNT(DISTINCT ip) AS n, MAX(at) AS last FROM facts WHERE st = ?1 AND at > ?2 GROUP BY f, v`)
      .bind(st, now() - 60 * 86400).all();
    return r.results;
  } catch (e) { return []; }
}

async function summaryOne(env, st) {
  const agg = await env.DB.prepare(
    `SELECT ROUND(AVG(r), 1) AS avg, COUNT(r) AS nr, COUNT(*) AS n FROM checkins WHERE st = ?1 AND cs != 'hidden'`
  ).bind(st).first();
  const items = await env.DB.prepare(
    `SELECT id, s, r, CASE WHEN cs = 'ok' THEN c END AS c, CASE WHEN cs = 'ok' THEN n END AS n, at
       FROM checkins WHERE st = ?1 AND cs != 'hidden' ORDER BY at DESC LIMIT 30`
  ).bind(st).all();
  const photos = await env.DB.prepare(
    `SELECT id, cap, w, h, at FROM photos WHERE st = ?1 AND status = 'ok' ORDER BY at DESC LIMIT 24`
  ).bind(st).all();
  return { ok: true, st, avg: agg.avg, nr: agg.nr, n: agg.n, items: items.results, photos: photos.results, facts: await factsOf(env, st) };
}

// ---------------------------------------------------------------- handlers
async function postCheckin(request, env, st) {
  let b;
  try { b = await request.json(); } catch (e) { return bad('json'); }
  if (b.hp) return json({ ok: true, pending: false });               // honeypot: silently accept
  if (typeof b.t === 'number' && b.t < 2500) return bad('too fast', 429);
  const s = String(b.s || '');
  if (!STATUSES.has(s)) return bad('status');
  let r = b.r == null || b.r === '' ? null : Math.round(Number(b.r));
  if (r !== null && !(r >= 1 && r <= 5)) return bad('rating');
  const c = clean(b.c, 500) || null, n = clean(b.n, 40) || null;
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'ci:' + ip, 30)) || !(await allow(env, 'cs:' + ip + ':' + st, 3))) return bad('limit', 429);
  let cs = 'none';
  if (c) cs = (LINKY.test(c) || contacty(c) || RUDE.test(c) || (n && (LINKY.test(n) || RUDE.test(n)))) ? 'pending' : 'ok';
  // a signed-in driver's report is also listed in "Moj BlokVolt" (never required)
  const uid = await reporter(request, env);
  await env.DB.prepare(
    'INSERT INTO checkins (st, s, r, c, n, cs, at, lang, ip' + (uid ? ', uid' : '') + ') VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9' + (uid ? ', ?10' : '') + ')'
  ).bind(st, s, r, c, n, cs, now(), clean(b.lang, 5) || null, ip, ...(uid ? [uid] : [])).run();
  // what went wrong ("Radi, uz problem" / "Ne radi"): optional, one of FACT_VALUES.why
  const why = String(b.why || '');
  if ((s === 'problem' || s === 'broken') && FACT_VALUES.why.has(why)) await addFact(env, st, 'why', why, ip, uid);
  return json({ ok: true, pending: cs === 'pending' });
}

// one short answer from the map card: cable on the charger or bring your own, parking free or paid, open 0–24 or limited.
// One answer per field, station and driver a day; at most 60 answers a day per driver.
async function postFact(request, env, st) {
  let b;
  try { b = await request.json(); } catch (e) { return bad('json'); }
  if (b.hp) return json({ ok: true });                                // honeypot: silently accept
  if (typeof b.t === 'number' && b.t < 1500) return bad('too fast', 429);
  const f = String(b.f || ''), v = String(b.v || '');
  if (f === 'why' || !FACT_VALUES[f] || !FACT_VALUES[f].has(v)) return bad('value');
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'fa:' + ip, 60)) || !(await allow(env, 'fs:' + ip + ':' + st + ':' + f, 1))) return bad('limit', 429);
  await addFact(env, st, f, v, ip, await reporter(request, env));
  return json({ ok: true });
}

async function postPhoto(request, env, st) {
  let fd;
  try { fd = await request.formData(); } catch (e) { return bad('form'); }
  if (fd.get('hp')) return json({ ok: true, pending: true });
  const t = Number(fd.get('t') || 0);
  if (t && t < 2500) return bad('too fast', 429);
  const img = fd.get('foto'), th = fd.get('thumb');
  if (!img || typeof img === 'string') return bad('foto');
  const buf = new Uint8Array(await img.arrayBuffer());
  if (buf.length < 2000 || buf.length > MAX_IMG) return bad('size');
  const isJpeg = buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff;
  const isWebp = buf[0] === 0x52 && buf[1] === 0x49 && buf[2] === 0x46 && buf[3] === 0x46 && buf[8] === 0x57 && buf[9] === 0x45;
  if (!isJpeg && !isWebp) return bad('type');
  let thBuf = null;
  if (th && typeof th !== 'string') {
    thBuf = new Uint8Array(await th.arrayBuffer());
    if (thBuf.length > MAX_TH || !(thBuf[0] === 0xff && thBuf[1] === 0xd8)) thBuf = null;
  }
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'ph:' + ip, 6))) return bad('limit', 429);
  const pend = await env.DB.prepare(`SELECT COUNT(*) AS n FROM photos WHERE st = ?1 AND status = 'pending'`).bind(st).first();
  if (pend && pend.n >= 20) return bad('queue full', 429);
  const w = Math.min(4000, Math.max(0, Math.round(Number(fd.get('w') || 0)))), h = Math.min(4000, Math.max(0, Math.round(Number(fd.get('h') || 0))));
  const uid = await reporter(request, env);
  await env.DB.prepare(
    'INSERT INTO photos (id, st, status, at, cap, w, h, mime, img, th, ip' + (uid ? ', uid' : '') + ') VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11' + (uid ? ', ?12' : '') + ')'
  ).bind(rid(), st, 'pending', now(), clean(fd.get('opis'), 140) || null, w || null, h || null,
    isJpeg ? 'image/jpeg' : 'image/webp', buf, thBuf, ip, ...(uid ? [uid] : [])).run();
  return json({ ok: true, pending: true });
}

async function getPhoto(env, id, thumb) {
  if (!/^[0-9a-f]{32}$/.test(id)) return new Response('not found', { status: 404 });
  const row = await env.DB.prepare('SELECT mime, img, th, status FROM photos WHERE id = ?1').bind(id).first();
  if (!row || row.status === 'no') return new Response('not found', { status: 404 });
  const data = thumb && row.th ? row.th : row.img;
  const bytes = data instanceof ArrayBuffer ? new Uint8Array(data) : new Uint8Array(data);
  return new Response(bytes, {
    headers: {
      'content-type': thumb && row.th ? 'image/jpeg' : row.mime,
      // approved photos never change; pending ones are only reachable by their random id (moderation)
      'cache-control': row.status === 'ok' ? 'public, max-age=31536000, immutable' : 'private, no-store',
      'x-content-type-options': 'nosniff',
    },
  });
}

async function postReport(request, env) {
  let b;
  try { b = await request.json(); } catch (e) { return bad('json'); }
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'rp:' + ip, 20))) return bad('limit', 429);
  // one report per item and visitor per day: "three visitors" in the rules means three different fingerprints
  if ((b.t === 'c' && Number.isInteger(b.id)) || (b.t === 'f' && /^[0-9a-f]{32}$/.test(String(b.id)))) {
    if (!(await allow(env, 'rx:' + b.t + ':' + b.id + ':' + ip, 1))) return json({ ok: true });
  }
  if (b.t === 'c' && Number.isInteger(b.id)) {
    await env.DB.prepare(`UPDATE checkins SET rep = rep + 1, cs = CASE WHEN rep + 1 >= 3 AND cs = 'ok' THEN 'pending' ELSE cs END WHERE id = ?1`).bind(b.id).run();
  } else if (b.t === 'f' && /^[0-9a-f]{32}$/.test(String(b.id))) {
    await env.DB.prepare(`UPDATE photos SET rep = rep + 1, status = CASE WHEN rep + 1 >= 2 AND status = 'ok' THEN 'pending' ELSE status END WHERE id = ?1`).bind(b.id).run();
  } else return bad('what');
  return json({ ok: true });
}

async function postRequest(request, env) {
  let b;
  try { b = await request.json(); } catch (e) { return bad('json'); }
  if (b.hp) return json({ ok: true });
  if (b.kind === 'pomoc') return postHelpful(request, env, b);   // a vote may come a second after the page opens
  if (typeof b.t === 'number' && b.t < 3000) return bad('too fast', 429);
  const kind = String(b.kind || '');
  if (!KINDS.has(kind)) return bad('kind');
  const data = {};
  for (const [k, v] of Object.entries(b.data || {})) {
    if (Object.keys(data).length >= 30) break;
    data[clean(k, 40)] = typeof v === 'boolean' ? v : clean(v, 3000);
  }
  const msg = (data.poruka || '') + (data.ime || '');
  if (!msg.trim()) return bad('empty');
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'rq:' + ip, 6))) return bad('limit', 429);
  const email = clean(b.email || data.email, 120) || null;
  await env.DB.prepare('INSERT INTO requests (kind, slug, data, email, at, ip) VALUES (?1, ?2, ?3, ?4, ?5, ?6)')
    .bind(kind, clean(b.slug, 80) || null, JSON.stringify(data), email, now(), ip).run();
  return json({ ok: true });
}

// "Da li vam je ovo pomoglo?" on the help pages: one row per vote (v: da | ne) and per optional note (v: komentar).
// Votes are stored with status 'vote' so they stay out of the moderation queue; notes are 'new' and show up there.
// Totals: GET /api/admin/pomoc (owner's key).
async function postHelpful(request, env, b) {
  const page = String(b.slug || '');
  if (!/^\/(en\/|ru\/)?pomoc\/[a-z0-9-]{0,80}\/?$/.test(page)) return bad('page');
  const v = String((b.data || {}).v || '');
  if (!['da', 'ne', 'komentar'].includes(v)) return bad('vote');
  const note = v === 'komentar' ? clean((b.data || {}).poruka, 1000) : '';
  if (v === 'komentar' && !note) return bad('empty');
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'pm:' + ip, 40))) return bad('limit', 429);
  await env.DB.prepare('INSERT INTO requests (kind, slug, data, email, at, status, ip) VALUES (?1, ?2, ?3, NULL, ?4, ?5, ?6)')
    .bind('pomoc', page, JSON.stringify(note ? { v, poruka: note } : { v }), now(), note ? 'new' : 'vote', ip).run();
  return json({ ok: true });
}

async function adminHelpful(env) {
  const votes = await env.DB.prepare(`SELECT slug, json_extract(data, '$.v') AS v, COUNT(*) AS n FROM requests
    WHERE kind = 'pomoc' AND status = 'vote' GROUP BY slug, v ORDER BY slug`).all();
  const notes = await env.DB.prepare(`SELECT id, slug, json_extract(data, '$.poruka') AS poruka, at FROM requests
    WHERE kind = 'pomoc' AND json_extract(data, '$.v') = 'komentar' ORDER BY at DESC LIMIT 100`).all();
  return json({ ok: true, votes: votes.results, notes: notes.results });
}

// ---------------------------------------------------------------- admin (optional, owner's key)
function adminOk(request, env) {
  if (!env.ADMIN_KEY || String(env.ADMIN_KEY).length < 16) return false;
  const h = request.headers.get('authorization') || '';
  return h === 'Bearer ' + env.ADMIN_KEY;
}

async function adminQueue(env) {
  const photos = await env.DB.prepare(`SELECT id, st, cap, at, rep, status FROM photos WHERE status = 'pending' ORDER BY at LIMIT 100`).all();
  const comments = await env.DB.prepare(`SELECT id, st, s, r, c, n, at, rep FROM checkins WHERE cs = 'pending' ORDER BY at LIMIT 200`).all();
  const requests = await env.DB.prepare(`SELECT id, kind, slug, data, email, at FROM requests WHERE status = 'new' ORDER BY at LIMIT 200`).all();
  return json({ ok: true, photos: photos.results, comments: comments.results, requests: requests.results });
}

async function adminDecide(request, env) {
  let b;
  try { b = await request.json(); } catch (e) { return bad('json'); }
  const ok = b.a === 'ok';
  if (b.t === 'f' && /^[0-9a-f]{32}$/.test(String(b.id))) {
    // an approved item starts counting reports from zero again, so the next single report does not hide it
    await env.DB.prepare('UPDATE photos SET status = ?1, rep = CASE WHEN ?1 = \'ok\' THEN 0 ELSE rep END WHERE id = ?2').bind(ok ? 'ok' : 'no', b.id).run();
  } else if (b.t === 'c' && Number.isInteger(b.id)) {
    await env.DB.prepare('UPDATE checkins SET cs = ?1, rep = CASE WHEN ?1 = \'ok\' THEN 0 ELSE rep END WHERE id = ?2').bind(ok ? 'ok' : 'hidden', b.id).run();
  } else if (b.t === 'z' && Number.isInteger(b.id)) {
    await env.DB.prepare('UPDATE requests SET status = ?1 WHERE id = ?2').bind(ok ? 'done' : 'rejected', b.id).run();
  } else return bad('what');
  return json({ ok: true });
}

// ================================================================ accounts and the newsletter (docs/RUNBOOK.md 3.27)
// "Moj BlokVolt" (/nalog/): sign-in without a password. POST /api/nalog/kod mails a six-digit code and a one-click link
// (both valid 15 minutes, stored only as SHA-256). The code belongs to the browser that asked for it (the HttpOnly
// cookie bv_n, or the nonce returned to the app), so strangers who ask for codes of the same address, or guess at them,
// never touch that browser's code; the link works anywhere. /potvrdi (code) or /link (the link's token, POSTed by the
// static page /nalog/?prijava=… only when the reader presses its button: mail scanners open links, and some of them run
// the page's scripts too) opens a session: 32 random bytes in the HttpOnly
// cookie bv_s (Path=/api) or, for the future native app ({app: true}), returned once and sent back as
// "Authorization: Bearer <token>". Only the SHA-256 of a token is stored. bv_in=1 (not HttpOnly) only tells the static
// pages that someone is signed in. Answers never reveal whether an address has an account or a subscription.
// The newsletter (Nedeljni pregled, /pregled/) is switched on only by the button on the page the confirmation mail
// links to (double opt-in) or, for a signed-in reader whose address the sign-in code has proved, in the account. Every
// consent and withdrawal is a row in `consents` (append-only; ZZPL art. 15: the controller must be able to prove
// consent); the history is deleted 3 years after the last withdrawal. A sign-up nobody confirms is deleted after 30
// days and its consent rows keep only the SHA-256 of the address.
// Bounces and spam complaints come from Resend's webhook (POST /api/posta/resend, signed by Svix): the newsletter of
// that address goes off and the SHA-256 of the address goes into `suppressions`, which every send checks first.
// Mail goes through Resend (secret RESEND_API_KEY; MAIL_FROM, MAIL_REPLY_TO optional). Without the key every endpoint
// that must send mail answers 503 mail_off. /nalog/kod and /posta/prijava answer before any mail work (ctx.waitUntil), so
// the time of the answer never tells anything about the address. MAIL_MODE=log (local tests only) writes the mail to the D1 table mail_log
// instead and leaves the Secure flag off the cookies, so they work on http://localhost.
// Tables are created here on first use (once per isolate), like dk: users, auth_codes, sessions, favs, subs, consents,
// suppressions, the sender's pg_previews, pg_issues, pg_queue, pg_clicks, pg_lock (and mail_log in log mode); checkins and
// photos get a uid column. Documentation: worker/schema.sql. Sending the issues: the section after the admin counts.
const DAY_S = 86400;
const SESSION_S = 90 * DAY_S;            // a session ends after 90 days without use
const CODE_S = 15 * 60;                  // sign-in code and link
const CODE_TRIES = 5;
const PENDING_S = 30 * DAY_S;            // unconfirmed newsletter sign-ups are deleted after 30 days
const CONSENT_KEEP_S = 3 * 365 * DAY_S;  // consent history, counted from the last withdrawal
const MAX_FAVS = 300;                    // the same limit as the map's localStorage list
// rate limits, per day unless said otherwise. codeIp / subIp: per daily IP fingerprint (generous: a mobile network puts
// many people behind one address); codeHour / codeDay: per address from one IP fingerprint, so nobody can use up the
// codes of someone else's address; codeMail: per address from everywhere; failIp: wrong or unknown codes from one IP
// fingerprint; subMail: newsletter sign-ups per address.
const LIMIT = { codeIp: 30, codeHour: 5, codeDay: 10, codeMail: 30, failIp: 30, subIp: 20, subMail: 3 };
const WEBHOOK_SKEW_S = 5 * 60;           // Svix: a signed timestamp may be this far from our clock
const LANGS = new Set(['sr', 'en', 'ru']);
const TOPICS = ['vesti', 'cene', 'punjaci', 'moji'];
const DEFAULT_TOPICS = 'vesti,cene,punjaci';
const DCS = new Set(['ccs2', 'chademo', 'none']);
const CONSENT_V = 'pregled-v1';          // version of the consent sentence under the newsletter forms
const MAIL_FROM = 'BlokVolt <obavestenja@mail.blokvolt.com>', MAIL_REPLY_TO = 'hello@blokvolt.com';
// build.py rewrites the next line in dist/_worker.js: the city slugs of content/data/gradovi.json, the day of "pregled"
// in content/data/site.json and whether it is on (the sender works only then); the values here are the ones the tests use
const CFG = { cities: ['beograd', 'novi-sad', 'nis', 'subotica', 'cacak', 'kragujevac'], day: 'petak', pregled: true };
// "the first issue arrives on <day>" in the three languages
const DAYS = {
  ponedeljak: { sr: 'u ponedeljak', en: 'on Monday', ru: 'в понедельник' }, utorak: { sr: 'u utorak', en: 'on Tuesday', ru: 'во вторник' },
  sreda: { sr: 'u sredu', en: 'on Wednesday', ru: 'в среду' }, 'četvrtak': { sr: 'u četvrtak', en: 'on Thursday', ru: 'в четверг' },
  petak: { sr: 'u petak', en: 'on Friday', ru: 'в пятницу' }, subota: { sr: 'u subotu', en: 'on Saturday', ru: 'в субботу' },
  nedelja: { sr: 'u nedelju', en: 'on Sunday', ru: 'в воскресенье' },
};

const enc = new TextEncoder();
const hex = buf => [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
function randHex(bytes) {
  const a = new Uint8Array(bytes);
  crypto.getRandomValues(a);
  return hex(a);
}
async function sha256(s) { return hex(await crypto.subtle.digest('SHA-256', enc.encode(s))); }
// compares two hashes without stopping at the first difference
function same(a, b) {
  a = String(a || ''); b = String(b || '');
  let d = a.length ^ b.length;
  for (let i = 0; i < Math.max(a.length, b.length); i++) d |= (a.charCodeAt(i) || 0) ^ (b.charCodeAt(i) || 0);
  return d === 0;
}
// six digits, every value equally likely (draws above the last full block of 1.000.000 are repeated)
function sixDigits() {
  const a = new Uint32Array(1), lim = Math.floor(0x100000000 / 1e6) * 1e6;
  do crypto.getRandomValues(a); while (a[0] >= lim);
  return String(a[0] % 1e6).padStart(6, '0');
}
const EMAILY = /^[a-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@(?=.{4,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]{2,59})$/;
// trimmed and lower-cased, at most 120 characters, no control characters; null when it is not an address
function normEmail(v) {
  if (typeof v !== 'string') return null;
  const e = v.trim().toLowerCase();
  if (!e || e.length > 120 || /[\u0000-\u001f\u007f\s]/.test(e) || !EMAILY.test(e) || /^\.|\.\.|\.@/.test(e)) return null;
  return e;
}
function maskEmail(e) {
  const [u, h] = String(e).split('@');
  return (u ? u[0] : '') + '***@' + (h || '');
}
const langOf = v => (LANGS.has(v) ? v : 'sr');
const lpre = lang => (lang === 'en' || lang === 'ru' ? '/' + lang : '');
const siteOf = env => String(env.SITE || 'https://www.blokvolt.rs').replace(/\/+$/, '');
const mailOn = env => env.MAIL_MODE === 'log' || !!env.RESEND_API_KEY;
const devMode = env => env.MAIL_MODE === 'log';
const replyTo = env => env.MAIL_REPLY_TO || MAIL_REPLY_TO;
const TOK32 = /^[0-9a-f]{32}$/, TOK64 = /^[0-9a-f]{64}$/;
// a short key for the rate limits of one address (the address itself is not written to rl)
const mailKey = async email => (await sha256('rl:' + email)).slice(0, 24);

function cookieOf(request, name) {
  const m = (request.headers.get('cookie') || '').match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
  return m ? m[1] : '';
}
// bv_s: the session (HttpOnly, only sent to /api); bv_in: a hint for the static pages. Empty token = sign out.
function sessionCookies(env, token) {
  const sec = devMode(env) ? '' : '; Secure', age = token ? SESSION_S : 0;
  return ['bv_s=' + (token || '') + '; Path=/api; HttpOnly' + sec + '; SameSite=Lax; Max-Age=' + age,
    'bv_in=' + (token ? '1' : '') + '; Path=/' + sec + '; SameSite=Lax; Max-Age=' + age];
}
// bv_n: the browser that asked for a sign-in code (HttpOnly, only sent to /api/nalog, as long as the code). Empty = clear.
function nonceCookie(env, nonce) {
  return 'bv_n=' + (nonce || '') + '; Path=/api/nalog; HttpOnly' + (devMode(env) ? '' : '; Secure') + '; SameSite=Lax; Max-Age=' + (nonce ? CODE_S : 0);
}
// the page a newsletter sign-up came from, as the consent's source; anything else is 'nepoznato', so the values the
// server writes itself (confirm-click, nalog, one-click, …) can never come from a request
const pagePath = v => (typeof v === 'string' && /^\/[a-z0-9/-]{0,79}$/.test(v) ? v : 'nepoznato');
// work after the answer (mail): logged when it fails, never thrown
function background(ctx, p) {
  const q = Promise.resolve(p).catch(e => console.log('background: ' + (e && e.message)));
  if (ctx && ctx.waitUntil) ctx.waitUntil(q);
  return q;
}
// today's count of a rate-limit key, without counting
async function used(env, key) {
  const r = await env.DB.prepare('SELECT n FROM rl WHERE k = ?1 AND day = ?2').bind(key, today()).first();
  return r ? r.n : 0;
}
function jsonC(obj, cookies) {
  const h = new Headers({ ...JSON_HEADERS, 'cache-control': 'no-store' });
  for (const c of cookies) h.append('set-cookie', c);
  return new Response(JSON.stringify(obj), { status: 200, headers: h });
}
async function readBody(request) {
  try {
    const b = await request.json();
    return b && typeof b === 'object' && !Array.isArray(b) ? b : null;
  } catch (e) { return null; }
}
// topics as a list or "a,b"; undefined when not given, null when nothing valid is in it
function topicsOf(v) {
  if (v === undefined) return undefined;
  const a = Array.isArray(v) ? v.map(String) : typeof v === 'string' ? v.split(',') : [];
  const t = TOPICS.filter(x => a.some(y => y.trim() === x));
  return t.length ? t.join(',') : null;
}

// ---------------------------------------------------------------- tables (created once per isolate)
// One run at a time per isolate: the background tick of the issues may start while a request checks the tables too.
let SCHEMA_OK = false, SCHEMA_RUN = null;
async function ensureSchema(env) {
  if (SCHEMA_OK) return;
  if (!SCHEMA_RUN) SCHEMA_RUN = createTables(env).finally(() => { SCHEMA_RUN = null; });
  return SCHEMA_RUN;
}
async function createTables(env) {
  // auth_codes is keyed by (address, nonce) since the codes are bound to a browser; a table of the older shape (one code
  // per address) is replaced: its rows live 15 minutes
  try { await env.DB.prepare('SELECT nonce FROM auth_codes LIMIT 1').first(); } catch (e) {
    if (/no such column/i.test(String(e && e.message))) await env.DB.prepare('DROP TABLE auth_codes').run();
  }
  const q = [
    `CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, lang TEXT, created_at INTEGER,
      verified_at INTEGER, last_login_at INTEGER, car TEXT, dc TEXT, tesla INTEGER DEFAULT 0, city TEXT)`,
    `CREATE TABLE IF NOT EXISTS auth_codes (email TEXT NOT NULL, nonce TEXT NOT NULL, code_hash TEXT, link_hash TEXT, salt TEXT,
      exp INTEGER, tries INTEGER DEFAULT 0, at INTEGER, lang TEXT, opt_in INTEGER DEFAULT 0, PRIMARY KEY (email, nonce))`,
    'CREATE INDEX IF NOT EXISTS auth_codes_link ON auth_codes (link_hash)',
    'CREATE TABLE IF NOT EXISTS sessions (h TEXT PRIMARY KEY, uid TEXT NOT NULL, at INTEGER, seen INTEGER, exp INTEGER, kind TEXT)',
    'CREATE INDEX IF NOT EXISTS sessions_uid ON sessions (uid)',
    'CREATE TABLE IF NOT EXISTS favs (uid TEXT NOT NULL, st TEXT NOT NULL, at INTEGER, PRIMARY KEY (uid, st))',
    `CREATE TABLE IF NOT EXISTS subs (email TEXT PRIMARY KEY, uid TEXT, lang TEXT, topics TEXT, freq TEXT, status TEXT,
      token TEXT UNIQUE, src TEXT, consent_v TEXT, created_at INTEGER, confirmed_at INTEGER, off_at INTEGER, off_reason TEXT)`,
    'CREATE INDEX IF NOT EXISTS subs_status ON subs (status, created_at)',
    `CREATE TABLE IF NOT EXISTS consents (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, kind TEXT, granted INTEGER,
      text_v TEXT, src TEXT, at INTEGER, ip TEXT)`,
    'CREATE INDEX IF NOT EXISTS consents_email ON consents (email)',
    'CREATE TABLE IF NOT EXISTS rl (k TEXT NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (k, day))',
    'CREATE TABLE IF NOT EXISTS suppressions (email_hash TEXT PRIMARY KEY, reason TEXT, at INTEGER)',
    // sending the issues
    'CREATE TABLE IF NOT EXISTS pg_previews (slug TEXT NOT NULL, hash TEXT NOT NULL, at INTEGER, PRIMARY KEY (slug, hash))',
    'CREATE TABLE IF NOT EXISTS pg_issues (slug TEXT PRIMARY KEY, hash TEXT, enqueued_at INTEGER, queued INTEGER, stopped_at INTEGER)',
    `CREATE TABLE IF NOT EXISTS pg_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL, email TEXT, lang TEXT, topics TEXT,
      month TEXT, status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, provider_id TEXT, at INTEGER, sent_at INTEGER, note TEXT,
      UNIQUE (slug, email))`,
    'CREATE INDEX IF NOT EXISTS pg_queue_status ON pg_queue (status, id)',
    'CREATE INDEX IF NOT EXISTS pg_queue_sent ON pg_queue (sent_at)',
    'CREATE INDEX IF NOT EXISTS pg_queue_email ON pg_queue (email, month)',
    'CREATE TABLE IF NOT EXISTS pg_clicks (slug TEXT NOT NULL, l INTEGER NOT NULL, day TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (slug, l, day))',
    'CREATE TABLE IF NOT EXISTS pg_lock (id INTEGER PRIMARY KEY CHECK (id = 1), at INTEGER NOT NULL DEFAULT 0, until INTEGER NOT NULL DEFAULT 0)',
  ];
  if (devMode(env)) q.push(`CREATE TABLE IF NOT EXISTS mail_log (id INTEGER PRIMARY KEY AUTOINCREMENT, at INTEGER, to_addr TEXT,
      subject TEXT, html TEXT, text TEXT, kind TEXT, hdr TEXT)`);
  await env.DB.batch(q.map(s => env.DB.prepare(s)));                  // a failure throws: not ready, tried again next time
  // reports and photos of a signed-in driver carry the account id (NULL for everyone else). Ready only when every step
  // worked; the one expected error is the column being there already.
  let ok = true;
  for (const t of ['checkins', 'photos']) {
    try { await env.DB.prepare(`ALTER TABLE ${t} ADD COLUMN uid TEXT`).run(); } catch (e) {
      if (!/duplicate column/i.test(String(e && e.message))) ok = false;
    }
    try { await env.DB.prepare(`CREATE INDEX IF NOT EXISTS ${t}_uid ON ${t} (uid)`).run(); } catch (e) { ok = false; }
  }
  SCHEMA_OK = ok;
}

// on ~2 % of the requests: expired codes and sessions, consent histories 3 years after their last withdrawal, and
// unconfirmed sign-ups older than 30 days — deleted; their consent rows stay as proof, with a row saying the sign-up
// expired, but keep only the SHA-256 of the address (as after a deleted account). At most 50 sign-ups a run. The rows of
// sent issues lose the address 60 days after they were sent (or given up): only the counts stay.
async function housekeeping(env) {
  const t = now(), cut = t - PENDING_S;
  await env.DB.batch([
    env.DB.prepare('DELETE FROM auth_codes WHERE exp < ?1').bind(t),
    env.DB.prepare('DELETE FROM sessions WHERE exp < ?1').bind(t),
    env.DB.prepare(`DELETE FROM consents WHERE email IN (SELECT c.email FROM consents c
      WHERE c.id = (SELECT MAX(x.id) FROM consents x WHERE x.email = c.email) AND c.granted = 0 AND c.at < ?1)`).bind(t - CONSENT_KEEP_S),
    env.DB.prepare(`UPDATE pg_queue SET email = NULL WHERE email IS NOT NULL AND status != 'queued' AND COALESCE(sent_at, at) < ?1`).bind(t - PG_KEEP_S),
  ]);
  const old = await env.DB.prepare(`SELECT email FROM subs WHERE status = 'pending' AND created_at < ?1 LIMIT 50`).bind(cut).all();
  const q = [];
  for (const { email } of old.results) {
    // one transaction per address, and each step only while the sign-up is still unconfirmed (a click may come meanwhile)
    const h = 'sha256:' + await sha256(email), still = `EXISTS (SELECT 1 FROM subs WHERE email = ?2 AND status = 'pending' AND created_at < ?3)`;
    q.push(env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip)
        SELECT ?1, 'pregled', 0, consent_v, 'isteklo', ?4, NULL FROM subs WHERE email = ?2 AND status = 'pending' AND created_at < ?3`).bind(h, email, cut, t),
      env.DB.prepare(`UPDATE consents SET email = ?1 WHERE email = ?2 AND ${still}`).bind(h, email, cut),
      env.DB.prepare(`DELETE FROM subs WHERE email = ?1 AND status = 'pending' AND created_at < ?2`).bind(email, cut));
  }
  if (q.length) await env.DB.batch(q);
}

// ---------------------------------------------------------------- sessions
// the session of this request: cookie bv_s or "Authorization: Bearer <token>"; null when there is none
async function sessionOf(request, env) {
  const m = (request.headers.get('authorization') || '').match(/^Bearer ([0-9a-f]{64})$/);
  const token = m ? m[1] : cookieOf(request, 'bv_s');
  if (!TOK64.test(token)) return null;
  await ensureSchema(env);
  const s = await env.DB.prepare('SELECT h, uid, seen, exp, kind FROM sessions WHERE h = ?1').bind(await sha256(token)).first();
  if (!s || s.exp < now()) return null;
  return Object.assign(s, { token, bearer: !!m });
}
// the account id for a report from the map, when the driver is signed in; a broken session never stops a report
async function reporter(request, env) {
  if (!cookieOf(request, 'bv_s') && !/^Bearer /.test(request.headers.get('authorization') || '')) return null;
  try { const s = await sessionOf(request, env); return s ? s.uid : null; } catch (e) { return null; }
}
// "seen" is written at most once an hour; each time the session runs for another 90 days
async function touch(env, s) {
  if (now() - (s.seen || 0) < 3600) return false;
  await env.DB.prepare('UPDATE sessions SET seen = ?1, exp = ?2 WHERE h = ?3').bind(now(), now() + SESSION_S, s.h).run();
  return true;
}
const subOut = s => ({ status: s.status, topics: (s.topics || '').split(',').filter(Boolean), freq: s.freq, lang: s.lang });
// what /api/nalog/ja (and a successful sign-in) answers
async function account(env, uid) {
  const u = await env.DB.prepare('SELECT email, lang, created_at, car, dc, tesla, city FROM users WHERE id = ?1').bind(uid).first();
  if (!u) return null;
  const f = await env.DB.prepare('SELECT st FROM favs WHERE uid = ?1 ORDER BY at, st').bind(uid).all();
  const sub = await env.DB.prepare('SELECT status, topics, freq, lang FROM subs WHERE email = ?1').bind(u.email).first();
  // owner: a short hash of the account id; the pages keep it next to the browser's favourites (bv:fav-owner), so a list
  // of another account is never joined with this one
  return { ok: true, user: { ...u, tesla: !!u.tesla, owner: (await sha256('fav-owner:' + uid)).slice(0, 16) },
    favs: f.results.map(r => r.st), sub: sub ? subOut(sub) : null };
}

// station ids a favourite may point to: Serbia's map (stationIds) and the neighbouring countries' layer of /mapa/.
// An empty set (map files not readable) means "do not check".
let MAPIDS = null, MAPIDS_AT = 0;
async function mapIds(env, request) {
  if (MAPIDS && Date.now() - MAPIDS_AT < 600000) return MAPIDS;
  const own = await stationIds(env, request);
  if (!own.size) return own;
  let rg = {};
  try { rg = await env.ASSETS.fetch(new Request(new URL('/assets/map/region.json', request.url))).then(r => r.json()); } catch (e) { rg = {}; }
  MAPIDS = new Set([...own, ...(rg.stations || []).map(s => s.id)]);
  MAPIDS_AT = Date.now();
  return MAPIDS;
}

// ---------------------------------------------------------------- mail (Resend)
// true when mail of this kind must not go to the address: it bounced for good or was marked as spam (Resend's webhook,
// postaResend). A sign-in code is the reader's own request and still goes out (Resend keeps its own hard-bounce list);
// a confirmation link too, because the click is a new, explicit consent. Everything else (welcome, newsletter) is held.
// Lifted by: a successful sign-in → 'bounce' (the code arrived, so the mailbox works); a confirmed newsletter sign-up and
// switching the newsletter on in the account (an explicit act with a proved address) → 'bounce' and 'complaint'.
async function suppressed(env, email, kind) {
  if (kind === 'code' || kind === 'confirm') return false;
  const r = await env.DB.prepare('SELECT 1 AS x FROM suppressions WHERE email_hash = ?1').bind(await sha256(email)).first();
  return !!r;
}
async function unsuppress(env, email, reasons) {
  const q = 'DELETE FROM suppressions WHERE email_hash = ?1 AND reason IN (' + reasons.map((_, i) => '?' + (i + 2)).join(', ') + ')';
  await env.DB.prepare(q).bind(await sha256(email), ...reasons).run();
}
// m: {to, subject, html, text, kind, idem, unsub, tags?}. unsub = the one-click URL of a newsletter mail: List-Unsubscribe
// (RFC 8058, with a mailto for clients without one-click). idem = Idempotency-Key, so a retry never sends twice.
// Every mail to a reader (code, confirmation, welcome, the issues) goes through a suppression check first: nothing is
// sent to a suppressed address, and the caller answers as if it had been, so the answer never tells that the address is
// on the list. sendMail does it for the mails of the accounts; the issues check a whole batch at once (pgSend).
async function sendMail(env, m) {
  if (await suppressed(env, m.to, m.kind)) return true;
  return (await deliver(env, m, false)).ok;
}
// one mail to Resend (or, in log mode, to mail_log): {ok, status, id}, status 0 = timeout or network error. A 5xx, a 429
// or a timeout is tried once more with the same Idempotency-Key, unless `once` (the issues: their loop waits for the next
// tick instead).
async function deliver(env, m, once) {
  const hdr = m.unsub ? { 'List-Unsubscribe': '<' + m.unsub + '>, <mailto:' + replyTo(env) + '?subject=odjava>', 'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click' } : null;
  if (devMode(env)) {
    const r = await env.DB.prepare('INSERT INTO mail_log (at, to_addr, subject, html, text, kind, hdr) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)')
      .bind(now(), m.to, m.subject, m.html, m.text, m.kind, JSON.stringify({ ...(hdr || {}), 'Idempotency-Key': m.idem || '' })).run();
    return { ok: true, status: 200, id: 'log-' + ((r.meta && r.meta.last_row_id) || '') };
  }
  if (!env.RESEND_API_KEY) return { ok: false, status: 0, id: null };
  const payload = { from: env.MAIL_FROM || MAIL_FROM, to: [m.to], reply_to: replyTo(env), subject: m.subject, html: m.html, text: m.text,
    tags: m.tags || [{ name: 'kind', value: m.kind }] };
  if (hdr) payload.headers = hdr;
  let out = { ok: false, status: 0, id: null };
  for (let i = 0; i < (once ? 1 : 2); i++) {
    if (i) await new Promise(ok => setTimeout(ok, 700));
    try {
      const r = await fetch('https://api.resend.com/emails', {
        method: 'POST', body: JSON.stringify(payload), signal: AbortSignal.timeout(8000),
        headers: { authorization: 'Bearer ' + env.RESEND_API_KEY, 'content-type': 'application/json', ...(m.idem ? { 'idempotency-key': m.idem } : {}) },
      });
      out = { ok: r.ok, status: r.status, id: null };
      if (r.ok) {
        try { out.id = String((await r.json()).id || '') || null; } catch (e) { /* sent; only the id is unknown */ }
        return out;
      }
      if (r.status < 500 && r.status !== 429) return out;          // refused: a retry would not help
    } catch (e) { out = { ok: false, status: 0, id: null }; }     // timeout or network error: once more, same Idempotency-Key
  }
  return out;
}

const MAIL_T = {
  sr: {
    code_subj: '{code} — vaš kod za BlokVolt', code_pre: 'Važi 15 minuta.', code_h: 'Vaš kod za prijavu',
    code_p: 'Upišite ga na stranici za prijavu. Kod važi 15 minuta i može se iskoristiti samo jednom.', code_btn: 'Prijavite se jednim klikom',
    code_small: 'Ako niste tražili kod, zanemarite ovaj mejl — bez koda niko ne može da uđe u vaš nalog.',
    code_why: 'Mejl je poslat jer je na www.blokvolt.rs zatražen kod za prijavu na ovu adresu.',
    conf_subj: 'Potvrdite prijavu na Nedeljni pregled', conf_pre: 'Jedan klik — i prvi broj stiže {day}.', conf_h: 'Još samo jedan korak',
    conf_p: 'Adresa {email} je prijavljena na Nedeljni pregled BlokVolt: vesti, cene javnog punjenja i novi punjači, jednom nedeljno.',
    conf_btn: 'Potvrđujem prijavu', conf_small: 'Ako niste vi, ignorišite ovaj mejl — bez potvrde vam ništa nećemo slati.',
    conf_why: 'Mejl je poslat jer je ova adresa upisana u prijavu za Nedeljni pregled na www.blokvolt.rs.',
    wel_subj: 'Prijava je potvrđena — Nedeljni pregled', wel_pre: 'Prvi broj stiže {day} ujutru.', wel_h: 'Prijava je potvrđena',
    wel_p: 'Hvala! Prvi broj stiže {day} ujutru.', wel_in: 'U svakom broju:',
    wel_list: ['3–5 vesti nedelje, svaka sa izvorom', 'Promene cena po mrežama, kad ih ima', 'Novi i popravljeni punjači na mapi'],
    wel_link: 'Izaberite teme i učestalost', wel_spam: 'Da mejlovi ne završe u spamu, dodajte {from} u kontakte.',
    wel_why: 'Mejl je poslat jer ste potvrdili prijavu na Nedeljni pregled na www.blokvolt.rs.', unsub: 'Odjavite se jednim klikom',
  },
  en: {
    code_subj: '{code} — your BlokVolt code', code_pre: 'Valid for 15 minutes.', code_h: 'Your sign-in code',
    code_p: 'Enter it on the sign-in page. The code is valid for 15 minutes and can be used only once.', code_btn: 'Sign in with one click',
    code_small: 'If you did not ask for a code, ignore this e-mail — nobody can get into your account without the code.',
    code_why: 'This e-mail was sent because a sign-in code for this address was requested on www.blokvolt.rs.',
    conf_subj: 'Confirm your subscription to the Weekly Digest', conf_pre: 'One click — and the first issue arrives {day}.', conf_h: 'Just one more step',
    conf_p: 'The address {email} has been signed up for the BlokVolt Weekly Digest: news, public charging prices and new chargers, once a week.',
    conf_btn: 'Confirm my subscription', conf_small: 'If this was not you, ignore this e-mail — without confirmation nothing will be sent to you.',
    conf_why: 'This e-mail was sent because this address was entered in the Weekly Digest sign-up form on www.blokvolt.rs.',
    wel_subj: 'Subscription confirmed — Weekly Digest', wel_pre: 'The first issue arrives {day} morning.', wel_h: 'Subscription confirmed',
    wel_p: 'Thank you! The first issue arrives {day} morning.', wel_in: 'In every issue:',
    wel_list: ['3–5 news stories of the week, each with its source', 'Price changes by network, when there are any', 'New and repaired chargers on the map'],
    wel_link: 'Choose topics and frequency', wel_spam: 'To keep these e-mails out of spam, add {from} to your contacts.',
    wel_why: 'This e-mail was sent because you confirmed your subscription to the Weekly Digest on www.blokvolt.rs.', unsub: 'Unsubscribe with one click',
  },
  ru: {
    code_subj: '{code} — ваш код для BlokVolt', code_pre: 'Действует 15 минут.', code_h: 'Ваш код для входа',
    code_p: 'Введите его на странице входа. Код действует 15 минут, и использовать его можно только один раз.', code_btn: 'Войти в один клик',
    code_small: 'Если вы не запрашивали код, не обращайте внимания на это письмо — без кода никто не войдёт в ваш аккаунт.',
    code_why: 'Письмо отправлено, потому что на www.blokvolt.rs запросили код для входа на этот адрес.',
    conf_subj: 'Подтвердите подписку на Еженедельный обзор', conf_pre: 'Один клик — и первый выпуск придёт {day}.', conf_h: 'Остался один шаг',
    conf_p: 'Адрес {email} подписан на Еженедельный обзор BlokVolt: новости, цены публичной зарядки и новые зарядные станции, раз в неделю.',
    conf_btn: 'Подтверждаю подписку', conf_small: 'Если это были не вы, не обращайте внимания на письмо — без подтверждения мы ничего не будем присылать.',
    conf_why: 'Письмо отправлено, потому что этот адрес указали в форме подписки на Еженедельный обзор на www.blokvolt.rs.',
    wel_subj: 'Подписка подтверждена — Еженедельный обзор', wel_pre: 'Первый выпуск придёт {day} утром.', wel_h: 'Подписка подтверждена',
    wel_p: 'Спасибо! Первый выпуск придёт {day} утром.', wel_in: 'В каждом выпуске:',
    wel_list: ['3–5 новостей недели, у каждой — источник', 'Изменения цен по сетям, если они есть', 'Новые и отремонтированные зарядные станции на карте'],
    wel_link: 'Выбрать темы и периодичность', wel_spam: 'Чтобы письма не попадали в спам, добавьте {from} в контакты.',
    wel_why: 'Письмо отправлено, потому что вы подтвердили подписку на Еженедельный обзор на www.blokvolt.rs.', unsub: 'Отписаться в один клик',
  },
};
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
// e-mail-safe HTML: tables, inline styles, one 600 px column, system fonts, no remote images.
// o: {lang, pre, h, p: [html], code, btn: [label, url], list: [text], after: [html], small, why, unsub: [label, url]}
function mailHtml(env, o) {
  const host = siteOf(env).replace(/^https?:\/\//, '');
  const P = 'margin:0 0 16px;font:16px/1.55 ' + FONT + ';color:#2A2F3A';
  let b = '<h1 style="margin:0 0 14px;font:700 24px/1.25 ' + FONT + ';color:#0D111A;letter-spacing:-.3px">' + esc(o.h) + '</h1>';
  for (const p of o.p || []) b += '<p style="' + P + '">' + p + '</p>';
  if (o.code) b += '<p style="margin:4px 0 20px"><span style="display:inline-block;padding:14px 20px 14px 26px;border-radius:12px;background:#F3FBD2;font:700 34px/1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:10px;color:#0D111A">' + esc(o.code) + '</span></p>';
  if (o.list) b += '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 18px">' + o.list.map(x =>
    '<tr><td valign="top" style="padding:3px 10px 3px 0;font:16px/1.5 ' + FONT + ';color:#6E8A12">&#9679;</td><td style="padding:3px 0;font:16px/1.5 ' + FONT + ';color:#2A2F3A">' + esc(x) + '</td></tr>').join('') + '</table>';
  if (o.btn) b += '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0 20px"><tr><td style="border-radius:12px;background:#0D111A">' +
    '<a href="' + esc(o.btn[1]) + '" style="display:inline-block;padding:14px 22px;border-radius:12px;font:600 16px/1.2 ' + FONT + ';color:#FFFFFF;text-decoration:none">' + esc(o.btn[0]) + '</a></td></tr></table>';
  for (const p of o.after || []) b += '<p style="' + P + '">' + p + '</p>';
  if (o.small) b += '<p style="margin:0;font:14px/1.5 ' + FONT + ';color:#5C6270">' + esc(o.small) + '</p>';
  const foot = esc(o.why) + (o.unsub ? ' <a href="' + esc(o.unsub[1]) + '" style="color:#5C6270">' + esc(o.unsub[0]) + '</a>' : '');
  return '<!DOCTYPE html><html lang="' + o.lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>' + esc(o.title) + '</title></head>' +
    '<body style="margin:0;padding:0;background:#F4F3EE">' +
    '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#F4F3EE">' + esc(o.pre) + '&#8199;&#65279;&#847;'.repeat(12) + '</div>' +
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F4F3EE"><tr><td align="center" style="padding:28px 12px 32px">' +
    '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px">' +
    '<tr><td style="padding:0 6px 16px"><span style="font:22px/1 ' + FONT + ';letter-spacing:-.6px;color:#0D111A">blok<b style="font-weight:800">volt</b></span>' +
    '<div style="width:34px;height:5px;margin-top:7px;border-radius:3px;background:#D9F45B;font-size:0;line-height:0">&nbsp;</div></td></tr>' +
    '<tr><td style="background:#FFFFFF;border:1px solid #E6E5DC;border-radius:18px;padding:30px 30px 26px">' + b + '</td></tr>' +
    '<tr><td style="padding:18px 8px 0;font:13px/1.55 ' + FONT + ';color:#5C6270">BlokVolt · ' + esc(host) + ' · ' + esc(replyTo(env)) + '<br>' + foot + '</td></tr>' +
    '</table></td></tr></table></body></html>';
}
function mailText(env, o) {
  const host = siteOf(env).replace(/^https?:\/\//, '');
  const t = [o.h, ''];
  for (const p of o.pText || []) t.push(p, '');
  if (o.code) t.push(o.code, '');
  if (o.list) t.push(...o.list.map(x => '• ' + x), '');
  if (o.btn) t.push(o.btn[0] + ': ' + o.btn[1], '');
  for (const p of o.afterText || []) t.push(p, '');
  if (o.small) t.push(o.small, '');
  t.push('—', 'BlokVolt · ' + host + ' · ' + replyTo(env), o.why);
  if (o.unsub) t.push(o.unsub[0] + ': ' + o.unsub[1]);
  return t.join('\n') + '\n';
}
function renderMail(env, kind, o, extra) {
  return Object.assign({ subject: o.title, html: mailHtml(env, o), text: mailText(env, o), kind }, extra);
}
const dayIn = lang => (DAYS[CFG.day] || DAYS.petak)[lang];
const fromAddr = env => ((env.MAIL_FROM || MAIL_FROM).match(/<([^>]+)>/) || [])[1] || env.MAIL_FROM || MAIL_FROM;

function mailCode(env, lang, email, code, link, idem) {
  const T = MAIL_T[lang], url = siteOf(env) + lpre(lang) + '/nalog/?prijava=' + link;
  return renderMail(env, 'code', { lang, title: T.code_subj.replace('{code}', code), pre: T.code_pre, h: T.code_h, p: [esc(T.code_p)], pText: [T.code_p],
    code, btn: [T.code_btn, url], small: T.code_small, why: T.code_why }, { to: email, idem });
}
function mailConfirm(env, lang, email, token, at) {
  const T = MAIL_T[lang], url = siteOf(env) + lpre(lang) + '/pregled/potvrda/?t=' + token;
  const p = T.conf_p.split('{email}');
  return renderMail(env, 'confirm', { lang, title: T.conf_subj, pre: T.conf_pre.replace('{day}', dayIn(lang)), h: T.conf_h,
    p: [esc(p[0]) + '<b style="color:#0D111A">' + esc(email) + '</b>' + esc(p[1])], pText: [T.conf_p.replace('{email}', email)],
    btn: [T.conf_btn, url], small: T.conf_small, why: T.conf_why }, { to: email, idem: 'confirm-' + token + '-' + at });
}
function mailWelcome(env, lang, email, token) {
  const T = MAIL_T[lang], S = siteOf(env) + lpre(lang), from = fromAddr(env);
  const prefs = S + '/pregled/odjava/?t=' + token + '&teme=1', out = S + '/pregled/odjava/?t=' + token;
  const spam = T.wel_spam.split('{from}');
  return renderMail(env, 'welcome', { lang, title: T.wel_subj, pre: T.wel_pre.replace('{day}', dayIn(lang)), h: T.wel_h,
    p: [esc(T.wel_p.replace('{day}', dayIn(lang))), esc(T.wel_in)], pText: [T.wel_p.replace('{day}', dayIn(lang)), T.wel_in], list: T.wel_list,
    after: ['<a href="' + esc(prefs) + '" style="color:#0D111A;font-weight:600">' + esc(T.wel_link) + '</a>',
      esc(spam[0]) + '<b style="color:#0D111A">' + esc(from) + '</b>' + esc(spam[1])],
    afterText: [T.wel_link + ': ' + prefs, T.wel_spam.replace('{from}', from)],
    why: T.wel_why, unsub: [T.unsub, out] }, { to: email, idem: 'welcome-' + token, unsub: siteOf(env) + '/api/posta/odjava?t=' + token });
}

// ---------------------------------------------------------------- sign-in
// {email, lang, opt_in?, hp, t, app?, nonce?}. The code is stored for (address, nonce): the nonce comes from this
// browser's cookie bv_n (or, for the app, from the body) and is new when there is none. Asking again from the same
// browser replaces its code; other browsers keep theirs. The mail is sent after the answer.
async function nalogKod(request, env, b, ctx) {
  if (b.hp) return json({ ok: true });                                   // honeypot: looks sent, nothing happens
  if (typeof b.t === 'number' && b.t < 1500) return bad('too fast', 429);
  const email = normEmail(b.email);
  if (!email) return bad('email');
  if (!mailOn(env)) return bad('mail_off', 503);
  await ensureSchema(env);
  const ip = await ipHash(request, env), mk = await mailKey(email), hour = new Date().toISOString().slice(0, 13);
  if (!(await allow(env, 'nk:' + ip, LIMIT.codeIp)) || !(await allow(env, 'nh:' + mk + ':' + ip + ':' + hour, LIMIT.codeHour)) ||
    !(await allow(env, 'nd:' + mk + ':' + ip, LIMIT.codeDay)) || !(await allow(env, 'na:' + mk, LIMIT.codeMail))) return bad('limit', 429);
  const app = b.app === true, given = app ? String(b.nonce || '') : cookieOf(request, 'bv_n');
  const nonce = TOK32.test(given) ? given : randHex(16);
  // only hashes are stored
  const lang = langOf(b.lang), code = sixDigits(), link = randHex(32), salt = randHex(16), t = now();
  await env.DB.prepare(`INSERT INTO auth_codes (email, nonce, code_hash, link_hash, salt, exp, tries, at, lang, opt_in)
    VALUES (?1, ?2, ?3, ?4, ?5, ?6, 0, ?7, ?8, ?9)
    ON CONFLICT (email, nonce) DO UPDATE SET code_hash = ?3, link_hash = ?4, salt = ?5, exp = ?6, tries = 0, at = ?7, lang = ?8, opt_in = ?9`)
    .bind(email, nonce, await sha256(salt + code), await sha256(link), salt, t + CODE_S, t, lang, b.opt_in === true ? 1 : 0).run();
  // after the answer: the page cannot learn about a failed send (logged; the reader has "Pošaljite ponovo")
  const m = mailCode(env, lang, email, code, link, 'code-' + (await sha256(salt + link)).slice(0, 40));
  background(ctx, sendMail(env, m).then(sent => { if (!sent) console.log('mail not sent: code'); }));
  return app ? json({ ok: true, nonce }) : jsonC({ ok: true }, [nonceCookie(env, nonce)]);
}

// {email, code, app?, nonce?}: only the code of this browser's nonce (cookie bv_n, or the app's nonce) is checked.
// Every attempt counts, the right one too; the fifth wrong one ends that code (and only that one). From one IP
// fingerprint at most 30 failures a day, then 429 for the rest of the day.
async function nalogPotvrdi(request, env, b) {
  await ensureSchema(env);
  const ip = await ipHash(request, env);
  if ((await used(env, 'nf:' + ip)) >= LIMIT.failIp) return bad('limit', 429);
  const fail = async (err, status) => { await allow(env, 'nf:' + ip, LIMIT.failIp); return bad(err, status); };
  const email = normEmail(b.email), code = String(b.code == null ? '' : b.code).replace(/\D/g, '');
  const app = b.app === true, nonce = app ? String(b.nonce || '') : cookieOf(request, 'bv_n');
  if (!email) return fail('email');
  if (code.length !== 6 || !TOK32.test(nonce)) return fail('code');
  const row = await env.DB.prepare(`UPDATE auth_codes SET tries = tries + 1 WHERE email = ?1 AND nonce = ?2 AND exp >= ?3
    RETURNING nonce, code_hash, salt, tries, lang, opt_in`).bind(email, nonce, now()).first();
  if (!row) return fail('code');
  const wrong = !same(await sha256(row.salt + code), row.code_hash);
  if (row.tries > CODE_TRIES || (wrong && row.tries >= CODE_TRIES)) {
    await env.DB.prepare('DELETE FROM auth_codes WHERE email = ?1 AND nonce = ?2').bind(email, nonce).run();
    return fail('tries', 429);
  }
  if (wrong) return fail('code');
  return signIn(request, env, email, row, app);
}

// {token}: signs in. {token, peek: true}: only which address the link is for (masked), for the page before the click;
// nothing is spent.
async function nalogLink(request, env, b) {
  const token = String(b.token || '');
  if (!TOK64.test(token)) return bad('code');
  await ensureSchema(env);
  const row = await env.DB.prepare('SELECT email, nonce, code_hash, lang, opt_in FROM auth_codes WHERE link_hash = ?1 AND exp >= ?2')
    .bind(await sha256(token), now()).first();
  if (!row) return bad('code');
  if (b.peek === true) return json({ ok: true, email_masked: maskEmail(row.email) });
  return signIn(request, env, row.email, row, b.app === true);
}

// the code (or link) is spent, other browsers' codes stay; the account is created on the first sign-in; a new session
async function signIn(request, env, email, row, app) {
  const del = await env.DB.prepare('DELETE FROM auth_codes WHERE email = ?1 AND nonce = ?2 AND code_hash = ?3').bind(email, row.nonce, row.code_hash).run();
  if (!del.meta || !del.meta.changes) return bad('code');                // spent a moment ago by another request
  const t = now(), lang = langOf(row.lang), token = randHex(32);
  const u = await env.DB.prepare(`INSERT INTO users (id, email, lang, created_at, verified_at, last_login_at) VALUES (?1, ?2, ?3, ?4, ?4, ?4)
    ON CONFLICT (email) DO UPDATE SET lang = ?3, verified_at = COALESCE(users.verified_at, ?4), last_login_at = ?4 RETURNING id`)
    .bind(randHex(16), email, lang, t).first();
  await env.DB.batch([
    env.DB.prepare('INSERT INTO sessions (h, uid, at, seen, exp, kind) VALUES (?1, ?2, ?3, ?3, ?4, ?5)').bind(await sha256(token), u.id, t, t + SESSION_S, app ? 'app' : 'web'),
    env.DB.prepare('UPDATE subs SET uid = ?1 WHERE email = ?2 AND uid IS NULL').bind(u.id, email),
  ]);
  await unsuppress(env, email, ['bounce']);                             // the code arrived: the mailbox works again
  // "Pošaljite mi i Nedeljni pregled" at sign-in: pending until the click in the confirmation mail, like every sign-up
  if (row.opt_in) await subscribe(request, env, email, { lang, uid: u.id, src: 'nalog-prijava' });
  const out = await account(env, u.id);
  return app ? json({ ...out, token }) : jsonC(out, sessionCookies(env, token).concat(nonceCookie(env, '')));
}

// ---------------------------------------------------------------- the account
async function nalogJa(request, env) {
  const s = await sessionOf(request, env);
  const out = s && await account(env, s.uid);
  if (!out) return bad('auth', 401);
  // once an hour: the session and the browser's cookies run for another 90 days
  return (await touch(env, s)) && !s.bearer ? jsonC(out, sessionCookies(env, s.token)) : json(out);
}

async function nalogOdjava(request, env, b) {
  const s = await sessionOf(request, env);
  if (s) await (b.all ? env.DB.prepare('DELETE FROM sessions WHERE uid = ?1').bind(s.uid) : env.DB.prepare('DELETE FROM sessions WHERE h = ?1').bind(s.h)).run();
  return jsonC({ ok: true }, sessionCookies(env, ''));
}

async function nalogPodesavanja(request, env, b) {
  const s = await sessionOf(request, env);
  if (!s) return bad('auth', 401);
  const set = {};
  if ('lang' in b) { if (!LANGS.has(b.lang)) return bad('lang'); set.lang = b.lang; }
  if ('car' in b) {
    const c = clean(b.car, 1000);
    if (c.length > 80) return bad('car');
    set.car = c || null;
  }
  if ('dc' in b) { if (b.dc && !DCS.has(b.dc)) return bad('dc'); set.dc = b.dc || null; }
  if ('tesla' in b) { if (typeof b.tesla !== 'boolean') return bad('tesla'); set.tesla = b.tesla ? 1 : 0; }
  if ('city' in b) { if (b.city && b.city !== 'drugo' && !CFG.cities.includes(b.city)) return bad('city'); set.city = b.city || null; }
  const keys = Object.keys(set);                                         // only the five names above
  if (keys.length) {
    await env.DB.prepare('UPDATE users SET ' + keys.map((k, i) => k + ' = ?' + (i + 2)).join(', ') + ' WHERE id = ?1')
      .bind(s.uid, ...keys.map(k => set[k])).run();
  }
  return json(await account(env, s.uid));
}

// {add: [ids], remove: [ids], replace: [ids]} — in that order: replace, remove, add. Ids that are not on the map are
// dropped (listed in `dropped`); above 300 favourites nothing more is added (`full`).
async function nalogOmiljeni(request, env, b) {
  const s = await sessionOf(request, env);
  if (!s) return bad('auth', 401);
  const ids = await mapIds(env, request), dropped = [];
  const valid = list => (Array.isArray(list) ? list : []).slice(0, 2 * MAX_FAVS).map(x => String(x)).filter(x => {
    const ok = /^[a-z0-9-]{3,60}$/.test(x) && (!ids.size || ids.has(x));
    if (!ok) dropped.push(x.slice(0, 60));
    return ok;
  });
  const rep = Array.isArray(b.replace) ? valid(b.replace) : null, rem = valid(b.remove), add = valid(b.add);
  const have = new Set(rep ? [] : (await env.DB.prepare('SELECT st FROM favs WHERE uid = ?1').bind(s.uid).all()).results.map(r => r.st));
  const q = [], t = now(), ins = x => q.push(env.DB.prepare('INSERT OR IGNORE INTO favs (uid, st, at) VALUES (?1, ?2, ?3)').bind(s.uid, x, t));
  let full = false;
  if (rep) {
    q.push(env.DB.prepare('DELETE FROM favs WHERE uid = ?1').bind(s.uid));
    for (const x of rep) {
      if (have.has(x)) continue;
      if (have.size >= MAX_FAVS) { full = true; continue; }
      have.add(x); ins(x);
    }
  }
  for (const x of rem) if (have.delete(x)) q.push(env.DB.prepare('DELETE FROM favs WHERE uid = ?1 AND st = ?2').bind(s.uid, x));
  for (const x of add) {
    if (have.has(x)) continue;
    if (have.size >= MAX_FAVS) { full = true; continue; }
    have.add(x); ins(x);
  }
  if (q.length) await env.DB.batch(q);
  const f = await env.DB.prepare('SELECT st FROM favs WHERE uid = ?1 ORDER BY at, st').bind(s.uid).all();
  return json({ ok: true, favs: f.results.map(r => r.st), dropped, full });
}

// "Moje prijave sa mape": the driver's reports and photos sent while signed in
async function nalogDoprinosi(request, env) {
  const s = await sessionOf(request, env);
  if (!s) return bad('auth', 401);
  const all = sql => env.DB.prepare(sql).bind(s.uid).all().then(r => r.results, () => []);
  // a photo that is not approved is reachable by its id alone (moderation), so its id is never shown
  const photos = (await all('SELECT id, st, status, at FROM photos WHERE uid = ?1 ORDER BY at DESC LIMIT 100'))
    .map(x => (x.status === 'ok' ? x : { st: x.st, status: x.status, at: x.at }));
  return json({ ok: true, checkins: await all('SELECT st, s, r, cs, at FROM checkins WHERE uid = ?1 ORDER BY at DESC LIMIT 200'), photos });
}

// everything stored about the account, as a JSON download (photos without the image bytes)
async function nalogIzvoz(request, env) {
  const s = await sessionOf(request, env);
  const u = s && await env.DB.prepare('SELECT * FROM users WHERE id = ?1').bind(s.uid).first();
  if (!u) return bad('auth', 401);
  const all = (sql, v) => env.DB.prepare(sql).bind(v).all().then(r => r.results, () => []);
  const out = {
    about: 'BlokVolt (www.blokvolt.rs) — podaci sačuvani uz vaš nalog / data stored with your account. Vreme: Unix sekunde (UTC).',
    exported_at: new Date().toISOString(),
    user: { ...u, tesla: !!u.tesla },
    favourites: await all('SELECT st, at FROM favs WHERE uid = ?1 ORDER BY at, st', s.uid),
    sessions: (await all('SELECT h, at, seen, exp, kind FROM sessions WHERE uid = ?1 ORDER BY at', s.uid))
      .map(x => ({ at: x.at, seen: x.seen, exp: x.exp, kind: x.kind, this_device: x.h === s.h })),
    newsletter: await env.DB.prepare(`SELECT email, lang, topics, freq, status, src, consent_v, created_at, confirmed_at, off_at, off_reason
      FROM subs WHERE email = ?1`).bind(u.email).first(),
    newsletter_issues: await all('SELECT slug, lang, status, at, sent_at FROM pg_queue WHERE email = ?1 ORDER BY id', u.email),
    consents: await all('SELECT kind, granted, text_v, src, at, ip FROM consents WHERE email = ?1 ORDER BY id', u.email),
    checkins: await all('SELECT id, st, s, r, c, n, cs, at, lang, ip FROM checkins WHERE uid = ?1 ORDER BY at', s.uid),
    photos: (await all('SELECT id, st, status, at, cap, w, h, mime, ip FROM photos WHERE uid = ?1 ORDER BY at', s.uid))
      .map(x => { if (x.status !== 'ok') delete x.id; return x; }),         // ids only of approved photos (as doprinosi)
  };
  return new Response(JSON.stringify(out, null, 1), { headers: { ...JSON_HEADERS, 'cache-control': 'no-store',
    'content-disposition': 'attachment; filename="blokvolt-nalog-' + today() + '.json"' } });
}

// deletes the account, its sessions, favourites, codes and newsletter sign-up. The consent history keeps only the
// SHA-256 of the address (proof of past consent without the address); reports and photos stay on the map without the link.
// The rows of the issues keep no address either, and an issue still waiting for this address is not sent.
async function nalogObrisi(request, env, b) {
  const s = await sessionOf(request, env);
  if (!s) return bad('auth', 401);
  if (b.confirm !== 'OBRISI') return bad('confirm');
  const u = await env.DB.prepare('SELECT email FROM users WHERE id = ?1').bind(s.uid).first();
  const q = [];
  if (u) {
    const sub = await env.DB.prepare('SELECT status, consent_v FROM subs WHERE email = ?1').bind(u.email).first();
    if (sub && sub.status !== 'off') {
      q.push(env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip) VALUES (?1, 'pregled', 0, ?2, 'brisanje-naloga', ?3, ?4)`)
        .bind(u.email, sub.consent_v || CONSENT_V, now(), await ipHash(request, env)));
    }
    q.push(env.DB.prepare('UPDATE consents SET email = ?1 WHERE email = ?2').bind('sha256:' + await sha256(u.email), u.email),
      env.DB.prepare('DELETE FROM subs WHERE email = ?1').bind(u.email),
      env.DB.prepare('DELETE FROM auth_codes WHERE email = ?1').bind(u.email),
      env.DB.prepare(`UPDATE pg_queue SET email = NULL, status = CASE WHEN status = 'queued' THEN 'cancelled' ELSE status END,
        note = CASE WHEN status = 'queued' THEN 'obrisan' ELSE note END WHERE email = ?1`).bind(u.email));
  }
  q.push(env.DB.prepare('DELETE FROM favs WHERE uid = ?1').bind(s.uid),
    env.DB.prepare('DELETE FROM sessions WHERE uid = ?1').bind(s.uid),
    env.DB.prepare('DELETE FROM users WHERE id = ?1').bind(s.uid));
  await env.DB.batch(q);
  for (const t of ['checkins', 'photos']) {
    try { await env.DB.prepare(`UPDATE ${t} SET uid = NULL WHERE uid = ?1`).bind(s.uid).run(); } catch (e) { /* no such table */ }
  }
  return jsonC({ ok: true }, sessionCookies(env, ''));
}

// the newsletter section of the account: the address is proved by the sign-in, so "on" needs no confirmation mail
async function nalogPregled(request, env, b) {
  const s = await sessionOf(request, env);
  const u = s && await env.DB.prepare('SELECT id, email, lang FROM users WHERE id = ?1').bind(s.uid).first();
  if (!u) return bad('auth', 401);
  if (typeof b.on !== 'boolean') return bad('on');
  const topics = topicsOf(b.topics);
  if (topics === null) return bad('topics');
  if (b.freq !== undefined && b.freq !== 'w' && b.freq !== 'm') return bad('freq');
  if (b.lang !== undefined && !LANGS.has(b.lang)) return bad('lang');
  const cur = await env.DB.prepare('SELECT status, token FROM subs WHERE email = ?1').bind(u.email).first();
  const t = now(), ip = await ipHash(request, env), q = [], was = cur ? cur.status : 'off';
  const consent = on => env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip) VALUES (?1, 'pregled', ?2, ?3, 'nalog', ?4, ?5)`)
    .bind(u.email, on ? 1 : 0, CONSENT_V, t, ip);
  const token = (cur && cur.token) || randHex(16);
  if (b.on) {
    q.push(env.DB.prepare(`INSERT INTO subs (email, uid, lang, topics, freq, status, token, src, consent_v, created_at, confirmed_at)
      VALUES (?1, ?2, COALESCE(?3, ?4), COALESCE(?5, ?6), COALESCE(?7, 'w'), 'on', ?8, 'nalog', ?9, ?10, ?10)
      ON CONFLICT (email) DO UPDATE SET uid = ?2, lang = COALESCE(?3, subs.lang), topics = COALESCE(?5, subs.topics), freq = COALESCE(?7, subs.freq),
        status = 'on', confirmed_at = CASE WHEN subs.status = 'on' THEN subs.confirmed_at ELSE ?10 END,
        src = CASE WHEN subs.status = 'on' THEN subs.src ELSE 'nalog' END,
        consent_v = CASE WHEN subs.status = 'on' THEN subs.consent_v ELSE ?9 END, off_at = NULL, off_reason = NULL`)
      .bind(u.email, u.id, b.lang || null, u.lang || 'sr', topics || null, DEFAULT_TOPICS, b.freq || null, token, CONSENT_V, t));
    if (was !== 'on') q.push(consent(true));
  } else if (cur) {
    q.push(env.DB.prepare(`UPDATE subs SET lang = COALESCE(?2, lang), topics = COALESCE(?3, topics), freq = COALESCE(?4, freq),
      status = 'off', off_at = CASE WHEN status = 'off' THEN off_at ELSE ?5 END, off_reason = CASE WHEN status = 'off' THEN off_reason ELSE 'nalog' END
      WHERE email = ?1`).bind(u.email, b.lang || null, topics || null, b.freq || null, t));
    if (was !== 'off') q.push(consent(false));
  }
  if (q.length) await env.DB.batch(q);
  if (b.on) await unsuppress(env, u.email, ['bounce', 'complaint']);   // an explicit act with a proved address
  const sub = await env.DB.prepare('SELECT status, topics, freq, lang FROM subs WHERE email = ?1').bind(u.email).first();
  if (b.on && was !== 'on' && mailOn(env)) await sendMail(env, mailWelcome(env, sub.lang, u.email, token));   // a failed welcome changes nothing
  return json({ ok: true, sub: sub ? subOut(sub) : null });
}

// ---------------------------------------------------------------- the newsletter without an account
// a sign-up waits for the click in the confirmation mail; one that is already on stays as it is (and nothing is sent)
async function subscribe(request, env, email, o) {
  const cur = await env.DB.prepare('SELECT status, token FROM subs WHERE email = ?1').bind(email).first();
  if (cur && cur.status === 'on') return true;
  const t = now(), token = (cur && cur.token) || randHex(16);
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO subs (email, uid, lang, topics, freq, status, token, src, consent_v, created_at)
      VALUES (?1, ?2, ?3, COALESCE(?4, ?5), 'w', 'pending', ?6, ?7, ?8, ?9)
      ON CONFLICT (email) DO UPDATE SET uid = COALESCE(subs.uid, ?2), lang = ?3, topics = COALESCE(?4, subs.topics), status = 'pending',
        src = ?7, consent_v = ?8, created_at = ?9, confirmed_at = NULL, off_at = NULL, off_reason = NULL`)
      .bind(email, o.uid || null, o.lang, o.topics || null, DEFAULT_TOPICS, token, o.src, CONSENT_V, t),
    env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip) VALUES (?1, 'pregled', 1, ?2, ?3, ?4, ?5)`)
      .bind(email, CONSENT_V, o.src, t, await ipHash(request, env)),
  ]);
  return sendMail(env, mailConfirm(env, o.lang, email, token, t));
}

// {email, lang, topics?, src, hp, t} — or {token, src} from the unsubscribe page ("Prijavite se ponovo"). The answer is
// the same, and comes as fast, for a new address, one that is on already or one that is suppressed: the sign-up and its
// mail are done after it. src is kept only when it is a page path.
async function postaPrijava(request, env, b, ctx) {
  if (b.hp) return json({ ok: true });
  if (typeof b.t === 'number' && b.t < 1500) return bad('too fast', 429);
  let email = normEmail(b.email), lang = langOf(b.lang);
  if (!email && TOK32.test(String(b.token || ''))) {
    await ensureSchema(env);
    const row = await env.DB.prepare('SELECT email, lang FROM subs WHERE token = ?1').bind(b.token).first();
    if (row) { email = row.email; lang = LANGS.has(b.lang) ? b.lang : langOf(row.lang); }
  }
  if (!email) return bad('email');
  const topics = topicsOf(b.topics);
  if (!mailOn(env)) return bad('mail_off', 503);
  await ensureSchema(env);
  const ip = await ipHash(request, env);
  if (!(await allow(env, 'pp:' + ip, LIMIT.subIp)) || !(await allow(env, 'pe:' + await mailKey(email), LIMIT.subMail))) return bad('limit', 429);
  background(ctx, subscribe(request, env, email, { lang, uid: null, src: pagePath(b.src), topics: topics || null })
    .then(sent => { if (!sent) console.log('mail not sent: confirm'); }));
  return json({ ok: true });
}

// the button "Potvrđujem prijavu" on /pregled/potvrda/ (the page itself only shows the state, so a scanner that opens
// the link confirms nothing)
async function postaPotvrdi(request, env, b) {
  const token = String(b.token || '');
  if (!TOK32.test(token)) return bad('token');
  await ensureSchema(env);
  const row = await env.DB.prepare('SELECT email, status, lang, consent_v FROM subs WHERE token = ?1').bind(token).first();
  if (!row || row.status === 'off') return bad('token');                // unknown, expired, or unsubscribed since
  if (row.status === 'pending') {
    const t = now();
    const up = await env.DB.prepare(`UPDATE subs SET status = 'on', confirmed_at = ?1 WHERE token = ?2 AND status = 'pending'`).bind(t, token).run();
    if (up.meta && up.meta.changes) {
      await env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip) VALUES (?1, 'pregled', 1, ?2, 'confirm-click', ?3, ?4)`)
        .bind(row.email, row.consent_v || CONSENT_V, t, await ipHash(request, env)).run();
      await unsuppress(env, row.email, ['bounce', 'complaint']);       // a new, explicit consent from a working mailbox
      if (mailOn(env)) await sendMail(env, mailWelcome(env, langOf(row.lang), row.email, token));
    }
  }
  return json({ ok: true, status: 'on', email_masked: maskEmail(row.email), lang: row.lang });
}

async function postaStanje(request, env, url) {
  const token = url.searchParams.get('t') || '';
  if (!TOK32.test(token)) return bad('token', 404);
  await ensureSchema(env);
  const row = await env.DB.prepare('SELECT email, status, topics, freq, lang FROM subs WHERE token = ?1').bind(token).first();
  if (!row) return bad('token', 404);
  return json({ ok: true, ...subOut(row), email_masked: maskEmail(row.email) });
}

// topics, frequency and language, by the token from the mail or by the session
async function postaPodesavanja(request, env, b) {
  await ensureSchema(env);
  let row = null;
  if (b.token !== undefined) {
    if (!TOK32.test(String(b.token))) return bad('token', 404);
    row = await env.DB.prepare('SELECT email FROM subs WHERE token = ?1').bind(b.token).first();
  } else {
    const s = await sessionOf(request, env);
    const u = s && await env.DB.prepare('SELECT email FROM users WHERE id = ?1').bind(s.uid).first();
    if (!u) return bad('auth', 401);
    row = await env.DB.prepare('SELECT email FROM subs WHERE email = ?1').bind(u.email).first();
  }
  if (!row) return bad('token', 404);
  const topics = topicsOf(b.topics);
  if (topics === null) return bad('topics');
  if (b.freq !== undefined && b.freq !== 'w' && b.freq !== 'm') return bad('freq');
  if (b.lang !== undefined && !LANGS.has(b.lang)) return bad('lang');
  await env.DB.prepare('UPDATE subs SET topics = COALESCE(?2, topics), freq = COALESCE(?3, freq), lang = COALESCE(?4, lang) WHERE email = ?1')
    .bind(row.email, topics || null, b.freq || null, b.lang || null).run();
  const out = await env.DB.prepare('SELECT email, status, topics, freq, lang FROM subs WHERE email = ?1').bind(row.email).first();
  return json({ ok: true, ...subOut(out), email_masked: maskEmail(out.email) });
}

// RFC 8058 one-click (POST ?t=…, empty body or List-Unsubscribe=One-Click; no origin check: mail providers call it) and
// the button on /pregled/odjava/ (JSON {token}). Idempotent: 200 for every valid token.
async function postaOdjava(request, env, url) {
  let token = url.searchParams.get('t') || '', src = 'one-click';
  if (/^application\/json\b/i.test(request.headers.get('content-type') || '')) {
    const b = await readBody(request);
    if (b && b.token) { token = String(b.token); src = 'odjava'; }
  }
  if (!TOK32.test(token)) return bad('token', 404);
  await ensureSchema(env);
  const row = await env.DB.prepare('SELECT email, status, lang, consent_v FROM subs WHERE token = ?1').bind(token).first();
  if (!row) return bad('token', 404);
  const t = now();
  const up = await env.DB.prepare(`UPDATE subs SET status = 'off', off_at = ?1, off_reason = 'link' WHERE token = ?2 AND status != 'off'`).bind(t, token).run();
  if (up.meta && up.meta.changes) {
    await env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip) VALUES (?1, 'pregled', 0, ?2, ?3, ?4, ?5)`)
      .bind(row.email, row.consent_v || CONSENT_V, src, t, await ipHash(request, env)).run();
  }
  return json({ ok: true, status: 'off', email_masked: maskEmail(row.email), lang: row.lang });
}

// ---------------------------------------------------------------- Resend's webhook: bounces and spam complaints
// Resend → Webhooks → endpoint https://www.blokvolt.rs/api/posta/resend, events email.bounced and email.complained; its
// signing secret ("whsec_…") is the Pages secret RESEND_WEBHOOK_SECRET. Svix signs "<svix-id>.<svix-timestamp>.<body>"
// with HMAC-SHA256 (key: the base64 after "whsec_"); svix-signature holds one or more "v1,<base64>". A timestamp more
// than 5 minutes from our clock is refused (replays). A hard bounce (bounce.type "Permanent", or no type) and a
// complaint switch the newsletter of the address off and put the address on the suppression list; everything else is
// acknowledged and ignored. Handling an event twice changes nothing. One Resend team sends for BlokVolt and Evolako, and
// every endpoint of the team receives the events of both: only mail sent from our own domain (MAIL_FROM) counts here,
// so the other brand's recipients are neither suppressed nor stored.
const b64bytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
// "BlokVolt <obavestenja@mail.blokvolt.com>" or a bare address → "mail.blokvolt.com"; anything else → ""
const senderDomain = s => {
  const v = String(s || '').trim(), a = (v.match(/<\s*([^<>\s]+)\s*>$/) || [])[1] || v;
  return /^[^@\s]+@[A-Za-z0-9.-]+$/.test(a) ? a.split('@')[1].toLowerCase() : '';
};
const bytesB64 = a => btoa(String.fromCharCode(...new Uint8Array(a)));
async function svixOk(request, body, secret) {
  const id = request.headers.get('svix-id') || '', ts = request.headers.get('svix-timestamp') || '';
  const sigs = (request.headers.get('svix-signature') || '').split(' ').filter(Boolean);
  if (!id || id.length > 200 || !/^\d{1,12}$/.test(ts) || !sigs.length) return false;
  if (Math.abs(now() - Number(ts)) > WEBHOOK_SKEW_S) return false;
  const key = await crypto.subtle.importKey('raw', b64bytes(secret.slice(6)), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const want = bytesB64(await crypto.subtle.sign('HMAC', key, enc.encode(id + '.' + ts + '.' + body)));
  let ok = false;
  for (const x of sigs.slice(0, 10)) {                                  // every entry is compared, in constant time
    const i = x.indexOf(',');
    if (i > 0 && x.slice(0, i) === 'v1' && same(x.slice(i + 1), want)) ok = true;
  }
  return ok;
}
// the newsletter of this address goes off (with a closing consent row) and the address is not mailed again
async function suppress(env, email, reason) {
  const t = now();
  const sub = await env.DB.prepare('SELECT status, consent_v FROM subs WHERE email = ?1').bind(email).first();
  const q = [env.DB.prepare(`INSERT INTO suppressions (email_hash, reason, at) VALUES (?1, ?2, ?3)
    ON CONFLICT (email_hash) DO UPDATE SET reason = ?2, at = ?3`).bind(await sha256(email), reason, t)];
  if (sub && sub.status !== 'off') {
    q.push(env.DB.prepare(`UPDATE subs SET status = 'off', off_at = ?2, off_reason = ?3 WHERE email = ?1 AND status != 'off'`).bind(email, t, reason),
      env.DB.prepare(`INSERT INTO consents (email, kind, granted, text_v, src, at, ip) VALUES (?1, 'pregled', 0, ?2, ?3, ?4, NULL)`)
        .bind(email, sub.consent_v || CONSENT_V, reason, t));
  }
  await env.DB.batch(q);
}
async function postaResend(request, env) {
  const secret = String(env.RESEND_WEBHOOK_SECRET || '');
  if (!/^whsec_[A-Za-z0-9+/]+={0,2}$/.test(secret)) return bad('webhook_off', 503);
  if (Number(request.headers.get('content-length') || 0) > 262144) return bad('size', 413);
  const body = await request.text();
  if (body.length > 262144) return bad('size', 413);
  let valid = false;
  try { valid = await svixOk(request, body, secret); } catch (e) { valid = false; }
  if (!valid) return bad('signature', 401);
  let ev;
  try { ev = JSON.parse(body); } catch (e) { return bad('json'); }
  const d = (ev && ev.data) || {}, bt = d.bounce && d.bounce.type;
  const ours = senderDomain(env.MAIL_FROM || MAIL_FROM);
  if (!ours || senderDomain(d.from) !== ours) return json({ ok: true, ignored: true, other_sender: true });
  const reason = ev && ev.type === 'email.complained' ? 'complaint'
    : ev && ev.type === 'email.bounced' && (!bt || /^permanent$/i.test(String(bt))) ? 'bounce' : null;
  if (!reason) return json({ ok: true, ignored: true });                  // soft bounces and all other events
  await ensureSchema(env);
  const to = [...new Set((Array.isArray(d.to) ? d.to : [d.to]).map(normEmail).filter(Boolean))].slice(0, 50);
  for (const email of to) await suppress(env, email, reason);
  return json({ ok: true, suppressed: to.length });
}

// counts for the owner; the cleanup runs first, so expired sign-ups are not counted. pregled: the issues — rows by status,
// clicks per link, previews, today's sends against the cap.
async function adminPosta(request, env) {
  await ensureSchema(env);
  await housekeeping(env);
  const n = async sql => ((await env.DB.prepare(sql).first()) || {}).n || 0;
  const by = await env.DB.prepare(`SELECT lang, COUNT(*) AS n FROM subs WHERE status = 'on' GROUP BY lang`).all();
  return json({ ok: true, users: await n('SELECT COUNT(*) AS n FROM users'), subs_on: await n(`SELECT COUNT(*) AS n FROM subs WHERE status = 'on'`),
    subs_pending: await n(`SELECT COUNT(*) AS n FROM subs WHERE status = 'pending'`), subs_off: await n(`SELECT COUNT(*) AS n FROM subs WHERE status = 'off'`),
    suppressed: await n('SELECT COUNT(*) AS n FROM suppressions'),
    by_lang: Object.fromEntries(by.results.map(r => [r.lang || '?', r.n])), pregled: await pgStats(request, env) });
}

// ================================================================ sending the issues (docs/RUNBOOK.md 3.27, "Sending the issues")
// build.py writes every issue of content/pregled/ as /pregled-mail/<slug>.json — the e-mail in sr, en and ru: a head, the
// sections by topic (uvod goes to everyone), a foot with {{PREFS}} and {{UNSUB}} for the reader's own links; every other
// link goes through the click counter GET /api/posta/klik — and lists them in /pregled-mail/index.json. The worker reads
// both through env.ASSETS. POST /api/posta/tick (a GitHub Actions schedule, .github/workflows/pregled-tick.yml; normal
// /api requests also start one in the background, at most every 10 minutes) does the work, one tick at a time (the
// one-row table pg_lock: a tick starts only when none runs and the last one started a minute ago), for every issue:
//   preview  — once per content hash: the issue in sr, en and ru to the team address (MAIL_REPLY_TO) and nowhere else,
//              subject "[PREVIEW <first 8 of the hash>] …", without List-Unsubscribe; recorded in pg_previews;
//   approved — when approved_hash is a previewed hash and still the file's hash, and send_at has passed: one row per reader
//              in pg_queue (newsletter on; a topic of the issue among the reader's topics; a monthly reader only while no
//              other issue of that calendar month is queued or sent to them), once per issue (pg_issues). A hash that does
//              not match sends nothing and the team one notice a day per issue and reason;
//   stopped  — its rows still queued are cancelled.
// Then the queued rows, oldest first, within the budget: PREGLED_DAILY_CAP newsletter mails per UTC day (default 30; 0
// pauses the sending), 25 a tick (10 in the background), paced for Resend's 2 requests a second, and within 45 D1 calls and
// fetches (the free plan allows 50 per request; 30 in the background, next to the request's own). Every mail is made at
// the moment it is sent, for the reader's current language and topics; a reader who unsubscribed meanwhile, whose topics
// no longer match or whose address was suppressed is skipped (cancelled). List-Unsubscribe as in the welcome mail, and an
// Idempotency-Key per issue and address, so a tick that died after sending never sends twice (Resend keeps keys a day).
// A 429, a 5xx or a timeout ends the tick and the row waits (failed after 5 attempts); 401 or 403 (the key or the domain)
// ends it without counting an attempt and tells the team. The answer has counts only, never an address.
const PG_GAP_S = 60, PG_AUTO_GAP_S = 600;          // POST /api/posta/tick: one a minute; the background tick: one every 10 minutes
const PG_MAX = 25, PG_AUTO_MAX = 10;                // newsletter mails a tick
const PG_SUB = 45, PG_AUTO_SUB = 30;                // D1 calls and fetches a tick may use
const PG_CAP = 30;                                  // newsletter mails a UTC day, unless PREGLED_DAILY_CAP says otherwise
const PG_TRIES = 5;                                 // attempts before a row is 'failed'
const PG_PACE_MS = 550;                             // Resend: 2 requests a second for the whole team (Evolako sends too)
const PG_HOLD_S = 600;                              // a tick that died holds the lock at most this long
const PG_KEEP_S = 60 * DAY_S;                       // the address of a finished row is removed after 60 days (housekeeping)
const PG_SLUG = /^[a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?$/;
const PG_LINK = /^https:\/\/(www\.blokvolt\.rs|blokvolt\.com)\/[^\s"<>\\]*$/;   // the same rule as scripts/pregled.py
const PG_TOPICS = ['vesti', 'cene', 'punjaci'];     // the topics an issue has sections for; 'moji' comes later
const PG_HASH = /^[0-9a-f]{64}$/;
const pgCap = env => {
  const v = String(env.PREGLED_DAILY_CAP == null ? '' : env.PREGLED_DAILY_CAP).trim();
  return /^\d{1,6}$/.test(v) ? Number(v) : PG_CAP;
};
const sleep = ms => new Promise(ok => setTimeout(ok, ms));

// a JSON file of the site, read through env.ASSETS; null when it is missing or broken
async function assetJson(env, base, path) {
  try {
    const r = await env.ASSETS.fetch(new Request(new URL(path, base)));
    return r.ok ? await r.json() : null;
  } catch (e) { return null; }
}

// the background tick: normal /api requests start one after their answer, at most every 10 minutes. The time of this
// isolate's last start is checked first, so a normal request costs nothing more; the D1 lock keeps it to one every 10
// minutes across isolates.
let PG_AUTO_AT = 0;
function pgAuto(request, env, ctx, path) {
  if (!CFG.pregled || !env.DB || !mailOn(env) || !ctx || !ctx.waitUntil || path.startsWith('/api/posta/tick')) return;
  const t = Date.now();
  if (t - PG_AUTO_AT < PG_AUTO_GAP_S * 1000) return;
  PG_AUTO_AT = t;
  ctx.waitUntil(pgTick(env, request.url, { gap: PG_AUTO_GAP_S, max: PG_AUTO_MAX, sub: PG_AUTO_SUB, ms: 20000 })
    .then(r => { if (!r.skipped) console.log('pregled tick (background): ' + JSON.stringify(r)); })
    .catch(e => console.log('pregled tick (background): ' + (e && e.message))));
}

// POST /api/posta/tick — public, no origin check (GitHub Actions calls it), idempotent: a second call within a minute
// answers {skipped: "busy"}.
async function postaTick(request, env) {
  if (!CFG.pregled) return json({ ok: true, skipped: 'off' });
  if (!mailOn(env)) return bad('mail_off', 503);
  const r = await pgTick(env, request.url, { gap: PG_GAP_S, max: PG_MAX, sub: PG_SUB, ms: 60000 });
  if (!r.skipped) console.log('pregled tick: ' + JSON.stringify(r));
  return json(r, r.ok ? 200 : 503);
}

async function pgTick(env, base, o) {
  const fresh = !SCHEMA_OK;
  await ensureSchema(env);
  const t = now();
  const lock = await env.DB.prepare(`INSERT INTO pg_lock (id, at, until) VALUES (1, ?1, ?2)
    ON CONFLICT (id) DO UPDATE SET at = ?1, until = ?2 WHERE pg_lock.at <= ?3 AND pg_lock.until <= ?1 RETURNING at`)
    .bind(t, t + PG_HOLD_S, t - o.gap).first();
  if (!lock) return { ok: true, skipped: 'busy' };
  const w = { env, base, o, t, sub: (fresh ? 7 : 0) + 2, files: new Map(), calls: 0, end: Date.now() + o.ms };
  try {
    return await pgWork(w);
  } finally {
    // released; the next tick may start `gap` seconds after this one started
    await env.DB.prepare('UPDATE pg_lock SET until = 0 WHERE id = 1 AND at = ?1').bind(t).run().catch(() => {});
  }
}

async function pgWork(w) {
  const { env, t } = w;
  const idx = await assetJson(env, w.base, '/pregled-mail/index.json');
  w.sub++;
  if (!idx || !Array.isArray(idx.issues)) return { ok: false, error: 'no_index' };
  const [pv, st, qd, sd] = (await env.DB.batch([
    env.DB.prepare('SELECT slug, hash FROM pg_previews'),
    env.DB.prepare('SELECT slug, enqueued_at, stopped_at FROM pg_issues'),
    env.DB.prepare(`SELECT slug, COUNT(*) AS n FROM pg_queue WHERE status = 'queued' GROUP BY slug`),
    env.DB.prepare(`SELECT COUNT(*) AS n FROM pg_queue WHERE status = 'sent' AND sent_at >= ?1`).bind(Math.floor(t / DAY_S) * DAY_S),
  ])).map(r => r.results);
  w.sub++;
  const previewed = new Set(pv.map(r => r.slug + ' ' + r.hash)), state = new Map(st.map(r => [r.slug, r]));
  const queued = new Map(qd.map(r => [r.slug, r.n]));
  const out = { ok: true, issues: [], sent: 0, sent_today: (sd[0] || {}).n || 0, cap: pgCap(env) }, ready = [];
  for (const it of idx.issues) {
    if (!it || typeof it !== 'object' || !PG_SLUG.test(String(it.slug)) || !PG_HASH.test(String(it.hash))) continue;
    const s = state.get(it.slug) || {}, r = { slug: it.slug, action: 'none', queued: queued.get(it.slug) || 0 };
    out.issues.push(r);
    if (it.status === 'preview') {
      r.action = previewed.has(it.slug + ' ' + it.hash) ? 'previewed' : await pgPreview(w, it);
    } else if (it.status === 'stopped') {
      r.action = 'stopped';
      if (r.queued) {
        r.cancelled = (await env.DB.prepare(`UPDATE pg_queue SET status = 'cancelled', note = 'stopped' WHERE slug = ?1 AND status = 'queued'`).bind(it.slug).run()).meta.changes;
        w.sub++;
        r.queued = 0;
      }
    } else if (it.status === 'approved') {
      if (s.stopped_at) { r.action = 'stopped'; continue; }                 // POST /api/admin/posta {stop}
      if (s.enqueued_at && !r.queued) { r.action = 'done'; continue; }
      const ah = String(it.approved_hash || '');
      const why = !previewed.has(it.slug + ' ' + ah) ? 'not_previewed' : ah !== it.hash ? 'hash_changed' : '';
      if (why) {
        r.action = 'blocked';
        r.reason = why;
        const pvs = pv.filter(x => x.slug === it.slug).map(x => x.hash.slice(0, 8));
        await pgNotice(w, it.slug, why, why === 'hash_changed'
          ? `Выпуск ${it.slug} не отправлен: текст изменился после одобрения (approved_hash ${ah.slice(0, 8) || '—'}, сейчас ${it.hash.slice(0, 8)}). ` +
            'Нужны новое превью и одобрение: status: preview и деплой, потом approved_hash нового превью и status: approved.'
          : `Выпуск ${it.slug} не отправлен: хэш одобрения не совпадает с превью (approved_hash ${ah.slice(0, 8)}; превью этого выпуска: ` +
            (pvs.length ? pvs.join(', ') : 'не было') + '). Одобрить можно только хэш из темы превью: [PREVIEW …].');
        continue;
      }
      if (!s.enqueued_at) {
        if (!(Date.parse(it.send_at) <= t * 1000)) { r.action = 'waiting'; r.send_at = it.send_at; continue; }
        r.queued = await pgEnqueue(w, it);
        r.action = 'enqueued';
      } else r.action = 'sending';
      if (r.queued) ready.push(it);
    }
  }
  if (ready.length) await pgSend(w, ready, out);
  return out;
}

// the issue's file, checked against the index (same hash, three languages); read once a tick
async function pgIssue(w, it) {
  if (!w.files.has(it.slug)) {
    const f = await assetJson(w.env, w.base, '/pregled-mail/' + it.slug + '.json');
    w.sub++;
    const ok = f && f.hash === it.hash && f.langs && [...LANGS].every(l => f.langs[l] && Array.isArray(f.langs[l].sections));
    w.files.set(it.slug, ok ? f : null);
  }
  return w.files.get(it.slug);
}

// one issue in one language for one reader: the head, the intro, the sections of the reader's topics (every section for a
// preview: topics null) and the foot, with the reader's own links in place of {{PREFS}} and {{UNSUB}} (the same pages
// the welcome mail links to; a preview gets /pregled/). n: how many sections of the reader's topics are in it.
function pgMail(env, issue, lang, topics, token) {
  const L = issue.langs[lang] || issue.langs.sr, S = siteOf(env) + lpre(lang);
  const prefs = token ? S + '/pregled/odjava/?t=' + token + '&teme=1' : S + '/pregled/';
  const out = token ? S + '/pregled/odjava/?t=' + token : S + '/pregled/';
  const secs = L.sections.filter(s => s.topic === 'uvod' || !topics || topics.includes(s.topic));
  const put = (s, e) => s.split('{{PREFS}}').join(e(prefs)).split('{{UNSUB}}').join(e(out));
  return { subject: L.subject, html: put(L.head_html + secs.map(s => s.html).join('') + L.foot_html, esc),
    text: put(L.head_text + secs.map(s => s.text).join('') + L.foot_text, x => x), n: secs.filter(s => s.topic !== 'uvod').length };
}

// the three previews of a new hash; recorded only when all three went out (the next tick tries again, and the
// Idempotency-Key keeps the ones already sent from going twice)
async function pgPreview(w, it) {
  const to = normEmail(replyTo(w.env));
  if (!to) return 'no_team_address';
  if (w.sub + 8 > w.o.sub) return 'later';                              // the budget of this tick: the next one sends it
  const issue = await pgIssue(w, it);
  if (!issue) return 'no_file';
  for (const lang of LANGS) {
    if (w.calls++ && !devMode(w.env)) await sleep(PG_PACE_MS);
    const m = pgMail(w.env, issue, lang, null, null);
    const r = await deliver(w.env, { to, subject: '[PREVIEW ' + it.hash.slice(0, 8) + '] ' + m.subject, html: m.html, text: m.text, kind: 'preview',
      idem: 'pregled-preview-' + it.slug + '-' + it.hash.slice(0, 16) + '-' + lang, tags: [{ name: 'kind', value: 'preview' }, { name: 'issue', value: it.slug }] }, true);
    w.sub++;
    if (!r.ok) return 'preview_failed';
  }
  await w.env.DB.prepare('INSERT OR IGNORE INTO pg_previews (slug, hash, at) VALUES (?1, ?2, ?3)').bind(it.slug, it.hash, now()).run();
  w.sub++;
  return 'preview_sent';
}

// one row per reader, once per issue; the number of rows
async function pgEnqueue(w, it) {
  const { env } = w, t = now();
  const topics = (Array.isArray(it.topics) ? it.topics : []).filter(x => PG_TOPICS.includes(x));
  const month = /^\d{4}-\d{2}$/.test(String(it.month)) ? it.month : String(it.date || '').slice(0, 7);
  const q = [];
  if (topics.length) {
    // the reader's topics ("vesti,cene") contain one of the issue's; a monthly reader has no other issue of this month
    const like = topics.map((_, i) => `(',' || COALESCE(s.topics, ?4) || ',') LIKE ?${i + 5}`).join(' OR ');
    q.push(env.DB.prepare(`INSERT OR IGNORE INTO pg_queue (slug, email, lang, topics, month, status, attempts, at)
      SELECT ?1, s.email, s.lang, s.topics, ?2, 'queued', 0, ?3 FROM subs s
      WHERE s.status = 'on' AND (${like}) AND (COALESCE(s.freq, 'w') != 'm' OR NOT EXISTS (SELECT 1 FROM pg_queue x
        WHERE x.email = s.email AND x.month = ?2 AND x.slug != ?1 AND x.status IN ('queued', 'sent')))`)
      .bind(it.slug, month, t, DEFAULT_TOPICS, ...topics.map(x => '%,' + x + ',%')));
  }
  q.push(env.DB.prepare(`INSERT INTO pg_issues (slug, hash, enqueued_at, queued) VALUES (?1, ?2, ?3, (SELECT COUNT(*) FROM pg_queue WHERE slug = ?1))
    ON CONFLICT (slug) DO UPDATE SET hash = ?2, enqueued_at = ?3, queued = excluded.queued`).bind(it.slug, it.hash, t));
  const r = await env.DB.batch(q);
  w.sub++;
  return topics.length ? r[0].meta.changes : 0;
}

// the queued rows of the issues that may be sent, oldest first, within the budget
async function pgSend(w, ready, out) {
  const { env } = w, by = new Map(out.issues.map(r => [r.slug, r]));
  const left = Math.min(w.o.max, out.cap - out.sent_today);
  if (left <= 0) { out.stop = 'cap'; return; }
  const slugs = ready.map(i => i.slug);
  const rows = (await env.DB.prepare(`SELECT q.id, q.slug, q.email, q.lang AS qlang, q.attempts, s.status AS sst, s.token, s.lang AS slang, s.topics AS stopics
    FROM pg_queue q LEFT JOIN subs s ON s.email = q.email WHERE q.status = 'queued' AND q.slug IN (${slugs.map((_, i) => '?' + (i + 2)).join(', ')})
    ORDER BY q.id LIMIT ?1`).bind(Math.min(50, left + 20), ...slugs).all()).results;
  w.sub++;
  // the suppression list for the whole batch at once (SHA-256 of the address, as suppressed() looks it up)
  const hs = await Promise.all(rows.map(r => (r.email ? sha256(r.email) : '')));
  const sup = new Set(hs.length ? (await env.DB.prepare(`SELECT email_hash FROM suppressions WHERE email_hash IN (${hs.map((_, i) => '?' + (i + 1)).join(', ')})`)
    .bind(...hs).all()).results.map(r => r.email_hash) : []);
  w.sub++;
  const upd = [], set = (sql, ...v) => upd.push(env.DB.prepare(sql).bind(...v));
  const count = (row, k) => { const r = by.get(row.slug); r[k] = (r[k] || 0) + 1; r.queued--; };   // a row that leaves the queue
  const cancel = (row, why) => { set(`UPDATE pg_queue SET status = 'cancelled', note = ?2 WHERE id = ?1`, row.id, why); count(row, 'cancelled'); };
  try {
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      if (out.sent >= left) break;
      if (w.sub + 3 > w.o.sub) { out.stop = 'budget'; break; }
      if (Date.now() > w.end) { out.stop = 'time'; break; }
      if (!row.email || row.sst !== 'on' || !row.token) { cancel(row, 'off'); continue; }   // unsubscribed (or deleted) since the enqueue
      if (sup.has(hs[i])) { cancel(row, 'suppressed'); continue; }
      const issue = await pgIssue(w, ready.find(x => x.slug === row.slug));
      if (!issue) { out.stop = 'no_file'; break; }
      const lang = langOf(row.slang || row.qlang);
      const m = pgMail(env, issue, lang, (row.stopics || DEFAULT_TOPICS).split(','), row.token);
      if (!m.n) { cancel(row, 'topics'); continue; }                         // the reader's topics changed since the enqueue
      if (w.calls++ && !devMode(env)) await sleep(PG_PACE_MS);
      const r = await deliver(env, { to: row.email, subject: m.subject, html: m.html, text: m.text, kind: 'pregled',
        unsub: siteOf(env) + '/api/posta/odjava?t=' + row.token, idem: 'pregled-' + row.slug + '-' + hs[i].slice(0, 16),
        tags: [{ name: 'kind', value: 'pregled' }, { name: 'issue', value: row.slug }] }, true);
      w.sub++;
      if (r.ok || r.status === 409) {                                         // 409: this Idempotency-Key was sent already
        set(`UPDATE pg_queue SET status = 'sent', attempts = attempts + 1, sent_at = ?2, provider_id = ?3, lang = ?4, note = ?5 WHERE id = ?1`,
          row.id, now(), r.id || null, lang, r.ok ? null : 'resend 409');
        out.sent++;
        count(row, 'sent');
      } else if (r.status === 401 || r.status === 403) {                      // the key or the domain: not this reader's fault
        out.stop = 'resend_' + r.status;
        await pgNotice(w, row.slug, 'resend_' + r.status, `Рассылка выпуска ${row.slug} остановлена: Resend отвечает ${r.status}. ` +
          'Проверьте ключ RESEND_API_KEY в Cloudflare Pages и домен mail.blokvolt.com в Resend. Письма ждут в очереди.');
        break;
      } else if (!r.status || r.status === 429 || r.status >= 500) {           // Resend is busy or down: this row waits
        set(`UPDATE pg_queue SET attempts = attempts + 1, status = CASE WHEN attempts + 1 >= ?2 THEN 'failed' ELSE 'queued' END, note = ?3 WHERE id = ?1`,
          row.id, PG_TRIES, 'resend ' + (r.status || 'timeout'));
        if (row.attempts + 1 >= PG_TRIES) count(row, 'failed');
        out.stop = 'resend_' + (r.status || 'timeout');
        break;
      } else {                                                                // refused (e.g. 422 for this address)
        set(`UPDATE pg_queue SET status = 'failed', attempts = attempts + 1, note = ?2 WHERE id = ?1`, row.id, 'resend ' + r.status);
        count(row, 'failed');
      }
    }
  } finally {
    if (upd.length) { await env.DB.batch(upd); w.sub++; }
  }
  out.sent_today += out.sent;
}

// one notice a day per issue and reason to the team address (in Russian: the team reads it)
async function pgNotice(w, slug, reason, text) {
  const to = normEmail(replyTo(w.env));
  w.sub++;
  if (!to || !(await allow(w.env, 'pgn:' + slug + ':' + reason, 1))) return false;
  if (w.calls++ && !devMode(w.env)) await sleep(PG_PACE_MS);
  const r = await deliver(w.env, { to, subject: 'BlokVolt: Nedeljni pregled ' + slug + ' — не отправлен', html: '<p>' + esc(text) + '</p>',
    text: text + '\n', kind: 'notice', idem: 'pregled-notice-' + slug + '-' + reason + '-' + today() }, true);
  w.sub++;
  return r.ok;
}

// GET /api/posta/klik?i=<slug>&l=<n> — the links in the issues: 302 to link n of the issue's table when it is one of our
// sites, else to /pregled/. Counts clicks per issue, link and day, nothing about the reader (no IP, no cookie).
const PG_LINKS = new Map();                          // slug → {links, at}: cached per isolate for 5 minutes
async function postaKlik(request, env, ctx, url) {
  const slug = url.searchParams.get('i') || '', l = url.searchParams.get('l') || '';
  let to = '';
  if (PG_SLUG.test(slug) && /^[1-9]\d{0,3}$/.test(l)) {
    let c = PG_LINKS.get(slug);
    if (!c || Date.now() - c.at > 300000) {
      const f = await assetJson(env, request.url, '/pregled-mail/' + slug + '.json');
      if (PG_LINKS.size > 50) PG_LINKS.clear();
      PG_LINKS.set(slug, c = { links: f && f.links && typeof f.links === 'object' ? f.links : {}, at: Date.now() });
    }
    const u = c.links[l];
    if (typeof u === 'string' && PG_LINK.test(u)) to = u;
  }
  if (to && request.method === 'GET') {
    ctx.waitUntil(ensureSchema(env).then(() => env.DB.prepare(`INSERT INTO pg_clicks (slug, l, day, n) VALUES (?1, ?2, ?3, 1)
      ON CONFLICT (slug, l, day) DO UPDATE SET n = n + 1`).bind(slug, Number(l), today()).run()).catch(e => console.log('klik: ' + (e && e.message))));
  }
  return new Response(null, { status: 302, headers: { location: to || siteOf(env) + '/pregled/', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' } });
}

// for GET /api/admin/posta: the issues of the index (newest 20) with their rows by status, previews, clicks per link
async function pgStats(request, env) {
  const idx = await assetJson(env, request.url, '/pregled-mail/index.json');
  const [rows, clicks, pv, st, sd] = (await env.DB.batch([
    env.DB.prepare('SELECT slug, status, COUNT(*) AS n FROM pg_queue GROUP BY slug, status'),
    env.DB.prepare('SELECT slug, l, SUM(n) AS n FROM pg_clicks GROUP BY slug, l ORDER BY slug, l'),
    env.DB.prepare('SELECT slug, hash, at FROM pg_previews ORDER BY at'),
    env.DB.prepare('SELECT slug, hash, enqueued_at, queued, stopped_at FROM pg_issues'),
    env.DB.prepare(`SELECT COUNT(*) AS n FROM pg_queue WHERE status = 'sent' AND sent_at >= ?1`).bind(Math.floor(now() / DAY_S) * DAY_S),
  ])).map(r => r.results);
  const list = ((idx && Array.isArray(idx.issues)) ? idx.issues : []).filter(it => it && PG_SLUG.test(String(it.slug))).slice(-20).reverse();
  const issues = [];
  for (const it of list) {
    const s = st.find(x => x.slug === it.slug) || {}, cl = clicks.filter(x => x.slug === it.slug);
    let links = {};
    if (cl.length) {
      const f = await assetJson(env, request.url, '/pregled-mail/' + it.slug + '.json');
      links = (f && f.links) || {};
    }
    const n = Object.fromEntries(['queued', 'sent', 'failed', 'cancelled'].map(k => [k, (rows.find(x => x.slug === it.slug && x.status === k) || {}).n || 0]));
    issues.push({ slug: it.slug, title: it.title, date: it.date, status: it.status, send_at: it.send_at, hash: String(it.hash || '').slice(0, 8),
      approved_hash: String(it.approved_hash || '').slice(0, 8), previews: pv.filter(x => x.slug === it.slug).map(x => ({ hash: x.hash.slice(0, 8), at: x.at })),
      enqueued_at: s.enqueued_at || null, stopped_at: s.stopped_at || null, rows: n,
      clicks: cl.map(x => ({ l: x.l, n: x.n, url: links[String(x.l)] || null })) });
  }
  return { on: CFG.pregled, cap: pgCap(env), sent_today: (sd[0] || {}).n || 0, issues };
}

// POST /api/admin/posta {"stop": "<slug>"} (owner's key): the issue's rows still queued are cancelled at once, and the tick
// never queues or sends that issue again. The lasting way is status: stopped in its Markdown and a deploy.
async function adminPostaStop(request, env) {
  if (!/^application\/json\b/i.test(request.headers.get('content-type') || '')) return bad('type', 415);
  const b = await readBody(request);
  const slug = b && String(b.stop || '');
  if (!slug || !PG_SLUG.test(slug)) return bad('stop');
  await ensureSchema(env);
  const t = now();
  const r = await env.DB.batch([
    env.DB.prepare(`UPDATE pg_queue SET status = 'cancelled', note = 'admin' WHERE slug = ?1 AND status = 'queued'`).bind(slug),
    env.DB.prepare(`INSERT INTO pg_issues (slug, stopped_at) VALUES (?1, ?2) ON CONFLICT (slug) DO UPDATE SET stopped_at = ?2`).bind(slug, t),
  ]);
  return json({ ok: true, slug, cancelled: r[0].meta.changes, stopped_at: t });
}

// path → [method, handler]; a known path with another method answers 405. POST handlers get the parsed JSON body.
const ACCOUNT_ROUTES = {
  '/api/nalog/status': ['GET', (rq, env) => json({ ok: true, mail: mailOn(env) }, 200, { 'cache-control': 'public, max-age=60' })],
  '/api/nalog/kod': ['POST', nalogKod],
  '/api/nalog/potvrdi': ['POST', nalogPotvrdi],
  '/api/nalog/link': ['POST', nalogLink],
  '/api/nalog/ja': ['GET', nalogJa],
  '/api/nalog/odjava': ['POST', nalogOdjava],
  '/api/nalog/podesavanja': ['POST', nalogPodesavanja],
  '/api/nalog/omiljeni': ['POST', nalogOmiljeni],
  '/api/nalog/doprinosi': ['GET', nalogDoprinosi],
  '/api/nalog/izvoz': ['GET', nalogIzvoz],
  '/api/nalog/obrisi': ['POST', nalogObrisi],
  '/api/nalog/pregled': ['POST', nalogPregled],
  '/api/posta/prijava': ['POST', postaPrijava],
  '/api/posta/potvrdi': ['POST', postaPotvrdi],
  '/api/posta/stanje': ['GET', postaStanje],
  '/api/posta/podesavanja': ['POST', postaPodesavanja],
  '/api/posta/odjava': ['POST', postaOdjava],
  '/api/posta/resend': ['POST', null],
  '/api/posta/tick': ['POST', null],
  '/api/posta/klik': ['GET', null],
  '/api/admin/posta': ['GET', null],
};

async function accountApi(request, env, ctx, url, p, m) {
  const r = ACCOUNT_ROUTES[p];
  if (!r) return bad('not found', 404);
  // somebody opened the one-click address in a browser: the page with the button (a GET never unsubscribes)
  if (p === '/api/posta/odjava' && m === 'GET') {
    return new Response(null, { status: 303, headers: { location: '/pregled/odjava/?t=' + encodeURIComponent((url.searchParams.get('t') || '').slice(0, 64)), 'cache-control': 'no-store' } });
  }
  if (p === '/api/posta/klik' && m === 'HEAD') return postaKlik(request, env, ctx, url);      // link checkers: redirect, no count
  if (p === '/api/admin/posta' && m === 'POST') {                                          // {"stop": "<slug>"}
    if (!adminOk(request, env)) return bad('not found', 404);
    return sameOrigin(request) ? adminPostaStop(request, env) : bad('origin', 403);
  }
  if (m !== r[0]) return json({ ok: false, error: 'method' }, 405, { allow: r[0] });
  if (Math.random() < 0.02) ctx.waitUntil(ensureSchema(env).then(() => housekeeping(env)).catch(() => {}));
  if (p === '/api/admin/posta') return adminOk(request, env) ? adminPosta(request, env) : bad('not found', 404);
  if (p === '/api/posta/klik') return postaKlik(request, env, ctx, url);
  if (p === '/api/posta/tick') return postaTick(request, env);               // GitHub Actions: no origin, no body
  if (p === '/api/posta/odjava') return postaOdjava(request, env, url);
  if (p === '/api/posta/resend') return postaResend(request, env);           // server to server: signed, no origin
  if (m === 'POST') {
    if (!sameOrigin(request)) return bad('origin', 403);
    if (!/^application\/json\b/i.test(request.headers.get('content-type') || '')) return bad('type', 415);
    const b = await readBody(request);
    return b ? r[1](request, env, b, ctx) : bad('json');
  }
  return r[1](request, env, url, ctx);
}

// ---------------------------------------------------------------- router
async function api(request, env, ctx) {
  const url = new URL(request.url);
  const p = url.pathname.replace(/\/+$/, '');
  const m = request.method;
  if (!env.DB) return bad('no database', 503);
  if (p.startsWith('/api/nalog/') || p.startsWith('/api/posta/') || p === '/api/admin/posta') return accountApi(request, env, ctx, url, p, m);

  if (m === 'GET' && p === '/api/stanice') {
    const cache = caches.default;
    const key = new Request(url.origin + '/api/stanice?c=' + Math.floor(Date.now() / 60000));
    let res = await cache.match(key);
    if (!res) {
      res = json({ ok: true, at: now(), st: await summaryAll(env) }, 200, { 'cache-control': 'public, max-age=60' });
      ctx.waitUntil(cache.put(key, res.clone()));
    }
    return res;
  }
  let mm = p.match(/^\/api\/stanica\/([a-z0-9-]{3,60})$/);
  if (m === 'GET' && mm) {
    return json(await summaryOne(env, mm[1]), 200, { 'cache-control': 'public, max-age=15' });
  }
  mm = p.match(/^\/api\/foto\/([0-9a-f]{32})(\.jpg)?$/);
  if (m === 'GET' && mm) return getPhoto(env, mm[1], url.searchParams.get('v') === 't');

  if (m === 'POST') {
    if (!sameOrigin(request)) return bad('origin', 403);
    mm = p.match(/^\/api\/stanica\/([a-z0-9-]{3,60})\/(prijava|foto|podatak)$/);
    if (mm) {
      const ids = await stationIds(env, request);
      if (ids.size && !ids.has(mm[1])) return bad('station', 404);
      return mm[2] === 'prijava' ? postCheckin(request, env, mm[1]) : mm[2] === 'podatak' ? postFact(request, env, mm[1]) : postPhoto(request, env, mm[1]);
    }
    if (p === '/api/prijavi') return postReport(request, env);
    if (p === '/api/zahtev') return postRequest(request, env);
    if (p === '/api/admin/odluka') return adminOk(request, env) ? adminDecide(request, env) : bad('not found', 404);
  }
  if (m === 'GET' && p === '/api/admin/red') return adminOk(request, env) ? adminQueue(env) : bad('not found', 404);
  if (m === 'GET' && p === '/api/admin/pomoc') return adminOk(request, env) ? adminHelpful(env) : bad('not found', 404);
  // the hidden link on /mapa/ (robots.txt forbids /api/, so only bots that ignore it follow it): counted per day and
  // fingerprint, nothing else — nobody is blocked (docs/RUNBOOK.md 3.28)
  if (m === 'GET' && p === '/api/zamka') {
    ctx.waitUntil(ipHash(request, env).then(ip => env.DB.batch([
      env.DB.prepare('CREATE TABLE IF NOT EXISTS trap (day TEXT NOT NULL, fp TEXT NOT NULL, n INTEGER NOT NULL DEFAULT 0, ua TEXT, PRIMARY KEY (day, fp))'),
      env.DB.prepare('INSERT INTO trap (day, fp, n, ua) VALUES (?1, ?2, 1, ?3) ON CONFLICT (day, fp) DO UPDATE SET n = n + 1')
        .bind(today(), ip, clean(request.headers.get('user-agent'), 120)),
    ])).catch(() => {}));
    return new Response('', { status: 204, headers: { 'cache-control': 'no-store', 'x-robots-tag': 'noindex, nofollow' } });
  }
  if (m === 'GET' && p === '/api/zdravlje') {
    const r = await env.DB.prepare('SELECT COUNT(*) AS n FROM checkins').first();
    return json({ ok: true, checkins: r.n });
  }
  return bad('not found', 404);
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname.startsWith('/api/')) {
      let res;
      try {
        res = await api(request, env, ctx);
      } catch (e) {
        res = json({ ok: false, error: 'server' }, 500);
      }
      pgAuto(request, env, ctx, url.pathname);        // after the answer is ready: the newsletter's background tick
      return res;
    }
    return env.ASSETS.fetch(request);
  },
};
