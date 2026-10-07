// dist/ as Cloudflare Pages would serve it, with the real worker: every request goes into dist/_worker.js running in
// Miniflare (workerd) with an in-memory D1 (worker/schema.sql applied at start) and MAIL_MODE=log, and the worker's
// env.ASSETS serves the static files like Pages (/x → /x.html, /x/ → /x/index.html, 404.html) with the headers of
// dist/_headers, so the Content-Security-Policy is enforced as in production (like scripts/qa/cfserve.py).
// For the browser tests of accounts and the newsletter (scripts/qa/nalog_ui_test.py, docs/RUNBOOK.md 3.27).
//   npm install --prefix /tmp/mf miniflare@4
//   MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_serve.mjs [dist] [port=8788] &
// Local-only helpers (not part of the site): GET /__dev/mail?to=<address>[&kind=code|confirm|welcome|preview|pregled|notice]
// → the newest mail to that address from D1 mail_log (JSON; ?id=<n> → that mail), GET /__dev/mails → all of them without
// the bodies, POST /__dev/tick-reset → the newsletter's tick lock is free again unless a tick runs (a real tick waits a
// minute; for scripts/qa/pregled_ui_test.py). A request header x-qa-ip becomes the visitor's IP (cf-connecting-ip), so tests can stay
// under the rate limits. BV_SITE=https://www.blokvolt.rs makes the links in the mails point to the real site (for looking
// at the rendered mails; the tests read only the paths).
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const DIST = path.resolve(process.argv[2] || path.join(REPO, 'dist'));
const PORT = Number(process.argv[3] || 8788);
const dir = process.env.MINIFLARE_DIR;
const { Miniflare } = dir
  ? await import(pathToFileURL(createRequire(path.join(path.resolve(dir), 'package.json')).resolve('miniflare')).href)
  : await import('miniflare');

// dist/_headers: "/path/*" lines, then indented "Name: value" lines
const RULES = [];
for (const line of fs.readFileSync(path.join(DIST, '_headers'), 'utf8').split('\n')) {
  if (!line.trim()) continue;
  if (!/^\s/.test(line)) RULES.push([new RegExp('^' + line.trim().replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*') + '$'), []]);
  else if (RULES.length && line.includes(':')) { const i = line.indexOf(':'); RULES.at(-1)[1].push([line.slice(0, i).trim(), line.slice(i + 1).trim()]); }
}
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.woff2': 'font/woff2',
  '.xml': 'application/xml', '.txt': 'text/plain; charset=utf-8', '.webmanifest': 'application/manifest+json', '.csv': 'text/csv; charset=utf-8', '.apk': 'application/vnd.android.package-archive' };
function resolve(p) {
  const f = path.join(DIST, decodeURIComponent(p));
  if (!f.startsWith(DIST)) return null;
  const tries = p.endsWith('/') ? [path.join(f, 'index.html')] : [f, f + '.html', path.join(f, 'index.html')];
  return tries.find(x => fs.existsSync(x) && fs.statSync(x).isFile()) || null;
}
// env.ASSETS of the worker
async function assets(req) {
  const u = new URL(req.url), file = resolve(u.pathname);
  const headers = new Headers();
  for (const [rx, hs] of RULES) if (rx.test(u.pathname)) for (const [k, v] of hs) headers.set(k, v);
  if (!file) {
    headers.set('content-type', 'text/html; charset=utf-8');
    return new Response(fs.readFileSync(path.join(DIST, '404.html')), { status: 404, headers });
  }
  headers.set('content-type', TYPES[path.extname(file)] || 'application/octet-stream');
  return new Response(fs.readFileSync(file), { status: 200, headers });
}

const mf = new Miniflare({
  modules: true, scriptPath: path.join(DIST, '_worker.js'), compatibilityDate: '2025-09-01',
  d1Databases: ['DB'], serviceBindings: { ASSETS: assets },
  // nothing leaves the machine: the only outside call of the worker here is the display currency's rate (/api/kurs →
  // kurs.resenje.org, RUNBOOK 3.29); it fails as if the source were down, and /api/kurs gives the fallback rate (stale)
  outboundService: () => new Response('blocked in local tests', { status: 599 }),
  bindings: { MAIL_MODE: 'log', SITE: process.env.BV_SITE || 'http://127.0.0.1:' + PORT, ADMIN_KEY: 'dev-admin-key-0123456789' },
});
const db = await mf.getD1Database('DB');
const schema = fs.readFileSync(path.join(REPO, 'worker', 'schema.sql'), 'utf8').replace(/--[^\n]*/g, '');
for (const s of schema.split(';').map(x => x.trim()).filter(Boolean)) await db.prepare(s).run();

http.createServer(async (rq, rs) => {
  try {
    const url = new URL(rq.url, 'http://127.0.0.1:' + PORT);
    if (url.pathname === '/__dev/mail' || url.pathname === '/__dev/mails') {
      const out = url.pathname === '/__dev/mails'
        ? (await db.prepare('SELECT id, at, to_addr, subject, kind, hdr FROM mail_log ORDER BY id').all()).results
        : url.searchParams.get('id') ? await db.prepare('SELECT * FROM mail_log WHERE id = ?1').bind(Number(url.searchParams.get('id'))).first()
        : await db.prepare('SELECT * FROM mail_log WHERE to_addr = ?1' + (url.searchParams.get('kind') ? ' AND kind = ?2' : '') + ' ORDER BY id DESC LIMIT 1')
          .bind(...[url.searchParams.get('to') || ''].concat(url.searchParams.get('kind') ? [url.searchParams.get('kind')] : [])).first();
      rs.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
      return rs.end(JSON.stringify(out));
    }
    if (url.pathname === '/__dev/tick-reset' && rq.method === 'POST') {
      // only a finished tick: one that runs (the background tick of the first request, say) keeps its lock
      await db.prepare("UPDATE pg_lock SET at = 0 WHERE until <= CAST(strftime('%s', 'now') AS INTEGER)").run().catch(() => {});
      rs.writeHead(200, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
      return rs.end('{"ok":true}');
    }
    const chunks = [];
    for await (const c of rq) chunks.push(c);
    const headers = new Headers();
    for (const [k, v] of Object.entries(rq.headers)) if (k !== 'host' && v !== undefined) headers.set(k, Array.isArray(v) ? v.join(', ') : v);
    headers.set('cf-connecting-ip', rq.headers['x-qa-ip'] || '127.0.0.1');
    const res = await mf.dispatchFetch(url.href, { method: rq.method, headers, body: chunks.length && !['GET', 'HEAD'].includes(rq.method) ? Buffer.concat(chunks) : undefined, redirect: 'manual' });
    const out = {};
    res.headers.forEach((v, k) => { if (k !== 'set-cookie' && k !== 'content-encoding' && k !== 'content-length' && !k.startsWith('mf-')) out[k] = v; });
    const cookies = res.headers.getSetCookie();
    if (cookies.length) out['set-cookie'] = cookies;
    const body = Buffer.from(await res.arrayBuffer());
    rs.writeHead(res.status, out);
    rs.end(rq.method === 'HEAD' ? undefined : body);
  } catch (e) {
    rs.writeHead(500, { 'content-type': 'text/plain' });
    rs.end('serve error: ' + e.message);
  }
}).listen(PORT, '127.0.0.1', () => console.log('dist + worker (MAIL_MODE=log) on http://127.0.0.1:' + PORT));
