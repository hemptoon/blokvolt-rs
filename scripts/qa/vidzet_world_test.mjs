// G5 world widgets: the field checks of POST /api/svet/vidzet (unit, plain Node, through globalThis.SVET_TEST).
// The routes themselves (/api/svet/vidzet, /api/svet/zahtev, /api/admin/vidzet) run in Miniflare like svet_worker_test.mjs
// once the worker is released with "релиз G5"; until then the widget sends nothing (config.widget_api is empty).
//   node scripts/qa/vidzet_world_test.mjs
import { pathToFileURL, fileURLToPath } from 'node:url';
import path from 'node:path';
const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
globalThis.SVET_TEST = {};
await import(pathToFileURL(path.join(REPO, 'worker', '_worker.js')).href);
const { vzParse } = globalThis.SVET_TEST;
let fails = 0;
const check = (c, w, d) => { if (c) console.log('ok   ' + w); else { fails++; console.log('FAIL ' + w + ' — ' + JSON.stringify(d)); } };
const P = o => vzParse(Object.assign({ k: 'map', l: 'en' }, o));
check(P({ h: 'www.Example.co.uk' }).h === 'example.co.uk', 'host lowercased, www. dropped', P({ h: 'www.Example.co.uk' }));
check(P({ h: '' }).h === '(direct)', 'no referrer → (direct)');
check(P({ h: 'localhost' }).h === '(local)' && P({ h: '192.168.1.5' }).h === '(local)', 'local hosts grouped');
for (const h of ['a b.com', 'x'.repeat(90) + '.com', 'evil.com/path', 'ana@mail.com', '<script>', 'com']) check(P({ h }).error === 'host', 'bad host ' + h.slice(0, 20), P({ h }));
check(P({ h: 'a.rs', k: 'cene' }).error === 'kind', 'unknown widget');
check(P({ h: 'a.rs', l: 'de' }).error === 'lang', 'unknown language');
check(!P({ h: 'a.rs', l: 'ru' }).error, 'ru ok');
check(vzParse([]).error === 'json' && vzParse(null).error === 'json', 'not an object');
console.log(fails ? `${fails} FAIL` : 'vidzet_world_test: ALL OK');
process.exit(fails ? 1 : 0);
