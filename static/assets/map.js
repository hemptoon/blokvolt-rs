/* BlokVolt — map of public chargers (/mapa/). MapLibre GL + OpenFreeMap; stations from
   /assets/map/punjaci.json (OSM + OCM, ODbL) completed with /assets/map/mreze.json (the networks' own lists),
   prices from /assets/map/cene.json (ours), our checked facts from /assets/map/dopune.json (exact place, hours, access,
   who charges free), drivers' reports, ratings and photos from /api (Cloudflare D1).
   On blokvolt.rs, cfg.region adds the neighbouring countries (/assets/map/region.json: open data of the blokvolt.com
   sections) as a second, quieter layer: no prices, reports or checks there, and each card links to that country's map.
   Favourites (★) are station ids kept in this browser (localStorage 'bv:fav'), and so is the "Imam Teslu" switch
   ('bv:tesla'). Only a reader signed in to "Moj BlokVolt" (cookie bv_in) also keeps them in the account (/api/nalog/*,
   'bv:fav-owner': whose list it is; docs/RUNBOOK.md 3.27); without the cookie nothing is sent anywhere.
   Since 06.10.2026: "Najbliži punjač" (the three nearest chargers a driver can use, and a route; the navigation app chosen
   last is kept as 'bv:nav'), "Moj auto" (the reader's car, 'bv:car', with the cars from /assets/map/auta.json: the cost per
   km at every charger, compared with petrol and with charging at home), the network's own price of every connector
   (mreze.json: pr), hours with "open now" (oh.w), own cable (cab), parking (park) and "Kako se puni ovde" (cene.json: kako).
   The location, the car and the navigation app never leave the browser. docs/RUNBOOK.md 3.18. */
import * as maplibregl from '/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs';

