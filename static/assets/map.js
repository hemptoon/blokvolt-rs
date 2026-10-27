/* BlokVolt — map of public chargers (/mapa/). MapLibre GL + OpenFreeMap; stations from
   /assets/map/punjaci.json (OSM + OCM, ODbL) completed with /assets/map/mreze.json (the networks' own lists),
   prices from /assets/map/cene.json (ours), our checked facts from /assets/map/dopune.json (exact place, hours, access,
   who charges free), drivers' reports, ratings and photos from /api (Cloudflare D1).
   On blokvolt.rs, cfg.region adds the neighbouring countries (/assets/map/region.json: open data of the blokvolt.com
   sections) as a second, quieter layer: no prices, reports or checks there, and each card links to that country's map.
   Favourites (★) are station ids kept in this browser (localStorage 'bv:fav'), and so is "Moj auto" ('bv:car', below).
   Only a reader signed in to "Moj BlokVolt" (cookie bv_in) also keeps them in the account (/api/nalog/*,
   'bv:fav-owner': whose list it is; docs/RUNBOOK.md 3.27); without the cookie nothing is sent anywhere.
   Since 06.10.2026: "Najbliži punjač" (the three nearest chargers a driver can use, and a route; the navigation app chosen
   last is kept as 'bv:nav2'), "Moj auto" (the reader's car, 'bv:car', with the cars from /assets/map/auta.json: the cost per
   km at every charger, compared with petrol and with charging at home), the network's own price of every connector
   (mreze.json: pr), hours with "open now" (oh.w), own cable (cab), parking (park) and "Kako se puni ovde" (cene.json: kako).
   The location and the navigation app never leave the browser; the car only goes to the account of a signed-in reader.
   docs/RUNBOOK.md 3.18. */
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
  list: svg('<path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/>'),
  road: svg('<path d="M6 21 9 3M18 21 15 3M12 5v2.5M12 11v2.5M12 17v2.5"/>'),
  loc: svg('<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>')
};
// directions: Google Maps first everywhere (owner's decision 25.10.2026), Apple Maps second on Apple devices, Waze always.
// The app a reader opens a route in comes first from then on ('bv:nav2' in this browser; the old 'bv:nav' is ignored: it kept the Apple Maps default of the Apple devices, 25.10.2026). Google: dir_action=navigate starts
// turn-by-turn at once in the Maps app on a phone; coordinates only, no API key.
const IS_APPLE = /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent);
const NAV_KEY = 'bv:nav2', NAV_NAME = { google: 'Google Maps', apple: 'Apple Maps', waze: 'Waze' };
let NAV_PREF = '';
try { NAV_PREF = localStorage.getItem(NAV_KEY) || ''; } catch (e) { NAV_PREF = ''; }
function navApps() { return IS_APPLE ? ['google', 'apple', 'waze'] : ['google', 'waze']; }
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

// A Tesla in "Moj auto" (or ?tesla=1, for that view only): Tesla-only chargers (the Superchargers) count as usable and,
// where drivers report it, free. Since 25.10.2026 there is no separate "Imam Teslu" switch: the car decides, as on the
// Evolako map. The old switch's 'bv:tesla' is removed from this browser.
let TESLA = false;
const TESLA_URL = /[?&]tesla=1\b/.test(location.search);
try { localStorage.removeItem('bv:tesla'); } catch (e) { /* private mode */ }
function teslaNow() { const c = carSpec(); return TESLA_URL || !!(c && c.mk === 'Tesla'); }

// "Moj auto": the reader's car in this browser only ('bv:car' = {id, cons, cab, opt}: the car's id in auta.json, the reader's
// own consumption in kWh/100 km, "I have my own Type 2 cable", the optional on-board charger). With a car the map shows the
// cost per km; a Tesla also makes the Tesla-only chargers usable. A signed-in reader's car is the account's car.
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
// have → nothing changes here and nothing is sent: /nalog/ asks the reader first. Once in step, every star (and the car)
// is also sent to the account, fire-and-forget: localStorage stays the offline copy. The account's car replaces this
// browser's (a car not on the map's list means no car here); an account without a car takes this browser's, unless the
// browser was last used by another account. A 401 removes the hint cookie; the map then works as before, locally. The
// account's fast-charging plug (user.dc) marks the matching connector.
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
    const u = j.user;
    if (u.car_id || u.car) {
      const next = u.car_id ? { id: u.car_id, cons: u.car_cons || null, cab: !!u.car_cab, opt: !!u.car_opt } : null;
      if (JSON.stringify(next) !== JSON.stringify(CAR)) {
        CAR = next; saveCar();
        if (CAR) loadCars().then(() => { carChanged(); if (sel) openCard(sel, false); }); else carChanged();
      }
    } else if (CAR && (!owner || owner === key)) carToAccount();
    favCount();
    refresh();
    if (sel) openCard(sel, false);
  }).catch(() => { /* offline: the local lists stay */ });
}

