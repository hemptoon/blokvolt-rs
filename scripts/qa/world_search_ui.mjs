// SEARCH (12.11.2026): the search field of blokvolt.com in a browser (Playwright, Chrome): the home, /map/, the hub
// ("Find a country"), the 404 and /search/, at 360 / 768 / 1440 px and in both themes.
//   node scripts/qa/world_search_ui.mjs dist-com [shots dir]      (serves dist-com itself, gzip like the hosts)
// Checks: the list opens on focus (recent / popular), "new" gives rows with groups, nothing covers the list (the element
// at the centre of each row belongs to the list), arrows + Enter open the chosen row, Esc closes, ARIA (combobox,
// listbox, aria-activedescendant, live count), a phone opens the search full screen, /map/ moves the map instead of
// leaving it, "Find a country" lists countries only, the 404 and /search/?q= answer. First suggestions after the first
// focus are timed with 4× CPU slowdown and a 4G-like network (Lighthouse "mobile"), budget 300 ms; a key press ≤ 30 ms.
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch (e) { pw = require('/opt/npm-tools/node_modules/playwright'); }
import http from 'http';
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';
const root = path.resolve(process.argv[2] || 'dist-com');
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp', '.avif': 'image/avif', '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.xml': 'application/xml' };
const server = http.createServer((req, res) => {
  let u = decodeURIComponent(req.url.split('?')[0]);
  let f = path.join(root, u);
  if (!f.startsWith(root)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, 'index.html');
  if (!fs.existsSync(f)) { res.writeHead(404, { 'content-type': 'text/html' }); return res.end(fs.readFileSync(path.join(root, '404.html'))); }
  const t = TYPES[path.extname(f)] || 'application/octet-stream', body = fs.readFileSync(f);
  if (/json|javascript|css|html|svg|xml/.test(t) && /gzip/.test(req.headers['accept-encoding'] || '')) {
    res.writeHead(200, { 'content-type': t, 'content-encoding': 'gzip' }); return res.end(zlib.gzipSync(body, { level: 6 }));
  }
  res.writeHead(200, { 'content-type': t }); res.end(body);
});
await new Promise(r => server.listen(0, r));
const base = `http://localhost:${server.address().port}`;
const shots = process.argv[3] || '';
const exe = process.env.CHROME || undefined;
const fails = [];
const ok = (c, m) => { if (!c) fails.push(m); };
const browser = await pw.chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
async function page(w, theme) {
  const ctx = await browser.newContext({ viewport: { width: w, height: w < 500 ? 780 : 900 }, hasTouch: w < 500, isMobile: w < 500 });
  await ctx.addInitScript(t => { try { localStorage.setItem('bv_theme', t); } catch (e) {} }, theme);
  const p = await ctx.newPage();
  p.on('pageerror', e => fails.push(`JS error ${w}/${theme}: ${e.message}`));
  return p;
}
async function covered(p) {
  return p.evaluate(() => {
    const sheet = document.querySelector('.bvs-sheet:not([hidden])');
    const pane = (sheet || document).querySelector('.bvs-pane:not([hidden])');
    if (!pane) return 'no pane';
    const bad = [], pr = pane.getBoundingClientRect();
    pane.querySelectorAll('[role=option] a, .bvs-more').forEach(a => {
      const r = a.getBoundingClientRect();
      if (r.bottom < Math.max(0, pr.top) || r.top > Math.min(innerHeight, pr.bottom) - r.height / 2 || r.height === 0) return;   // scrolled out of the list
      const x = r.left + r.width / 2, y = r.top + r.height / 2, e = document.elementFromPoint(x, y);
      if (e && !pane.contains(e)) bad.push(a.textContent.slice(0, 30) + ' under ' + (e.className || e.tagName));
    });
    const s = getComputedStyle(sheet || pane);
    if (s.backgroundColor === 'rgba(0, 0, 0, 0)' || s.backgroundColor === 'transparent') bad.push('transparent list');
    return bad.join('; ');
  });
}
// a phone opens the search in a full-screen sheet with its own field
async function field(p, sel, w) {
  if (w >= 500) return p.locator(sel).first();
  await p.locator(sel).first().click();
  await p.waitForSelector('.bvs-sheet:not([hidden]) input', { timeout: 3000 }).catch(() => ok(false, `${sel} ${w}: no full-screen sheet`));
  const box = await p.evaluate(() => { const r = document.querySelector('.bvs-sheet:not([hidden])').getBoundingClientRect(); return [r.width, r.height, innerWidth, innerHeight]; }).catch(() => [0, 0, 1, 1]);
  ok(box[0] >= box[2] && box[1] >= box[3], `${sel} ${w}: the sheet does not cover the screen ${box}`);
  return p.locator('.bvs-sheet:not([hidden]) input');
}
for (const theme of ['dark', 'light']) {
  for (const w of [360, 768, 1440]) {
    const p = await page(w, theme);
    // ---------------------------------------------------------------- home
    await p.goto(base + '/', { waitUntil: 'load' });
    const q = await field(p, '#wh-q', w);
    await q.focus();
    await p.waitForSelector('.bvs-pane:not([hidden]) [role=option]', { timeout: 5000 }).catch(() => ok(false, `home ${w}/${theme}: no popular list on focus`));
    if (shots && w === 360) await p.screenshot({ path: `${shots}/home-focus-${w}-${theme}.png` });
    await q.fill('new');
    await p.waitForTimeout(150);
    const n = await p.locator('.bvs-pane [role=option]').count();
    ok(n >= 6, `home ${w}/${theme}: "new" gives ${n} rows`);
    const cov = await covered(p);
    ok(!cov, `home ${w}/${theme}: covered: ${cov}`);
    ok((await q.getAttribute('role')) === 'combobox' && (await q.getAttribute('aria-expanded')) === 'true', `home ${w}: ARIA combobox`);
    ok(/: \d+/.test(await p.locator(w < 500 ? '.bvs-sheet [role=status]' : 'form.wh-search [role=status]').textContent()), `home ${w}: live count`);
    if (shots) await p.screenshot({ path: `${shots}/home-new-${w}-${theme}.png` });
    await q.press('ArrowDown');
    ok(!!(await q.getAttribute('aria-activedescendant')), `home ${w}: arrow does not select`);
    await q.press('Escape');
    ok(w < 500 ? await p.locator('.bvs-sheet').first().isHidden() : await p.locator('.bvs-pane').first().isHidden(), `home ${w}: Esc does not close`);
    const q2 = await field(p, '#wh-q', w);
    await q2.focus();
    await q2.fill('muenhen');
    await p.waitForTimeout(150);
    await q2.press('ArrowDown');
    await Promise.all([p.waitForNavigation({ timeout: 5000 }).catch(() => null), q2.press('Enter')]);
    ok(/munich|munchen|muenchen|grad=2867714/i.test(p.url()), `home ${w}: Enter on "muenhen" went to ${p.url()}`);
    // ---------------------------------------------------------------- 404
    await p.goto(base + '/no-such-page/', { waitUntil: 'load' });
    if (await p.locator('#bvs-404-q').count()) {
      await (await field(p, '#bvs-404-q', w)).fill('ionity');
      await p.waitForSelector('.bvs-pane:not([hidden]) [role=option]', { timeout: 5000 }).catch(() => ok(false, `404 ${w}: no list`));
      if (shots && w === 1440) await p.screenshot({ path: `${shots}/404-${theme}.png` });
    }
    // ---------------------------------------------------------------- /search/
    await p.goto(base + '/search/?q=tesla%20berlin', { waitUntil: 'load' });
    await p.waitForSelector('.bvs-all .bvs-sec', { timeout: 5000 }).catch(() => ok(false, `/search/ ${w}: no results`));
    if (shots) await p.screenshot({ path: `${shots}/search-page-${w}-${theme}.png`, fullPage: false });
    // ---------------------------------------------------------------- hub: Find a country
    await p.goto(base + '/charging-stations/', { waitUntil: 'load' });
    if (await p.locator('.wd-find input').count()) {
      const f = await field(p, '.wd-find input', w);
      await f.fill('germ');
      await p.waitForTimeout(400);
      const lid = await f.getAttribute('aria-controls');
      const kinds = await p.$$eval(`#${lid} [role=option] .sr-only`, xs => xs.map(x => x.textContent));
      ok(kinds.length > 0 && kinds.every(k => /Country/.test(k)), `hub ${w}: Find a country gives ${kinds.join('|')}`);
      if (shots && w !== 768) await p.screenshot({ path: `${shots}/hub-find-${w}-${theme}.png` });
    }
    // ---------------------------------------------------------------- /map/
    await p.goto(base + '/map/', { waitUntil: 'load' });
    ok(await p.locator('#wm-find-q').count() === 1, `map ${w}: no search field`);
    if (await p.locator('#wm-find-q').count()) {
      await p.waitForFunction(() => window.BVWorldMap && window.BVWorldMap.map, null, { timeout: 8000 }).catch(() => {});
      const m = await field(p, '#wm-find-q', w);
      await m.fill('ionity munich');
      await p.waitForTimeout(200);
      await m.press('Enter');
      await p.waitForTimeout(500);
      ok(/\/map\/\?/.test(p.url()) && /grad=2867714/.test(p.url()) && /mreza=ionity/.test(p.url()), `map ${w}: "ionity munich" → ${p.url()}`);
      if (shots && w !== 768) await p.screenshot({ path: `${shots}/map-${w}-${theme}.png` });
    }
    await p.context().close();
  }
}
// ---------------------------------------------------------------- speed (Moto G-like: 4× CPU, slow 4G)
{
  const ctx = await browser.newContext({ viewport: { width: 412, height: 823 }, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  const cdp = await ctx.newCDPSession(p);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 1.6 * 1024 * 1024 / 8 * 1.0, uploadThroughput: 750 * 1024 / 8 });
  await p.goto(base + '/', { waitUntil: 'load' });
  await p.waitForTimeout(500);
  const t = await p.evaluate(async () => {
    const q = document.getElementById('wh-q'), t0 = performance.now();
    q.focus();
    await new Promise(r => { const i = setInterval(() => { if (document.querySelector('.bvs-pane:not([hidden]) [role=option]')) { clearInterval(i); r(); } }, 5); });
    const first = performance.now() - t0;
    await new Promise(r => { const i = setInterval(() => { if (window.BVWorldSearch.ready()) { clearInterval(i); r(); } }, 20); });
    // typing three words letter by letter, three times from cold (what was searched before is forgotten); the median of
    // the three runs for each key (one garbage collection is not a key press)
    const keys = ['m', 'mu', 'mun', 'muni', 'munic', 'munich', 'b', 'be', 'ber', 'berl', 'berli', 'berlin', 'n', 'ne', 'new', 'new y', 'ionity', 'ionity m'];
    const runs = [];
    for (let k = 0; k < 3; k++) {
      window.BVWorldSearch.cold();
      runs.push(keys.map(s => { q.value = s; const a = performance.now(); q.dispatchEvent(new Event('input')); return performance.now() - a; }));
    }
    const times = keys.map((_, i) => runs.map(r => r[i]).sort((x, y) => x - y)[1]);
    return { first, worst: Math.max(...times), avg: times.reduce((a, b) => a + b, 0) / times.length };
  });
  console.log(`speed (4× CPU, ${'slow 4G'}): first suggestions ${t.first.toFixed(0)} ms after the first focus; key press avg ${t.avg.toFixed(1)} ms, worst ${t.worst.toFixed(1)} ms`);
  ok(t.first <= 300, `first suggestions ${t.first.toFixed(0)} ms > 300`);
  ok(t.worst <= 30, `key press ${t.worst.toFixed(1)} ms > 30`);
  await ctx.close();
}
await browser.close();
server.close();
console.log(fails.length ? 'world_search_ui: FAIL\n  ' + fails.join('\n  ') : 'world_search_ui: OK (5 places × 3 widths × 2 themes, keyboard, ARIA, phone full screen, speed)');
process.exit(fails.length ? 1 : 0);