const d = document;
const cfg = JSON.parse(d.getElementById('map-cfg').textContent);
const T = JSON.parse(d.getElementById('bv-i18n').textContent);
const LANG = (d.documentElement.lang || 'sr').slice(0, 2);
const LOC = LANG === 'sr' ? 'sr-Latn-RS' : LANG;
// units in the card and the lists (Russian writes them in Cyrillic); the labels next to pins stay ASCII
const U = { kw: T.u_kw || 'kW', km: T.u_km || 'km', m: T.u_m || 'm' };
// blokvolt.rs pages exist in /en/ and /ru/ too: its own links built here follow the page language
const LP = LANG === 'en' || LANG === 'ru' ? '/' + LANG : '';
const lp = u => (u && u.charAt(0) === '/' ? LP + u : u);
const fold = s => (s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
// the search box also ignores the script and the spelling of š/č/ž, gj/kj: Cyrillic is read as Latin and sh/ch/zh as one
// letter, so "Охрид" finds "Ohrid", "Shtip" finds "Штип" and "Kicevo" finds "Kičevo" (the open data mixes all of them).
// Price and free-charging matching keep plain fold(): their place keys in the data are folded that way.
const CYR = { а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', ѓ: 'g', ђ: 'd', е: 'e', ж: 'z', з: 'z', ѕ: 'dz', и: 'i', ј: 'j', к: 'k', ќ: 'k',
  л: 'l', љ: 'lj', м: 'm', н: 'n', њ: 'nj', о: 'o', п: 'p', р: 'r', с: 's', т: 't', ћ: 'c', у: 'u', ф: 'f', х: 'h', ц: 'c', ч: 'c',
  џ: 'dz', ш: 's', й: 'j', ы: 'y', э: 'e', ю: 'ju', я: 'ja', ё: 'e', щ: 's', ь: '', ъ: '' };
const sfold = s => fold(String(s || '').toLowerCase().replace(/[\u0400-\u04ff]/g, c => (c in CYR ? CYR[c] : c)))
  .replace(/([szc])h/g, '$1').replace(/([gk])j/g, '$1').replace(/dj/g, 'd');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
// notes from the price data and idle fees, translated on /en/ and /ru/ through the page's string table
const tr = s => (s && T['tx:' + s]) || s;
// the same script draws the country maps of blokvolt.com: centre, zoom, currency and the correction link come from the
// page's config (defaults = Serbia on www.blokvolt.rs)
const C0 = cfg.center || [20.9, 44.1], Z0 = cfg.zoom || 6.3, CUR = cfg.cur || 'RSD';
// blokvolt.com sections pass their own separators (a browser without Albanian or Macedonian locale data would print
// "0.39"); prices in lek and denars drop trailing zeros ("28–40 ден.", "10,2 lekë")
const NF = cfg.num || null;
const fmt = (n, dg = 0) => {
  if (!NF) return Number(n).toLocaleString(LOC, { minimumFractionDigits: dg, maximumFractionDigits: dg });
  const x = Number(n), p = Math.abs(x).toFixed(dg).split('.'), f = NF.trim ? (p[1] || '').replace(/0+$/, '') : (p[1] || '');
  return (x < 0 && +p.join('.') > 0 ? '−' : '') + p[0].replace(/\B(?=(\d{3})+(?!\d))/g, NF.thou) + (f ? NF.dec + f : '');
};
const CONN = { ccs2: 'CCS2', ccs1: 'CCS1', chademo: 'CHAdeMO', type2: 'Type 2', type1: 'Type 1', tesla: 'Tesla', gbt: 'GB/T', schuko: T.schuko, cee: 'CEE', other: T.other };
const svg = p => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>';
const ICON = {
  x: svg('<path d="M6 6l12 12M18 6 6 18"/>'),
  nav: svg('<path d="M3.5 11 20.5 3.5 13 20.5l-2-7.5-7.5-2Z"/>'),
  ext: svg('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
  flag: svg('<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>'),
  ok: svg('<path d="M20 6 9 17l-5-5"/>'),
  warn: svg('<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17.5v.01"/>'),
  cam: svg('<path d="M4 8h3l2-3h6l2 3h3v11H4V8Z"/><circle cx="12" cy="13" r="3.5"/>'),
  share: svg('<path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 12v7a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-7"/>'),
  copy: svg('<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>'),
  clock: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'),
  pin: svg('<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>'),
  info: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 8v.01"/>'),
  car: svg('<path d="M5 16.5h14M6.5 16.5v2M17.5 16.5v2M4.5 16.5v-4l2-5h11l2 5v4"/><path d="M4.5 12.5h15"/><circle cx="8" cy="14.5" r=".6"/><circle cx="16" cy="14.5" r=".6"/>'),
  cable: svg('<path d="M7 3v4M11 3v4M5.5 7h7v3.5a3.5 3.5 0 0 1-7 0V7Z"/><path d="M9 14v2a4 4 0 0 0 4 4h1a4 4 0 0 0 4-4V8"/>'),
  park: svg('<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M10 16V8h3a2.5 2.5 0 0 1 0 5h-3"/>'),
  home: svg('<path d="M4 11.5 12 5l8 6.5"/><path d="M6.5 10v9h11v-9"/><path d="M12.8 12.5 11 15.5h2l-1.8 3"/>'),
  bolt: svg('<path d="M13 2.5 5 13.5h6l-1 8 8-11h-6l1-8Z"/>'),
  list: svg('<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>')
};
// directions: Apple Maps first on Apple devices (it is the default there), Google Maps first elsewhere, Waze always.
// The app a reader opens a route in comes first from then on ('bv:nav' in this browser). Google: dir_action=navigate starts
// turn-by-turn at once in the Maps app on a phone; coordinates only, no API key.
const IS_APPLE = /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent);
const NAV_KEY = 'bv:nav', NAV_NAME = { google: 'Google Maps', apple: 'Apple Maps', waze: 'Waze' };
let NAV_PREF = '';
try { NAV_PREF = localStorage.getItem(NAV_KEY) || ''; } catch (e) { NAV_PREF = ''; }
function navApps() { return IS_APPLE ? ['apple', 'google', 'waze'] : ['google', 'waze']; }
function navPref() { return navApps().indexOf(NAV_PREF) >= 0 ? NAV_PREF : navApps()[0]; }
function setNavPref(a) {
  if (navApps().indexOf(a) < 0 || a === NAV_PREF) return;
  NAV_PREF = a;
  try { localStorage.setItem(NAV_KEY, a); } catch (e) { /* private mode: this visit only */ }
}
function navUrl(a, s) {
  const ll = s.lat + ',' + s.lon;
  if (a === 'apple') return 'https://maps.apple.com/?daddr=' + ll + '&dirflg=d';
  if (a === 'waze') return 'https://waze.com/ul?ll=' + ll + '&navigate=yes&utm_source=blokvolt';
  return 'https://www.google.com/maps/dir/?api=1&destination=' + ll + '&travelmode=driving&dir_action=navigate';
}
function navLinks(s) {
  const p = navPref();
  return [p].concat(navApps().filter(a => a !== p)).map(a => [NAV_NAME[a], navUrl(a, s), a]);
}
// a price older than a year is shown with a warning. Dates in the price data: "22.09.2026", "oktobar 2021",
// "2022 / 2024" — the newest date mentioned counts; a bare year counts as its last day
const MONTHS_SR = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar'];
function ageDays(ds) {
  if (!ds) return Infinity;
  let t = 0;
  const re = /(?:(\d{1,2})\.(\d{1,2})\.|([a-zčćšžđ]+)\s+)?(\d{4})/gi;
  for (let m; (m = re.exec(ds));) {
    const y = +m[4];
    const mi = m[2] ? +m[2] - 1 : m[3] ? MONTHS_SR.indexOf(m[3].toLowerCase()) : -1;
    const dt = m[1] ? new Date(y, mi, +m[1]) : mi >= 0 ? new Date(y, mi + 1, 0) : new Date(y, 11, 31);
    t = Math.max(t, dt.getTime());
  }
  return t > 0 ? (Date.now() - t) / 86400000 : Infinity;
}
function stale(ds) { const a = ageDays(ds); return a !== Infinity && a > 365; }
const ST_LABEL = { ok: T.ci_ok, problem: T.ci_problem, broken: T.ci_broken, missing: T.ci_missing };
const STAR = '<svg class="star" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.6l2.55 5.17 5.7.83-4.13 4.02.98 5.68L12 16.62l-5.1 2.68.98-5.68L3.75 9.6l5.7-.83L12 3.6Z"/></svg>';
// usage events go through bv.js (window.bvTrack); a missing or blocked analytics script never breaks the map
const track = (e, p) => { try { if (window.bvTrack) window.bvTrack(e, p); } catch (x) { /* ignore */ } };

// ---------- favourites (this browser only) ----------
const FAV_KEY = 'bv:fav';
let FAV = new Set();
try { FAV = new Set((JSON.parse(localStorage.getItem(FAV_KEY) || '[]') || []).filter(x => typeof x === 'string').slice(0, 300)); } catch (e) { FAV = new Set(); }
function saveFav() { try { localStorage.setItem(FAV_KEY, JSON.stringify([...FAV])); } catch (e) { /* private mode: kept for this visit only */ } }
function isFav(s) { return FAV.has(s.id); }

// "Imam Teslu": Tesla-only chargers (the two Superchargers) count as usable and, where drivers report it, free
const TESLA_KEY = 'bv:tesla';
let TESLA = false;
try { TESLA = localStorage.getItem(TESLA_KEY) === '1'; } catch (e) { TESLA = false; }
function saveTesla() { try { localStorage.setItem(TESLA_KEY, TESLA ? '1' : '0'); } catch (e) { /* private mode: this visit only */ } }

// "Moj auto": the reader's car in this browser only ('bv:car' = {id, cons, cab, opt}: the car's id in auta.json, the reader's
// own consumption in kWh/100 km, "I have my own Type 2 cable", the optional on-board charger). With a car the map shows the
// cost per km; a Tesla also switches "Imam Teslu" on (and another car off).
const CAR_KEY = 'bv:car';
let CAR = null, CARS = null, CARS_P = null, COSTV = 0;
try {
  const c = JSON.parse(localStorage.getItem(CAR_KEY) || 'null');
  if (c && typeof c.id === 'string' && c.id.length < 90) CAR = { id: c.id, cons: +c.cons || null, cab: !!c.cab, opt: !!c.opt };
} catch (e) { CAR = null; }
function saveCar() { try { if (CAR) localStorage.setItem(CAR_KEY, JSON.stringify(CAR)); else localStorage.removeItem(CAR_KEY); } catch (e) { /* private mode */ } }
function loadCars() {
  if (CARS) return Promise.resolve(CARS);
  if (!CARS_P) CARS_P = (cfg.cars ? fetch(cfg.cars).then(r => { if (!r.ok) throw new Error('cars'); return r.json(); }) : Promise.reject(new Error('cars')))
    .then(j => (CARS = j.cars || [], CARS)).catch(() => { CARS_P = null; return null; });
  return CARS_P;
}
// the car as the cost engine reads it: the specs from auta.json with the reader's own consumption and on-board charger
function carSpec() {
  if (!CAR || !CARS) return null;
  const c = CARS.find(x => x.id === CAR.id);
  if (!c) return null;
  const o = CAR.opt && c.opt ? c.opt : c;
  return Object.assign({}, c, { ac: o.ac, ph: o.ph, a: o.a, cons: CAR.cons && CAR.cons >= 8 && CAR.cons <= 40 ? CAR.cons : c.cons, cab: CAR.cab });
}
function carName(c) { return c ? c.mk + ' ' + c.md.replace(/\s*\(.*?\)\s*/g, ' ').trim() : ''; }

// ---------- hours: "open now" in Serbia's time, whatever the reader's time zone ----------
function nowMin() {
  try {
    const p = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Belgrade', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date());
    return (+p.find(x => x.type === 'hour').value % 24) * 60 + (+p.find(x => x.type === 'minute').value);
  } catch (e) { const n = new Date(); return n.getHours() * 60 + n.getMinutes(); }
}
const hhmm = x => String(Math.floor(x / 60) % 24).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0');
// oh.w: the daily open windows in minutes ([[300, 1500]] = 05:00 to 01:00 the next day). null = hours unknown
function openState(s, t) {
  const oh = s.oh;
  if (!oh) return null;
  if (oh.h24) return { open: true, h24: true };
  if (!oh.w || !oh.w.length) return null;
  const m = t == null ? nowMin() : t;
  for (const [a, b] of oh.w) if ((m >= a && m < b) || (m + 1440 >= a && m + 1440 < b)) return { open: true, until: b % 1440 };
  let next = null;
  for (const [a] of oh.w) { const dl = ((a - m) % 1440 + 1440) % 1440; if (!next || dl < next.d) next = { d: dl, at: a % 1440 }; }
  return { open: false, at: next ? next.at : null };
}
function closedNow(s) { const o = openState(s); return !!o && !o.open; }

// ---------- the account ("Moj BlokVolt"), only with the cookie bv_in=1 ----------
// After the map data is in, /api/nalog/ja is asked once. The browser's list follows its owner ('bv:fav-owner', a short
// hash the server gives each account): the same account → both lists joined and saved in both; another account → the
// signed-in account's list replaces it, never mixed; a list from before any sign-in with stations the account does not
// have → nothing changes here and nothing is sent: /nalog/ asks the reader first. Once in step, every star (and the Tesla
// switch) is also sent to the account, fire-and-forget: localStorage stays the offline copy. A 401 removes the hint
// cookie; the map then works as before, locally. The account's fast-charging plug (user.dc) marks the matching connector.
const OWNER_KEY = 'bv:fav-owner';
let ACC = false, MYDC = '';
function accPost(path, body) {
  return fetch(cfg.api + '/nalog/' + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body), credentials: 'same-origin' }).catch(() => null);
}
function accSync() {
  if (!cfg.api || !/(?:^|;\s*)bv_in=1(?:;|$)/.test(d.cookie)) return;
  fetch(cfg.api + '/nalog/ja', { credentials: 'same-origin' }).then(r => {
    if (r.status === 401) { d.cookie = 'bv_in=; Max-Age=0; Path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : ''); return null; }
    return r.ok ? r.json() : null;
  }).then(j => {
    if (!j || !j.ok) return;
    MYDC = (j.user && j.user.dc) || '';
    let owner = null;
    try { owner = localStorage.getItem(OWNER_KEY); } catch (e) { owner = null; }
    const key = j.user.owner, acc = new Set(j.favs || []), same = (a, b) => a.size === b.size && [...a].every(x => b.has(x));
    if (!owner && [...FAV].some(id => !acc.has(id))) { refresh(); if (sel) openCard(sel, false); return; }   // /nalog/ asks first
    ACC = true;
    const ids = new Set(ST.map(s => s.id)), mine = [...acc].filter(id => ids.has(id));
    const next = new Set((owner === key ? [...mine, ...FAV] : mine).slice(0, 300));
    if (!same(next, FAV)) { FAV = next; saveFav(); }
    try { localStorage.setItem(OWNER_KEY, key); } catch (e) { /* private mode */ }
    if (!same(next, acc)) accPost('omiljeni', { replace: [...next] });
    const tesla = !!(j.user && j.user.tesla);
    if (tesla !== TESLA && !/[?&]tesla=1\b/.test(location.search)) setTesla(tesla, true);
    favCount();
    refresh();
    if (sel) openCard(sel, false);
  }).catch(() => { /* offline: the local lists stay */ });
}

let ST = [], NETS = {}, CI = {}, CI_STATE = 'loading', map, me = null, sel = null, city = null, opened = 0;
// the neighbouring countries (cfg.region): their links, and how many stations are Serbian (NSR) and how many are not (NRG)
let RGC = {}, NSR = 0, NRG = 0;
const state = { q: '', f: 'all', ok: false, cheap: false, bounds: null, lim: 20 };
let userMove = false;
const $list = d.getElementById('mlist'), $count = d.getElementById('mcount'), $card = d.getElementById('mcard');
const $q = d.getElementById('mq'), $chips = d.getElementById('mchips'), $me = d.getElementById('mme');

// ---------- data ----------
// our checked fact first (dopune.json: fee.free = all | limited | tesla), then the network's price data
function teslaOnly(s) { return !!(s.ax && s.ax.who === 'tesla'); }
function isFree(s) {
  if (s.cc) return false;
  const f = s.fee && s.fee.free;
  if (f) return f === 'all' || f === 'limited' || (f === 'tesla' && TESLA);
  const n = NETS[s.net];
  if (!n || !n.free) return false;
  if (!n.free_where) return true;
  const hay = fold([s.n, s.a, s.t].join(' '));
  return n.free_where.some(w => hay.indexOf(w) >= 0);
}
// v.s: ok = on a network's own list or checked by hand; nep = only in the open databases; prob = recent reports that it does not work
function ver(s) { return (s.v && s.v.s) || 'nep'; }
// state motorway chargers carry the official status (s.ps): none working now = 'off'
function isOff(s) { return (!!s.ps && !s.ps.l.some(l => l[2] === 1)) || ver(s) === 'prob'; }
function kind(s) {
  if (isOff(s)) return 'off';
  if (isFree(s)) return 'free';
  if (teslaOnly(s) && !TESLA) return 'tesla';
  return (s.dc || 0) > 0 ? 'dc' : 'ac';
}
// a neighbouring country's station never takes a Serbian network's data (the same slug can mean another company there)
function netOf(s) { return s.cc ? null : NETS[s.net] || null; }
function netName(s) { if (s.cc) return s.nn || s.opn || ''; const n = netOf(s); return n ? n.name : (s.opn || ''); }
// a station without a name is called by its network, else by its street
function cleanName(n) { return (n || '').replace(/^charge\s*&\s*go\s*[-–:,]?\s*/i, '').replace(/^BS\s+(?=gazprom|nis|evoil)/i, '').trim(); }
function title(s) { return cleanName(s.n) || netName(s) || (s.a ? s.a.split(',')[0] : T.charger); }
function hayOf(s) { return fold([s.n, s.a].concat(s.al || []).join(' ')); }
function place(s) {
  const near = s.t ? T.near.replace('{t}', s.t) : '';
  const p = !s.n && !netName(s) && s.a ? s.a.split(',').slice(1).join(',').trim() || near : s.a || near;
  return s.cc ? [p, T['cc_' + s.cc]].filter(Boolean).join(', ') : p;
}
function power(s) { return s.dc || s.ac || 0; }

// one price line: v = RSD/min, k = RSD/kWh, h = RSD/hour, st = start or connection fee, ut + pm = Spectra "units" + RSD/min
// (fx: the line's number and unit for the display currency, 3.29)
function stationLines(s) {
  const P = s.pr, unit = P.u === 'kwh' ? T.per_kwh : T.per_min;
  return P.l.map(l => ({ cur: l[0], kw: l[1], n: l[3], v: P.u === 'min' ? l[2] : null, k: P.u === 'kwh' ? l[2] : null, st: P.st || 0,
    label: fmt(l[2], 2) + ' ' + unit, fx: [l[2], unit.replace(/^RSD/, '')], date: P.d, src: P.src, charger: l[0].toUpperCase() + ' ' + fmt(l[1], l[1] % 1 ? 1 : 0) + ' ' + U.kw }));
}
function price(s) {
  if (s.cc) return { kind: 'rg' };
  const fee = s.fee;
  if (fee && fee.free) {
    const lbl = { label: tr(fee.t), src: tr(fee.src), note: tr(fee.note) };
    if (isFree(s)) return Object.assign({ kind: 'free', text: T.p_free, date: '' }, lbl);
    if (fee.free === 'tesla') return Object.assign({ kind: 'tesla', text: T.p_tesla_only }, lbl);
  }
  let n = netOf(s);
  if (!n) return { kind: 'none', text: T.p_unknown };
  if (n.via && NETS[n.via]) n = NETS[n.via];
  if (n.free && isFree(s)) return { kind: 'free', text: T.p_free, note: tr(n.free_note) || '', date: n.date || '' };
  const hay = hayOf(s);
  const receipt = (n.receipts || []).filter(r => r.where.some(w => hay.indexOf(w) >= 0));
  // the network's own price of every connector of this very station (its app, mreze.json: pr)
  if (s.pr && s.pr.l && s.pr.l.length) {
    const lines = stationLines(s);
    return { kind: 'station', t: lines[0], lines, receipt, note: tr(n.note) };
  }
  if (n.free && !(n.tiers || []).length && !(n.places || []).length) return { kind: 'none', text: tr(n.note) || T.p_unknown };
  const cur = s.dc ? 'dc' : 'ac', P = power(s);
  const fits = t => t.cur === cur && (t.lo == null || (P >= t.lo - 5 && P <= t.hi + 5));
  // 'guard' copies in cene.json are for older map code (evolako.rs, the apps' first versions), not for this one
  const all = (n.tiers || []).concat(n.places || []).filter(t => !t.guard);
  const exact = all.filter(t => t.where.some(w => hay.indexOf(w) >= 0));
  // the price recorded at this place: the one for this current and power, or the only one for this current (a place
  // that has one price for several powers); never the price of the other current
  const ex = exact.filter(fits)[0] || (exact.length === 1 && exact[0].cur === cur ? exact[0] : null);
  if (ex) return { kind: 'exact', t: ex, receipt, note: tr(n.note) };
  if (n.kwh) {
    const fit = (n.tiers || []).filter(t => t.cur === cur && fits(t));
    if (fit.length) return { kind: 'kwh', list: fit, note: tr(n.note) };
    return { kind: 'none', text: tr(n.note) || T.p_unknown };
  }
  // the network's tariff for this power (networks with one price list for all their chargers: tiers; per-place prices are
  // in "places" and only count where they were recorded)
  const tiers = (n.tiers || []).filter(t => t.cur === cur);
  const t = tiers.filter(fits)[0];
  if (t) return { kind: 'tier', t, receipt, note: tr(n.note) };
  if (cur === 'dc' && tiers.length && P && tiers.every(x => x.v != null)) {
    const lower = tiers.filter(x => x.hi <= P).pop(), upper = tiers.filter(x => x.lo >= P)[0];
    if (lower && upper) return { kind: 'range', lo: lower, hi: upper, note: tr(n.note) };
  }
  const same = all.filter(x => x.cur === cur);
  if (same.length) return { kind: 'seen', list: same, note: tr(n.note) };
  return { kind: 'none', text: tr(n.note) || T.p_unknown };
}

// ---------- cost per kWh and per km ----------
// What a car really takes: AC — the car's on-board charger, the station's phases and current (a 22 kW post is 3 × 32 A,
// 11 kW 3 × 16 A, 7,4 kW 1 × 32 A); DC — the car's average from 10 to 80 %, at most 88 % of the station's nameplate power.
// Without a car: a typical car (REAL_KW, AC 11 kW). Efficiency from the charger to the battery: DC 96 %, AC 84–92 % by
// power (ADAC 08/2026). A start fee is spread over a session of half the battery (25 kWh without a car). Winter: the car's
// consumption × its winter factor in December–February, half of it in November and March.
const REAL_KW = [[30, 30], [50, 45], [60, 50], [115, 90], [165, 100], [240, 130]];
function realKw(P, cur) {
  if (!P) return null;
  if (cur !== 'dc') return Math.min(P, 11);
  if (P <= 30) return P;
  for (let i = 1; i < REAL_KW.length; i++) {
    const [x1, y1] = REAL_KW[i - 1], [x2, y2] = REAL_KW[i];
    if (P <= x2) return y1 + (y2 - y1) * (P - x1) / (x2 - x1);
  }
  return 130;
}
function perKwh(v, s) { const k = realKw(power(s), s.dc ? 'dc' : 'ac'); return v && k ? v * 60 / k : null; }
const ETA_DC = 0.96;
const etaAc = p => (p >= 10 ? 0.92 : p >= 6 ? 0.9 : p >= 3.3 ? 0.88 : 0.84);
const acPost = kw => (kw >= 21 ? [3, 32] : kw >= 10.5 ? [3, 16] : kw >= 7 ? [1, 32] : [1, 16]);
function winterShare() { const m = new Date().getMonth(); return m === 11 || m <= 1 ? 1 : m === 10 || m === 2 ? 0.5 : 0; }
function carKw(car, cur, kw) {
  if (!kw) return null;
  if (cur === 'dc') return Math.min(car.dc, 0.88 * kw);
  const [ph, a] = acPost(kw);
  return Math.min(car.ac, kw, 0.23 * Math.min(a, car.a) * Math.min(ph, car.ph));
}
// one tariff at one connector → {kw: what the car takes, kwh: RSD per kWh from the charger, km: RSD per km (with a car)}
function lineCost(t, cur, kw) {
  const car = carSpec();
  const P = car ? carKw(car, cur, kw) : realKw(kw, cur);
  if (!P || t.ut || (t.v == null && t.k == null && t.h == null)) return null;   // Spectra "units" are not kWh
  const eta = cur === 'dc' ? ETA_DC : etaAc(P);
  const sess = car ? car.kwh * 0.5 / eta : 25;
  const kwh = (t.k || 0) + (t.v ? t.v * 60 / P : 0) + (t.h ? t.h / P : 0) + (t.pm ? t.pm * 60 / P : 0) + (t.st ? t.st / sess : 0);
  const cons = car ? car.cons * (1 + (car.wf - 1) * winterShare()) : null;
  return { kw: P, kwh, km: car ? kwh * cons / 100 / eta : null, eta };
}
// the car can use this station: a CHAdeMO car needs a CHAdeMO plug for DC, a CCS car a CCS one (Tesla stalls: Teslas only)
function dcUsable(s, car) {
  if (!car || !s.c.length) return true;
  if (car.pl === 'chademo') return s.c.some(c => c[0] === 'chademo');
  return s.c.some(c => c[1] === 'dc' && c[0] !== 'chademo' && (c[0] !== 'tesla' || car.mk === 'Tesla'));
}
function acUsable(s, car) { return !s.c.length || s.c.some(c => c[1] !== 'dc') || (!s.dc && s.ac); }
// the price lines a driver can choose from at this station, each with its cost for the car (or a typical car)
function costLines(s, p) {
  p = p || price(s);
  const car = carSpec();
  let ls = [];
  if (p.kind === 'station') ls = p.lines.map(t => ({ t, cur: t.cur, kw: t.kw }));
  else if (p.kind === 'exact' || p.kind === 'tier') {
    ls = [{ t: p.t, cur: s.dc ? 'dc' : 'ac', kw: power(s) }];
    // a station with both AC and DC: the AC line from the network's tariffs too (a 22 kW car may be cheaper on AC)
    const n = netOf(s);
    if (s.dc && s.ac && n && p.kind === 'tier') {
      const at = (n.tiers || []).find(x => x.cur === 'ac' && (x.lo == null || (s.ac >= x.lo - 5 && s.ac <= x.hi + 5)));
      if (at) ls.push({ t: at, cur: 'ac', kw: s.ac });
    }
  } else return [];
  return ls.filter(l => !car || (l.cur === 'dc' ? dcUsable(s, car) : acUsable(s, car)))
    .map(l => Object.assign(l, { c: lineCost(l.t, l.cur, l.kw) })).filter(l => l.c);
}
// the line the driver will most likely use (the most powerful one the car can use) and a cheaper one at the same station
function costOf(s) {
  if (s._cv === COSTV) return s._co;
  let out = null;
  if (!s.cc && !isOff(s)) {
    const p = price(s);
    const ls = p.kind === 'free' || p.kind === 'tesla' ? [] : costLines(s, p);
    if (ls.length) {
      const main = ls.slice().sort((a, b) => b.c.kw - a.c.kw)[0];
      const cheap = ls.slice().sort((a, b) => a.c.kwh - b.c.kwh)[0];
      out = { p, main, alt: cheap !== main && cheap.c.kwh < main.c.kwh * 0.8 ? cheap : null };
    }
  }
  s._cv = COSTV; s._co = out;
  return out;
}
// 9,4 · 13 (one decimal under 10)
const fmtKm = x => fmt(x, x < 10 ? 1 : 0);
// home at night (EPS, lower tariff, green and blue zone, all fees) and fuel, per km for the car
function homeKm(car) { return (cfg.home || []).map(h => h * car.cons / 100 / 0.92); }
function fuelKm(kind) { const f = cfg.fuel; return f ? (kind === 'd' ? f.d * f.ld : f.b * f.lb) / 100 : null; }
function priceShort(s) {
  if (isOff(s)) return { t: ver(s) === 'prob' ? T.v_prob_t : T.off, cls: 'off' };
  const p = price(s);
  if (p.kind === 'free') return { t: T.free, cls: 'free' };
  if (p.kind === 'tesla') return { t: T.tesla_only, cls: 'off' };
  if (carSpec()) {
    const co = costOf(s);
    if (co && co.main.c.km != null) return { t: '≈ ' + fmtKm(co.main.c.km) + ' ' + T.per_km, cls: '' };
  }
  const rc = freshReceipts(p);
  if (rc) return { t: rc + ' ' + T.per_kwh, cls: '' };
  if (p.kind === 'exact' || p.kind === 'tier' || p.kind === 'station') return { t: p.t.label, cls: '' };
  if (p.kind === 'range') return { t: fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + T.per_min, cls: '' };
  if (p.kind === 'kwh') return { t: kwhSpan(p.list, '–') + ' ' + T.per_kwh, cls: '' };
  return { t: '', cls: '' };
}

// receipts of this very station not older than 90 days: they win over the network's tariff for the power (min–max RSD/kWh)
function freshReceipts(p, dash) {
  const rc = (p.receipt || []).filter(r => ageDays(r.date) <= 90);
  if (!rc.length) return '';
  const lo = Math.min(...rc.map(r => r.kwh)), hi = Math.max(...rc.map(r => r.kwh));
  return lo === hi ? fmt(lo) : fmt(lo) + (dash || '–') + fmt(hi);
}
// per-kWh tariffs: the lowest and the highest price of the tiers that fit (0,35–0,42)
function kwhSpan(list, dash) {
  const v = list.map(t => t.v).filter(x => x != null);
  if (!v.length) return '?';
  const lo = Math.min(...v), hi = Math.max(...v);
  return lo === hi ? fmt(lo, 2) : fmt(lo, 2) + dash + fmt(hi, 2);
}
// the label next to a pin (zoom 12+): only ASCII, the map font has no other glyphs everywhere
function pinPrice(s) {
  if (isOff(s) || s.cc) return { t: '', c: '' };
  const p = price(s);
  if (p.kind === 'free') return { t: '0 ' + CUR, c: 'free' };
  if (p.kind === 'tesla') return { t: '', c: '' };
  const old = d => stale(d) ? 'old' : '';
  if (carSpec()) {
    const co = costOf(s);
    if (co && co.main.c.km != null) return { t: '~' + fmtKm(co.main.c.km) + ' ' + CUR + '/km', c: old(co.main.t.date) };
  }
  const rc = freshReceipts(p, '-');
  if (rc) return { t: rc + ' ' + CUR + '/kWh', c: '' };
  if (p.kind === 'station' || ((p.kind === 'exact' || p.kind === 'tier') && (p.t.v != null || p.t.k != null || p.t.h != null))) {
    const co = costOf(s);
    if (co) {
      const exact = co.main.t.k != null && !co.main.t.v && !co.main.t.h && !co.main.t.st;
      return { t: (exact ? '' : '~') + Math.round(co.main.c.kwh) + ' ' + CUR + '/kWh', c: old(co.main.t.date) };
    }
  }
  if (p.kind === 'range') {
    const a = perKwh(p.lo.v, s), b = perKwh(p.hi.v, s);
    if (a && b) return { t: '~' + Math.round(Math.min(a, b)) + '-' + Math.round(Math.max(a, b)) + ' ' + CUR + '/kWh', c: old(p.lo.date) };
  }
  if (p.kind === 'kwh') { const sp = kwhSpan(p.list, '-'); return sp === '?' ? { t: '?', c: 'unk' } : { t: sp + ' ' + CUR, c: old(p.list[0].date) }; }
  return { t: '?', c: 'unk' };
}

// ---------- filters ----------
// the chip filter alone (also used by "Najbliži punjač", which ignores the search text and the visible part of the map)
function matchChip(s, f) {
  if (f === 'fast' && !((s.dc || 0) >= 50)) return false;
  if (f === 'ac' && !(s.ac || s.c.some(c => c[1] !== 'dc'))) return false;
  if (f === 'free' && kind(s) !== 'free') return false;
  if (f === 'chademo' && !s.c.some(c => c[0] === 'chademo')) return false;
  if (f === 'fav' && !FAV.has(s.id)) return false;
  if (f.indexOf('net:') === 0 && (s.cc || s.net !== f.slice(4))) return false;
  return true;
}
function match(s) {
  if (!matchChip(s, state.f)) return false;
  if (state.ok && ver(s) !== 'ok') return false;
  if (state.q) {
    const hay = s._q || (s._q = sfold([s.n, s.a, s.t, netName(s), s.opn].concat(s.al || []).join(' ')));
    for (const w of sfold(state.q).split(/\s+/).filter(Boolean)) if (hay.indexOf(w) < 0) return false;
  }
  return true;
}
function visible() { return ST.filter(match); }
function inView(s) {
  const b = state.bounds;
  return !b || (s.lat >= b.s && s.lat <= b.n && s.lon >= b.w && s.lon <= b.e);
}

// ---------- list ----------
function distKm(a, b) {
  const r = Math.PI / 180, dLa = (b.lat - a.lat) * r, dLo = (b.lon - a.lon) * r;
  const h = Math.sin(dLa / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLo / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
}
function badge(s) {
  const v = ver(s);
  if (v === 'nep') return ' <i class="vq" title="' + esc(T.v_nep) + '">?</i>';
  if (v === 'prob') return ' <i class="vq no" title="' + esc(T.v_prob_t) + '">!</i>';
  return '';
}
function rating(s) {
  const c = CI[s.id];
  return c && c.a ? ' · ★ ' + fmt(c.a, 1) : '';
}
function renderList() {
  let rows = visible().filter(inView);
  // the whole-country list is Serbia's; the neighbouring countries join it when the map is zoomed in there, a search
  // finds them or the reader asks for the chargers near them
  const home = !state.bounds && !state.q && !me;
  const rgAll = home && NRG ? rows.filter(s => s.cc).length : 0;
  if (home) rows = rows.filter(s => !s.cc);
  const ref = me || city;
  if (ref) rows = rows.map(s => (s._d = distKm(ref, s), s)).sort((a, b) => a._d - b._d);
  // "Najjeftinije za moj auto": the cost per km for the reader's car first (free = 0), unknown prices last; distance breaks ties
  const cheap = state.cheap && !!carSpec();
  if (cheap) {
    const km = s => (isOff(s) ? Infinity : isFree(s) ? 0 : (costOf(s) && costOf(s).main.c.km != null ? costOf(s).main.c.km : Infinity));
    rows = rows.map((s, i) => (s._k = km(s), s._o = i, s)).sort((a, b) => a._k - b._k || a._o - b._o);
  }
  const all = home ? NSR : ST.length;
  const txt = state.bounds ? T.in_view.replace('{n}', rows.length) : (rows.length === all ? T.count_all : T.count).replace('{n}', rows.length).replace('{all}', all);
  $count.innerHTML = esc(txt + (rgAll && T.rg_count ? ' · ' + T.rg_count.replace('{n}', rgAll) : '') + (cheap ? ' · ' + T.sorted_cheap : ref ? ' · ' + T.sorted_near : '')) + (state.bounds ? ' · <button class="lnkbtn" type="button" data-all>' + esc(T.all_serbia) + '</button>' : '');
  const lim = window.innerWidth <= 900 ? state.lim : Infinity, more = rows.length - lim;
  const html = rows.slice(0, lim).map(s => {
    const k = kind(s), ps = priceShort(s), pw = power(s);
    const sub = [netName(s), place(s), closedNow(s) ? T.closed_now : ''].filter(Boolean).join(' · ') + rating(s);
    const dist = ref ? '<span>' + fmt(s._d, s._d < 10 ? 1 : 0) + ' km</span>' : '';
    return '<button class="st' + (sel === s ? ' is-on' : '') + (ver(s) === 'nep' ? ' is-nep' : '') + '" data-id="' + esc(s.id) + '"><span class="dot ' + k + '">' + (pw ? Math.round(pw) : '') + '</span>' +
      '<span class="nm"><b>' + (isFav(s) ? '<i class="fv">' + STAR + '<span class="sr-only">' + esc(T.fav_sr) + '</span></i>' : '') + esc(title(s)) + badge(s) + '</b><span class="sb">' + esc(sub) + '</span></span><span class="pr ' + ps.cls + '">' + esc(ps.t) + dist + '</span></button>';
  }).join('');
  $list.innerHTML = (html || '<p class="empty">' + esc(state.f === 'fav' && !FAV.size ? T.fav_none : T.none) + '</p>') + (more > 0 ? '<div class="more"><button class="btn sm" type="button" data-more>' + esc(T.more.replace('{n}', more)) + '</button></div>' : '');
  fxList();
}

// ---------- card ----------
function connLine(c) {
  const [type, cur, kw, n] = c;
  return (CONN[type] || type) + ' · ' + cur.toUpperCase() + (kw ? ' · ' + fmt(kw, kw % 1 ? 1 : 0) + ' ' + U.kw : '') + (n > 1 ? ' × ' + n : '');
}
function estHtml(v, s) {
  const e = perKwh(v, s);
  return e ? '<small class="est">' + fxt(T.p_est, { k: [e, fmt(Math.round(e))], w: [null, fmt(Math.round(realKw(power(s), s.dc ? 'dc' : 'ac')))] }) + '</small>' : '';
}
// the evolako.rs link of the "Izdvojeno" line: the page language travels with it (RUNBOOK 3.9)
function evoUrl(campaign) {
  if (!cfg.evo) return '';
  return cfg.evo + '?utm_source=blokvolt&utm_medium=mapa&utm_campaign=' + campaign + (LANG !== 'sr' ? '&lang=' + LANG : '');
}
// "Za vaš auto": cost per km for the reader's car, 100 km, the power the car takes; petrol and home at night beside it;
// a cheaper connector here or a much cheaper charger within 10 km. Without a car: a link to choose one.
function costHtml(s, p) {
  if (s.cc || p.kind === 'free' || p.kind === 'tesla' || p.kind === 'none' || isOff(s)) return '';
  const car = carSpec();
  if (!car) {
    if (!(cfg.cars && (p.kind === 'station' || p.kind === 'exact' || p.kind === 'tier'))) return '';
    return '<p class="cost-pick"><button class="lnkbtn" type="button" data-car-open>' + ICON.car + '<span>' + esc(T.cost_pick) + '</span></button></p>';
  }
  const co = costOf(s);
  if (!co) {
    if (p.kind === 'station' || p.kind === 'exact' || p.kind === 'tier') {
      const why = car.pl === 'chademo' && !dcUsable(s, car) ? T.cost_no_dc : T.cost_na;
      return '<div class="cost na">' + ICON.car + '<div><small>' + esc(why.replace('{car}', carName(car))) + '</small></div></div>';
    }
    return '';
  }
  const m = co.main, km = m.c.km;
  let h = '<div class="cost">' + ICON.car + '<div><b>' + fxt(T.cost_t, { car: [null, carName(car)], x: [km, fmtKm(km)] }) + '</b>' +
    '<small>' + fxt(T.cost_100, { x: [km * 100, fmt(Math.round(km * 100))] }) + ' · ' +
    fxt(T.cost_kw, { w: [null, fmt(Math.round(m.c.kw))], k: [m.c.kwh, fmt(Math.round(m.c.kwh))] }) +
    (co.p.kind === 'station' && co.p.lines.length > 1 ? ' (' + esc(m.t.charger) + ')' : '') + '</small>';
  if (m.t.st) h += '<small>' + fxt(T.cost_start, { s: [m.t.st, fmt(m.t.st)] }) + '</small>';
  if (winterShare()) h += '<small>' + esc(T.cost_winter.replace('{p}', fmt(Math.round((car.wf - 1) * winterShare() * 100)))) + '</small>';
  if (co.alt && co.alt.c.km != null) h += '<small class="tip">' + fxt(T.cost_alt, { c: [null, co.alt.t.charger || (co.alt.cur.toUpperCase() + ' ' + fmt(co.alt.kw) + ' ' + U.kw)], x: [co.alt.c.km, fmtKm(co.alt.c.km)] }) + '</small>';
  const nb = nearCheaper(s, km);
  if (nb) {
    const what = title(nb.s) + ' (' + (nb.s.dc ? 'DC ' + Math.round(nb.s.dc) : 'AC ' + Math.round(nb.s.ac || 0)) + ' ' + U.kw + ')';
    h += '<small class="tip">' + fxt(nb.km ? T.cost_near : T.cost_near_free, { t: [null, what], d: [null, fmtDist(nb.d)], x: [nb.km, fmtKm(nb.km)] }) + '</small>';
  }
  const fb = fuelKm('b'), hm = homeKm(car);
  if (fb && hm.length) h += '<small class="cmp">' + fxt(T.cost_cmp, { b: [fb, fmtKm(fb)], h: [hm.length > 1 ? [Math.min(...hm), Math.max(...hm)] : hm[0], hm.length > 1 ? fmt(Math.min(...hm), 1) + '–' + fmt(Math.max(...hm), 1) : fmt(hm[0], 1)] }) + '</small>';
  return h + '</div></div>';
}
// a charger within 10 km that costs at least 40 % less per km for the reader's car (open now, works, usable by the car)
function nearCheaper(s, km) {
  if (!km) return null;
  let best = null;
  for (const x of ST) {
    if (x === s || x.cc || ver(x) !== 'ok' || !nearUsable(x)) continue;
    if (Math.abs(x.lat - s.lat) > 0.1 || Math.abs(x.lon - s.lon) > 0.14) continue;
    const dkm = distKm(s, x);
    if (dkm > 10) continue;
    const c = isFree(x) ? 0 : (costOf(x) && costOf(x).main.c.km);
    if (c == null || c === false || c > km * 0.6) continue;
    if (!best || c < best.km || (c === best.km && dkm < best.d)) best = { s: x, km: c, d: dkm };
  }
  return best;
}
// "Izdvojeno": charging at home at night, per km for the reader's car (or per kWh), and one link to Evolako
function promoHtml(s, p) {
  if (s.cc || !cfg.evo || !cfg.home || p.kind === 'free' || p.kind === 'tesla' || isOff(s)) return '';
  const car = carSpec(), hm = car ? homeKm(car) : cfg.home;
  const span = hm.length > 1 ? fmt(Math.min(...hm), 1) + '–' + fmt(Math.max(...hm), 1) : fmt(hm[0], 1);
  return '<a class="pmini" href="' + esc(evoUrl('kartica')) + '" rel="noopener" data-evo><span class="badge feat">' + esc(T.promo_badge) + '</span>' +
    '<span>' + fxt(car ? T.promo_km : T.promo_kwh, { h: [hm.length > 1 ? [Math.min(...hm), Math.max(...hm)] : hm[0], span] }) + ' <b>' + esc(T.promo_link) + '</b></span></a>';
}
function priceHtml(s) {
  const p = price(s);
  let h = '<div class="cbox"><span>' + esc(T.price) + '</span>';
  if (p.kind === 'rg') {
    // a neighbouring country: its networks' prices (in its currency, with date and source) are on its blokvolt.com page
    const r = RGC[s.cc];
    return h + (r && r.prices ? '<div><a class="lnk" href="' + esc(r.prices) + '" target="_blank" rel="noopener">' + esc(T.rg_prices.replace('{c}', T['cc_' + s.cc] || '')) + '</a></div>' : '') +
      '<small>' + esc(T.rg_note) + '</small></div>';
  }
  if (p.kind === 'free') {
    h += '<div class="price free">' + esc(p.label || T.p_free) + '</div>' + (p.src ? '<small>' + esc(p.src) + '</small>' : '') + (p.note ? '<small>' + esc(p.note) + '</small>' : '');
  } else if (p.kind === 'tesla') {
    h += '<div class="price">' + esc(T.p_tesla_only) + '</div>' + (p.label ? '<small>' + esc(T.p_tesla_fee.replace('{t}', p.label).replace('{s}', p.src || '')) + '</small>' : '') +
      (p.note ? '<small>' + esc(p.note) + '</small>' : '') + '<small>' + esc(T.p_tesla_hint) + '</small>';
  } else if (p.kind === 'station') {
    // the network's app, connector by connector: the most powerful first
    const t = p.t, rc = freshReceipts(p);
    if (rc) h += '<div class="price">' + esc(rc + ' ' + T.per_kwh) + '</div><small>' + esc(T.p_by_receipt.replace('{d}', [...new Set(p.receipt.map(r => r.date))].join(', '))) + '</small>';
    else h += '<div class="price">' + fxl(t.label, t.fx[0], t.fx[1]) + (p.lines.length > 1 ? ' <span class="pc">' + esc(t.charger) + '</span>' : '') + '</div>' + (carSpec() ? '' : estHtml(t.v, Object.assign({}, s, { dc: t.cur === 'dc' ? t.kw : null, ac: t.cur === 'ac' ? t.kw : null })));
    if (p.lines.length > 1 || rc) h += '<ul class="plines">' + p.lines.map(l => '<li><span>' + esc(l.charger) + (l.n > 1 ? ' × ' + l.n : '') + '</span><b>' + fxl(l.label, l.fx[0], l.fx[1]) + '</b></li>').join('') + '</ul>';
    h += '<small>' + esc(T.p_station.replace('{d}', t.date).replace('{s}', tr(t.src))) + '</small>';
    (p.receipt || []).slice(0, 2).forEach(r => { h += '<small>' + fxt(T.p_receipt, { l: [null, tr(r.label)], k: [r.kwh, fmt(r.kwh)] }) + '</small>'; });
  } else if (p.kind === 'exact' || p.kind === 'tier') {
    const t = p.t, rc = freshReceipts(p);
    const tariff = (p.kind === 'exact' ? T.p_exact : T.p_tier.replace('{c}', t.charger)) + ' · ' + t.date + (t.src ? ' · ' + tr(t.src) : '');
    if (rc) {
      // a receipt from this very charger wins over the network's tariff for the power (the tariff is shown under it)
      h += '<div class="price">' + esc(rc + ' ' + T.per_kwh) + '</div><small>' + esc(T.p_by_receipt.replace('{d}', [...new Set(p.receipt.map(r => r.date))].join(', '))) + '</small>';
      h += '<small>' + esc(tariff + ': ') + fxd(t.label) + '</small>';
    } else {
      h += '<div class="price">' + fxd(t.label) + '</div>' + (carSpec() ? '' : estHtml(t.v, s));
      h += '<small>' + esc(tariff) + '</small>';
    }
    if (t.extra) h += '<small>' + fxd(tr(t.extra)) + '</small>';
    (p.receipt || []).slice(0, 2).forEach(r => { h += '<small>' + fxt(T.p_receipt, { l: [null, tr(r.label)], k: [r.kwh, fmt(r.kwh)] }) + '</small>'; });
  } else if (p.kind === 'range') {
    h += '<div class="price">' + fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + esc(T.per_min) + '</div>';
    const a = perKwh(p.lo.v, s), b = perKwh(p.hi.v, s);
    if (a && b) h += '<small class="est">' + fxt(T.p_est, { k: [[Math.min(a, b), Math.max(a, b)], fmt(Math.round(a)) + '–' + fmt(Math.round(b))], w: [null, fmt(Math.round(realKw(power(s), 'dc')))] }) + '</small>';
    h += '<small>' + esc(T.p_range.replace('{a}', p.lo.charger).replace('{b}', p.hi.charger)) + ' · ' + esc(p.lo.date) + '</small>';
  } else if (p.kind === 'kwh') {
    const t0 = p.list[0];
    h += '<div class="price">' + esc(kwhSpan(p.list, '–') + ' ' + T.per_kwh) + '</div>';
    if (p.list.length > 1 || t0.extra) h += '<ul>' + p.list.map(t => '<li><b>' + fxd(t.label) + '</b>' + (t.extra ? ' — ' + fxd(tr(t.extra)) : '') + '</li>').join('') + '</ul>';
    h += '<small>' + esc(T.p_list.replace('{d}', t0.date || '')) + (t0.src ? ' · ' + esc(tr(t0.src)) : '') + '</small>';
  } else if (p.kind === 'seen') {
    h += '<div>' + esc(T.p_seen) + '</div><ul>' + p.list.slice(0, 3).map(t => '<li><b>' + fxd(t.label) + '</b> — ' + esc(t.charger) + (t.extra ? ', ' + fxd(tr(t.extra)) : '') + '</li>').join('') + '</ul>';
    h += '<small>' + esc(p.note || '') + ' · ' + esc(p.list[0].date) + '</small>';
  } else {
    h += '<div>' + esc(p.text) + '</div>';
  }
  if (p.note && (p.kind === 'exact' || p.kind === 'tier' || p.kind === 'range' || p.kind === 'kwh' || p.kind === 'station')) h += '<small>' + esc(p.note) + '</small>';
  const pd = p.kind === 'exact' || p.kind === 'tier' || p.kind === 'station' ? p.t.date : p.kind === 'range' ? p.lo.date : p.kind === 'seen' || p.kind === 'kwh' ? p.list[0].date :
    p.kind === 'free' ? p.date : '';
  if (stale(pd)) h += '<small class="stale">' + esc(T.p_old) + '</small>';
  const idle = cfg.idle && cfg.idle[(netOf(s) && netOf(s).via) || s.net];
  if (idle && p.kind !== 'free' && p.kind !== 'none') h += '<small>' + esc(T.idle).replace('{x}', fxd(tr(idle))) + '</small>';
  return h + costHtml(s, p) + promoHtml(s, p) + '</div>';
}
// "Kako se puni ovde": the network's steps, payment, without registration, after charging (cene.json: kako) — folded
function kakoHtml(s) {
  if (s.cc) return '';
  const n = netOf(s), k = n && n.kako;
  if (!k) return '';
  const row = (lbl, x) => (x ? '<p><b>' + esc(lbl) + '</b> ' + esc(tr(x)) + '</p>' : '');
  const links = (k.apps || []).map(a => '<a class="lnk" href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(a.l)) + '</a>').join(' · ');
  const src = (k.src || []).map(a => '<a href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(a.l)) + '</a>').join(' · ');
  return '<details class="cbox kako"><summary>' + esc(T.kako_t.replace('{n}', n.name)) + '</summary>' +
    (k.start && k.start.length ? '<ol>' + k.start.map(x => '<li>' + esc(tr(x)) + '</li>').join('') + '</ol>' : '') +
    row(T.kako_pay, k.pay) + row(T.kako_guest, k.guest) + row(T.kako_after, k.after) + row(T.kako_refund, k.refund) +
    (links ? '<p class="kako-apps">' + esc(T.kako_apps) + ' ' + links + '</p>' : '') +
    '<small>' + esc(T.kako_checked.replace('{d}', k.checked || '')) + (src ? ' · ' + src : '') + '</small></details>';
}
function statusHtml(s) {
  if (!s.ps) return '';
  const li = s.ps.l.map(l => '<li class="' + (l[2] === 1 ? 'ok' : 'no') + '"><i></i><span>' + esc([l[0], l[1]].filter(Boolean).join(' · ')) +
    ' · <b>' + esc(l[2] === 1 ? T.st_ok : T.st_off) + '</b>' + (l[3] && T['st_' + l[3]] ? ' (' + esc(T['st_' + l[3]]) + ')' : '') + '</span></li>').join('');
  return '<div class="cbox"><span>' + esc(T.status) + '</span><ul class="stl">' + li + '</ul><small>' + esc(T.st_src.replace('{d}', s.ps.d)) + '</small></div>';
}
const VBY = () => ({ cg: T.v_cg, rm: T.v_rm, te: T.v_te, ps: T.v_ps, g: T.v_g, own: T.v_own });
// hours and access in one row of badges (dopune.json)
function tagsHtml(s) {
  const t = [], car = carSpec();
  if (s.oh && s.oh.t) {
    // the hours, and whether the charger can be used right now (Serbian time)
    const o = openState(s);
    const now = o && !o.h24 ? (o.open ? T.oh_open.replace('{t}', hhmm(o.until)) : T.oh_closed.replace('{t}', o.at != null ? hhmm(o.at) : '?')) : '';
    t.push('<span class="tag' + (s.oh.h24 ? ' ok' : o && !o.open ? ' warn' : '') + '">' + ICON.clock + esc(tr(s.oh.t)) + (now ? ' · ' + esc(now) : '') + '</span>');
  }
  if (s.cab && s.cab.own) t.push('<span class="tag' + (car && !car.cab ? ' warn' : '') + '">' + ICON.cable + esc(T.cab_own) + '</span>');
  if (s.park && s.park.t) t.push('<span class="tag">' + ICON.park + esc(tr(s.park.t)) + '</span>');
  if (s.ax && s.ax.t) t.push('<span class="tag' + (s.ax.who === 'tesla' ? ' warn' : '') + '">' + esc(tr(s.ax.t)) + '</span>');
  if (s.ax && s.ax.limit) t.push('<span class="tag">' + esc(tr(s.ax.limit)) + '</span>');
  return t.length ? '<div class="tags">' + t.join('') + '</div>' : '';
}
function noteHtml(s) { return s.note ? '<p class="cnote">' + ICON.info + '<span>' + esc(tr(s.note)) + '</span></p>' : ''; }
// ---------- exact place: address, coordinates to copy, DMS for older car navigation, Plus Code ----------
function dms(v, pos, neg) {
  const a = Math.abs(v);
  let dg = Math.floor(a), m = Math.floor((a - dg) * 60), sc = Math.round(((a - dg) * 60 - m) * 600) / 10;
  if (sc >= 60) { sc = 0; m += 1; }
  if (m >= 60) { m = 0; dg += 1; }
  return dg + '°' + String(m).padStart(2, '0') + '′' + sc.toFixed(1).padStart(4, '0') + '″' + (v >= 0 ? pos : neg);
}
const OLC = '23456789CFGHJMPQRVWX';
function plusCode(lat, lon) {
  let la = Math.floor((Math.min(Math.max(lat, -90), 89.9999999) + 90) * 8000 + 1e-7);
  let lo = Math.floor(((((lon + 180) % 360) + 360) % 360) * 8000 + 1e-7);
  let c = '';
  for (let i = 0; i < 5; i++) { c = OLC[la % 20] + OLC[lo % 20] + c; la = Math.floor(la / 20); lo = Math.floor(lo / 20); }
  return c.slice(0, 8) + '+' + c.slice(8);
}
// where the point comes from: a network's own list, OpenStreetMap, Open Charge Map, or the car park / building only
function pointQ(s) {
  if (s.loc && s.loc.q) return s.loc.q;
  const pre = s.id.split('-')[0];
  return { cg: 'net', rm: 'net', te: 'net', ps: 'site', osm: 'osm', ocm: 'ocm' }[pre] || '';
}
function whereHtml(s) {
  const L = s.loc || {}, ll = (+s.lat).toFixed(5) + ', ' + (+s.lon).toFixed(5);
  const q = T['q_' + pointQ(s)];
  return '<div class="cbox where"><span>' + esc(T.where) + '</span>' +
    '<p class="w-adr">' + (s.a ? esc(s.a) : '<i>' + esc(T.addr_none) + '</i>') + (L.venue ? '<small>' + esc(tr(L.venue)) + '</small>' : '') + '</p>' +
    (L.find ? '<p class="w-find">' + ICON.pin + '<span>' + esc(tr(L.find)) + '</span></p>' : '') +
    '<div class="w-ll"><code translate="no">' + ll + '</code><button class="btn sm" type="button" data-copy="' + ll + '">' + ICON.copy + '<span>' + esc(T.copy) + '</span></button></div>' +
    '<small translate="no">' + dms(+s.lat, 'N', 'S') + ' ' + dms(+s.lon, 'E', 'W') + ' · Plus Code ' + plusCode(+s.lat, +s.lon) + '</small>' +
    (q ? '<small>' + esc(q) + '</small>' : '') + '</div>';
}
function copyLL(b) {
  const txt = b.dataset.copy, lbl = b.querySelector('span');
  const ok = () => { lbl.textContent = T.copied_ll; setTimeout(() => { if (b.isConnected) lbl.textContent = T.copy; }, 2500); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(ok, () => prompt(T.copy, txt));
  else prompt(T.copy, txt);
}
// "What does the label mean?" → the help article (blokvolt.rs only: cfg.help)
function vHelp() { return cfg.help && T.v_help ? ' · <a class="vf-help" href="' + esc(lp(cfg.help)) + '">' + esc(T.v_help) + '</a>' : ''; }
function verHtml(s) {
  const v = s.v || { s: 'nep', g: 'g_none' };
  if (v.s === 'src') return '<p class="vf vf-src">' + ICON.info + '<span>' + esc(T.v_src) + '</span></p>';
  if (v.s === 'ok') {
    const by = (v.by || []).map(b => VBY()[b]).filter(Boolean).join('; ');
    return '<p class="vf">' + ICON.ok + '<span><b>' + esc(T.v_ok) + '</b> ' + esc(by) + (v.d ? ' · ' + esc(v.d) : '') + vHelp() + '</span></p>';
  }
  const why = v.s === 'prob' ? T.v_prob : (v.g === 'test' ? T.v_test : v.g === 'g_old' ? T.v_old : T.v_none);
  return '<div class="vf-warn' + (v.s === 'prob' ? ' no' : '') + '"><b>' + ICON.warn + esc(v.s === 'prob' ? T.v_prob_t : T.v_nep) + '</b><p>' + esc(why) + '</p><small>' + esc(T.v_checked.replace('{d}', v.d || '')) + vHelp() + '</small></div>';
}
function openCard(s, fly, fromNear) {
  sel = s;
  opened = Date.now();
  nearOpen = false;
  cardNear = !!(fromNear && NEAR);
  const n = netOf(s);
  const logo = n && n.logo ? '<span class="lg w' + (n.logo_dark ? ' dark' : '') + '"><img src="' + esc(n.logo) + '" alt=""></span>' : '<span class="lg w mono" aria-hidden="true">' + esc((netName(s) || '?').slice(0, 2).toUpperCase()) + '</span>';
  const netRole = s.cc ? (s.nn ? T.net_known : T.operator) : n && n.page ? T.net_known : (s.opn && !n ? T.operator : T.net_unknown);
  const netLine = netName(s) ? '<div class="net">' + logo + '<div><b>' + esc(netName(s)) + '</b><span>' + esc(netRole) + '</span></div></div>' : '';
  const conns = s.c.length ? '<div class="cbox"><span>' + esc(T.conn) + '</span><ul>' + s.c.map(c => '<li>' + esc(connLine(c)) +
    (MYDC && c[0] === MYDC ? ' <b class="mine">· ' + esc(T.conn_mine) + '</b>' : '') + '</li>').join('') + '</ul></div>' : '';
  const acc = s.acc === 'customers' ? '<div class="cbox"><span>' + esc(T.access) + '</span><div>' + esc(T.customers) + '</div></div>' : '';
  const navs = navLinks(s);
  // a neighbouring country's station: the button opens it on that country's map on blokvolt.com (prices, the country's networks)
  const rg = s.cc && RGC[s.cc];
  const site = rg ? rg.map + '#' + encodeURIComponent(s.id) : n && n.page ? n.page : (n && n.site ? n.site : '');
  const fix = cfg.fix ? cfg.fix.replace('{id}', encodeURIComponent(s.id)) : lp('/ispravka/?stanica=') + encodeURIComponent(s.id);
  const SRC = { ocm: 'Open Charge Map', osm: 'OpenStreetMap', ps: 'JP Putevi Srbije', cg: 'Charge&GO', rm: T.src_rm, te: 'Tesla', cga: T.src_cga };
  const srcs = s.src.filter(x => x.u).map(x => '<a href="' + esc(x.u) + '" rel="noopener nofollow">' + esc(tr(x.l) || SRC[x.d] || x.d) + '</a>' + (x.upd ? ' (' + esc(x.upd) + ')' : '')).join(' · ');
  $card.innerHTML = '<div class="ccard" role="dialog" aria-label="' + esc(title(s)) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    favBtn(s) + (cardNear ? '<button class="lnkbtn nr-back" type="button" data-nr="back">← ' + esc(T.nr_title) + '</button>' : '') +
    '<h2>' + esc(title(s)) + '</h2><p class="addr">' + esc(place(s)) + '</p>' + verHtml(s) + tagsHtml(s) + netLine + priceHtml(s) + noteHtml(s) + kakoHtml(s) + statusHtml(s) + conns + acc + whereHtml(s) +
    '<div class="acts"><a class="btn dark full" href="' + navs[0][1] + '" target="_blank" rel="noopener" data-nav="' + navs[0][2] + '">' + ICON.nav + esc(T.navigate) + '</a>' +
    '<p class="nav-alt">' + esc(T.nav_in) + ' ' + navs.slice(1).map(x => '<a class="lnk" href="' + x[1] + '" target="_blank" rel="noopener" data-nav="' + x[2] + '">' + x[0] + '</a>').join(' · ') + '</p>' +
    (site ? '<a class="btn' + (rg ? ' full' : '') + '" href="' + esc(site) + '"' + (site[0] === '/' ? '' : ' target="_blank" rel="noopener"') + '>' + ICON.ext + esc(rg ? T.rg_open : n && n.page ? T.about_net : T.site) + '</a>' : '') +
    (rg ? '' : '<a class="btn" href="' + fix + '">' + ICON.flag + esc(T.report) + '</a>') +
    '<button class="btn' + (site ? ' full' : '') + '" type="button" data-share>' + ICON.share + esc(T.share) + '</button></div>' +
    rvHtml(s) +
    '<p class="src">' + esc(T.data) + ': ' + srcs + '</p></div>';
  $card.classList.add('is-open');
  fxCard();
  $card.querySelector('.x').addEventListener('click', closeCard);
  $card.querySelector('.fav').addEventListener('click', () => toggleFav(s));
  $card.querySelector('[data-copy]').addEventListener('click', e => { copyLL(e.currentTarget); track('map_copy_coords', { station: s.id, network: s.net || '' }); });
  $card.querySelector('.acts').addEventListener('click', e => {
    if (e.target.closest('[data-share]')) { shareStation(s); return; }
    const a = e.target.closest('a');
    if (!a) return;
    if (a.dataset.nav) { setNavPref(a.dataset.nav); track('map_navigate', { station: s.id, network: s.net || '', app: a.dataset.nav, from: cardNear ? 'nearest' : 'card' }); }
    else track(s.cc ? 'map_region_link' : a.href.indexOf('/ispravka/') >= 0 || a.href.indexOf('mailto:') === 0 ? 'map_report_error' : 'map_network_link', { station: s.id, network: s.net || '' });
  });
  rvBind(s);
  track('map_card_open', { station: s.id, network: s.net || '', verified: ver(s), favourite: isFav(s) });
  if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [feat(s)] });
  if (fly && map) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 13), speed: 1.4, padding: padding() });
  history.replaceState(null, '', location.pathname + location.search + '#' + s.id);
  renderList();
}
function shareStation(s) {
  const url = location.origin + location.pathname + '#' + encodeURIComponent(s.id);
  const done = how => track('map_share', { station: s.id, network: s.net || '', how });
  if (navigator.share) {
    navigator.share({ title: title(s), text: [title(s), place(s)].filter(Boolean).join(' — '), url }).then(() => done('sheet'), () => {});
    return;
  }
  const b = $card.querySelector('[data-share]');
  const ok = () => { if (b) { b.lastChild.textContent = T.copied; setTimeout(() => { if (b.isConnected) b.lastChild.textContent = T.share; }, 2500); } done('copy'); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(ok, () => prompt(T.share, url));
  else prompt(T.share, url);
}
function favBtn(s) {
  const on = isFav(s);
  return '<button class="fav" type="button" aria-pressed="' + on + '" aria-label="' + esc(on ? T.fav_del : T.fav_add) + '" title="' + esc(on ? T.fav_del : T.fav_add) + '">' + STAR + '</button>';
}
function favCount() {
  const n = d.querySelector('[data-favn]');
  if (n) { n.textContent = FAV.size; n.hidden = !FAV.size; }
}
function toggleFav(s) {
  const on = !FAV.has(s.id);
  if (on) FAV.add(s.id); else FAV.delete(s.id);
  saveFav();
  favCount();
  const b = $card.querySelector('.fav');
  if (b && sel === s) {
    b.setAttribute('aria-pressed', on);
    b.setAttribute('aria-label', on ? T.fav_del : T.fav_add);
    b.title = on ? T.fav_del : T.fav_add;
  }
  track(on ? 'favourite_add' : 'favourite_remove', { station: s.id, network: s.net || '', total: FAV.size });
  if (ACC) accPost('omiljeni', on ? { add: [s.id] } : { remove: [s.id] });
  setData();
  renderList();
}
function closeCard() {
  if (nearOpen && !sel) { closeNear(); return; }
  cardNear = false;
  sel = null;
  $card.classList.remove('is-open');
  $card.innerHTML = '';
  if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [] });
  history.replaceState(null, '', location.pathname + location.search);
  renderList();
}
function padding() {
  return window.innerWidth > 900 ? { left: 0, right: 400, top: 0, bottom: 0 } : { top: 0, bottom: 0, left: 0, right: 0 };
}