let ST = [], NETS = {}, CI = {}, CI_STATE = 'loading', map, me = null, sel = null, city = null, opened = 0;
// the neighbouring countries (cfg.region): their links, and how many stations are Serbian (NSR) and how many are not (NRG)
let RGC = {}, NSR = 0, NRG = 0;
const state = { q: '', f: 'all', ok: false, cheap: false, bounds: null, lim: 20 };
let userMove = false, llAt = null;
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
  return (s.dc || 0) > 0 || s.kd === 'dc' ? 'dc' : 'ac';
}
// a neighbouring country's station never takes a Serbian network's data (the same slug can mean another company there)
function netOf(s) { return s.cc ? null : NETS[s.net] || null; }
function netName(s) { if (s.cc) return s.nn || s.opn || ''; const n = netOf(s); return n ? n.name : (s.opn || ''); }
// a station without a name is called by its network, else by its street
function cleanName(n) { return (n || '').replace(/^charge\s*&\s*go\s*[-–:,]?\s*/i, '').replace(/^BS\s+(?=gazprom|nis|evoil)/i, '').trim(); }
function title(s) { return cleanName(s.n) || netName(s) || (s.a ? s.a.split(',')[0] : s.vz ? T.vz_title : T.charger); }
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
  // a charger added by a driver: what the driver said about the price, never drawn as free (it is not checked yet)
  if (s.vz) return { kind: 'none', text: s.vz.fee === 'besplatno' ? T.vz_free : s.vz.fee === 'placa' ? T.vz_paid : T.p_unknown };
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
// the face of each plug, drawn like the other icons (24 px grid, 1.8 stroke, pins as dots): the reader recognises the
// socket on the charger and on the car without knowing the standard's name (owner, 25.10.2026). The same drawings are in
// scripts/evomap/evomap.src.js (evolako.rs) — change both.
const dot = (x, y, r) => '<circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="currentColor" stroke="none"/>';
const PLUG = {
  type2: svg('<path d="M6.52 6h10.96A8.5 8.5 0 1 1 6.52 6Z"/>' + dot(9.6, 8.7, .95) + dot(14.4, 8.7, .95) + dot(7.9, 12.3, 1.25) + dot(12, 12.3, 1.25) + dot(16.1, 12.3, 1.25) + dot(9.9, 16.2, 1.25) + dot(14.1, 16.2, 1.25)),
  ccs2: svg('<path d="M8.95 3.2h6.1a6.2 6.2 0 1 1-6.1 0Z"/><rect x="5.6" y="16.4" width="12.8" height="5.4" rx="2.7"/>' + dot(10.4, 5.5, .7) + dot(13.6, 5.5, .7) + dot(8.7, 8.7, .95) + dot(12, 8.7, .95) + dot(15.3, 8.7, .95) + dot(10.4, 11.9, .95) + dot(13.6, 11.9, .95) + dot(9, 19.1, 1.3) + dot(15, 19.1, 1.3)),
  chademo: svg('<circle cx="12" cy="12.5" r="8.5"/><path d="M10.6 4.1v-1.4h2.8v1.4"/><circle cx="8.4" cy="12.7" r="2.1"/><circle cx="15.6" cy="12.7" r="2.1"/>' + dot(12, 8.3, .9) + dot(12, 17, .9)),
  type1: svg('<circle cx="12" cy="12" r="8.5"/>' + dot(8.7, 10.2, 1.45) + dot(15.3, 10.2, 1.45) + dot(12, 16.2, 1.45) + dot(8.9, 14.7, .8) + dot(15.1, 14.7, .8)),
  tesla: svg('<path d="M12 3.5c4.4 0 7.5 3 7.5 7.3 0 5-3.6 9.7-7.5 9.7s-7.5-4.7-7.5-9.7C4.5 6.5 7.6 3.5 12 3.5Z"/>' + dot(9.2, 10.8, 1.6) + dot(14.8, 10.8, 1.6) + dot(12, 15.7, 1.2) + dot(10.6, 6.9, .7) + dot(13.4, 6.9, .7)),
  gbt: svg('<circle cx="12" cy="12" r="8.5"/>' + dot(9.6, 8.4, .95) + dot(14.4, 8.4, .95) + dot(7.8, 12, 1.25) + dot(12, 12, 1.25) + dot(16.2, 12, 1.25) + dot(9.9, 15.9, 1.25) + dot(14.1, 15.9, 1.25)),
  schuko: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5v2.3M12 18.2v2.3"/>' + dot(8.6, 12, 1.35) + dot(15.4, 12, 1.35)),
  cee: svg('<circle cx="12" cy="12.5" r="8.5"/><path d="M10.8 4.1V2.8h2.4v1.3"/>' + dot(12, 8, 1) + dot(7.6, 11.4, 1) + dot(16.4, 11.4, 1) + dot(9.2, 16.6, 1) + dot(14.8, 16.6, 1) + dot(12, 12.6, 1.2))
};
PLUG.ccs1 = PLUG.ccs2;
// does this plug fit the reader's car („Moj auto“)? 1 yes, 0 no, null = cannot tell (a household socket, CEE).
// Without a car: the signed-in account's fast-charging plug (MYDC) is marked, nothing is greyed out.
function plugFit(c, car) {
  const [type, cur] = c;
  if (!car) return MYDC && cur === 'dc' && type === MYDC ? 1 : null;
  if (cur === 'dc') {
    if (!car.dc) return 0;
    if (type === 'chademo') return car.pl === 'chademo' ? 1 : 0;
    if (type === 'ccs2') return car.pl === 'ccs2' ? 1 : 0;
    if (type === 'tesla') return car.mk === 'Tesla' ? 1 : 0;
    return 0;
  }
  if (type === 'type2') return 1;
  if (type === 'tesla') return car.mk === 'Tesla' ? 1 : 0;
  if (type === 'type1' || type === 'gbt') return 0;
  return null;
}
// the connectors as tiles, one per plug and current: "CCS2 · DC · 30–75 kW · ×3" (owner, 26.10.2026); as many in a row as fit
function connTiles(s) {
  const g = [], by = {}, car = carSpec();
  s.c.forEach(c => {
    const k = c[0] + '|' + c[1];
    if (!by[k]) g.push(by[k] = { c, lo: null, hi: null, n: 0 });
    const x = by[k];
    if (c[2]) { x.lo = x.lo == null ? c[2] : Math.min(x.lo, c[2]); x.hi = x.hi == null ? c[2] : Math.max(x.hi, c[2]); }
    x.n += c[3] || 1;
  });
  const kw = x => x.lo == null ? '' : (x.lo === x.hi ? fmt(x.lo, x.lo % 1 ? 1 : 0) : fmt(x.lo, 0) + '–' + fmt(x.hi, 0)) + ' ' + U.kw;
  return '<ul class="cns">' + g.map(x => {
    const [type, cur] = x.c, fit = plugFit(x.c, car);
    return '<li class="cn' + (cur === 'dc' ? ' dc' : '') + (fit === 0 ? ' no' : fit === 1 ? ' yes' : '') + '"><i aria-hidden="true">' + (PLUG[type] || ICON.cable) + '</i>' +
      '<b>' + esc(CONN[type] || type) + '</b><small>' + esc([cur.toUpperCase(), kw(x)].filter(Boolean).join(' · ')) + '</small>' +
      (x.n > 1 ? '<em class="n">×' + x.n + '</em>' : '') +
      (fit === 1 ? '<em class="fit">' + esc(T.conn_mine) + '</em>' : fit === 0 ? '<em class="fit">' + esc(T.conn_no) + '</em>' : '') + '</li>';
  }).join('') + '</ul>';
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
  return '<a class="pmini solo" href="' + esc(evoUrl('kartica')) + '" rel="noopener" data-evo><span class="badge feat">' + esc(T.promo_badge) + '</span>' +
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
    // the same line recorded at two places of the network is shown once
    h += '<div>' + esc(T.p_seen) + '</div><ul>' + [...new Set(p.list.map(t => '<li><b>' + fxd(t.label) + '</b> — ' + esc(t.charger) + (t.extra ? ', ' + fxd(tr(t.extra)) : '') + '</li>'))].slice(0, 3).join('') + '</ul>';
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
  return h + costHtml(s, p) + '</div>';
}
// "Kako se puni ovde" as a picture (owner, 25.10.2026): 2–4 steps with an icon and a few words, up to three facts, the
// network's apps; the full text of the network (cene.json: kako) and its sources stay folded under "Detaljno".
// Every station gets a scheme: its network's (kako.steps), or a general one from what is known about the place
// (access through staff, a card at the desk, RFID, guests only, free, or an unknown network) — marked „Opšte uputstvo“.
// The same logic is in scripts/evomap/evomap.src.js (howOf) — change both. ?qa=1: window.bvKakoQa().
const HI = {
  app: svg('<rect x="7" y="2.8" width="10" height="18.4" rx="2.4"/><path d="M11 17.6h2"/>'),
  qr: svg('<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z"/><path d="M14 14h2.5v2.5H14zM17.5 17.5H20V20h-2.5zM20 14v1.5M14 20v-1"/>'),
  plug: svg('<path d="M9 2.8v4M15 2.8v4M6.8 6.8h10.4v3.7a5.2 5.2 0 0 1-10.4 0V6.8Z"/><path d="M12 15.7v5.5"/>'),
  stop: svg('<circle cx="12" cy="12" r="8.5"/><rect x="9.2" y="9.2" width="5.6" height="5.6" rx="1"/>'),
  play: svg('<circle cx="12" cy="12" r="8.5"/><path d="M10.4 8.7v6.6l5.2-3.3-5.2-3.3Z"/>'),
  card: svg('<rect x="3" y="5.5" width="18" height="13" rx="2.2"/><path d="M3 9.8h18M6.8 14.6h3.6"/>'),
  receipt: svg('<path d="M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21V3Z"/><path d="M9 8h6M9 11.5h6M9 15h3.5"/>'),
  noacc: svg('<circle cx="10" cy="8" r="3.6"/><path d="M3.5 20a6.5 6.5 0 0 1 10.6-5"/><path d="m16.3 15.3 4.2 4.2M20.5 15.3l-4.2 4.2"/>'),
  user: svg('<circle cx="12" cy="8" r="3.8"/><path d="M5 20.5a7 7 0 0 1 14 0"/>'),
  timer: svg('<circle cx="12" cy="13.5" r="7.5"/><path d="M12 9.6v3.9l2.6 1.6M9.6 2.8h4.8"/>'),
  free: svg('<path d="M3.5 12.4V4.5h7.9l9.1 9.1-7.9 7.9-9.1-9.1Z"/><circle cx="7.9" cy="8.9" r="1.3"/>'),
  ok: svg('<circle cx="12" cy="12" r="8.5"/><path d="m8.3 12.3 2.5 2.5 5-5.2"/>'),
  eye: svg('<path d="M2.5 12s3.5-6.3 9.5-6.3 9.5 6.3 9.5 6.3-3.5 6.3-9.5 6.3S2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="2.8"/>'),
  desk: svg('<path d="M3.5 19.5h17M5.5 16.5a6.5 6.5 0 0 1 13 0Z"/><path d="M12 10V8.2M10.6 8.2h2.8"/>'),
  rfid: svg('<rect x="3" y="7" width="11" height="10" rx="1.8"/><path d="M17.3 9a4.4 4.4 0 0 1 0 6M19.8 6.8a7.6 7.6 0 0 1 0 10.4"/>'),
  car: ICON.car, list: ICON.list, cable: ICON.cable, park: ICON.park, info: ICON.info
};
function howOf(s) {
  // a neighbour's station on /mapa/, or a page without the scheme's words (the country maps of blokvolt.com: their
  // strings cover the card, not this scheme) — no scheme rather than icons without text
  if (s.cc || !T.hw_t) return null;
  const n = netOf(s), k = n && n.kako, ax = s.ax || {}, fee = (s.fee && s.fee.free) || '';
  const onlyAc = !s.dc && (s.c.length ? s.c.every(c => c[1] === 'ac') : !!s.ac);
  const acCable = onlyAc && !(s.cab && s.cab.own) ? [['cable', T.hw_g_cable]] : [];
  if (k && k.steps) {
    return { k: 'net', name: n.name, steps: k.steps.map(x => [x.i, tr(x.t)]), facts: (k.facts || []).filter(x => !(x.i === 'cable' && s.cab && s.cab.own)).map(x => [x.i, tr(x.t)]), kako: k };
  }
  // what the place itself says (dopune.json: ax.how), then who may charge, then free, then nothing known
  const g = ax.how === 'card-desk' ? 'desk' : ax.how === 'rfid' ? 'rfid' : ax.how === 'staff' ? 'staff'
    : (ax.who === 'guests' || ax.who === 'customers' || s.acc === 'customers') ? 'guests' : fee ? 'free' : 'unk';
  const STEPS = {
    desk: [['desk', T.hw_g_desk], ['rfid', T.hw_g_tap], ['plug', T.hw_g_plug]],
    rfid: [['rfid', T.hw_g_rfid], ['plug', T.hw_g_plug], ['ok', T.hw_g_start]],
    staff: [['park', T.hw_g_park], ['user', T.hw_g_staff], ['plug', T.hw_g_plug]],
    guests: [['desk', T.hw_g_ask], ['park', T.hw_g_park], ['plug', T.hw_g_plug]],
    free: [['park', T.hw_g_park], ['plug', T.hw_g_plug], ['user', T.hw_g_help]],
    unk: [['eye', T.hw_g_look], ['qr', T.hw_g_qr], ['plug', T.hw_g_plugstart]]
  };
  return { k: g, gen: true, known: !!(n || s.opn), name: n ? n.name : '', steps: STEPS[g], facts: g === 'desk' || g === 'staff' || g === 'rfid' ? [] : acCable, kako: k || null };
}
function howHtml(s) {
  const h = howOf(s);
  if (!h) return '';
  const steps = '<ol class="hw-steps" style="--n:' + h.steps.length + '">' + h.steps.map((x, i) => '<li><i aria-hidden="true">' + (HI[x[0]] || HI.info) +
    '<b>' + (i + 1) + '</b></i><span>' + esc(x[1]) + '</span></li>').join('') + '</ol>';
  const facts = h.facts.length ? '<ul class="hw-facts">' + h.facts.map(x => '<li>' + (HI[x[0]] || HI.info) + '<span>' + esc(x[1]) + '</span></li>').join('') + '</ul>' : '';
  const k = h.kako;
  // the app stores as buttons, this device's store first; the network's websites go under „Detaljno“
  const all = (k && k.apps) || [], store = a => /apps\.apple\.com|play\.google\.com/.test(a.u);
  const own = a => (/apps\.apple\.com/.test(a.u) ? IS_APPLE : /Android/.test(navigator.userAgent)) ? 0 : 1;
  const stores = all.filter(store).sort((a, b) => own(a) - own(b)), sites = all.filter(a => !store(a));
  const apps = stores.length ? '<p class="hw-apps">' + stores.map(a => '<a href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + HI.app +
    '<span>' + esc(/apps\.apple\.com/.test(a.u) ? 'App Store' : 'Google Play') + '</span></a>').join('') + '</p>' : '';
  let more = '';
  if (k) {
    const row = (lbl, x) => (x ? '<p><b>' + esc(lbl) + '</b> ' + esc(tr(x)) + '</p>' : '');
    const src = (k.src || []).map(a => '<a href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(a.l)) + '</a>').join(' · ');
    more = '<details class="hw-more"><summary>' + esc(T.hw_more) + '</summary>' +
      (k.start && k.start.length ? '<ol>' + k.start.map(x => '<li>' + esc(tr(x)) + '</li>').join('') + '</ol>' : '') +
      row(T.kako_pay, k.pay) + row(T.kako_guest, k.guest) + row(T.kako_after, k.after) + row(T.kako_refund, k.refund) +
      (sites.length ? '<p><b>' + esc(T.hw_sites) + '</b> ' + sites.map(a => '<a href="' + esc(a.u) + '" target="_blank" rel="noopener nofollow">' + esc(tr(a.l)) + '</a>').join(' · ') + '</p>' : '') +
      '<small>' + esc(T.kako_checked.replace('{d}', k.checked || '')) + (src ? ' · ' + src : '') + '</small></details>';
  }
  const fix = cfg.fix ? cfg.fix.replace('{id}', encodeURIComponent(s.id)) : lp('/ispravka/?stanica=') + encodeURIComponent(s.id);
  const gen = h.gen ? '<p class="hw-gen">' + esc(h.k === 'unk' && !h.known ? T.hw_gen_unk : T.hw_gen) + ' <a href="' + fix + '">' + esc(T.hw_tell) + '</a></p>' : '';
  return '<section class="cbox hw' + (h.gen ? ' is-gen' : '') + '" aria-label="' + esc(T.hw_t) + '"><div class="hw-h"><span>' + esc(T.hw_t) + '</span>' +
    (h.gen ? '<em>' + esc(T.hw_general) + '</em>' : h.name ? '<em>' + esc(h.name) + '</em>' : '') + '</div>' + steps + facts + apps + gen + more + '</section>';
}
function statusHtml(s) {
  if (!s.ps) return '';
  const li = s.ps.l.map(l => '<li class="' + (l[2] === 1 ? 'ok' : 'no') + '"><i></i><span>' + esc([l[0], l[1]].filter(Boolean).join(' · ')) +
    ' · <b>' + esc(l[2] === 1 ? T.st_ok : T.st_off) + '</b>' + (l[3] && T['st_' + l[3]] ? ' (' + esc(T['st_' + l[3]]) + ')' : '') + '</span></li>').join('');
  return '<div class="cbox"><span>' + esc(T.status) + '</span><ul class="stl">' + li + '</ul><small>' + esc(T.st_src.replace('{d}', s.ps.d)) + '</small></div>';
}
const VBY = () => ({ cg: T.v_cg, rm: T.v_rm, te: T.v_te, ps: T.v_ps, g: T.v_g, own: T.v_own, sp: T.v_sp, ye: T.v_ye, bp: T.v_bp, to: T.v_to, mr: T.v_mr });
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
  return { cg: 'net', rm: 'net', te: 'net', ps: 'site', osm: 'osm', ocm: 'ocm', vz: 'vz', ye: 'net', bp: 'net', sp: 'site', own: 'site', tim: 'tim' }[pre] || '';
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
  const why = v.s === 'prob' ? T.v_prob : (v.g === 'vz' ? T.v_vz : v.g === 'tim' && T.v_tim ? T.v_tim : v.g === 'test' ? T.v_test : v.g === 'g_old' ? T.v_old : T.v_none);
  const when = (v.g === 'vz' ? T.v_vz_d : v.g === 'tim' && T.v_tim_d ? T.v_tim_d : T.v_checked).replace('{d}', v.d || '');
  return '<div class="vf-warn' + (v.s === 'prob' ? ' no' : '') + '"><b>' + ICON.warn + esc(v.s === 'prob' ? T.v_prob_t : T.v_nep) + '</b><p>' + esc(why) + '</p><small>' + esc(when) + vHelp() + '</small></div>';
}
function openCard(s, fly, fromNear) {
  rtPopClose();
  sel = s;
  opened = Date.now();
  nearOpen = false;
  // from = true: opened from "Najbliži punjač"; 'rt': from "Punjači na putu" (or tapped on the map while the route was open)
  cardRt = !!RT.route && (fromNear === 'rt' || (fromNear !== true && (rtOpen || RT.min || (cardRt && RT.shown))));
  rtOpen = false; RT.min = false;
  cardNear = !cardRt && !!(fromNear && NEAR);
  if (!cardRt && RT.shown) rtClear();
  const n = netOf(s);
  const logo = n && n.logo ? '<span class="lg w' + (n.logo_dark ? ' dark' : '') + '"><img src="' + esc(n.logo) + '" alt=""></span>' : '<span class="lg w mono" aria-hidden="true">' + esc((netName(s) || '?').slice(0, 2).toUpperCase()) + '</span>';
  const netRole = s.cc ? (s.nn ? T.net_known : T.operator) : n && n.page ? T.net_known : (s.opn && !n ? T.operator : T.net_unknown);
  const netLine = netName(s) ? '<div class="net">' + logo + '<div><b>' + esc(netName(s)) + '</b><span>' + esc(netRole) + '</span></div></div>' : '';
  const conns = s.c.length ? '<div class="cbox cbx-cn"><span>' + esc(T.conn) + '</span>' + connTiles(s) + '</div>' : '';
  const acc = s.acc === 'customers' ? '<div class="cbox"><span>' + esc(T.access) + '</span><div>' + esc(T.customers) + '</div></div>' : '';
  const navs = navLinks(s);
  // a neighbouring country's station: the button opens it on that country's map on blokvolt.com (prices, the country's networks)
  const rg = s.cc && RGC[s.cc];
  const site = rg ? rg.map + '#' + encodeURIComponent(s.id) : n && n.page ? n.page : (n && n.site ? n.site : '');
  const fix = cfg.fix ? cfg.fix.replace('{id}', encodeURIComponent(s.id)) : lp('/ispravka/?stanica=') + encodeURIComponent(s.id);
  const SRC = { ocm: 'Open Charge Map', osm: 'OpenStreetMap', ps: 'JP Putevi Srbije', cg: 'Charge&GO', rm: T.src_rm, te: 'Tesla', cga: T.src_cga, vz: T.src_vz,
    sp: T.src_sp, ye: T.src_ye, bp: 'Best in Parking', own: T.src_own, tim: T.src_tim };
  const srcs = s.src.filter(x => x.u).map(x => '<a href="' + esc(lp(x.u)) + '" rel="noopener nofollow">' + esc(tr(x.l) || SRC[x.d] || x.d) + '</a>' + (x.upd ? ' (' + esc(x.upd) + ')' : '')).join(' · ');
  $card.innerHTML = '<div class="ccard" role="dialog" aria-label="' + esc(title(s)) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    favBtn(s) + (cardNear ? '<button class="lnkbtn nr-back" type="button" data-nr="back">← ' + esc(T.nr_title) + '</button>' : cardRt ? '<button class="lnkbtn nr-back" type="button" data-rt="back">← ' + esc(T.rt_title) + '</button>' : '') +
    '<h2>' + esc(title(s)) + '</h2><p class="addr">' + esc(place(s)) + '</p>' + verHtml(s) + tagsHtml(s) + netLine + conns + priceHtml(s) + noteHtml(s) + howHtml(s) + promoHtml(s, price(s)) + statusHtml(s) + acc + whereHtml(s) +
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
    if (a.dataset.nav) { setNavPref(a.dataset.nav); track('map_navigate', { station: s.id, network: s.net || '', app: a.dataset.nav, from: cardNear ? 'nearest' : cardRt ? 'route' : 'card' }); }
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
  if (rtOpen && !sel) { rtClose(); return; }
  if (cardRt) rtClear();
  cardNear = false; cardRt = false;
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
// visible part of the map do not; never a charger that does not work, is only for Tesla vehicles (unless "Moj auto" is a Tesla), is
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
  cardNear = false; cardRt = false; rtOpen = false;
  if (RT.shown) rtClear();
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

// ---------- "Punjači na putu": fast chargers along a route the reader enters (owner's decision 24.10.2026) ----------
// The reader types where to (and where from; empty = the reader's location). The places are looked up in Photon
// (photon.komoot.io, OpenStreetMap data) and the route in OSRM on the FOSSGIS server (routing.openstreetmap.de): the
// browser sends them only the typed text, a point picked by a long press (below) and the two points; the site gets and
// stores nothing (RUNBOOK 3.18).
// Chargers: DC ≥ 50 kW that work (never "Ne radi"), not only for Tesla (unless "Moj auto" is a Tesla), usable by the reader's car
// when one is chosen; within R km of the route (straight line), ordered by the distance along the route. Confirmed only,
// unless the reader asks for the rest (or none is confirmed); with "Potvrđeni" on, confirmed only. The chip filter and
// the search text do not count: the route has its own rule. No network or firm is ever put first.
const RT_GEO = 'https://photon.komoot.io/api/', RT_OSRM = 'https://routing.openstreetmap.de/routed-car/route/v1/driving/';
const RT_RS = [2, 5, 10], RT_MAXR = 10;
let RT = { r: 5, nep: false, from: null, to: null }, rtOpen = false, cardRt = false;
const $rtBtn = d.getElementById('mroute');
// Serbian Cyrillic place names from OpenStreetMap are shown in Latin script on the Serbian and English pages
const LATN = { а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', ђ: 'đ', ѓ: 'gj', е: 'e', ж: 'ž', з: 'z', ѕ: 'dz', и: 'i', ј: 'j', к: 'k', ќ: 'kj',
  л: 'l', љ: 'lj', м: 'm', н: 'n', њ: 'nj', о: 'o', п: 'p', р: 'r', с: 's', т: 't', ћ: 'ć', у: 'u', ф: 'f', х: 'h', ц: 'c', ч: 'č', џ: 'dž', ш: 'š' };
const latn = x => (LANG === 'ru' ? String(x || '') : String(x || '').replace(/[Ѐ-ӿ]/g, c => {
  const l = c.toLowerCase(), t = LATN[l];
  return t == null ? c : c === l ? t : t.charAt(0).toUpperCase() + t.slice(1);
}));
function geoLabel(f) {
  const a = f.properties || {}, out = [];
  const street = a.street ? a.street + (a.housenumber ? ' ' + a.housenumber : '') : '';
  [a.name, street, a.city || a.town || a.village || a.district, a.country].forEach(x => {
    const v = latn(x).trim();
    if (v && out.indexOf(v) < 0) out.push(v);
  });
  return out.join(', ');
}
let geoCtl = null;
// own = a lookup the reader cannot cancel by typing on (the search on submit); suggestions cancel each other
async function geoSearch(q, own) {
  let sig;
  if (!own) { if (geoCtl) geoCtl.abort(); geoCtl = new AbortController(); sig = geoCtl.signal; }
  const u = RT_GEO + '?q=' + encodeURIComponent(q) + '&limit=6&lang=' + (LANG === 'ru' ? 'default' : 'en') + '&lat=' + C0[1] + '&lon=' + C0[0];
  const r = await fetch(u, { signal: sig, credentials: 'omit' });
  if (!r.ok) throw Object.assign(new Error('geo ' + r.status), { code: 'net' });
  const j = await r.json(), seen = new Set();
  const all = (j.features || []).filter(f => f.geometry && f.geometry.coordinates).map((f, i) => ({
    label: geoLabel(f), pt: { lon: +f.geometry.coordinates[0], lat: +f.geometry.coordinates[1] }, rk: geoRank(f), i
  })).filter(x => x.label && !seen.has(x.label) && seen.add(x.label)).sort((a, b) => a.rk - b.rk || a.i - b.i);
  return geoTowns(q, all).slice(0, 5).map(x => ({ label: x.label, pt: x.pt }));
}
// Photon folds "Nis" to Niš but may rank a railway station or a street above the town: places come first (city > town >
// village > the rest), then everything else in Photon's order. On top, the towns the site lists (cfg.towns, the same as
// scripts/map_data.py TOWNS) whose folded name is the typed text or starts with it, so "Nis", "Cacak", "Uzice" or "Ниш"
// offer Niš, Čačak, Užice first even on a keyboard without š, č, ž (owner's request 26.10.2026).
const GEO_RK = { city: 0, town: 1, village: 2 };
const geoRank = f => { const a = f.properties || {}; return a.osm_key === 'place' ? (a.osm_value in GEO_RK ? GEO_RK[a.osm_value] : 3) : 4; };
const TOWNS = Array.isArray(cfg.towns) ? cfg.towns : [];
// Serbian Cyrillic for a town name on the Russian page (Photon's own names there are Serbian Cyrillic too)
const CYRL = { lj: 'љ', nj: 'њ', dž: 'џ', a: 'а', b: 'б', c: 'ц', č: 'ч', ć: 'ћ', d: 'д', đ: 'ђ', e: 'е', f: 'ф', g: 'г', h: 'х', i: 'и', j: 'ј', k: 'к',
  l: 'л', m: 'м', n: 'н', o: 'о', p: 'п', r: 'р', s: 'с', š: 'ш', t: 'т', u: 'у', v: 'в', z: 'з', ž: 'ж' };
const townName = n => (LANG !== 'ru' ? n : n.replace(/lj|nj|dž|[a-zčćđšž]/gi, m => {
  const l = m.toLowerCase(), t = CYRL[l];
  return t == null ? m : m.charAt(0) === m.charAt(0).toLowerCase() ? t : t.toUpperCase();
}));
function townHits(q) {
  const k = sfold(q);
  if (k.length < 3) return [];
  const ex = [], pre = [];
  TOWNS.forEach(t => { const n = sfold(t[0]); if (n === k) ex.push(t); else if (n.indexOf(k) === 0) pre.push(t); });
  return ex.concat(pre).slice(0, 3);
}
function geoTowns(q, list) {
  const top = [];
  townHits(q).forEach(t => {
    const pt = { lat: t[1], lon: t[2] }, n = sfold(t[0]);
    // Photon's own entry for that town (its label, e.g. "Niš, Serbia"), else the town from our list
    const i = list.findIndex(x => (sfold(x.label.split(',')[0]) === n && distKm(x.pt, pt) < 15) || (x.rk <= 1 && distKm(x.pt, pt) < 4));
    top.push(i >= 0 ? list.splice(i, 1)[0] : { label: townName(t[0]), pt });
  });
  return top.concat(list);
}
async function rtResolve(q) {
  const r = await geoSearch(q, true);
  if (!r.length) throw Object.assign(new Error('nf'), { code: 'nf', q });
  return r[0];
}
function rtMe() {
  return new Promise((ok, no) => {
    if (!navigator.geolocation) { no(Object.assign(new Error('unavail'), { code: 'unavail' })); return; }
    navigator.geolocation.getCurrentPosition(p => ok({ label: '', pt: { lat: p.coords.latitude, lon: p.coords.longitude } }),
      e => no(Object.assign(new Error('geo'), { code: e && e.code === 1 ? 'denied' : 'unavail' })),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 120000 });
  });
}
async function rtFetch(a, b) {
  const ll = p => p.lon.toFixed(5) + ',' + p.lat.toFixed(5);
  let r;
  try { r = await fetch(RT_OSRM + ll(a) + ';' + ll(b) + '?overview=full&geometries=geojson&alternatives=false&steps=false', { credentials: 'omit' }); }
  catch (e) { throw Object.assign(new Error('net'), { code: 'net' }); }
  const j = r.ok || r.status === 400 ? await r.json().catch(() => null) : null;
  if (!j) throw Object.assign(new Error('route ' + r.status), { code: 'net' });
  if (j.code !== 'Ok' || !j.routes || !j.routes.length) throw Object.assign(new Error(j.code || 'noroute'), { code: 'noroute' });
  const x = j.routes[0];
  return { km: x.distance / 1000, min: x.duration / 60, line: x.geometry.coordinates };
}
// the route on a flat plane in km (good to a few per cent across the region); points closer than 150 m to the last
// kept one are skipped. a = the distance along the route, scaled to the router's own length.
function rtGeom(R) {
  const L = R.line, lat0 = L[Math.floor(L.length / 2)][1] * Math.PI / 180, kx = 111.32 * Math.cos(lat0), ky = 110.57;
  const P = [], bb = [Infinity, Infinity, -Infinity, -Infinity];
  let acc = 0, prev = null;
  L.forEach((c, i) => {
    const p = { x: c[0] * kx, y: c[1] * ky };
    if (prev) {
      const dd = Math.hypot(p.x - prev.x, p.y - prev.y);
      if (dd < 0.15 && i < L.length - 1) return;
      acc += dd;
    }
    p.a = acc; P.push(p); prev = p;
    bb[0] = Math.min(bb[0], p.x); bb[1] = Math.min(bb[1], p.y); bb[2] = Math.max(bb[2], p.x); bb[3] = Math.max(bb[3], p.y);
  });
  const k = acc > 0 ? R.km / acc : 1;
  return { P, kx, ky, bb, k };
}
function rtDist(G, s) {
  const x = s.lon * G.kx, y = s.lat * G.ky;
  if (x < G.bb[0] - RT_MAXR || x > G.bb[2] + RT_MAXR || y < G.bb[1] - RT_MAXR || y > G.bb[3] + RT_MAXR) return null;
  const P = G.P;
  let best = Infinity, at = 0;
  if (P.length === 1) best = (x - P[0].x) ** 2 + (y - P[0].y) ** 2;
  for (let i = 1; i < P.length; i++) {
    const a = P[i - 1], b = P[i], dx = b.x - a.x, dy = b.y - a.y, l2 = dx * dx + dy * dy;
    let t = l2 ? ((x - a.x) * dx + (y - a.y) * dy) / l2 : 0;
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    const qx = a.x + t * dx - x, qy = a.y + t * dy - y, dd = qx * qx + qy * qy;
    if (dd < best) { best = dd; at = a.a + t * Math.sqrt(l2); }
  }
  const dk = Math.sqrt(best);
  return dk <= RT_MAXR ? { d: dk, at: at * G.k } : null;
}
function rtUsable(s) {
  if ((s.dc || 0) < 50 || isOff(s) || (teslaOnly(s) && !TESLA) || !isFinite(s.lat) || !isFinite(s.lon)) return false;
  const car = carSpec();
  return !car || dcUsable(s, car);
}
function rtList() {
  const all = (RT.cand || []).filter(x => x.d <= RT.r && rtUsable(x.s)).sort((a, b) => a.at - b.at || a.d - b.d);
  const ok = all.filter(x => ver(x.s) === 'ok');
  const every = !state.ok && (RT.nep || !ok.length);
  const rows = every ? all : ok;
  return { rows, every, more: !every && !state.ok ? all.length - ok.length : 0 };
}
function rtDur(min) {
  const m = Math.max(1, Math.round(min / 5) * 5), h = Math.floor(m / 60), r = m % 60;
  return h ? T.rt_h.replace('{h}', h).replace('{m}', r) : T.rt_m.replace('{m}', m);
}
// the longest stretch without a fast charger: start → first, between two, last → destination
function rtGap(rows) {
  if (!RT.route) return 0;
  let last = 0, g = 0;
  rows.forEach(x => { g = Math.max(g, x.at - last); last = x.at; });
  return Math.max(g, RT.route.km - last);
}
function rtRow(x) {
  const s = x.s, k = kind(s), pw = power(s), ps = priceShort(s), a = navPref(), tags = [];
  if (ver(s) !== 'ok') tags.push('<span class="tag warn">' + ICON.warn + esc(ver(s) === 'src' ? T.v_src_short : T.v_nep) + '</span>');
  if (closedNow(s)) tags.push('<span class="tag">' + ICON.clock + esc(T.closed_now) + '</span>');
  if (s.ax && s.ax.t) tags.push('<span class="tag">' + esc(tr(s.ax.t)) + '</span>');
  else if (s.acc === 'customers') tags.push('<span class="tag">' + esc(T.customers) + '</span>');
  const off = x.d < 0.3 ? T.rt_on : T.rt_off.replace('{d}', fmtDist(x.d));
  return '<li class="nr rt-row">' +
    '<button class="nr-main" type="button" data-rt-open="' + esc(s.id) + '"><span class="dot ' + k + (ver(s) === 'nep' ? ' nep' : '') + '">' + (pw ? Math.round(pw) : '') + '</span>' +
    '<span class="nr-nm"><b>' + esc(title(s)) + '</b><span class="nr-sb">' + esc([netName(s), place(s)].filter(Boolean).join(' · ')) + '</span>' +
    '<span class="nr-meta"><b>' + esc(T.rt_at.replace('{km}', fmt(x.at, 0))) + '</b> · ' + esc(off) + (ps.t ? ' · <span class="nr-pr">' + esc(ps.t) + '</span>' : '') + '</span></span></button>' +
    '<a class="btn sm nr-go" href="' + esc(navUrl(a, s)) + '" target="_blank" rel="noopener" data-nav="' + a + '" data-st="' + esc(s.id) + '" aria-label="' +
    esc(T.nr_nav_to.replace('{t}', title(s)).replace('{d}', fmt(x.at, 0) + ' ' + U.km)) + '">' + ICON.nav + '<span>' + esc(T.navigate) + '</span></a>' +
    (tags.length ? '<div class="tags nr-tags">' + tags.slice(0, 2).join('') + '</div>' : '') + '</li>';
}
const FC0 = { type: 'FeatureCollection', features: [] };
function rtDraw(rows) {
  if (!map || !map.getSource('rt')) return;
  const R = RT.route;
  map.getSource('rt').setData(R ? { type: 'Feature', geometry: { type: 'LineString', coordinates: R.line }, properties: {} } : FC0);
  map.getSource('rte').setData(R ? { type: 'FeatureCollection', features: [
    { type: 'Feature', geometry: { type: 'Point', coordinates: R.line[0] }, properties: { e: 'a' } },
    { type: 'Feature', geometry: { type: 'Point', coordinates: R.line[R.line.length - 1] }, properties: { e: 'b' } }] } : FC0);
  map.getSource('rts').setData(R && rows ? { type: 'FeatureCollection', features: rows.map(x => feat(x.s)) } : FC0);
}
function rtClear() { RT.shown = false; RT.min = false; if (map && map.getSource('rt')) { map.getSource('rt').setData(FC0); map.getSource('rte').setData(FC0); map.getSource('rts').setData(FC0); } }
function rtFit() {
  if (!map || !RT.route) return;
  const b = new maplibregl.LngLatBounds(RT.route.line[0], RT.route.line[0]);
  RT.route.line.forEach(c => b.extend(c));
  const pad = window.innerWidth > 900 ? { top: 60, bottom: 60, left: 50, right: 420 } : { top: 50, bottom: 100, left: 30, right: 30 };
  map.fitBounds(b, { padding: pad, maxZoom: 13, duration: 900 });
}
function rtBtnPaint() {
  if (!$rtBtn) return;
  const v = $rtBtn.querySelector('[data-rtlbl]'), on = !!(RT.route && RT.to);
  $rtBtn.classList.toggle('is-set', on);
  if (v) v.textContent = on ? T.rt_btn_set.replace('{t}', RT.to.label.split(',')[0]).replace('{n}', rtList().rows.length) : T.rt_btn_sub;
}
const RT_ERR = { nf: 'rt_nf', denied: 'rt_denied', unavail: 'rt_unavail', noroute: 'rt_noroute', same: 'rt_same', need: 'rt_need', net: 'rt_err' };
function rtBody(fit) {
  const box = $card.querySelector('.rt-res');
  if (!box) return;
  let h = '';
  if (RT.wait) h = '<p class="nr-wait" role="status"><span class="nr-spin" aria-hidden="true"></span>' + esc(T.rt_wait) + '</p>';
  else if (RT.err) h = '<p class="nr-msg" role="alert">' + esc((T[RT_ERR[RT.err] || 'rt_err'] || '').replace('{q}', RT.errq || '')) + '</p>';
  else if (RT.route) {
    const r = rtList(), R = RT.route, car = carSpec(), a = navPref(), gap = rtGap(r.rows);
    const out = R.line.some(c => c[0] < 13 || c[0] > 23.6 || c[1] < 39.5 || c[1] > 46.6);
    h = '<p class="rt-sum"><b>' + esc(fmt(R.km, 0) + ' ' + U.km) + '</b> · ' + esc(rtDur(R.min)) + '</p>' +
      '<p class="addr">' + esc((r.every ? T.rt_sub_all : T.rt_sub).replace('{r}', RT.r)) + (car ? ' ' + esc(T.rt_car.replace('{car}', carName(car))) : '') + '</p>' +
      '<button class="btn rt-mapbtn" type="button" data-rt="map">' + ICON.road + '<span>' + esc(T.rt_map) + '</span></button>' +
      '<div class="nr-chips rt-chips" role="group" aria-label="' + esc(T.rt_r_l) + '">' + RT_RS.map(x => '<button class="chip" type="button" data-rt-r="' + x + '" aria-pressed="' + (x === RT.r) + '">' + esc(T.rt_r.replace('{r}', x)) + '</button>').join('') + '</div>' +
      (r.rows.length ? '<ol class="nrl rtl">' + r.rows.map(rtRow).join('') + '</ol>' : '<p class="nr-msg">' + esc(T.rt_none.replace('{r}', RT.r)) + '</p>') +
      (r.more ? '<p class="nr-more"><button class="lnkbtn" type="button" data-rt="nep">' + esc(T.rt_nep.replace('{n}', r.more)) + '</button></p>' : '') +
      (gap >= 100 ? '<p class="nr-msg rt-gap">' + ICON.warn + '<span>' + esc(T.rt_gap.replace('{x}', fmt(gap, 0) + ' ' + U.km)) + '</span></p>' : '') +
      (out ? '<p class="nr-msg">' + esc(T.rt_area) + '</p>' : '') +
      '<a class="btn rt-dest" href="' + esc(navUrl(a, RT.to.pt)) + '" target="_blank" rel="noopener" data-nav="' + a + '" data-st="">' + ICON.nav + '<span>' + esc(T.rt_dest) + '</span></a>';
    rtDraw(r.rows);
    RT.shown = true;
    if (fit) rtFit();
  }
  box.innerHTML = h + '<p class="nr-note">' + esc(T.rt_privacy) + '</p>' +
    '<p class="nr-note rt-attr">' + esc(T.rt_attr) + ' · <a href="https://www.openstreetmap.org/fixthemap" target="_blank" rel="noopener">' + esc(T.rt_fix) + '</a></p>';
  fxCard();
  rtBtnPaint();
}
function rtField(id, lab, ph, val) {
  return '<div class="rt-f"><label for="' + id + '">' + esc(lab) + '</label><div class="rt-in"><input class="input" id="' + id + '" type="text" autocomplete="off" spellcheck="false" enterkeyhint="search" placeholder="' + esc(ph) + '" value="' + esc(val) + '"' +
    ' role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="' + id + '-l">' +
    (id === 'rt-from' ? '<button class="rt-loc" type="button" data-rt="me" title="' + esc(T.rt_me) + '" aria-label="' + esc(T.rt_me) + '">' + ICON.loc + '</button>' : '') +
    '</div><ul class="rt-sug" id="' + id + '-l" role="listbox" hidden></ul></div>';
}
function rtPanel(source) {
  rtPopClose();
  if (sel) { sel = null; history.replaceState(null, '', location.pathname + location.search); renderList(); }
  nearOpen = false; cardNear = false; cardRt = false; rtOpen = true; RT.min = false;
  carOpen = false;
  if (map && map.getSource('sel')) map.getSource('sel').setData(FC0);
  $card.innerHTML = '<div class="ccard rtp" role="dialog" aria-label="' + esc(T.rt_title) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(T.rt_title) + '</h2><p class="addr">' + esc(T.rt_lead) + '</p><p class="nr-note rt-tip">' + esc(T.rt_tip) + '</p>' +
    '<form class="rt-form" novalidate>' + rtField('rt-from', T.rt_from, T.rt_me, RT.from ? RT.from.label : '') + rtField('rt-to', T.rt_to, T.rt_to_ph, RT.to ? RT.to.label : '') +
    '<button class="btn dark rt-go" type="submit">' + ICON.road + '<span>' + esc(T.rt_go) + '</span></button></form><div class="rt-res" aria-live="polite"></div></div>';
  $card.classList.add('is-open');
  rtBody(!!RT.route);
  const f = $card.querySelector(RT.to ? '.x' : '#rt-to');
  if (f && (window.innerWidth > 900 || RT.to)) f.focus({ preventScroll: true });
  if (source) track('map_route_open', { source });
}
function rtClose() {
  rtOpen = false;
  RT.job = null;
  $card.classList.remove('is-open');
  $card.innerHTML = '';
  rtClear();
  if ($rtBtn && window.innerWidth > 900) $rtBtn.focus({ preventScroll: true });
}
async function rtRun() {
  const fin = $card.querySelector('#rt-from'), tin = $card.querySelector('#rt-to');
  if (!fin || !tin) return;
  rtSugHide();
  const fq = fin.value.trim(), tq = tin.value.trim();
  const job = RT.job = {};
  RT.err = ''; RT.errq = '';
  if (!tq) { RT.route = null; RT.err = 'need'; rtClear(); rtBody(); tin.focus(); return; }
  RT.wait = true; rtBody();
  try {
    const to = RT.to && RT.to.pt && RT.to.label === tq ? RT.to : await rtResolve(tq);
    const from = !fq ? await rtMe() : RT.from && RT.from.pt && RT.from.label === fq ? RT.from : await rtResolve(fq);
    if (RT.job !== job) return;
    if (distKm(from.pt, to.pt) < 0.3) throw Object.assign(new Error('same'), { code: 'same' });
    const R = await rtFetch(from.pt, to.pt);
    if (RT.job !== job) return;
    const G = rtGeom(R), cand = [];
    ST.forEach(s => { if ((s.dc || 0) >= 50) { const x = rtDist(G, s); if (x) cand.push({ s, d: x.d, at: x.at }); } });
    RT.from = fq ? from : null; RT.to = to; RT.route = R; RT.cand = cand; RT.nep = false; RT.wait = false;
    if (!fq) { me = from.pt; showMe(); }
    if (tin.value.trim() === tq) tin.value = to.label;
    if (fq && fin.value.trim() === fq) fin.value = from.label;
    rtBody(true);
    track('map_route', { ok: true, km: Math.round(R.km), rows: rtList().rows.length, radius: RT.r, from_me: !fq, car: !!CAR, confirmed_only: state.ok });
  } catch (e) {
    if (RT.job !== job) return;
    RT.wait = false; RT.route = null; RT.err = e.code || 'net'; RT.errq = e.q || '';
    rtClear(); rtBody();
    track('map_route', { ok: false, error: RT.err });
  }
}
// address suggestions under the field being typed in (Photon), after a short pause
let rtT = 0;
function rtSugHide() {
  $card.querySelectorAll('.rt-sug').forEach(u => { u.hidden = true; u.innerHTML = ''; });
  $card.querySelectorAll('.rt-in input').forEach(i => i.setAttribute('aria-expanded', 'false'));
}
function rtSug(inp) {
  clearTimeout(rtT);
  const key = inp.id === 'rt-from' ? 'from' : 'to', q = inp.value.trim(), ul = d.getElementById(inp.id + '-l');
  if (RT[key] && RT[key].label !== inp.value.trim()) RT[key] = null;
  if (q.length < 3 || !ul) { if (ul) { ul.hidden = true; ul.innerHTML = ''; } return; }
  rtT = setTimeout(() => {
    geoSearch(q).then(list => {
      if (!inp.isConnected || inp.value.trim() !== q || d.activeElement !== inp) return;
      RT.sug = list;
      ul.innerHTML = list.map((x, i) => '<li role="option"><button type="button" data-sug="' + i + '" data-for="' + key + '">' + ICON.pin + '<span>' + esc(x.label) + '</span></button></li>').join('');
      ul.hidden = !list.length;
      inp.setAttribute('aria-expanded', String(!!list.length));
    }, () => {});
  }, 300);
}
function rtClick(t) {
  if (!rtOpen) {
    if (sel && cardRt && t.closest('[data-rt="back"]')) { rtPanel(); return true; }
    return false;
  }
  const sg = t.closest('[data-sug]');
  if (sg) {
    const x = RT.sug && RT.sug[+sg.dataset.sug];
    if (x) {
      RT[sg.dataset.for] = x;
      const inp = $card.querySelector(sg.dataset.for === 'from' ? '#rt-from' : '#rt-to');
      if (inp) inp.value = x.label;
      rtSugHide();
      if (sg.dataset.for === 'to' || $card.querySelector('#rt-to').value.trim()) rtRun();
      else { const ti = $card.querySelector('#rt-to'); if (ti) ti.focus(); }
    }
    return true;
  }
  const op = t.closest('[data-rt-open]');
  if (op) { const s = ST.find(x => x.id === op.dataset.rtOpen); if (s) openCard(s, true, 'rt'); return true; }
  const rr = t.closest('[data-rt-r]');
  if (rr) { RT.r = +rr.dataset.rtR; rtBody(false); track('map_route_radius', { radius: RT.r }); return true; }
  const b = t.closest('[data-rt]');
  if (!b) { if (!t.closest('.rt-f')) rtSugHide(); return false; }
  const k = b.dataset.rt;
  if (k === 'nep') { RT.nep = true; rtBody(false); }
  else if (k === 'map') {
    // phone: the sheet covers the map — hide it and keep the route; a tap on a charger opens its card with "← back"
    rtOpen = false; RT.min = true;
    $card.classList.remove('is-open'); $card.innerHTML = '';
    const w = d.querySelector('.map-wrap'); if (w) w.scrollIntoView({ behavior: 'smooth', block: 'center' });
    rtFit();
  }
  else if (k === 'me') { const fi = $card.querySelector('#rt-from'); if (fi) { fi.value = ''; RT.from = null; } if ($card.querySelector('#rt-to').value.trim()) rtRun(); else $card.querySelector('#rt-to').focus(); }
  return true;
}
if ($rtBtn) $rtBtn.addEventListener('click', () => (rtOpen ? rtClose() : rtPanel('button')));
$card.addEventListener('submit', e => { if (e.target.closest('.rt-form')) { e.preventDefault(); rtRun(); } });
$card.addEventListener('input', e => { if (e.target.closest('.rt-in')) rtSug(e.target); });
$card.addEventListener('keydown', e => {
  const t = e.target;
  if (e.key === 'Escape' && t.closest('.rt-f') && $card.querySelector('.rt-sug:not([hidden])')) { rtSugHide(); e.stopPropagation(); return; }
  if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && t.closest('.rt-f')) {
    const box = t.closest('.rt-f'), bs = [...box.querySelectorAll('.rt-sug button')];
    if (!bs.length) return;
    e.preventDefault();
    const i = bs.indexOf(t), n = e.key === 'ArrowDown' ? i + 1 : i - 1;
    if (n < 0) box.querySelector('input').focus(); else bs[Math.min(n, bs.length - 1)].focus();
  }
});

