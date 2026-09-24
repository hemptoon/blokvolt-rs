// BlokVolt API — Cloudflare Pages "advanced mode" worker (copied to dist/_worker.js by build.py).
// Only /api/* reaches it (dist/_routes.json); everything else is served as static files.
// Binding: DB = D1 database "blokvolt" (schema: worker/schema.sql). Optional secret: ADMIN_KEY (set by the owner
// in Pages → Settings → Variables and Secrets; without it the /api/admin/* endpoints answer 404).

const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8' };
const STATUSES = new Set(['ok', 'problem', 'broken', 'missing']);
const KINDS = new Set(['firma', 'mreza', 'ispravka', 'stanica']);
const MAX_IMG = 950 * 1024, MAX_TH = 90 * 1024;
const LINKY = /(https?:\/\/|www\.|\b[a-z0-9-]+\.(com|rs|net|org|info|me|io)\b)/i;
const CONTACTY = /(\S+@\S+\.\S+|(\+?\d[\d\s\/.-]{7,}\d))/;
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

async function ipHash(request) {
  const ip = request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for') || '0';
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ip + '|' + today() + '|blokvolt'));
  return [...new Uint8Array(buf)].slice(0, 12).map(b => b.toString(16).padStart(2, '0')).join('');
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
  return { ok: true, st, avg: agg.avg, nr: agg.nr, n: agg.n, items: items.results, photos: photos.results };
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
  const ip = await ipHash(request);
  if (!(await allow(env, 'ci:' + ip, 30)) || !(await allow(env, 'cs:' + ip + ':' + st, 3))) return bad('limit', 429);
  let cs = 'none';
  if (c) cs = (LINKY.test(c) || CONTACTY.test(c) || RUDE.test(c) || (n && (LINKY.test(n) || RUDE.test(n)))) ? 'pending' : 'ok';
  await env.DB.prepare(
    'INSERT INTO checkins (st, s, r, c, n, cs, at, lang, ip) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)'
  ).bind(st, s, r, c, n, cs, now(), clean(b.lang, 5) || null, ip).run();
  return json({ ok: true, pending: cs === 'pending' });
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
  const ip = await ipHash(request);
  if (!(await allow(env, 'ph:' + ip, 6))) return bad('limit', 429);
  const pend = await env.DB.prepare(`SELECT COUNT(*) AS n FROM photos WHERE st = ?1 AND status = 'pending'`).bind(st).first();
  if (pend && pend.n >= 20) return bad('queue full', 429);
  const w = Math.min(4000, Math.max(0, Math.round(Number(fd.get('w') || 0)))), h = Math.min(4000, Math.max(0, Math.round(Number(fd.get('h') || 0))));
  await env.DB.prepare(
    'INSERT INTO photos (id, st, status, at, cap, w, h, mime, img, th, ip) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)'
  ).bind(rid(), st, 'pending', now(), clean(fd.get('opis'), 140) || null, w || null, h || null,
    isJpeg ? 'image/jpeg' : 'image/webp', buf, thBuf, ip).run();
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
  const ip = await ipHash(request);
  if (!(await allow(env, 'rp:' + ip, 20))) return bad('limit', 429);
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
  const ip = await ipHash(request);
  if (!(await allow(env, 'rq:' + ip, 6))) return bad('limit', 429);
  const email = clean(b.email || data.email, 120) || null;
  await env.DB.prepare('INSERT INTO requests (kind, slug, data, email, at, ip) VALUES (?1, ?2, ?3, ?4, ?5, ?6)')
    .bind(kind, clean(b.slug, 80) || null, JSON.stringify(data), email, now(), ip).run();
  return json({ ok: true });
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
    await env.DB.prepare('UPDATE photos SET status = ?1 WHERE id = ?2').bind(ok ? 'ok' : 'no', b.id).run();
  } else if (b.t === 'c' && Number.isInteger(b.id)) {
    await env.DB.prepare('UPDATE checkins SET cs = ?1 WHERE id = ?2').bind(ok ? 'ok' : 'hidden', b.id).run();
  } else if (b.t === 'z' && Number.isInteger(b.id)) {
    await env.DB.prepare('UPDATE requests SET status = ?1 WHERE id = ?2').bind(ok ? 'done' : 'rejected', b.id).run();
  } else return bad('what');
  return json({ ok: true });
}

// ---------------------------------------------------------------- router
async function api(request, env, ctx) {
  const url = new URL(request.url);
  const p = url.pathname.replace(/\/+$/, '');
  const m = request.method;
  if (!env.DB) return bad('no database', 503);

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
    mm = p.match(/^\/api\/stanica\/([a-z0-9-]{3,60})\/(prijava|foto)$/);
    if (mm) {
      const ids = await stationIds(env, request);
      if (ids.size && !ids.has(mm[1])) return bad('station', 404);
      return mm[2] === 'prijava' ? postCheckin(request, env, mm[1]) : postPhoto(request, env, mm[1]);
    }
    if (p === '/api/prijavi') return postReport(request, env);
    if (p === '/api/zahtev') return postRequest(request, env);
    if (p === '/api/admin/odluka') return adminOk(request, env) ? adminDecide(request, env) : bad('not found', 404);
  }
  if (m === 'GET' && p === '/api/admin/red') return adminOk(request, env) ? adminQueue(env) : bad('not found', 404);
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
      try {
        return await api(request, env, ctx);
      } catch (e) {
        return json({ ok: false, error: 'server' }, 500);
      }
    }
    return env.ASSETS.fetch(request);
  },
};