// ---------- "Najbliži punjač": the three nearest chargers a driver can use, and a route in a navigation app ----------
// The same rules as the Evolako and BlokVolt apps and evolako.rs/mapa-punjaca: the chip filter counts, the search text and the
// visible part of the map do not; never a charger that does not work, is only for Tesla vehicles (unless "Imam Teslu"), is
// closed now, or that the reader's car cannot use (its DC plug; a Type 2 socket without a cable when the reader has none);
// only confirmed ones unless the reader asks for the rest (or none is confirmed); with "Potvrđeni" on, confirmed only.
// Order: the straight-line distance, then DC ≥ 50 kW, then the name — no network or firm is ever put first.
// The location stays in the browser: nothing is sent and nothing is stored.
let NEAR = null, nearOpen = false, cardNear = false;
const $near = d.getElementById('mnear');
function nearUsable(s) {
  if (isOff(s) || (teslaOnly(s) && !TESLA) || closedNow(s) || !isFinite(s.lat) || !isFinite(s.lon)) return false;
  const car = carSpec();
  if (car) {
    const dcOk = (s.dc || 0) > 0 && dcUsable(s, car);
    const acOk = (s.ac || s.c.some(c => c[1] !== 'dc')) && !(s.cab && s.cab.own && !car.cab);
    if (!dcOk && !acOk) return false;
  }
  return true;
}
function nearestList(pt, withNep) {
  const all = ST.filter(s => nearUsable(s) && matchChip(s, state.f))
    .map(s => ({ s, d: distKm(pt, s) }))
    .sort((a, b) => a.d - b.d || (((b.s.dc || 0) >= 50) - ((a.s.dc || 0) >= 50)) || fold(title(a.s)).localeCompare(fold(title(b.s))));
  const ok = all.filter(x => ver(x.s) === 'ok');
  const every = !state.ok && (withNep || !ok.length);
  const rows = (every ? all : ok).slice(0, 3);
  const last = rows.length ? rows[rows.length - 1].d : Infinity;
  const more = !every && !state.ok && all.some(x => ver(x.s) !== 'ok' && (rows.length < 3 || x.d < last));
  return { rows, every, more };
}
// 230 m · 2,4 km · 17 km (metres rounded to ten)
function fmtDist(km) { const m = Math.round(km * 100) * 10; return m < 1000 ? m + ' ' + U.m : fmt(km, km < 10 ? 1 : 0) + ' ' + U.km; }
function chipLabel(f) {
  const el = $chips.querySelector('[data-f="' + (window.CSS && CSS.escape ? CSS.escape(f) : f) + '"]');
  if (!el) return f;
  const c = el.cloneNode(true);
  c.querySelectorAll('.n, svg').forEach(x => x.remove());
  return c.textContent.trim();
}
function nearRow(x, i) {
  const s = x.s, k = kind(s), pw = power(s), ps = priceShort(s), a = navPref(), dist = fmtDist(x.d), tags = [];
  if (ver(s) !== 'ok') tags.push('<span class="tag warn">' + ICON.warn + esc(ver(s) === 'src' ? T.v_src_short : T.v_nep) + '</span>');
  const o = openState(s);
  if (o && !o.h24 && o.open) tags.push('<span class="tag">' + ICON.clock + esc(T.oh_open.replace('{t}', hhmm(o.until))) + '</span>');
  if (s.cab && s.cab.own) tags.push('<span class="tag">' + ICON.cable + esc(T.cab_own) + '</span>');
  if (s.ax && s.ax.t) tags.push('<span class="tag">' + esc(tr(s.ax.t)) + '</span>');
  else if (s.acc === 'customers') tags.push('<span class="tag">' + esc(T.customers) + '</span>');
  return '<li class="nr' + (i ? '' : ' first') + '">' +
    '<button class="nr-main" type="button" data-open="' + esc(s.id) + '"><span class="dot ' + k + (ver(s) === 'nep' ? ' nep' : '') + '">' + (pw ? Math.round(pw) : '') + '</span>' +
    '<span class="nr-nm"><b>' + esc(title(s)) + '</b><span class="nr-sb">' + esc([netName(s), place(s)].filter(Boolean).join(' · ')) + '</span>' +
    '<span class="nr-meta"><b>' + esc(dist) + '</b>' + (ps.t ? ' · <span class="nr-pr">' + esc(ps.t) + '</span>' : '') + '</span></span></button>' +
    '<a class="btn ' + (i ? 'sm' : 'dark') + ' nr-go" href="' + esc(navUrl(a, s)) + '" target="_blank" rel="noopener" data-nav="' + a + '" data-st="' + esc(s.id) + '" aria-label="' +
    esc(T.nr_nav_to.replace('{t}', title(s)).replace('{d}', dist)) + '">' + ICON.nav + '<span>' + esc(T.navigate) + '</span></a>' +
    (tags.length ? '<div class="tags nr-tags">' + tags.slice(0, 2).join('') + '</div>' : '') + '</li>';
}
function nearChips() {
  const f = state.f, other = f !== 'all' && f !== 'fast';
  return '<div class="nr-chips"><button class="chip" type="button" data-nr="fast" aria-pressed="' + (f === 'fast') + '">' + ICON.bolt + esc(T.nr_fast) + '</button>' +
    (other ? '<button class="chip" type="button" data-nr="all" aria-pressed="true">' + esc(chipLabel(f)) + ' <span aria-hidden="true">✕</span><span class="sr-only">' + esc(T.nr_unfilter) + '</span></button>' : '') + '</div>';
}
// the reader and the chargers of the panel on one screen, clear of the panel on a computer and of the sheet on a phone
function nearFit(pt, rows) {
  if (!map || !pt) return;
  const b = new maplibregl.LngLatBounds([pt.lon, pt.lat], [pt.lon, pt.lat]);
  rows.forEach(x => b.extend([x.s.lon, x.s.lat]));
  const pad = window.innerWidth > 900 ? { top: 70, bottom: 70, left: 60, right: 420 } : { top: 50, bottom: 60, left: 36, right: 36 };
  map.fitBounds(b, { padding: pad, maxZoom: 15, duration: 900 });
}
function showMe() {
  if (map && map.getSource('me')) map.getSource('me').setData({ type: 'FeatureCollection', features: me ? [{ type: 'Feature', geometry: { type: 'Point', coordinates: [me.lon, me.lat] }, properties: {} }] : [] });
}
function nearPanel(o, fit) {
  const was = nearOpen || !!sel;
  if (sel) { sel = null; history.replaceState(null, '', location.pathname + location.search); renderList(); }
  nearOpen = true;
  cardNear = false;
  let body;
  if (o.wait) body = '<p class="nr-wait" role="status"><span class="nr-spin" aria-hidden="true"></span>' + esc(T.nr_wait) + '</p>';
  else if (o.ask) body = '<p class="nr-msg">' + esc(T.nr_ask) + '</p><button class="btn dark nr-cta" type="button" data-nr="go">' + ICON.nav + '<span>' + esc(T.nr_find) + '</span></button>';
  else if (o.err) body = '<p class="nr-msg" role="alert">' + esc(o.err === 'denied' ? T.nr_denied : T.nr_unavail) + '</p><button class="btn nr-cta" type="button" data-nr="go">' + esc(T.nr_retry) + '</button>';
  else {
    const r = nearestList(o.pt, o.withNep), a = navPref(), apps = navApps();
    o.rows = r.rows;
    body = '<p class="addr">' + esc(r.every ? T.nr_sub_all : T.nr_sub) + '</p>' + nearChips() +
      (r.rows.length
        ? '<ol class="nrl">' + r.rows.map(nearRow).join('') + '</ol>' + (r.rows[0].d > 100 ? '<p class="nr-msg">' + esc(T.nr_far) + '</p>' : '')
        : '<p class="nr-msg">' + esc(T.none) + '</p>' + (state.f !== 'all' ? '<button class="btn sm" type="button" data-nr="all">' + esc(T.nr_unfilter) + '</button>' : '')) +
      (r.more ? '<p class="nr-more"><button class="lnkbtn" type="button" data-nr="nep">' + esc(T.nr_nep) + '</button></p>' : '') +
      (r.rows.length && apps.length > 1
        ? '<p class="nr-app">' + esc(T.nr_opens.replace('{a}', NAV_NAME[a])) + ' · <button class="lnkbtn" type="button" data-nr="apps" aria-expanded="false">' + esc(T.nr_change) + '</button></p>' +
          '<div class="nr-apps" hidden>' + apps.map(x => '<button class="chip" type="button" data-app="' + x + '" aria-pressed="' + (x === a) + '">' + NAV_NAME[x] + '</button>').join('') + '</div>'
        : '') +
      '<p class="nr-note">' + esc(T.nr_privacy) + '</p>';
    if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: r.rows.length ? [feat(r.rows[0].s)] : [] });
    if (fit) nearFit(o.pt, r.rows);
    if (!o.tracked) { o.tracked = true; track('map_nearest', { source: o.source || 'button', rows: r.rows.length, filter: state.f, confirmed_only: state.ok, car: !!CAR }); }
  }
  $card.innerHTML = '<div class="ccard nrp" role="dialog" aria-label="' + esc(T.nr_title) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(T.nr_title) + '</h2>' + body + '</div>';
  $card.classList.add('is-open');
  fxCard();
  if (!was) { const x = $card.querySelector('.x'); if (x) x.focus({ preventScroll: true }); }
}
function nearGo(source) {
  const o = NEAR = { pt: null, withNep: false, source };
  if (!navigator.geolocation) { o.err = 'unavail'; nearPanel(o); return; }
  o.wait = true;
  nearPanel(o);
  const btns = d.querySelectorAll('[data-near]');
  btns.forEach(b => { b.disabled = true; });
  navigator.geolocation.getCurrentPosition(pos => {
    btns.forEach(b => { b.disabled = false; });
    if (NEAR !== o) return;
    o.wait = false;
    me = o.pt = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    state.bounds = null;
    state.lim = 20;
    showMe();
    renderList();
    if (nearOpen) nearPanel(o, true);   // not when the panel was closed while the browser was looking for the location
  }, err => {
    btns.forEach(b => { b.disabled = false; });
    if (NEAR !== o) return;
    o.wait = false;
    o.err = err && err.code === 1 ? 'denied' : 'unavail';
    track('map_nearest', { source, ok: false, error: o.err });
    if (nearOpen) nearPanel(o);
  }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 120000 });
}
function closeNear() {
  nearOpen = false;
  $card.classList.remove('is-open');
  $card.innerHTML = '';
  if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [] });
  if (window.innerWidth > 900 && $near) $near.focus({ preventScroll: true });
}
// clicks inside the panel (its HTML is rebuilt on every change) and the "back" link of a card opened from it
function nearClick(t) {
  if (!NEAR) return false;
  if (!nearOpen) {
    if (sel && t.closest('[data-nr="back"]')) { nearPanel(NEAR, false); return true; }
    return false;
  }
  const op = t.closest('[data-open]');
  if (op) { const s = ST.find(x => x.id === op.dataset.open); if (s) openCard(s, true, true); return true; }
  const ap = t.closest('[data-app]');
  if (ap) { setNavPref(ap.dataset.app); nearPanel(NEAR, false); return true; }
  const b = t.closest('[data-nr]');
  if (!b) return false;
  const k = b.dataset.nr;
  if (k === 'go') nearGo(NEAR.source || 'button');
  else if (k === 'fast') { setChip(state.f === 'fast' ? 'all' : 'fast', true); nearPanel(NEAR, true); }
  else if (k === 'all') { setChip('all', true); nearPanel(NEAR, true); }
  else if (k === 'nep') { NEAR.withNep = true; nearPanel(NEAR, true); }
  else if (k === 'apps') {
    const box = $card.querySelector('.nr-apps');
    if (box) { box.hidden = !box.hidden; b.setAttribute('aria-expanded', String(!box.hidden)); }
  }
  return true;
}