// ---------- the destination picked on the map (owner's request 26.10.2026) ----------
// A tap on the name of a city, town or village of the base map, a long press (touch, ~550 ms without moving) or a right
// click anywhere opens a small popup at that place: its name, "Punjači na putu dovde" (the route from the reader's
// location or the start already set) and "Polazak odavde". A name tapped on the map comes from the map tiles (nothing is
// sent anywhere); a pressed point is named by Photon's reverse lookup (the browser sends Photon that point), or
// "Izabrana tačka" when that fails. A long press on a charger opens the charger, as a tap does. Not while "Dodaj punjač"
// places its pin, and only where the page has the route ($rtBtn: not on the country maps of blokvolt.com).
const RT_REV = 'https://photon.komoot.io/reverse', PLACE_CLS = new Set(['city', 'town', 'village', 'hamlet', 'suburb']);
const CYR_RE = /[Ѐ-ӿ]/;
let rtPop = null, lpAt = 0;
// the label's name in the page language: Latin script on the Serbian and English page, as the rest of the route panel
function placeName(p) {
  if (LANG === 'ru') return String(p['name:ru'] || p['name:sr'] || p.name || p['name:latin'] || '').trim();
  let n = (LANG === 'en' && (p['name:en'] || p.name_en)) || p['name:sr-Latn'] || latn(p.name || '');
  if (!n || CYR_RE.test(n)) n = p['name:latin'] || p.name_int || n;
  return String(n || '').trim();
}
function placeAt(p) {
  const r = matchMedia('(pointer: coarse)').matches ? 10 : 4;
  let fs = [];
  try { fs = map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]]); } catch (e) { return null; }
  const f = fs.find(x => x.sourceLayer === 'place' && x.properties && PLACE_CLS.has(x.properties.class) && x.geometry && x.geometry.type === 'Point');
  const name = f && placeName(f.properties);
  return name ? { label: name, pt: { lon: +f.geometry.coordinates[0], lat: +f.geometry.coordinates[1] } } : null;
}
const ptLabel = pt => T.rt_pt + ' ' + pt.lat.toFixed(4) + ' / ' + pt.lon.toFixed(4);
async function geoRev(pt) {
  const u = RT_REV + '?lat=' + pt.lat.toFixed(5) + '&lon=' + pt.lon.toFixed(5) + '&limit=1&lang=' + (LANG === 'ru' ? 'default' : 'en');
  const ctl = new AbortController(), tm = setTimeout(() => ctl.abort(), 6000);
  try {
    const r = await fetch(u, { signal: ctl.signal, credentials: 'omit' });
    const j = r.ok ? await r.json() : null, f = j && (j.features || [])[0];
    return (f && geoLabel(f)) || ptLabel(pt);
  } catch (e) { return ptLabel(pt); } finally { clearTimeout(tm); }
}
function rtPopClose() { if (rtPop) { const P = rtPop; rtPop = null; P.pop.remove(); } }
function rtPopPaint() {
  const P = rtPop;
  if (!P) return;
  const t = P.el.querySelector('.rtpop-t'), go = P.el.querySelector('[data-pop="to"]');
  t.innerHTML = P.label ? '<b>' + esc(P.label.split(',')[0]) + '</b>' + (P.label.indexOf(',') > 0 ? '<span>' + esc(P.label.slice(P.label.indexOf(',') + 1).trim()) + '</span>' : '')
    : '<span class="nr-spin" aria-hidden="true"></span><span>' + esc(T.rt_pop_wait) + '</span>';
  t.classList.toggle('is-wait', !P.label);
  P.el.setAttribute('aria-label', P.label || T.rt_pop_wait);
  go.setAttribute('aria-label', P.label ? T.rt_pop_go_l.replace('{t}', P.label.split(',')[0]) : T.rt_pop_go);
}
// how: 'label' (a name tapped), 'press' (long press), 'right' (right click)
function rtPopOpen(pt, label, how) {
  rtPopClose();
  const el = d.createElement('div');
  el.className = 'rtpop';
  el.setAttribute('role', 'dialog');
  el.innerHTML = '<button class="x" type="button" data-pop="x" aria-label="' + esc(T.close) + '">' + ICON.x + '</button><p class="rtpop-t" aria-live="polite"></p>' +
    '<button class="btn dark sm" type="button" data-pop="to">' + ICON.road + '<span>' + esc(T.rt_pop_go) + '</span></button>' +
    '<button class="btn sm" type="button" data-pop="from">' + ICON.pin + '<span>' + esc(T.rt_pop_from) + '</span></button>';
  const pop = new maplibregl.Popup({ closeButton: false, closeOnClick: false, closeOnMove: false, focusAfterOpen: false, maxWidth: '280px', offset: 12, className: 'bv-pop' })
    .setLngLat([pt.lon, pt.lat]).setDOMContent(el).addTo(map);
  const P = rtPop = { pt, label, how, el, pop };
  pop.on('close', () => { if (rtPop === P) rtPop = null; });
  P.wait = label ? Promise.resolve(label) : geoRev(pt).then(l => { P.label = l; if (rtPop === P) rtPopPaint(); return l; });
  rtPopPaint();
  el.addEventListener('click', e => { const b = e.target.closest('[data-pop]'); if (b) rtPopPick(b.dataset.pop); });
  el.addEventListener('keydown', e => { if (e.key === 'Escape') { e.stopPropagation(); rtPopClose(); map.getCanvas().focus(); } });
  // the keyboard reaches the buttons at once (a tap on a phone does not move the focus, so no keyboard pops up)
  if (!matchMedia('(pointer: coarse)').matches) el.querySelector('[data-pop="to"]').focus({ preventScroll: true });
  track('map_pick_open', { how });
}
async function rtPopPick(k) {
  const P = rtPop;
  if (!P || k === 'x') { rtPopClose(); return; }
  const label = P.label || await P.wait;
  if (rtPop !== P) return;
  rtPopClose();
  const x = { label, pt: P.pt };
  // a start typed in the open panel but not yet looked up is kept
  const fin = rtOpen && $card.querySelector('#rt-from'), keep = fin && !RT.from ? fin.value.trim() : '';
  if (k === 'to') RT.to = x; else RT.from = x;
  rtPanel('map_' + P.how);
  const fi = $card.querySelector('#rt-from'), ti = $card.querySelector('#rt-to');
  if (keep && fi && k === 'to') fi.value = keep;
  track('map_pick', { how: P.how, as: k });
  if (k === 'to' || (ti && ti.value.trim())) rtRun();
  else if (ti && window.innerWidth > 900) ti.focus({ preventScroll: true });
}
// a tap on the map that hit no charger: the name of a place under it, if any (the popup closes otherwise)
function rtTapPlace(p) {
  if (!$rtBtn || adding) return false;
  const pl = placeAt(p);
  if (pl) rtPopOpen(pl.pt, pl.label, 'label'); else rtPopClose();
  return !!pl;
}
// long press (touch) and right click: a charger under it opens as with a tap; else the popup at the pressed point
function rtPress(cx, cy, how) {
  if (!map || Date.now() - lpAt < 800) return;   // Android sends both the long press and a contextmenu
  lpAt = Date.now();
  if (adding) return;
  const b = map.getCanvas().getBoundingClientRect(), p = new maplibregl.Point(cx - b.left, cy - b.top);
  if (mapTap(p)) return;
  if (!$rtBtn) return;
  const pl = placeAt(p);
  if (pl) { rtPopOpen(pl.pt, pl.label, how); return; }
  const ll = map.unproject(p);
  rtPopOpen({ lon: ll.lng, lat: ll.lat }, null, how);
}
function pressInit() {
  const box = map.getCanvasContainer();
  let tm = 0, sx = 0, sy = 0, tAt = 0, fired = false;
  const stop = () => { clearTimeout(tm); tm = 0; };
  box.addEventListener('touchstart', e => {
    stop();
    tAt = Date.now(); fired = false;
    if (e.touches.length !== 1) return;   // a pinch never opens it
    sx = e.touches[0].clientX; sy = e.touches[0].clientY;
    tm = setTimeout(() => { tm = 0; fired = true; rtPress(sx, sy, 'press'); }, 550);
  }, { passive: true });
  box.addEventListener('touchmove', e => {
    if (tm && (e.touches.length !== 1 || Math.hypot(e.touches[0].clientX - sx, e.touches[0].clientY - sy) > 10)) stop();
  }, { passive: true });
  // a finger lifted after a long press may still send a click: it must not close the popup that just opened
  box.addEventListener('touchend', () => { stop(); if (fired) lpAt = Date.now(); }, { passive: true });
  box.addEventListener('touchcancel', stop, { passive: true });
  // the browser's own menu never opens over the map (right click, and the long press of Android)
  box.addEventListener('contextmenu', e => { e.preventDefault(); stop(); rtPress(e.clientX, e.clientY, Date.now() - tAt < 1500 ? 'press' : 'right'); });
  map.on('dragstart', stop);
  map.on('zoomstart', stop);
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
// Serbia and the neighbouring countries are two sources: the neighbours are drawn quieter, under Serbia's chargers
function data(rg) { return { type: 'FeatureCollection', features: visible().filter(s => !s.cc === !rg).map(feat) }; }
function setData() {
  if (map && map.getSource('st')) map.getSource('st').setData(data());
  if (map && map.getSource('rg')) map.getSource('rg').setData(data(true));
}
function refresh() {
  state.lim = 20;
  setData();
  renderList();
  if (rtOpen && RT.route) rtBody(false);
  else if (cardRt && RT.shown) rtDraw(rtList().rows);
  rtBtnPaint();
}
// One tap handler for Serbia and the region. The dots are small on the country view, so a tap looks at a small box
// around the finger (larger on touch screens): one charger there opens its card; several zoom the map in on them
// (at least two steps, at most zoom 14), and from zoom 13 the dot nearest to the tap opens. true = a charger was hit.
function mapTap(p) {
  const r = window.matchMedia && matchMedia('(pointer: coarse)').matches ? 14 : 8;
  const hits = map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]], { layers: NRG ? ['pt', 'rg-pt'] : ['pt'] });
  if (!hits.length) return false;
  rtPopClose();
  const ids = new Set(hits.map(f => f.properties.id)), z0 = map.getZoom();
  if (ids.size > 1 && z0 < 13) {
    const b = new maplibregl.LngLatBounds();
    hits.forEach(f => b.extend(f.geometry.coordinates));
    const cam = map.cameraForBounds(b, { padding: 60 });
    userMove = true;
    map.easeTo({ center: b.getCenter(), zoom: Math.min(14, Math.max(z0 + 2, cam && isFinite(cam.zoom) ? cam.zoom : 0)) });
    track('map_zoom_in_tap', { n: ids.size });
    return true;
  }
  let best = hits[0], bd = Infinity;
  hits.forEach(f => {
    const q = map.project(f.geometry.coordinates), dd = (q.x - p.x) * (q.x - p.x) + (q.y - p.y) * (q.y - p.y);
    if (dd < bd) { bd = dd; best = f; }
  });
  const s = ST.find(x => x.id === best.properties.id);
  if (s) openCard(s, false);
  return true;
}
function initMap() {
  map = new maplibregl.Map({
    container: 'map', style: cfg.style, center: C0, zoom: Z0, minZoom: 5, maxZoom: 18,
    attributionControl: false, cooperativeGestures: false, dragRotate: false, pitchWithRotate: false
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  if (cfg.add && cfg.api) map.addControl(new AddControl(), 'top-right');
  map.on('load', () => {
    const font = cfg.font;
    // Every charger is drawn at every zoom, no number clusters (owner's decision 20.10.2026): small dots on the
    // country view that grow as the reader zooms in. Within a layer, working and confirmed chargers are drawn above
    // the faded ones, and fast DC above the rest (circle-sort-key: the higher key is drawn on top).
    const nep = ['any', ['==', ['get', 'v'], 'nep'], ['==', ['get', 'v'], 'cl']];
    const zr = (a, b, c, e) => ['interpolate', ['linear'], ['zoom'], 5, a, 8, b, 12, c, 16, e];
    if (NRG) {
      // the neighbouring countries under Serbia's layers: white points with a grey ring, smaller and quieter
      map.addSource('rg', { type: 'geojson', data: data(true) });
      map.addLayer({ id: 'rg-pt', type: 'circle', source: 'rg',
        layout: { 'circle-sort-key': ['match', ['get', 'k'], 'dc', 1, 0] },
        paint: {
          'circle-radius': zr(2, 3.5, 8, 11),
          'circle-color': ['match', ['get', 'k'], 'dc', '#5C6270', '#FFFFFF'], 'circle-opacity': 0.85,
          'circle-stroke-width': zr(0.8, 1.2, 2, 2), 'circle-stroke-color': '#8A909B'
        } });
      map.addLayer({ id: 'rg-kw', type: 'symbol', source: 'rg', minzoom: 12,
        layout: { 'text-field': ['to-string', ['get', 'p']], 'text-font': font, 'text-size': 10, 'text-allow-overlap': true },
        paint: { 'text-color': ['match', ['get', 'k'], 'dc', '#FFFFFF', '#3A3F4A'] } });
    }
    map.addSource('st', { type: 'geojson', data: data() });
    map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addSource('me', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'pt', type: 'circle', source: 'st',
      layout: { 'circle-sort-key': ['+', ['case', nep, 0, 10], ['match', ['get', 'k'], 'dc', 4, 'free', 3, 'tesla', 2, 'off', 0, 1]] },
      paint: {
        'circle-radius': zr(3, 4.5, 9, 12),
        'circle-color': ['match', ['get', 'k'], 'dc', '#0D111A', 'free', '#D9F45B', 'off', '#E3E5E9', 'tesla', '#E3E5E9', '#FFFFFF'],
        'circle-opacity': ['case', nep, 0.5, 1],
        'circle-stroke-width': zr(1.2, 1.6, 2.5, 2.5),
        'circle-stroke-opacity': ['case', nep, 0.55, 1],
        'circle-stroke-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#8A909B', 'tesla', '#5C6270', '#0D111A']
      } });
    // favourites: a ring around the point
    map.addLayer({ id: 'pt-fav', type: 'circle', source: 'st', filter: ['==', ['get', 'f'], 1],
      paint: { 'circle-radius': zr(6, 8, 14, 17), 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-width': zr(1.6, 2, 2.5, 2.5), 'circle-stroke-color': '#6E8A12' } });
    map.addLayer({ id: 'pt-kw', type: 'symbol', source: 'st', minzoom: 12,
      layout: { 'text-field': ['to-string', ['get', 'p']], 'text-font': font, 'text-size': 10, 'text-allow-overlap': true },
      paint: { 'text-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#5C6270', 'tesla', '#3A3F4A', '#0D111A'] } });
    // price next to the pin from zoom 12: 0 RSD / RSD per kWh from a receipt / ~ estimate from the per-minute tariff / ?
    map.addLayer({ id: 'pt-pr', type: 'symbol', source: 'st', filter: ['!=', ['get', 'pl'], ''], minzoom: 12,
      layout: { 'text-field': ['get', 'pl'], 'text-font': font, 'text-size': 11.5, 'text-anchor': 'left', 'text-offset': [1.25, 0], 'text-padding': 2 },
      paint: { 'text-color': ['match', ['get', 'pc'], 'free', '#3F5206', 'old', '#8A909B', 'unk', '#8A909B', '#0D111A'], 'text-halo-color': '#FFFFFF', 'text-halo-width': 2.4 } });
    // "Punjači na putu": the route under the chargers, its fast chargers as larger dark points with a lime ring
    map.addSource('rt', { type: 'geojson', data: FC0 });
    map.addSource('rts', { type: 'geojson', data: FC0 });
    map.addSource('rte', { type: 'geojson', data: FC0 });
    const below = NRG ? 'rg-pt' : 'pt';
    map.addLayer({ id: 'rt-case', type: 'line', source: 'rt', layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: { 'line-color': '#FFFFFF', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 5, 12, 10] } }, below);
    map.addLayer({ id: 'rt-line', type: 'line', source: 'rt', layout: { 'line-join': 'round', 'line-cap': 'round' },
      paint: { 'line-color': '#2E6BFF', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 3, 12, 6], 'line-opacity': 0.9 } }, below);
    // the fast chargers of the route: a blue halo (the route's colour) under their own points
    map.addLayer({ id: 'rts', type: 'circle', source: 'rts',
      paint: { 'circle-radius': zr(6, 8, 14, 17), 'circle-color': 'rgba(46,107,255,.2)', 'circle-stroke-width': zr(1.6, 2, 2.5, 2.5), 'circle-stroke-color': '#2E6BFF' } });
    map.addLayer({ id: 'sel', type: 'circle', source: 'sel',
      paint: { 'circle-radius': zr(9, 11, 16, 16), 'circle-color': 'rgba(217,244,91,.35)', 'circle-stroke-width': 3, 'circle-stroke-color': '#0D111A' } }, 'pt');
    map.addLayer({ id: 'rte', type: 'circle', source: 'rte',
      paint: { 'circle-radius': 7, 'circle-color': ['match', ['get', 'e'], 'a', '#FFFFFF', '#0D111A'], 'circle-stroke-width': 3,
        'circle-stroke-color': ['match', ['get', 'e'], 'a', '#2E6BFF', '#FFFFFF'] } });
    // the reader's own position ("Blizu mene", "Najbliži punjač"): a blue dot, never sent anywhere
    map.addLayer({ id: 'me-halo', type: 'circle', source: 'me', paint: { 'circle-radius': 22, 'circle-color': 'rgba(46,107,255,.16)' } });
    map.addLayer({ id: 'me-dot', type: 'circle', source: 'me', paint: { 'circle-radius': 7, 'circle-color': '#FFFFFF', 'circle-stroke-width': 4, 'circle-stroke-color': '#2E6BFF' } });
    showMe();
    if (RT.route && (rtOpen || cardRt)) { rtDraw(rtList().rows); RT.shown = true; if (rtOpen) rtFit(); }
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
    // taps: mapTap (a charger), else rtTapPlace (a place name → the route popup); long press and right click: pressInit
    const HIT = NRG ? ['pt', 'rg-pt'] : ['pt'];
    map.on('click', e => {
      if (Date.now() - lpAt < 800) return;   // the click some browsers send after a long press
      if (!mapTap(e.point)) rtTapPlace(e.point);
    });
    pressInit();
    // a pointer over a place name on a computer: it can be clicked (the route popup)
    let hov = 0;
    if ($rtBtn) map.on('mousemove', e => {
      if (hov) return;
      hov = requestAnimationFrame(() => {
        hov = 0;
        const c = map.getCanvas();
        if (adding || (c.style.cursor && c.style.cursor !== 'pointer')) return;
        const on = !!placeAt(e.point) || map.queryRenderedFeatures(e.point, { layers: HIT }).length > 0;
        c.style.cursor = on ? 'pointer' : '';
      });
    });
    HIT.forEach(l => {
      map.on('mouseenter', l, () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', l, () => { map.getCanvas().style.cursor = ''; });
    });
    if (sel) {
      map.getSource('sel').setData({ type: 'FeatureCollection', features: [feat(sel)] });
      map.jumpTo({ center: [sel.lon, sel.lat], zoom: 13, padding: padding() });
    } else if (llAt) map.jumpTo({ center: [llAt.lon, llAt.lat], zoom: 17 });
    else if (city) map.jumpTo({ center: [city.lon, city.lat], zoom: 11.2 });
  });
}

// ---------- controls ----------
function paintChips() {
  [].forEach.call($chips.querySelectorAll('.chip'), c =>
    c.setAttribute('aria-pressed', (c.dataset.f === 'ok' ? state.ok : c.dataset.f === 'cheap' ? state.cheap : c.dataset.f === state.f) ? 'true' : 'false'));
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
d.addEventListener('keydown', e => {
  if (e.key !== 'Escape' || d.querySelector('.lb')) return;
  if (rtPop) { rtPopClose(); return; }
  if (adding) { addEnd(); return; }
  if (sel || nearOpen || carOpen || rtOpen) { if (carOpen) closeCar(); else closeCard(); }
});
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
  if (t.closest('.rtp .x')) { rtClose(); return; }
  const rv = t.closest('.rtp a[data-nav]');
  if (rv) { setNavPref(rv.dataset.nav); track('map_navigate', { station: rv.dataset.st || '', app: rv.dataset.nav, from: rv.dataset.st ? 'route' : 'route_destination' }); return; }
  if (rtClick(t)) return;
  const nv = t.closest('.nrp a[data-nav]');
  if (nv) { setNavPref(nv.dataset.nav); track('map_navigate', { station: nv.dataset.st || '', app: nv.dataset.nav, from: 'nearest' }); return; }
  if (nearClick(t)) return;
  if (t.closest('[data-car-open]')) { openCar('card'); return; }
  if (t.closest('[data-evo]')) track('map_evolako', { station: sel ? sel.id : '', network: sel ? sel.net || '' : '', car: !!CAR });
});
// the "Mapu održava tim Evolako" line under the title (RUNBOOK 3.18; owner's decision 24.10.2026)
d.querySelector('.map-by a')?.addEventListener('click', () => track('map_evolako', { from: 'zaglavlje' }));

