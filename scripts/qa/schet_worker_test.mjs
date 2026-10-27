// POST /api/s/p — our visit counter (docs/RUNBOOK.md 3.16): the real worker/_worker.js imported in Node with a fake
// service binding BOT (nothing leaves the machine; runs in Site checks). Checks that a page view goes on to the bot
// unchanged (method, path /s/p, body, Origin, User-Agent, CF-Connecting-IP), that the bot's answer comes back, that the
// counter does not need the database, and that without the binding — or when the bot fails — the hit is dropped with
// 204. Usage: node --no-warnings scripts/qa/schet_worker_test.mjs
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const W = (await import(pathToFileURL(path.join(REPO, 'worker', '_worker.js')).href)).default;

const SITE = 'https://www.blokvolt.rs';
let fails = 0, oks = 0;
function check(cond, what, detail) {
  if (cond) { oks++; console.log('ok   ' + what); } else { fails++; console.log('FAIL ' + what + (detail !== undefined ? ' — ' + JSON.stringify(detail).slice(0, 400) : '')); }
}

const seen = [];
let botMode = 'ok';
const BOT = {
  async fetch(req) {
    const u = new URL(req.url);
    seen.push({ method: req.method, path: u.pathname, search: u.search, body: req.method === 'POST' ? await req.text() : '',
      origin: req.headers.get('origin'), ua: req.headers.get('user-agent'), ip: req.headers.get('cf-connecting-ip') });
    if (botMode === 'throw') throw new Error('network');
    if (botMode === '500') return new Response('error', { status: 500 });
    return new Response(null, { status: 204, headers: { 'x-from': 'bot' } });
  },
};
const ASSETS = { fetch: () => new Response('not found', { status: 404 }) };
const ctx = { waitUntil() {}, passThroughOnException() {} };
const hit = JSON.stringify({ h: 'www.blokvolt.rs', p: '/mapa/', r: '', t: 0, us: '', um: '', uc: '', l: 'sr' });
const hdr = { origin: SITE, 'content-type': 'text/plain;charset=UTF-8', 'user-agent': 'Mozilla/5.0 test', 'cf-connecting-ip': '203.0.113.7' };
const post = (env, p = '/api/s/p') => W.fetch(new Request(SITE + p, { method: 'POST', headers: hdr, body: hit }), env, ctx);

console.log('— with the binding, no database');
let r = await post({ BOT, ASSETS });
check(r.status === 204 && r.headers.get('x-from') === 'bot', 'POST /api/s/p → the bot answers (its 204), no database needed', [r.status, [...r.headers]]);
const s = seen[0] || {};
check(seen.length === 1 && s.method === 'POST' && s.path === '/s/p' && s.search === '', 'the bot gets one POST on /s/p', seen);
check(s.body === hit, 'body unchanged', s.body);
check(s.origin === SITE && s.ua === 'Mozilla/5.0 test' && s.ip === '203.0.113.7', 'Origin, User-Agent and CF-Connecting-IP passed on', s);
r = await W.fetch(new Request(SITE + '/api/s/p?x=1', { method: 'OPTIONS', headers: { origin: SITE, 'access-control-request-method': 'POST' } }), { BOT, ASSETS }, ctx);
check(seen.length === 2 && seen[1].method === 'OPTIONS' && seen[1].path === '/s/p' && seen[1].search === '', 'other methods go to the bot as they are (it answers them); the query is not passed on', seen[1]);
for (const mode of ['500', 'throw']) {
  botMode = mode;
  r = await post({ BOT, ASSETS });
  check(r.status === 204 && r.headers.get('x-from') === null && r.headers.get('cache-control') === 'no-store', `bot fails (${mode}) → dropped quietly with 204`, r.status);
}
botMode = 'ok';
const before = seen.length;
r = await post({ BOT, ASSETS }, '/api/s/pp');
check(seen.length === before && r.status !== 204, 'only the exact path is the counter (/api/s/pp is not)', [seen.length, r.status]);

console.log('— without the binding');
seen.length = 0;
r = await post({ ASSETS });
check(r.status === 204 && r.headers.get('cache-control') === 'no-store' && seen.length === 0, 'no binding → 204, nothing sent', [r.status, seen.length]);

console.log(`\ncounter worker: ${oks} ok, ${fails} failed`);
process.exit(fails ? 1 : 0);