// ---------- drivers' reports, ratings and photos (/api, stored in Cloudflare D1) ----------
function ago(t) {
  const days = Math.floor((Date.now() / 1000 - t) / 86400);
  if (days < 1) return T.today;
  if (days < 2) return T.yesterday;
  if (days < 7) return T.days_ago.replace('{n}', days);
  return new Date(t * 1000).toLocaleDateString(LOC, { day: 'numeric', month: 'numeric', year: 'numeric' });
}
function starBar(r) {
  const n = Math.round(r);
  return '<span class="sb5" aria-hidden="true">' + '★★★★★'.slice(0, n) + '<i>' + '★★★★★'.slice(n) + '</i></span>';
}
function rvSum(s) {
  const c = CI[s.id];
  // no data yet: say nothing while loading, and do not claim "no reports" when the reports could not be loaded
  if (!c && CI_STATE === 'loading') return '<p class="rv-empty"></p>';
  if (!c && CI_STATE === 'off') return '<p class="rv-empty">' + esc(T.rv_off || T.rv_empty) + '</p>';
  if (!c || !c.n) return '<p class="rv-empty">' + esc(T.rv_empty) + '</p>';
  return '<div class="rv-sum">' + (c.a ? '<b>' + fmt(c.a, 1) + '</b>' + starBar(c.a) + '<span>' + esc(T.ratings.replace('{n}', c.nr)) + '</span>' : '') +
    (c.s ? '<span class="rv-last ' + esc(c.s) + '">' + esc(T.last_report) + ': <b>' + esc(ST_LABEL[c.s] || c.s) + '</b>, ' + esc(ago(c.t)) + '</span>' : '') + '</div>';
}
// what went wrong (with "Radi, uz problem" / "Ne radi") and three one-tap questions after a report: cable, parking, hours.
// Each answer is one row in /api (station, field, value, day's fingerprint); the card shows an answer once two different
// drivers gave it in the last 60 days and it outweighs the other one (worker: summaryOne → facts).
const WHY = ['busy', 'broken', 'app', 'cable', 'closed', 'short'];
const FACTS = [['cab', ['att', 'own']], ['park', ['free', 'paid']], ['oh', ['24', 'lim']]];
function factsAsk(s) {
  const qs = FACTS.filter(([f]) => f !== 'cab' || s.ac || s.c.some(c => c[1] !== 'dc'));
  return '<div class="rv-facts" hidden><p>' + esc(T.f_q) + '</p>' + qs.map(([f, vs]) => '<div class="rv-frow" data-fact="' + f + '"><span>' + esc(T['f_' + f]) + '</span>' +
    vs.map(v => '<button type="button" class="chip" data-v="' + v + '" aria-pressed="false">' + esc(T['f_' + f + '_' + v]) + '</button>').join('') + '</div>').join('') + '</div>';
}
function factsSeen(j) {
  const out = [], by = {};
  (j.facts || []).forEach(x => { (by[x.f] = by[x.f] || []).push(x); });
  FACTS.forEach(([f, vs]) => {
    const rows = (by[f] || []).filter(x => vs.indexOf(x.v) >= 0).sort((a, b) => b.n - a.n);
    if (rows.length && rows[0].n >= 2 && (!rows[1] || rows[0].n > rows[1].n)) out.push(T['f_' + f] + ': ' + T['f_' + f + '_' + rows[0].v] + ' (' + T.f_by.replace('{n}', rows[0].n) + ')');
  });
  const why = (by.why || []).filter(x => x.n >= 2 && WHY.indexOf(x.v) >= 0).sort((a, b) => b.n - a.n);
  if (why.length) out.push(T.why_seen.replace('{x}', why.slice(0, 2).map(x => T['why_' + x.v] + ' ×' + x.n).join(', ')));
  return out.length ? '<ul class="rv-seen">' + out.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul>' : '';
}
function rvHtml(s) {
  if (!cfg.api || s.cc) return '';
  const starsIn = [1, 2, 3, 4, 5].map(i => '<button type="button" data-r="' + i + '" aria-label="' + i + '/5" aria-pressed="false">★</button>').join('');
  return '<div class="cbox rv"><span>' + esc(T.rv_title) + '</span><div class="rv-top">' + rvSum(s) + '</div>' +
    '<p class="rv-q">' + esc(T.rv_q) + '</p><div class="rv-btns">' +
    ['ok', 'problem', 'broken', 'missing'].map(k => '<button type="button" class="chip" data-ci="' + k + '" aria-pressed="false">' + esc(ST_LABEL[k]) + '</button>').join('') + '</div>' +
    '<form class="rv-form" hidden novalidate>' +
    '<div class="rv-why" hidden><span>' + esc(T.why_q) + '</span><div class="rv-chips">' + WHY.map(k => '<button type="button" class="chip" data-why="' + k + '" aria-pressed="false">' + esc(T['why_' + k]) + '</button>').join('') + '</div></div>' +
    '<div class="rv-stars" role="group" aria-label="' + esc(T.rv_rate) + '"><span>' + esc(T.rv_rate) + '</span>' + starsIn + '</div>' +
    '<label class="sr-only" for="rv-c">' + esc(T.rv_comment) + '</label><textarea class="input" id="rv-c" maxlength="500" rows="3" placeholder="' + esc(T.rv_comment_ph) + '"></textarea>' +
    '<label class="sr-only" for="rv-n">' + esc(T.rv_name) + '</label><input class="input" id="rv-n" maxlength="40" autocomplete="nickname" placeholder="' + esc(T.rv_name) + '">' +
    '<input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">' +
    '<div class="rv-row"><button class="btn dark sm" type="submit">' + esc(T.rv_send) + '</button><button class="btn sm" type="button" data-cancel>' + esc(T.rv_cancel) + '</button></div>' +
    '<small>' + esc(T.rv_rules) + ' <a href="' + esc(lp('/pravila-objavljivanja/')) + '">' + esc(T.rv_rules_link) + '</a></small></form>' +
    '<p class="rv-msg" role="status" aria-live="polite"></p>' + factsAsk(s) + '<div class="rv-list"></div>' +
    '<div class="rv-ph"><div class="rv-thumbs"></div><label class="btn sm rv-add">' + ICON.cam + '<span>' + esc(T.add_photo) + '</span>' +
    '<input type="file" accept="image/*" hidden></label><small class="rv-phnote">' + esc(T.photo_note) + '</small></div></div>';
}
function rvItems(j) {
  const its = (j.items || []).slice(0, 8);
  if (!its.length) return '';
  return '<ul class="rv-its">' + its.map(it => '<li><div class="rv-h"><span class="rv-s ' + esc(it.s) + '">' + esc(ST_LABEL[it.s] || it.s) + '</span>' + (it.r ? starBar(it.r) : '') +
    '<time>' + esc(ago(it.at)) + '</time></div>' + (it.c ? '<p>' + esc(it.c) + '</p>' : '') + (it.n ? '<small>— ' + esc(it.n) + '</small>' : '') +
    (it.c ? '<button class="lnkbtn rv-rep" type="button" data-rep="' + it.id + '">' + esc(T.report_abuse) + '</button>' : '') + '</li>').join('') + '</ul>';
}
function rvLoad(s, box) {
  // the reports could not be loaded (offline, server error): say so instead of "no reports yet"
  const off = () => { if (sel === s && box.isConnected && !(CI[s.id] && CI[s.id].n)) box.querySelector('.rv-top').innerHTML = '<p class="rv-empty">' + esc(T.rv_off || T.rv_empty) + '</p>'; };
  fetch(cfg.api + '/stanica/' + encodeURIComponent(s.id)).then(r => r.ok ? r.json() : null).then(j => {
    if (sel !== s) return;
    if (!j || !j.ok) { off(); return; }
    CI[s.id] = { a: j.avg, nr: j.nr, n: j.n, s: j.items[0] && j.items[0].s, t: j.items[0] && j.items[0].at, f: j.photos.length, fs: factsSeen(j) };
    box.querySelector('.rv-top').innerHTML = rvSum(s) + CI[s.id].fs;
    box.querySelector('.rv-list').innerHTML = rvItems(j);
    box.querySelector('.rv-thumbs').innerHTML = j.photos.map(p => '<button class="rv-th" type="button" data-full="' + cfg.api + '/foto/' + p.id + '.jpg"><img src="' + cfg.api + '/foto/' + p.id + '.jpg?v=t" alt="' + esc(p.cap || T.photo_alt) + '" loading="lazy" width="96" height="72"></button>').join('');
  }).catch(off);
}
function post(url, body, isForm) {
  return fetch(url, isForm ? { method: 'POST', body } : { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
    .then(r => r.json().catch(() => ({ ok: false })).then(j => (j.status = r.status, j)));
}
// 429 means three different things; each gets its own words
function errText(j) {
  if (j.status !== 429) return T.rv_err;
  if (j.error === 'too fast') return T.rv_fast || T.rv_err;
  if (j.error === 'queue full') return T.photo_queue || T.rv_limit;
  return T.rv_limit;
}
function rvBind(s) {
  const box = $card.querySelector('.rv');
  if (!box) return;
  const form = box.querySelector('.rv-form'), msg = box.querySelector('.rv-msg');
  let status = '', r = 0;
  let why = '';
  const whyBox = box.querySelector('.rv-why');
  box.querySelector('.rv-btns').addEventListener('click', e => {
    const b = e.target.closest('[data-ci]');
    if (!b) return;
    status = b.dataset.ci;
    box.querySelectorAll('[data-ci]').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
    form.hidden = false;
    whyBox.hidden = !(status === 'problem' || status === 'broken');
    if (whyBox.hidden) { why = ''; whyBox.querySelectorAll('[data-why]').forEach(x => x.setAttribute('aria-pressed', 'false')); }
    msg.textContent = '';
    form.querySelector('textarea').focus({ preventScroll: true });
  });
  whyBox.addEventListener('click', e => {
    const b = e.target.closest('[data-why]');
    if (!b) return;
    why = why === b.dataset.why ? '' : b.dataset.why;
    whyBox.querySelectorAll('[data-why]').forEach(x => x.setAttribute('aria-pressed', x.dataset.why === why ? 'true' : 'false'));
  });
  const facts = box.querySelector('.rv-facts');
  if (facts) facts.addEventListener('click', e => {
    const b = e.target.closest('[data-v]'), row = b && b.closest('[data-fact]');
    if (!row || row.classList.contains('is-done')) return;
    row.classList.add('is-done');
    row.querySelectorAll('[data-v]').forEach(x => { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); x.disabled = true; });
    post(cfg.api + '/stanica/' + encodeURIComponent(s.id) + '/podatak', { f: row.dataset.fact, v: b.dataset.v, hp: '', t: Date.now() - opened })
      .then(j => { if (!j.ok) { row.classList.remove('is-done'); row.querySelectorAll('[data-v]').forEach(x => { x.disabled = false; }); return; } track('fact_sent', { station: s.id, field: row.dataset.fact, value: b.dataset.v }); })
      .catch(() => { row.classList.remove('is-done'); row.querySelectorAll('[data-v]').forEach(x => { x.disabled = false; }); });
  });
  box.querySelector('.rv-stars').addEventListener('click', e => {
    const b = e.target.closest('[data-r]');
    if (!b) return;
    r = +b.dataset.r === r ? 0 : +b.dataset.r;
    box.querySelectorAll('[data-r]').forEach(x => x.setAttribute('aria-pressed', +x.dataset.r <= r ? 'true' : 'false'));
  });
  form.querySelector('[data-cancel]').addEventListener('click', () => { form.hidden = true; box.querySelectorAll('[data-ci]').forEach(x => x.setAttribute('aria-pressed', 'false')); });
  form.addEventListener('submit', e => {
    e.preventDefault();
    if (!status) return;
    const btn = form.querySelector('[type=submit]');
    btn.disabled = true;
    post(cfg.api + '/stanica/' + encodeURIComponent(s.id) + '/prijava', {
      s: status, r: r || null, c: form.querySelector('textarea').value, n: form.querySelector('#rv-n').value,
      why: (status === 'problem' || status === 'broken') && why ? why : null,
      hp: form.querySelector('.hp').value, t: Date.now() - opened, lang: LANG
    }).then(j => {
      btn.disabled = false;
      if (!j.ok) { msg.textContent = errText(j); return; }
      form.hidden = true;
      track('checkin_sent', { station: s.id, network: s.net || '', status, rating: r || 0, comment: !!form.querySelector('textarea').value.trim(), reason: why || '' });
      form.reset(); r = 0; why = '';
      msg.textContent = j.pending ? T.rv_thanks_pending : T.rv_thanks;
      if (facts && status !== 'missing') facts.hidden = false;
      rvLoad(s, box);
    }).catch(() => { btn.disabled = false; msg.textContent = T.rv_err; });
  });
  box.querySelector('.rv-list').addEventListener('click', e => {
    const b = e.target.closest('[data-rep]');
    if (!b) return;
    post(cfg.api + '/prijavi', { t: 'c', id: +b.dataset.rep }).then(() => { b.textContent = T.reported; b.disabled = true; }).catch(() => {});
  });
  box.querySelector('.rv-thumbs').addEventListener('click', e => { const b = e.target.closest('[data-full]'); if (b) lightbox(b.dataset.full, b.querySelector('img').alt); });
  box.querySelector('.rv-add input').addEventListener('change', e => {
    const f = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!f) return;
    const note = box.querySelector('.rv-phnote');
    note.textContent = T.photo_wait;
    // a picture the browser cannot open (e.g. HEIC on a computer) and a failed upload are different problems
    shrink(f).catch(() => null).then(p => {
      if (!p) { note.textContent = T.photo_bad; return; }
      const fd = new FormData();
      fd.append('foto', p.big, 'foto.jpg');
      fd.append('thumb', p.th, 'thumb.jpg');
      fd.append('w', p.w); fd.append('h', p.h); fd.append('t', Date.now() - opened); fd.append('hp', '');
      return post(cfg.api + '/stanica/' + encodeURIComponent(s.id) + '/foto', fd, true)
        .then(j => { note.textContent = j.ok ? T.photo_thanks : errText(j); if (j.ok) track('photo_sent', { station: s.id, network: s.net || '' }); });
    }).catch(() => { note.textContent = T.rv_err; });
  });
  rvLoad(s, box);
}
// photos are re-encoded in the browser: at most 1600 px, JPEG, without EXIF (no GPS or camera data leaves the phone)
function loadImg(file) {
  return new Promise((ok, no) => {
    const u = URL.createObjectURL(file), im = new Image();
    im.onload = () => { URL.revokeObjectURL(u); ok(im); };
    im.onerror = () => { URL.revokeObjectURL(u); no(new Error('img')); };
    im.src = u;
  });
}
function scaled(im, max) {
  const k = Math.min(1, max / Math.max(im.naturalWidth, im.naturalHeight));
  const c = d.createElement('canvas');
  c.width = Math.round(im.naturalWidth * k); c.height = Math.round(im.naturalHeight * k);
  c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
  return c;
}
const blob = (c, q) => new Promise(ok => c.toBlob(ok, 'image/jpeg', q));
async function shrink(file) {
  const im = await loadImg(file);
  const big = scaled(im, 1600), th = scaled(im, 360);
  let q = 0.82, b = await blob(big, q);
  while (b && b.size > 900 * 1024 && q > 0.45) { q -= 0.12; b = await blob(big, q); }
  const t = await blob(th, 0.7);
  if (!b || !t) throw new Error('encode');
  return { big: b, th: t, w: big.width, h: big.height };
}
function lightbox(src, alt) {
  const lb = d.createElement('div');
  lb.className = 'lb';
  lb.setAttribute('role', 'dialog');
  lb.innerHTML = '<button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button><img src="' + esc(src) + '" alt="' + esc(alt || '') + '">' +
    '<button class="lnkbtn lb-rep" type="button">' + esc(T.report_photo) + '</button>';
  const close = () => { lb.remove(); d.removeEventListener('keydown', key); };
  const key = e => { if (e.key === 'Escape') close(); };
  lb.addEventListener('click', e => { if (e.target === lb || e.target.closest('.x')) close(); });
  lb.querySelector('.lb-rep').addEventListener('click', e => {
    const id = (src.match(/[0-9a-f]{32}/) || [])[0];
    if (id) post(cfg.api + '/prijavi', { t: 'f', id }).then(() => { e.target.textContent = T.reported; e.target.disabled = true; }).catch(() => {});
  });
  d.addEventListener('keydown', key);
  d.body.appendChild(lb);
  lb.querySelector('.x').focus();
}
function loadSummaries() {
  if (!cfg.api) return;
  const off = () => {
    CI_STATE = 'off';
    const top = sel && $card.querySelector('.rv-top');
    if (top && !CI[sel.id]) top.innerHTML = rvSum(sel);
  };
  fetch(cfg.api + '/stanice').then(r => r.ok ? r.json() : null).then(j => {
    if (!j || !j.ok) { off(); return; }
    CI = Object.assign(j.st || {}, CI);
    CI_STATE = 'ok';
    renderList();
    const top = sel && $card.querySelector('.rv-top');
    if (top) top.innerHTML = rvSum(sel) + ((CI[sel.id] && CI[sel.id].fs) || '');
  }).catch(off);
}