// ---------- "Dodaj punjač": a driver adds a charger the map lacks (POST /api/novi-punjac; RUNBOOK 3.11d) ----------
// Step 1: a pin in the middle of the map; the driver moves the map until the pin is on the charger ("Ovde sam" centres it
// on the driver's own position, which stays in the browser). Step 2: a short form in the card panel. Nothing is published
// before moderation; approved chargers come back from /api/novi-punjaci as "Nije potvrđeno · dodao vozač".
// Only on blokvolt.rs (cfg.add) and only in Serbia.
let adding = false, addPt = null, addAt = 0;
const $wrap = d.querySelector('.map-wrap');
const ADD_BOX = { s: 41.85, n: 46.2, w: 18.8, e: 23.05 };
const PIN = '<svg viewBox="0 0 40 52" aria-hidden="true"><path d="M20 50s-16-15.5-16-29a16 16 0 0 1 32 0c0 13.5-16 29-16 29Z" fill="#0D111A" stroke="#fff" stroke-width="2.5"/><circle cx="20" cy="21" r="6.5" fill="#D9F45B"/></svg>';
const dmy = t => { const x = new Date(t * 1000); return String(x.getDate()).padStart(2, '0') + '.' + String(x.getMonth() + 1).padStart(2, '0') + '.' + x.getFullYear(); };
const PLUGS = [['type2', 'Type 2'], ['ccs2', 'CCS2'], ['chademo', 'CHAdeMO'], ['tesla', 'Tesla'], ['schuko', T.schuko]];
function addHint(msg) { const h = $wrap.querySelector('.add-hint'); if (h) h.textContent = msg || ''; }
function addStart(source, at) {
  if (!map || adding) return;
  if (carOpen) closeCar();
  if (sel || nearOpen) closeCard();
  adding = true; addAt = Date.now();
  $wrap.classList.add('is-adding');
  const pin = d.createElement('div');
  pin.className = 'add-pin';
  pin.innerHTML = PIN + '<i></i>';
  const bar = d.createElement('div');
  bar.className = 'add-bar';
  bar.setAttribute('role', 'dialog');
  bar.setAttribute('aria-label', T.add_t);
  bar.innerHTML = '<p><b>' + esc(T.add_t) + '</b> ' + esc(T.add_step1) + '</p><p class="add-hint" aria-live="polite"></p><div class="add-acts">' +
    (navigator.geolocation ? '<button class="btn sm" type="button" data-add="here">' + ICON.pin + esc(T.add_here) + '</button>' : '') +
    '<button class="btn sm" type="button" data-add="cancel">' + esc(T.add_cancel) + '</button>' +
    '<button class="btn sm dark" type="button" data-add="next">' + esc(T.add_next) + ' →</button></div>';
  $wrap.append(pin, bar);
  bar.addEventListener('click', addBar);
  if (at) map.jumpTo({ center: [at.lon, at.lat], zoom: Math.max(map.getZoom(), 17) });
  bar.querySelector('[data-add="next"]').focus({ preventScroll: true });
  if (!at) track('map_add_start', { source: source || 'button', zoom: Math.round(map.getZoom()) });
}
function addEnd() {
  adding = false; addPt = null;
  $wrap.classList.remove('is-adding');
  $wrap.querySelectorAll('.add-pin, .add-bar').forEach(x => x.remove());
}
function addBar(e) {
  const b = e.target.closest('[data-add]');
  if (!b) return;
  const a = b.dataset.add;
  if (a === 'cancel') { addEnd(); return; }
  if (a === 'here') {
    b.disabled = true;
    navigator.geolocation.getCurrentPosition(pos => {
      b.disabled = false;
      map.jumpTo({ center: [pos.coords.longitude, pos.coords.latitude], zoom: 18 });
      addHint(T.add_here_hint);
    }, () => { b.disabled = false; addHint(T.no_location); }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 });
    return;
  }
  // "Dalje": the pin must sit on the charger, so a zoomed-out map is first brought close
  if (map.getZoom() < 15) { map.easeTo({ zoom: 17 }); addHint(T.add_zoom); return; }
  const c = map.getCenter();
  if (c.lat < ADD_BOX.s || c.lat > ADD_BOX.n || c.lng < ADD_BOX.w || c.lng > ADD_BOX.e) { addHint(T.add_out); return; }
  addPt = { lat: Math.round(c.lat * 1e6) / 1e6, lon: Math.round(c.lng * 1e6) / 1e6 };
  $wrap.querySelectorAll('.add-pin, .add-bar').forEach(x => x.remove());
  addForm();
}
function addRadio(name, opts, on) {
  return '<div class="opts" role="radiogroup">' + opts.map(o => '<label class="chip"><input type="radio" name="' + name + '" value="' + o[0] + '"' + (o[0] === on ? ' checked' : '') + '> ' + esc(o[1]) + '</label>').join('') + '</div>';
}
function addForm() {
  const pt = addPt;
  if (map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [{ type: 'Feature', geometry: { type: 'Point', coordinates: [pt.lon, pt.lat] }, properties: {} }] });
  // a charger already on the map within 60 m: probably the same one, so its card is offered first
  let dup = null, dm = Infinity;
  ST.forEach(s => { if (s.cc) return; const m = distKm(pt, s) * 1000; if (m < dm) { dm = m; dup = s; } });
  const dupHtml = dup && dm <= 60 ? '<div class="vf-warn"><p>' + esc(T.add_dup.replace('{m}', Math.max(1, Math.round(dm))).replace('{t}', title(dup))) + '</p><button class="lnkbtn" type="button" data-add-open="' + esc(dup.id) + '">' + esc(T.add_dup_open) + '</button></div>' : '';
  const ll = pt.lat.toFixed(5) + ', ' + pt.lon.toFixed(5);
  $card.innerHTML = '<div class="ccard addp" role="dialog" aria-label="' + esc(T.add_t) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(T.add_t) + '</h2><p class="addr">' + esc(T.add_lead) + '</p>' + dupHtml +
    '<form class="car-form add-form" novalidate>' +
    '<div class="field add-pt"><span>' + esc(T.add_point) + '</span><div class="w-ll"><code translate="no">' + ll + '</code><button class="btn sm" type="button" data-add-move>' + ICON.pin + '<span>' + esc(T.add_move) + '</span></button></div></div>' +
    '<label class="field"><span>' + esc(T.add_name) + '</span><input class="input" name="n" type="text" maxlength="80" autocomplete="off" placeholder="' + esc(T.add_name_ph) + '"></label>' +
    '<div class="field"><span>' + esc(T.add_kind) + '</span>' + addRadio('k', [['dc', T.k_dc], ['ac', T.k_ac], ['uticnica', T.k_ut], ['nz', T.k_nz]], 'nz') + '</div>' +
    '<div class="field"><span>' + esc(T.add_plugs) + '</span><div class="opts">' + PLUGS.map(x => '<label class="chip"><input type="checkbox" name="pl" value="' + x[0] + '"> ' + esc(x[1]) + '</label>').join('') + '</div></div>' +
    '<label class="field"><span>' + esc(T.add_kw) + '</span><input class="input" name="kw" type="text" inputmode="decimal" maxlength="5" autocomplete="off"></label>' +
    '<div class="field"><span>' + esc(T.add_acc) + '</span>' + addRadio('acc', [['svi', T.acc_svi], ['gosti', T.acc_gosti], ['nz', T.k_nz]], 'nz') + '</div>' +
    '<div class="field"><span>' + esc(T.add_fee) + '</span>' + addRadio('fee', [['besplatno', T.fee_free], ['placa', T.fee_paid], ['nz', T.k_nz]], 'nz') + '</div>' +
    '<label class="field"><span>' + esc(T.add_note) + '</span><textarea class="input" name="c" maxlength="300" rows="2" placeholder="' + esc(T.add_note_ph) + '"></textarea></label>' +
    '<label class="field"><span>' + esc(T.add_photo) + '</span><input name="foto" type="file" accept="image/*"><small>' + esc(T.photo_note) + '</small></label>' +
    '<label class="field"><span>' + esc(T.rv_name) + '</span><input class="input" name="nick" type="text" maxlength="40" autocomplete="nickname"><small>' + esc(T.add_nick_note) + '</small></label>' +
    '<label class="check add-ja"><input type="checkbox" name="ja"> <span>' + esc(T.add_ja) + '</span></label>' +
    '<input class="hp" name="hp" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">' +
    '<p class="add-msg" role="status"></p>' +
    '<div class="car-acts"><button class="btn dark" type="submit">' + esc(T.add_send) + '</button><button class="btn" type="button" data-add-cancel>' + esc(T.add_cancel) + '</button></div>' +
    '<small>' + esc(T.add_rules) + ' <a class="lnk" href="' + esc(lp('/pravila-objavljivanja/#novi-punjac')) + '">' + esc(T.rv_rules_link) + '</a></small></form></div>';
  $card.classList.add('is-open');
  const f = $card.querySelector('form'), msg = f.querySelector('.add-msg');
  const close = () => { addEnd(); $card.classList.remove('is-open'); $card.innerHTML = ''; if (map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [] }); };
  $card.querySelector('.x').addEventListener('click', close);
  f.querySelector('[data-add-cancel]').addEventListener('click', close);
  f.querySelector('[data-add-move]').addEventListener('click', () => { const p = addPt; close(); addStart('move', p); });
  const op = $card.querySelector('[data-add-open]');
  if (op) op.addEventListener('click', () => { const s = ST.find(x => x.id === op.dataset.addOpen); close(); if (s) openCard(s, true); track('map_add_dup', { station: s ? s.id : '' }); });
  f.addEventListener('submit', e => {
    e.preventDefault();
    if (!f.elements.ja.checked) { msg.textContent = T.add_err_ja; f.elements.ja.focus(); return; }
    const kwv = f.elements.kw.value.trim().replace(',', '.');
    if (kwv && !(+kwv >= 1 && +kwv <= 400)) { msg.textContent = T.add_err_kw; f.elements.kw.focus(); return; }
    const fd = new FormData();
    fd.append('lat', pt.lat); fd.append('lon', pt.lon);
    fd.append('n', f.elements.n.value); fd.append('k', f.elements.k.value || 'nz'); fd.append('kw', kwv);
    fd.append('pl', [...f.querySelectorAll('input[name=pl]:checked')].map(x => x.value).join(','));
    fd.append('acc', f.elements.acc.value || 'nz'); fd.append('fee', f.elements.fee.value || 'nz');
    fd.append('c', f.elements.c.value); fd.append('nick', f.elements.nick.value); fd.append('ja', '1');
    fd.append('t', Date.now() - addAt); fd.append('hp', f.elements.hp.value); fd.append('lang', LANG);
    const btn = f.querySelector('[type=submit]'), file = f.elements.foto.files && f.elements.foto.files[0];
    btn.disabled = true; msg.textContent = T.photo_wait;
    (file ? shrink(file).catch(() => null) : Promise.resolve(null)).then(p => {
      if (p) { fd.append('foto', p.big, 'foto.jpg'); fd.append('thumb', p.th, 'thumb.jpg'); fd.append('w', p.w); fd.append('h', p.h); }
      return post(cfg.api + '/novi-punjac', fd, true);
    }).then(j => {
      btn.disabled = false;
      if (!j.ok) { msg.textContent = j.error === 'outside' ? T.add_out : j.error === 'confirm' ? T.add_err_ja : errText(j); return; }
      track('map_add_sent', { kind: f.elements.k.value || 'nz', photo: !!file, plugs: f.querySelectorAll('input[name=pl]:checked').length });
      f.innerHTML = '<p class="add-done">' + ICON.ok + '<span>' + esc(T.add_thanks) + '</span></p><div class="car-acts"><button class="btn" type="button" data-add-cancel>' + esc(T.close) + '</button></div>';
      f.querySelector('[data-add-cancel]').addEventListener('click', close);
    }).catch(() => { btn.disabled = false; msg.textContent = T.rv_err; });
  });
}
// approved chargers from drivers (GET /api/novi-punjaci), as map stations: id vz-<n>, "Nije potvrđeno · dodao vozač"
function vzStation(x) {
  const cur = x.k === 'dc' ? 'dc' : 'ac', kw = +x.kw || 0;
  const pl = x.pl && x.pl.length ? x.pl : (x.k === 'uticnica' ? ['schuko'] : []);
  const c = pl.map(p => [p, p === 'ccs2' || p === 'chademo' ? 'dc' : p === 'tesla' ? cur : 'ac', p === 'schuko' ? null : kw || null, 1]);
  return { id: x.id, n: x.n || '', a: '', t: '', lat: +x.lat, lon: +x.lon, net: '', opn: '', c, kd: x.k,
    dc: cur === 'dc' ? kw : 0, ac: cur === 'ac' ? kw : 0, acc: x.acc === 'gosti' ? 'customers' : '',
    loc: { q: 'vz', find: x.c || '' }, src: [{ d: 'vz', l: T.src_vz, u: lp('/pravila-objavljivanja/#novi-punjac') }],
    v: { s: 'nep', g: 'vz', d: dmy(x.ok || x.at) }, vz: { fee: x.fee, acc: x.acc } };
}
function loadNovi() {
  if (!cfg.api || !cfg.add) return;
  fetch(cfg.api + '/novi-punjaci').then(r => (r.ok ? r.json() : null)).then(j => {
    if (!j || !j.ok || !j.st || !j.st.length) return;
    const have = new Set(ST.map(s => s.id)), add = j.st.filter(x => !have.has(x.id) && isFinite(x.lat) && isFinite(x.lon)).map(vzStation);
    if (!add.length) return;
    // Serbia's stations come first in ST and the region after them (NSR counts Serbia's)
    ST = ST.slice(0, NSR).concat(add, ST.slice(NSR));
    NSR += add.length;
    ST.forEach((s, i) => { s._i = i; });
    setData();
    renderList();
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && !sel && id.indexOf('vz-') === 0) { const s = ST.find(x => x.id === id); if (s) openCard(s, false); }
  }).catch(() => { /* the map works without them */ });
}
// the "Dodaj punjač" button sits under the zoom buttons
class AddControl {
  onAdd() {
    const w = d.createElement('div');
    w.className = 'maplibregl-ctrl maplibregl-ctrl-group map-addctl';
    w.innerHTML = '<button type="button" title="' + esc(T.add_t) + '"><span aria-hidden="true">+</span>' + esc(T.add_btn) + '</button>';
    w.querySelector('button').addEventListener('click', () => addStart('button'));
    return w;
  }
  onRemove() {}
}

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
  nearOpen = false; cardNear = false; carOpen = true; cardRt = false; rtOpen = false;
  if (RT.shown) rtClear();
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
    carChanged();
    carToAccount();
    closeCar();
  });
  const del = f.querySelector('[data-car-del]');
  if (del) del.addEventListener('click', () => { CAR = null; saveCar(); track('map_car_set', { removed: true }); carChanged(); carToAccount(); closeCar(); });
}
// a new car: new costs everywhere, and a Tesla makes the Tesla-only chargers usable
function carChanged() {
  COSTV++;
  TESLA = teslaNow();
  paintCar();
  refresh();
}
// the signed-in reader's car goes to the account too (the same fields as "Moj auto" on /nalog/); no car = none there
function carToAccount() {
  if (!ACC) return;
  const c = CAR && CARS && CARS.find(x => x.id === CAR.id);
  accPost('podesavanja', c ? { car_id: c.id, car: (c.mk + ' ' + c.md).slice(0, 80), car_cons: CAR.cons, car_cab: !!CAR.cab, car_opt: !!CAR.opt, dc: c.pl === 'chademo' ? 'chademo' : 'ccs2' }
    : { car_id: '', car: '', car_cons: null, car_cab: false, car_opt: false, dc: '' });
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
  const c = g && (cfg.cities || {})[g];
  if (c) city = { lat: c[0], lon: c[1] };
  // ?ll=<lat>,<lon>: the map opens close on that point (the moderation page links new chargers from drivers this way)
  const ll = (p.get('ll') || '').split(',').map(Number);
  if (ll.length === 2 && ll.every(isFinite) && Math.abs(ll[0]) <= 90 && Math.abs(ll[1]) <= 180) llAt = { lat: ll[0], lon: ll[1] };
  paintChips();
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
  TESLA = teslaNow();
  paintCar();
  // favourites of stations that are no longer on the map are dropped quietly
  const ids = new Set(ST.map(s => s.id));
  if ([...FAV].some(id => !ids.has(id))) { FAV = new Set([...FAV].filter(id => ids.has(id))); saveFav(); }
  favCount();
  fromUrl();
  loadSummaries();
  loadNovi();
  accSync();
  try { initMap(); } catch (e) { d.getElementById('map').classList.add('is-off'); }
  // scripts/qa/map_extra_test.py reads the pin data (kind, power label, price label) through this, only with ?qa=1;
  // bvMapQa(true) gives the neighbouring countries' pins (scripts/qa/map_region_test.py); bvNearQa(lat, lon, nep) gives the
  // rows of "Najbliži punjač" for a point (the apps and evolako.rs are compared with it); bvCostQa(id) the cost lines
  if (/[?&]qa=1\b/.test(location.search)) {
    window.bvMapQa = rg => data(rg).features.map(f => f.properties);
    // every station with its network and the "Kako se puni ovde" scheme it gets (scripts/qa/map_kako_test.py)
    window.bvKakoQa = () => ST.map(s => { const h = howOf(s); return { id: s.id, how: h && { k: h.k, steps: h.steps, facts: h.facts } }; });
    window.bvStQa = id => ST.find(x => x.id === id);
    window.bvNearQa = (lat, lon, nep) => nearestList({ lat, lon }, !!nep).rows.map(r => ({ id: r.s.id, t: title(r.s), m: Math.round(r.d * 1000) }));
    window.bvCostQa = id => { const s = ST.find(x => x.id === id), co = s && costOf(s); return co ? { kw: co.main.c.kw, kwh: co.main.c.kwh, km: co.main.c.km, alt: co.alt ? co.alt.c.km : null } : null; };
    // the map itself, for scripts/qa/map_nocluster_test.py (zoom, rendered dots, taps)
    window.bvMapObjQa = () => map;
    // "Punjači na putu" (scripts/qa/map_route_test.py): the rows shown, whether the route is drawn, and the rows for any
    // line [[lon, lat], …] and radius — evolako.rs is compared with it
    window.bvRouteQa = () => ({ shown: !!RT.shown, open: rtOpen, r: RT.r, km: RT.route ? RT.route.km : null,
      rows: RT.route ? rtList().rows.map(x => ({ id: x.s.id, dc: x.s.dc, v: ver(x.s), at: Math.round(x.at * 10) / 10, d: Math.round(x.d * 100) / 100 })) : [],
      line: map && map.getSource('rt') ? ((map.getSource('rt').serialize() || {}).data || {}).type || null : null });
    window.bvRouteLineQa = (line, km, r, nep) => {
      const R = { km, line }, G = rtGeom(R), out = [];
      ST.forEach(s => { if (rtUsable(s)) { const x = rtDist(G, s); if (x && x.d <= r && (nep || ver(s) === 'ok')) out.push({ id: s.id, at: x.at, d: x.d }); } });
      return out.sort((a, b) => a.at - b.at || a.d - b.d).map(x => ({ id: x.id, at: Math.round(x.at * 10) / 10, d: Math.round(x.d * 100) / 100 }));
    };
  }
}).catch(() => { $count.textContent = T.load_err; });