// ---------- display currency (blokvolt.rs only: window.bvFx from /assets/valuta.js; docs/RUNBOOK.md 3.29) ----------
// Prices stay in RSD here; a reader who chose EUR or USD sees them converted: in the card in full (≈ € first, RSD after) —
// the price, every connector's price, "Za vaš auto" (RSD/km, 100 km, per kWh, start fee, cheaper nearby, petrol and home),
// the estimate, receipts, extras and idle fees; in the list, "Najbliži punjač" and the labels next to the pins only
// converted (RSD in the tooltip and the card). The country maps of blokvolt.com (cfg.cur, their own currency, no
// window.bvFx) and the neighbouring countries' layer are never converted: there every helper returns the plain text.
const FX = !cfg.cur && window.bvFx ? window.bvFx : null;
// Every price is marked as <span class="fxm"> around its text exactly as written ("≈ 8,4 RSD/km", "0,7–1,0 RSD/km",
// "≈ 52 RSD po kWh"); fx.js reads the number from that text, so the dinars shown after the euros are the same as with
// RSD (rounding, "≈", ranges) and a value is never converted twice (a converted span is skipped by the next scan).
const fxOk = v => (Array.isArray(v) ? v.every(x => x != null && isFinite(x)) : v != null && isFinite(v));
const fxm = h => '<span class="fxm">' + h + '</span>';
// a price whose number the map knows: "16,67 RSD/min" (v = 16.67; no number → plain text)
function fxl(text, v) {
  return FX && fxOk(v) ? fxm(esc(text)) : esc(text);
}
// a translated sentence with prices in it (T.cost_t "Za vaš {car}: ≈ {x} RSD/km"): each placeholder with its "≈" and the
// "RSD…" after it becomes one marked price. vals: {key: [number or [lo, hi] or null, text]}; null = not a price.
// A translation that words it differently keeps the dinars (nothing breaks).
function fxt(tpl, vals) {
  let h = esc(tpl);
  Object.keys(vals).forEach(k => {
    const v = vals[k][0], txt = esc(vals[k][1]);
    h = h.replace(new RegExp('(≈ )?\\{' + k + '\\}( RSD(?:/[^\\s.,;:)]+| po kWh| per kWh| за кВт·ч)?)?'), (m, ap, u) => {
      const plain = (ap || '') + txt + (u || '');
      return FX && u && fxOk(v) ? fxm(plain) : plain;
    });
  });
  return h;
}
// a text from the price data (Serbian numbers whatever the page language: "+ 50 RSD priključenje", "1.000 RSD/sat")
const FX_TOK = /(^|[^\w.,\-–])((?:≈ ?)?(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)(?:\s*[–-]\s*(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?))?\s*RSD(?!\s*\/\s*(?:€|\$|EUR|USD))(?:\/(?:kWh|min|sat|h|km|кВт·ч|мин|ч|км))?)(?![\wčćšđž])/g;
function fxd(text) {
  const h = esc(text);
  return FX ? h.replace(FX_TOK, (m, pre, all) => pre + fxm(all)) : h;
}
function fxCard() {
  if (!FX) return;
  FX.scan($card, { selector: '.price, .fxm' });           // ≈ € first, RSD after (.price: a line that is only a price, e.g. by receipts)
  FX.scan($card, { selector: '.nr-pr', compact: true });  // "Najbliži punjač": converted only, as in the list
}
function fxList() {
  if (!FX) return;
  [].forEach.call($list.querySelectorAll('.st .pr'), el => {      // the price is the first text of .pr (a distance may follow)
    const t = el.firstChild;
    if (t && t.nodeType === 3 && t.nodeValue.indexOf('RSD') >= 0) { const w = d.createElement('i'); w.className = 'fxw'; el.insertBefore(w, t); w.appendChild(t); }
  });
  FX.scan($list, { selector: '.fxw', compact: true });
}
// a pin label (ASCII only, see pinPrice): "~68 RSD/kWh" → "~0,58 EUR/kWh", "~9,4 RSD/km" → "~0,080 EUR/km"
function fxPin(t) {
  if (!FX || !t || FX.get() === 'RSD') return t;
  const m = /^(~?)(\d+(?:[.,]\d+)?)(?:-(\d+(?:[.,]\d+)?))? RSD(\/kWh|\/km)?$/.exec(t);
  if (!m) return t;
  const n = x => Number(x.replace(',', '.')), lo = n(m[2]), hi = m[3] ? n(m[3]) : null, o = { unit: m[4] || '', compact: true, rate: true };
  const r = hi != null && hi !== lo ? FX.range(lo, hi, o) : FX.money(lo, o);
  return r.primary.replace(/ /g, ' ').replace('≈ ', '~').replace('–', '-').replace('€', 'EUR').replace('$', 'USD');
}
if (FX) FX.on(() => { setData(); fxList(); fxCard(); });

// ---------- map ----------
function feat(s) {
  const v = ver(s), k = kind(s), p = k === 'tesla' ? 'T' : (Math.round(power(s)) || ''), pp = pinPrice(s);
  // a charger that is closed now (its hours, oh.w) is drawn faded like an unconfirmed one
  return { type: 'Feature', id: s._i, geometry: { type: 'Point', coordinates: [s.lon, s.lat] },
    properties: { id: s.id, k, v: closedNow(s) && v !== 'nep' ? 'cl' : v, p: v === 'nep' && k !== 'tesla' ? p + '?' : p, f: FAV.has(s.id) ? 1 : 0, pl: fxPin(pp.t), pc: pp.c } };
}
// Serbia and the neighbouring countries are two sources: the neighbours are drawn quieter and cluster on their own
function data(rg) { return { type: 'FeatureCollection', features: visible().filter(s => !s.cc === !rg).map(feat) }; }
function setData() {
  if (map && map.getSource('st')) map.getSource('st').setData(data());
  if (map && map.getSource('rg')) map.getSource('rg').setData(data(true));
}
function refresh() {
  state.lim = 20;
  setData();
  renderList();
}
function initMap() {
  map = new maplibregl.Map({
    container: 'map', style: cfg.style, center: C0, zoom: Z0, minZoom: 5, maxZoom: 18,
    attributionControl: false, cooperativeGestures: false, dragRotate: false, pitchWithRotate: false
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.on('load', () => {
    const font = cfg.font;
    if (NRG) {
      // the neighbouring countries under Serbia's layers: grey clusters and white points with a grey ring
      map.addSource('rg', { type: 'geojson', data: data(true), cluster: true, clusterRadius: 42, clusterMaxZoom: 11 });
      map.addLayer({ id: 'rg-cl', type: 'circle', source: 'rg', filter: ['has', 'point_count'],
        paint: { 'circle-color': '#FFFFFF', 'circle-opacity': 0.92, 'circle-radius': ['step', ['get', 'point_count'], 14, 10, 18, 30, 22], 'circle-stroke-width': 2.5, 'circle-stroke-color': '#8A909B' } });
      map.addLayer({ id: 'rg-cl-n', type: 'symbol', source: 'rg', filter: ['has', 'point_count'],
        layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': font, 'text-size': 12, 'text-allow-overlap': true },
        paint: { 'text-color': '#3A3F4A' } });
      map.addLayer({ id: 'rg-pt', type: 'circle', source: 'rg', filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 5, 12, 8, 16, 11],
          'circle-color': ['match', ['get', 'k'], 'dc', '#5C6270', '#FFFFFF'], 'circle-opacity': 0.85,
          'circle-stroke-width': 2, 'circle-stroke-color': '#8A909B'
        } });
      map.addLayer({ id: 'rg-kw', type: 'symbol', source: 'rg', filter: ['!', ['has', 'point_count']], minzoom: 12,
        layout: { 'text-field': ['to-string', ['get', 'p']], 'text-font': font, 'text-size': 10, 'text-allow-overlap': true },
        paint: { 'text-color': ['match', ['get', 'k'], 'dc', '#FFFFFF', '#3A3F4A'] } });
      map.on('click', 'rg-cl', e => {
        userMove = true;
        const f = e.features[0];
        map.getSource('rg').getClusterExpansionZoom(f.properties.cluster_id).then(z => map.easeTo({ center: f.geometry.coordinates, zoom: z + 0.3 }));
      });
      map.on('click', 'rg-pt', e => { const s = ST.find(x => x.id === e.features[0].properties.id); if (s) openCard(s, false); });
      ['rg-cl', 'rg-pt'].forEach(l => {
        map.on('mouseenter', l, () => { map.getCanvas().style.cursor = 'pointer'; });
        map.on('mouseleave', l, () => { map.getCanvas().style.cursor = ''; });
      });
    }
    map.addSource('st', { type: 'geojson', data: data(), cluster: true, clusterRadius: 42, clusterMaxZoom: 11 });
    map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addSource('me', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    const nep = ['any', ['==', ['get', 'v'], 'nep'], ['==', ['get', 'v'], 'cl']];
    map.addLayer({ id: 'cl', type: 'circle', source: 'st', filter: ['has', 'point_count'],
      paint: { 'circle-color': '#0D111A', 'circle-radius': ['step', ['get', 'point_count'], 15, 10, 19, 30, 24], 'circle-stroke-width': 3, 'circle-stroke-color': 'rgba(217,244,91,.55)' } });
    map.addLayer({ id: 'cl-n', type: 'symbol', source: 'st', filter: ['has', 'point_count'],
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': font, 'text-size': 13, 'text-allow-overlap': true },
      paint: { 'text-color': '#FFFFFF' } });
    map.addLayer({ id: 'pt', type: 'circle', source: 'st', filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 6, 12, 9, 16, 12],
        'circle-color': ['match', ['get', 'k'], 'dc', '#0D111A', 'free', '#D9F45B', 'off', '#E3E5E9', 'tesla', '#E3E5E9', '#FFFFFF'],
        'circle-opacity': ['case', nep, 0.5, 1],
        'circle-stroke-width': 2.5,
        'circle-stroke-opacity': ['case', nep, 0.55, 1],
        'circle-stroke-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#8A909B', 'tesla', '#5C6270', '#0D111A']
      } });
    // favourites: a ring around the point
    map.addLayer({ id: 'pt-fav', type: 'circle', source: 'st', filter: ['all', ['!', ['has', 'point_count']], ['==', ['get', 'f'], 1]],
      paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 10, 12, 14, 16, 17], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-width': 2.5, 'circle-stroke-color': '#6E8A12' } });
    map.addLayer({ id: 'pt-kw', type: 'symbol', source: 'st', filter: ['!', ['has', 'point_count']], minzoom: 12,
      layout: { 'text-field': ['to-string', ['get', 'p']], 'text-font': font, 'text-size': 10, 'text-allow-overlap': true },
      paint: { 'text-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#5C6270', 'tesla', '#3A3F4A', '#0D111A'] } });
    // price next to the pin from zoom 12: 0 RSD / RSD per kWh from a receipt / ~ estimate from the per-minute tariff / ?
    map.addLayer({ id: 'pt-pr', type: 'symbol', source: 'st', filter: ['all', ['!', ['has', 'point_count']], ['!=', ['get', 'pl'], '']], minzoom: 12,
      layout: { 'text-field': ['get', 'pl'], 'text-font': font, 'text-size': 11.5, 'text-anchor': 'left', 'text-offset': [1.25, 0], 'text-padding': 2 },
      paint: { 'text-color': ['match', ['get', 'pc'], 'free', '#3F5206', 'old', '#8A909B', 'unk', '#8A909B', '#0D111A'], 'text-halo-color': '#FFFFFF', 'text-halo-width': 2.4 } });
    map.addLayer({ id: 'sel', type: 'circle', source: 'sel',
      paint: { 'circle-radius': 16, 'circle-color': 'rgba(217,244,91,.35)', 'circle-stroke-width': 3, 'circle-stroke-color': '#0D111A' } }, 'pt');
    // the reader's own position ("Blizu mene", "Najbliži punjač"): a blue dot, never sent anywhere
    map.addLayer({ id: 'me-halo', type: 'circle', source: 'me', paint: { 'circle-radius': 22, 'circle-color': 'rgba(46,107,255,.16)' } });
    map.addLayer({ id: 'me-dot', type: 'circle', source: 'me', paint: { 'circle-radius': 7, 'circle-color': '#FFFFFF', 'circle-stroke-width': 4, 'circle-stroke-color': '#2E6BFF' } });
    showMe();
    if (nearOpen && NEAR && NEAR.rows) {
      map.getSource('sel').setData({ type: 'FeatureCollection', features: NEAR.rows.length ? [feat(NEAR.rows[0].s)] : [] });
      nearFit(NEAR.pt, NEAR.rows);
    }
    map.on('moveend', e => {
      if (!e.originalEvent && !userMove) return;
      userMove = false;
      if (map.getZoom() >= 8) {
        const b = map.getBounds();
        state.bounds = { s: b.getSouth(), n: b.getNorth(), w: b.getWest(), e: b.getEast() };
      } else state.bounds = null;
      renderList();
    });
    map.on('click', 'cl', e => {
      userMove = true;
      const f = e.features[0];
      map.getSource('st').getClusterExpansionZoom(f.properties.cluster_id).then(z => map.easeTo({ center: f.geometry.coordinates, zoom: z + 0.3 }));
    });
    map.on('click', 'pt', e => { const s = ST.find(x => x.id === e.features[0].properties.id); if (s) openCard(s, false); });
    ['cl', 'pt'].forEach(l => {
      map.on('mouseenter', l, () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', l, () => { map.getCanvas().style.cursor = ''; });
    });
    if (sel) {
      map.getSource('sel').setData({ type: 'FeatureCollection', features: [feat(sel)] });
      map.jumpTo({ center: [sel.lon, sel.lat], zoom: 13, padding: padding() });
    } else if (city) map.jumpTo({ center: [city.lon, city.lat], zoom: 11.2 });
  });
}

// ---------- controls ----------
function paintChips() {
  [].forEach.call($chips.querySelectorAll('.chip'), c =>
    c.setAttribute('aria-pressed', (c.dataset.f === 'ok' ? state.ok : c.dataset.f === 'tesla' ? TESLA : c.dataset.f === 'cheap' ? state.cheap : c.dataset.f === state.f) ? 'true' : 'false'));
}
// "Imam Teslu" is a switch like "Potvrđeni": kept in this browser, it changes which chargers are free and usable
function setTesla(on, quiet, keep) {
  TESLA = on;
  COSTV++;
  if (!keep) saveTesla();
  if (!quiet) track('map_tesla', { on });
  if (!quiet && ACC) accPost('podesavanja', { tesla: on });
  paintChips();
  refresh();
  if (sel) openCard(sel, false, cardNear);
}
function setChip(f, quiet) {
  state.f = f;
  if (!quiet) track('map_filter', { filter: f, confirmed_only: state.ok, favourites: FAV.size });
  paintChips();
  refresh();
}
// "Potvrđeni" is a switch that works together with any other chip (fast + confirmed, a network + confirmed …)
function setOk(on, quiet) {
  state.ok = on;
  if (!quiet) track('map_filter', { filter: state.f, confirmed_only: on, favourites: FAV.size });
  paintChips();
  refresh();
}
$chips.addEventListener('click', e => {
  const c = e.target.closest('.chip');
  if (!c) return;
  if (c.dataset.f === 'ok') setOk(!state.ok);
  else if (c.dataset.f === 'tesla') setTesla(!TESLA);
  else if (c.dataset.f === 'cheap') { state.cheap = !state.cheap; track('map_sort', { cheapest: state.cheap }); paintChips(); refresh(); }
  else setChip(c.dataset.f);
});
$count.addEventListener('click', e => {
  if (!e.target.closest('[data-all]')) return;
  state.bounds = null; me = null; city = null;
  showMe();
  if (map) map.flyTo({ center: C0, zoom: Z0 });
  renderList();
});
let qt;
let qTrack;
$q.addEventListener('input', () => {
  clearTimeout(qt); clearTimeout(qTrack);
  qt = setTimeout(() => { state.q = $q.value.trim(); refresh(); }, 120);
  // one event per finished query (the reader stopped typing), not per keystroke
  qTrack = setTimeout(() => { const q = $q.value.trim(); if (q.length >= 3) track('map_search', { query: q.slice(0, 60), results: visible().length }); }, 1500);
});
$list.addEventListener('click', e => {
  if (e.target.closest('[data-more]')) { state.lim += 30; renderList(); return; }
  const b = e.target.closest('.st'); if (b) { const s = ST.find(x => x.id === b.dataset.id); if (s) openCard(s, true); }
});
d.addEventListener('keydown', e => { if (e.key === 'Escape' && (sel || nearOpen || carOpen) && !d.querySelector('.lb')) { if (carOpen) closeCar(); else closeCard(); } });
$me.addEventListener('click', () => {
  if (!navigator.geolocation) return;
  $me.disabled = true;
  navigator.geolocation.getCurrentPosition(pos => {
    me = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    state.bounds = null;
    $me.disabled = false;
    track('map_near_me', { ok: true });
    showMe();
    if (map) map.flyTo({ center: [me.lon, me.lat], zoom: 11 });
    renderList();
  }, () => { $me.disabled = false; alertNote(T.no_location); track('map_near_me', { ok: false }); }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
});
function alertNote(msg) { $count.textContent = msg; }
d.querySelectorAll('[data-near]').forEach(b => b.addEventListener('click', () => nearGo(b === $near ? 'button' : 'button-list')));

// clicks inside the card area: the "Najbliži punjač" panel, the "Moj auto" panel, "choose a car" and the Evolako line
$card.addEventListener('click', e => {
  const t = e.target;
  if (t.closest('.nrp .x')) { closeNear(); return; }
  if (t.closest('.carp .x')) { closeCar(); return; }
  const nv = t.closest('.nrp a[data-nav]');
  if (nv) { setNavPref(nv.dataset.nav); track('map_navigate', { station: nv.dataset.st || '', app: nv.dataset.nav, from: 'nearest' }); return; }
  if (nearClick(t)) return;
  if (t.closest('[data-car-open]')) { openCar('card'); return; }
  if (t.closest('[data-evo]')) track('map_evolako', { station: sel ? sel.id : '', network: sel ? sel.net || '' : '', car: !!CAR });
});

// ---------- "Moj auto" ----------
let carOpen = false, carBack = null;
const $carBtn = d.getElementById('mcar'), $cheap = $chips.querySelector('[data-f="cheap"]');
function paintCar() {
  const c = carSpec();
  const lbl = d.querySelector('[data-carlbl]');
  if (lbl) lbl.textContent = c ? carName(c) : (CAR && !CARS ? '…' : T.car_none);
  if ($carBtn) $carBtn.classList.toggle('is-set', !!c);
  if ($cheap) { $cheap.hidden = !c; if (!c && state.cheap) state.cheap = false; }
}
function modelOpts(list, mk, id) {
  return '<option value="">' + esc(T.car_choose_model) + '</option>' + list.filter(c => c.mk === mk)
    .map(c => '<option value="' + esc(c.id) + '"' + (c.id === id ? ' selected' : '') + '>' + esc(c.md + ' · ' + c.y) + '</option>').join('');
}
function openCar(source) {
  carBack = sel;
  if (sel) { sel = null; history.replaceState(null, '', location.pathname + location.search); renderList(); }
  nearOpen = false; cardNear = false; carOpen = true;
  $card.innerHTML = '<div class="ccard carp" role="dialog" aria-label="' + esc(T.car_title) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(T.car_title) + '</h2><p class="addr">' + esc(T.car_lead) + '</p><div class="car-body"><p class="nr-wait" role="status"><span class="nr-spin" aria-hidden="true"></span>' + esc(T.loading) + '</p></div></div>';
  $card.classList.add('is-open');
  const x = $card.querySelector('.x'); if (x) x.focus({ preventScroll: true });
  track('map_car_open', { source: source || 'button', set: !!CAR });
  loadCars().then(list => { if (carOpen) carForm(list); });
}
function closeCar() {
  carOpen = false;
  $card.classList.remove('is-open');
  $card.innerHTML = '';
  const back = carBack; carBack = null;
  if (back) openCard(back, false);
  else if ($carBtn && window.innerWidth > 900) $carBtn.focus({ preventScroll: true });
}
function carForm(list) {
  const box = $card.querySelector('.car-body');
  if (!box) return;
  if (!list) { box.innerHTML = '<p class="nr-msg" role="alert">' + esc(T.car_load_err) + '</p>'; return; }
  const cur = CAR && list.find(c => c.id === CAR.id), mk = cur ? cur.mk : '';
  const makes = [...new Set(list.map(c => c.mk))];
  box.innerHTML = '<form class="car-form" novalidate>' +
    '<label class="field"><span>' + esc(T.car_make) + '</span><select class="select" name="mk"><option value="">' + esc(T.car_choose_make) + '</option>' +
    makes.map(m => '<option' + (m === mk ? ' selected' : '') + '>' + esc(m) + '</option>').join('') + '</select></label>' +
    '<label class="field"><span>' + esc(T.car_model) + '</span><select class="select" name="id"' + (mk ? '' : ' disabled') + '>' + modelOpts(list, mk, cur && cur.id) + '</select></label>' +
    '<label class="field"><span>' + esc(T.car_cons) + '</span><input class="input" name="cons" type="text" inputmode="decimal" autocomplete="off" maxlength="5"><small>' + esc(T.car_cons_hint) + '</small></label>' +
    '<label class="check car-opt" hidden><input type="checkbox" name="opt"> <span></span></label>' +
    '<label class="check"><input type="checkbox" name="cab"' + (CAR && CAR.cab ? ' checked' : '') + '> <span>' + esc(T.car_cab) + '</span></label>' +
    '<div class="car-acts"><button class="btn dark" type="submit">' + esc(T.car_save) + '</button>' + (CAR ? '<button class="btn" type="button" data-car-del>' + esc(T.car_del) + '</button>' : '') + '</div>' +
    '<small>' + esc(T.car_note) + '</small><small>' + esc(T.car_src) + '</small></form>';
  const f = box.querySelector('form'), sMk = f.elements.mk, sId = f.elements.id, iCons = f.elements.cons, wOpt = f.querySelector('.car-opt');
  const fill = () => {
    const c = list.find(x => x.id === sId.value);
    iCons.placeholder = c ? fmt(c.cons, 1) : '';
    iCons.value = c && CAR && CAR.id === c.id && CAR.cons ? fmt(CAR.cons, 1) : '';
    wOpt.hidden = !(c && c.opt);
    if (c && c.opt) {
      wOpt.querySelector('span').textContent = T.car_opt.replace('{k}', fmt(c.opt.ac, c.opt.ac % 1 ? 1 : 0));
      f.elements.opt.checked = !!(CAR && CAR.id === c.id && CAR.opt);
    }
  };
  fill();
  sMk.addEventListener('change', () => { sId.innerHTML = modelOpts(list, sMk.value, ''); sId.disabled = !sMk.value; fill(); if (sMk.value) sId.focus(); });
  sId.addEventListener('change', fill);
  f.addEventListener('submit', e => {
    e.preventDefault();
    const c = list.find(x => x.id === sId.value);
    if (!c) { sId.focus(); return; }
    const v = parseFloat(String(iCons.value).replace(',', '.'));
    CAR = { id: c.id, cons: v >= 8 && v <= 40 && Math.abs(v - c.cons) > 0.05 ? Math.round(v * 10) / 10 : null, cab: f.elements.cab.checked, opt: !!(c.opt && f.elements.opt.checked) };
    saveCar();
    track('map_car_set', { make: c.mk, model: c.md, own_consumption: !!CAR.cons, cable: CAR.cab });
    carChanged(c.mk === 'Tesla');
    closeCar();
  });
  const del = f.querySelector('[data-car-del]');
  if (del) del.addEventListener('click', () => { CAR = null; saveCar(); track('map_car_set', { removed: true }); carChanged(null); closeCar(); });
}
// a new car: new costs everywhere; a Tesla switches "Imam Teslu" on, another car off (no car: the switch stays as it is)
function carChanged(isTesla) {
  COSTV++;
  paintCar();
  if (isTesla != null && isTesla !== TESLA) setTesla(isTesla);
  else refresh();
}
if ($carBtn) $carBtn.addEventListener('click', () => openCar('button'));

// ?mreza=<net> ?grad=<city> ?q=<text> ?f=fast|ac|chademo|free|fav, ?ok=1 (or the old ?f=ok) and #<station id>; applied before the map loads,
// so the list is right even when the map tiles cannot be loaded. ?najblizi=1 (=brzi: fast only) opens "Najbliži punjač": at
// once when the browser already allows the location, otherwise the panel asks first — the page never asks by itself.
function fromUrl() {
  const p = new URLSearchParams(location.search);
  const net = p.get('mreza'), g = p.get('grad'), q = p.get('q'), f = p.get('f');
  if (q) { $q.value = q; state.q = q; }
  if (f === 'ok' || p.get('ok') === '1') { state.ok = true; paintChips(); }
  if (p.get('tesla') === '1') { TESLA = true; paintChips(); }
  const c = g && (cfg.cities || {})[g];
  if (c) city = { lat: c[0], lon: c[1] };
  paintChips();   // "Imam Teslu" kept in this browser (or the account) shows on its chip from the first paint
  if (net && $chips.querySelector('[data-f="net:' + net + '"]')) setChip('net:' + net, true);
  else if (net) { state.q = state.q || net.replace(/-/g, ' '); refresh(); }
  else if (f && f !== 'ok' && f !== 'cheap' && $chips.querySelector('[data-f="' + f + '"]')) setChip(f, true);
  else refresh();
  const id = decodeURIComponent(location.hash.slice(1));
  if (id) { const s = ST.find(x => x.id === id); if (s) { openCard(s, false); return; } }
  const nz = p.get('najblizi');
  if (nz) {
    if (nz === 'brzi') setChip('fast', true);
    const ask = () => { NEAR = { pt: null, withNep: false, source: 'link', ask: true }; nearPanel(NEAR); };
    if (navigator.permissions && navigator.permissions.query) navigator.permissions.query({ name: 'geolocation' }).then(r => { if (r.state === 'granted') nearGo('link'); else ask(); }, ask);
    else ask();
  }
}

const getJson = u => fetch(u).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
Promise.all([getJson(cfg.stations), cfg.nets ? getJson(cfg.nets).catch(() => ({ upd: {}, add: [] })) : { upd: {}, add: [] }, getJson(cfg.prices),
  cfg.extra ? getJson(cfg.extra).catch(() => ({ upd: {} })) : { upd: {} },
  cfg.region ? getJson(cfg.region).catch(() => null) : null,
  CAR ? loadCars() : null]).then(([a, m, b, x, rg]) => {
  ST = a.stations;
  const join = (layer, list) => list.forEach(s => {
    const u = layer.upd && layer.upd[s.id];
    if (!u) return;
    Object.keys(u).forEach(k => { if (k !== 'src') s[k] = u[k]; });
    s.src = s.src.concat(u.src || []);
  });
  // the networks' own lists: their connectors and names for the stations they confirm, and the stations the open data lacks
  join(m, ST);
  ST = ST.concat(m.add || []);
  // our checked facts last: exact place, hours, access, who charges free (dopune.json)
  join(x, ST);
  NSR = ST.length;
  // the neighbouring countries (blokvolt.rs only): a map without them still works if the file cannot be loaded
  if (rg && rg.stations) { RGC = rg.cc || {}; NRG = rg.stations.length; ST = ST.concat(rg.stations); }
  ST.sort((x, y) => (!x.n - !y.n) || fold(x.n).localeCompare(fold(y.n)) || (x.id < y.id ? -1 : 1));
  NETS = b.nets;
  ST.forEach((s, i) => { s._i = i; });
  COSTV++;
  paintCar();
  // favourites of stations that are no longer on the map are dropped quietly
  const ids = new Set(ST.map(s => s.id));
  if ([...FAV].some(id => !ids.has(id))) { FAV = new Set([...FAV].filter(id => ids.has(id))); saveFav(); }
  favCount();
  fromUrl();
  loadSummaries();
  accSync();
  try { initMap(); } catch (e) { d.getElementById('map').classList.add('is-off'); }
  // scripts/qa/map_extra_test.py reads the pin data (kind, power label, price label) through this, only with ?qa=1;
  // bvMapQa(true) gives the neighbouring countries' pins (scripts/qa/map_region_test.py); bvNearQa(lat, lon, nep) gives the
  // rows of "Najbliži punjač" for a point (the apps and evolako.rs are compared with it); bvCostQa(id) the cost lines
  if (/[?&]qa=1\b/.test(location.search)) {
    window.bvMapQa = rg => data(rg).features.map(f => f.properties);
    window.bvNearQa = (lat, lon, nep) => nearestList({ lat, lon }, !!nep).rows.map(r => ({ id: r.s.id, t: title(r.s), m: Math.round(r.d * 1000) }));
    window.bvCostQa = id => { const s = ST.find(x => x.id === id), co = s && costOf(s); return co ? { kw: co.main.c.kw, kwh: co.main.c.kwh, km: co.main.c.km, alt: co.alt ? co.alt.c.km : null } : null; };
  }
}).catch(() => { $count.textContent = T.load_err; });
