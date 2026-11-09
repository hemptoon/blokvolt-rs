/* BlokVolt — world map of public chargers on blokvolt.com: /map/ (EN), /sr/mapa/, /ru/karta/ (task K2, P1 §2).
   Points: one PMTiles file (layer `sites`, attributes i p o c a s — contract v1 §3) read with the pmtiles:// protocol;
   every filter is a MapLibre expression over those attributes, so a filter never loads data. A click loads one card file
   (cards/<geohash>.json, contract §4) and keeps it in memory. manifest-YYYY-MM-DD.json (via latest.json) names the files,
   the networks (index = `o`), the sources and their licences (contract §5).
   No clusters (owner's decision 20.10.2026, RUNBOOK 3.11): zoomed out, tippecanoe drops part of the densest points; a tap
   on a group zooms in, as on /mapa/. No prices, ratings or Evolako here (RUNBOOK §0, P1 §2.3).
   State lives in the URL (contract §8): ?snaga=ac,dc,hpc,nepoznato &mreza=<slug>,… &p=40|50|70 &pristup=javni|svi
   &izvor=drz,zaj,mre,bv (Napredno) &zemlja=<cc> &grad=<geonameid> &id=<pid>, the view in the hash #z/lat/lon.
   Reports ("Prijavi grešku") go to cfg.reports_api (contract §10). This file does not touch map.js, bv.js or bv.css. */
import * as maplibregl from '/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs';

const d = document;
// read before MapLibre (hash: true) writes its own #z/lat/lon: a link with a view keeps it, zemlja/grad then do not move it
const HAD_HASH = /^#\d/.test(location.hash);
const cfg = JSON.parse(d.getElementById('wm-cfg').textContent);
const T = JSON.parse(d.getElementById('wm-i18n').textContent);
const LANG = cfg.lang;
const LOC = LANG === 'sr' ? 'sr-Latn-RS' : LANG === 'ru' ? 'ru-RU' : 'en-GB';
const t = (k, v) => {
  let s = T[k] == null ? k : T[k];
  if (v) for (const x in v) s = s.split('{' + x + '}').join(v[x]);
  return s;
};
const $ = id => d.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fold = s => String(s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
// network slug = ASCII, lowercase, hyphens (contract §7). The real slugs come from manifest.networks_slug (K1 from K4's
// networks.csv); this function is only the fallback for a manifest without them
const slug = s => fold(s).replace(/ß/g, 'ss').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const IS_TOUCH = window.matchMedia && matchMedia('(pointer: coarse)').matches;
const UA = navigator.userAgent;
const IS_ANDROID = /Android/i.test(UA), IS_IOS = /iPhone|iPad|iPod/i.test(UA);

// ------------------------------------------------------------------ state <-> URL
const SNAGA = ['ac', 'dc', 'hpc', 'nepoznato'];
const IZVOR = { drz: 1, zaj: 2, mre: 4, bv: 8 };
const PCODES = { ac: [1, 2], dc: [3, 4], hpc: [5], nepoznato: [0, 6, 7] };
const st = { snaga: new Set(SNAGA), mreza: new Set(), p: 40, pristup: 'javni', izvor: new Set(Object.keys(IZVOR)), zemlja: '', grad: '', id: '' };
function readUrl() {
  const q = new URLSearchParams(location.search);
  const list = (k, ok) => (q.get(k) || '').split(',').map(x => x.trim().toLowerCase()).filter(x => x && (!ok || ok.includes(x)));
  const sn = list('snaga', SNAGA);
  if (sn.length) st.snaga = new Set(sn);
  st.mreza = new Set(list('mreza').map(slug).filter(Boolean));
  const p = +q.get('p');
  st.p = [40, 50, 70].includes(p) ? p : 40;
  st.pristup = q.get('pristup') === 'svi' ? 'svi' : 'javni';
  const iz = list('izvor', Object.keys(IZVOR));
  if (iz.length) st.izvor = new Set(iz);
  st.zemlja = (q.get('zemlja') || '').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2);
  st.grad = (q.get('grad') || '').replace(/\D/g, '');
  st.id = (q.get('id') || '').replace(/\D/g, '');
}
function writeUrl() {
  const q = new URLSearchParams();
  if (st.snaga.size !== SNAGA.length) q.set('snaga', SNAGA.filter(x => st.snaga.has(x)).join(','));
  if (st.mreza.size) q.set('mreza', [...st.mreza].join(','));
  if (st.p !== 40) q.set('p', String(st.p));
  if (st.pristup !== 'javni') q.set('pristup', 'svi');
  if (st.izvor.size !== 4) q.set('izvor', Object.keys(IZVOR).filter(x => st.izvor.has(x)).join(','));
  if (st.zemlja) q.set('zemlja', st.zemlja);
  if (st.grad) q.set('grad', st.grad);
  if (st.id) q.set('id', st.id);
  const s = q.toString().replace(/%2C/g, ',');
  history.replaceState(history.state, '', location.pathname + (s ? '?' + s : '') + location.hash);
}

// ------------------------------------------------------------------ data
const base = cfg.data_base.replace(/\/?$/, '/');
// a manifest may name its files by absolute URL (dev: tiles on GitHub Pages, cards next to the site)
const at = u => (/^https?:\/\//.test(u) ? u : base + u);
let M = null;                     // manifest
const NETS = [];                  // [{i, name, slug, k}] index = tile attribute o
const BY_SLUG = new Map();        // slug -> [o, …]
let SPLIT = new Set();
const CARD_FILES = new Map();     // file name -> Promise<{sites}>
async function getJson(u) {
  const r = await fetch(u, { mode: 'cors' });
  if (!r.ok) throw new Error(r.status + ' ' + u);
  return r.json();
}
async function loadManifest() {
  const latest = await getJson(base + 'latest.json');
  M = await getJson(at(latest.manifest));
  SPLIT = new Set(M.cards_split || []);
  (M.networks || []).forEach((n, i) => {
    if (!i || !n) return;
    const s = (M.networks_slug && M.networks_slug[i]) || slug(n);
    NETS.push({ i, name: n, slug: s, k: fold(n) });
    if (!BY_SLUG.has(s)) BY_SLUG.set(s, []);
    BY_SLUG.get(s).push(i);
  });
  return M;
}

// geohash (base32, standard)
const GH = '0123456789bcdefghjkmnpqrstuvwxyz';
function geohash(lat, lon, n) {
  let la = [-90, 90], lo = [-180, 180], h = '', bit = 0, ch = 0, even = true;
  while (h.length < n) {
    const r = even ? lo : la, v = even ? lon : lat, mid = (r[0] + r[1]) / 2;
    if (v >= mid) { ch = (ch << 1) | 1; r[0] = mid; } else { ch <<= 1; r[1] = mid; }
    even = !even;
    if (++bit === 5) { h += GH[ch]; bit = 0; ch = 0; }
  }
  return h;
}
function cardFile(g5) {
  let L = 3;
  while (L < 5 && SPLIT.has(g5.slice(0, L))) L++;
  return g5.slice(0, L);
}
function loadCards(prefix) {
  if (!CARD_FILES.has(prefix)) {
    const p = getJson(at(M.cards_base) + prefix + '.json').catch(e => {
      CARD_FILES.delete(prefix);
      if (/^404 /.test(e.message)) return { sites: {} };
      throw e;
    });
    CARD_FILES.set(prefix, p);
  }
  return CARD_FILES.get(prefix);
}
// a tile quantises coordinates, so a point next to a cell border can sit in the neighbouring file: look there next
async function findCard(pid, lon, lat) {
  const g = geohash(lat, lon, 5), first = cardFile(g);
  const f = await loadCards(first);
  if (f.sites && f.sites[pid]) return { card: f.sites[pid], g };
  const dLat = 180 / 2 ** 12, dLon = 360 / 2 ** 13;     // size of a 5-character cell
  const seen = new Set([first]);
  for (const [a, b] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const gn = geohash(Math.max(-89.99, Math.min(89.99, lat + a * dLat)), ((lon + b * dLon + 540) % 360) - 180, 5), pre = cardFile(gn);
    if (seen.has(pre)) continue;
    seen.add(pre);
    const x = await loadCards(pre);
    if (x.sites && x.sites[pid]) return { card: x.sites[pid], g: gn };
  }
  return null;
}

// ------------------------------------------------------------------ map
let map = null, ready = false, mapLoaded = false;
const SRC = 'wm', LYR = 'wm-pt';
function pFilter() {
  const f = ['all'];
  const codes = [];
  st.snaga.forEach(k => codes.push(...PCODES[k]));
  if (codes.length < 8) f.push(['in', ['get', 'p'], ['literal', codes]]);
  if (st.mreza.size) {
    const os = [];
    st.mreza.forEach(s => { if (s === 'nepoznata') os.push(0); else (BY_SLUG.get(s) || []).forEach(o => os.push(o)); });
    f.push(['in', ['get', 'o'], ['literal', os.length ? os : [-1]]]);
  }
  if (st.p > 40) f.push(['>=', ['get', 'c'], st.p]);
  // "Samo javni": public and unknown access (P1 §2.2: unknown is shown with the public ones, its card says so)
  if (st.pristup === 'javni') f.push(['!=', ['get', 'a'], 1]);
  if (st.izvor.size < 4) {
    let m = 0;
    st.izvor.forEach(k => { m |= IZVOR[k]; });
    // bitwise "s & m != 0" without a bitwise operator in the expression language: test each bit
    const any = ['any'];
    for (const b of [1, 2, 4, 8]) if (m & b) any.push(['>=', ['%', ['get', 's'], b * 2], b]);
    f.push(any.length > 1 ? any : false);
  }
  return f.length > 1 ? f : true;
}
const zr = (a, b, c, e) => ['interpolate', ['linear'], ['zoom'], 3, a, 7, b, 12, c, 16, e];
// zoom must be the outer expression: the 150 kW+ points get larger values at every stop
const zrb = (big, x, y) => ['interpolate', ['linear'], ['zoom'], ...[3, 7, 12, 16].flatMap((z, k) => [z, ['case', big, x[k], y[k]]])];
// colours: the same language as /mapa/ — DC dark with the lime ring, AC white with the dark ring; 150 kW+ is a larger
// dark point with a thicker lime ring; unknown power is grey (dark grey when it is known to be DC)
const P_COLOR = ['match', ['get', 'p'], [3, 4, 5], '#0D111A', 7, '#5C6270', 0, '#E3E5E9', '#FFFFFF'];
const P_STROKE = ['match', ['get', 'p'], [3, 4, 5], '#D9F45B', [0, 6, 7], '#8A909B', '#0D111A'];
function addLayers() {
  if (!M || !mapLoaded || map.getSource(SRC)) return;
  map.addSource(SRC, { type: 'vector', url: 'pmtiles://' + at(M.tiles), attribution: '' });
  const big = ['==', ['get', 'p'], 5];
  map.addLayer({
    id: LYR, type: 'circle', source: SRC, 'source-layer': 'sites', filter: pFilter(),
    layout: { 'circle-sort-key': ['match', ['get', 'p'], 5, 4, [3, 4], 3, [1, 2], 2, 7, 1, 0] },
    paint: {
      'circle-radius': zrb(big, [1.8, 4, 9, 12.5], [1.2, 3, 7.5, 11]),
      'circle-color': P_COLOR,
      'circle-stroke-color': P_STROKE,
      'circle-stroke-width': zrb(big, [0.7, 1.5, 3, 3.2], [0.4, 1, 2, 2.4]),
      // restricted places (only with "Prikaži i ostale") are drawn faded
      'circle-opacity': ['case', ['==', ['get', 'a'], 1], 0.45, 1],
      'circle-stroke-opacity': ['case', ['==', ['get', 'a'], 1], 0.55, 1]
    }
  });
  // max kW inside the point from zoom 12, as on /mapa/ (tile attribute k; a point without k simply has no number)
  map.addLayer({
    id: 'wm-kw', type: 'symbol', source: SRC, 'source-layer': 'sites', minzoom: 12, filter: kwFilter(),
    layout: { 'text-field': ['to-string', ['get', 'k']], 'text-font': cfg.font, 'text-size': 10, 'text-allow-overlap': true, 'text-ignore-placement': true,
      'symbol-sort-key': ['match', ['get', 'p'], 5, 4, [3, 4], 3, [1, 2], 2, 7, 1, 0] },
    paint: { 'text-color': ['match', ['get', 'p'], [3, 4, 5], '#D9F45B', 7, '#FFFFFF', [0, 6], '#5C6270', '#0D111A'],
      'text-opacity': ['case', ['==', ['get', 'a'], 1], 0.6, 1] }
  });
  map.addSource('wm-sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer({ id: 'wm-sel', type: 'circle', source: 'wm-sel',
    paint: { 'circle-radius': zr(8, 10, 15, 18), 'circle-color': 'rgba(217,244,91,.35)', 'circle-stroke-width': 3, 'circle-stroke-color': '#0D111A' } });
  ready = true;
  map.once('idle', () => { topNets(); if (st.id) openFromUrl(); });
}
function kwFilter() {
  const f = pFilter();
  return f === true ? ['has', 'k'] : ['all', ['has', 'k'], f];
}
function applyFilter() {
  if (ready) { map.setFilter(LYR, pFilter()); map.setFilter('wm-kw', kwFilter()); }
  writeUrl();
  paintFilters();
}
function selPoint(c) {
  const s = map && map.getSource('wm-sel');
  if (s) s.setData({ type: 'FeatureCollection', features: c ? [{ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: c } }] : [] });
}

function initMap() {
  const proto = new window.pmtiles.Protocol();
  maplibregl.addProtocol('pmtiles', proto.tile);
  try {
    map = new maplibregl.Map({
      container: 'map', style: cfg.style, center: cfg.center, zoom: cfg.zoom, minZoom: 1.5, maxZoom: 18, hash: true,
      attributionControl: false, dragRotate: false, pitchWithRotate: false, cooperativeGestures: false
    });
  } catch (e) {
    msg(t('no_map'));
    return;
  }
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.on('load', () => { mapLoaded = true; addLayers(); });
  map.on('click', e => tap(e.point));
  map.on('mousemove', e => {
    if (!ready) return;
    const r = 6, hit = map.queryRenderedFeatures([[e.point.x - r, e.point.y - r], [e.point.x + r, e.point.y + r]], { layers: [LYR] });
    map.getCanvas().style.cursor = hit.length ? 'pointer' : '';
  });
  let tm = 0;
  map.on('moveend', () => { clearTimeout(tm); tm = setTimeout(topNets, 350); });
  map.on('error', e => {
    // a missing or unreachable tile file: say it once on the map (MapLibre logs the details itself only in dev)
    if (e && e.sourceId === SRC) msg(t('data_err'));
    else if (e && e.error) console.warn('map:', e.error.message || e.error);
  });
}
// a tap looks at a small box around the finger: one place opens its card, several zoom in (as on /mapa/)
function tap(p) {
  if (!ready) return;
  const r = IS_TOUCH ? 14 : 8;
  const hits = map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]], { layers: [LYR] });
  if (!hits.length) return;
  const ids = new Set(hits.map(f => f.properties.i)), z0 = map.getZoom();
  if (ids.size > 1 && z0 < 13) {
    const b = new maplibregl.LngLatBounds();
    hits.forEach(f => b.extend(f.geometry.coordinates));
    const cam = map.cameraForBounds(b, { padding: 60 });
    map.easeTo({ center: b.getCenter(), zoom: Math.min(14, Math.max(z0 + 2, cam && isFinite(cam.zoom) ? cam.zoom : 0)) });
    return;
  }
  let best = hits[0], bd = Infinity;
  hits.forEach(f => {
    const q = map.project(f.geometry.coordinates), dd = (q.x - p.x) ** 2 + (q.y - p.y) ** 2;
    if (dd < bd) { bd = dd; best = f; }
  });
  openCard(String(best.properties.i), best.geometry.coordinates, best.properties);
}
function msg(s) {
  const m = $('wm-msg');
  m.textContent = s;
  m.hidden = !s;
}

// ------------------------------------------------------------------ filters UI
const fForm = $('wm-filters');
function paintFilters() {
  fForm.querySelectorAll('[data-snaga]').forEach(b => b.setAttribute('aria-pressed', String(st.snaga.has(b.dataset.snaga))));
  fForm.querySelectorAll('[data-p]').forEach(b => b.setAttribute('aria-pressed', String(+b.dataset.p === st.p)));
  fForm.querySelectorAll('[data-pristup]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.pristup === st.pristup)));
  fForm.querySelectorAll('[data-izvor]').forEach(b => b.setAttribute('aria-pressed', String(st.izvor.has(b.dataset.izvor))));
  fForm.querySelectorAll('[data-net]').forEach(b => b.setAttribute('aria-pressed', String(st.mreza.has(b.dataset.net))));
  if (st.izvor.size < 4) $('wm-adv').open = true;
  // selected networks, each with its own "remove" chip
  const sel = $('wm-sel'), names = [...st.mreza].map(s => [s, s === 'nepoznata' ? t('net_unknown') : netName(s)]);
  sel.innerHTML = names.map(([s, n]) => `<button class="chip is-on wm-x" type="button" data-unnet="${esc(s)}" aria-label="${esc(t('net_remove', { x: n }))}">${esc(n)} <span aria-hidden="true">×</span></button>`).join('');
  $('wm-selh').hidden = !names.length;
  const n = (st.snaga.size !== 4) + st.mreza.size + (st.p !== 40) + (st.pristup !== 'javni') + (st.izvor.size !== 4);
  const fn = $('wm-fn');
  fn.textContent = n ? String(n) : '';
  fn.hidden = !n;
}
function netName(s) {
  const os = BY_SLUG.get(s);
  return os && os.length ? M.networks[os[0]] : s;
}
fForm.addEventListener('submit', e => e.preventDefault());
fForm.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b || !fForm.contains(b)) return;
  const ds = b.dataset;
  if (ds.snaga) {
    if (st.snaga.has(ds.snaga)) { if (st.snaga.size > 1) st.snaga.delete(ds.snaga); } else st.snaga.add(ds.snaga);
  } else if (ds.p) st.p = +ds.p;
  else if (ds.pristup) st.pristup = ds.pristup;
  else if (ds.izvor) {
    if (st.izvor.has(ds.izvor)) { if (st.izvor.size > 1) st.izvor.delete(ds.izvor); } else st.izvor.add(ds.izvor);
  } else if (ds.net) {
    if (st.mreza.has(ds.net)) st.mreza.delete(ds.net); else st.mreza.add(ds.net);
  } else if (ds.unnet) {
    st.mreza.delete(ds.unnet);
    const q = $('wm-q');
    applyFilter();
    q.focus();
    return;
  } else if (b.id === 'wm-reset') {
    st.snaga = new Set(SNAGA); st.mreza.clear(); st.p = 40; st.pristup = 'javni'; st.izvor = new Set(Object.keys(IZVOR));
  } else return;
  applyFilter();
});
// network search over the whole dictionary of the manifest
const q = $('wm-q'), qres = $('wm-qres');
let qTm = 0;
q.addEventListener('input', () => { clearTimeout(qTm); qTm = setTimeout(search, 120); });
function search() {
  const s = fold(q.value.trim());
  if (!s || !M) { qres.innerHTML = ''; return; }
  const seen = new Set(), out = [];
  for (const n of NETS) {
    if (seen.has(n.slug)) continue;
    const at = n.k.indexOf(s);
    if (at < 0) continue;
    seen.add(n.slug);
    out.push([at === 0 ? 0 : 1, n]);
  }
  out.sort((a, b) => a[0] - b[0] || a[1].name.length - b[1].name.length);
  qres.innerHTML = out.length
    ? out.slice(0, 8).map(([, n]) => `<button class="chip" type="button" data-net="${esc(n.slug)}" aria-pressed="${st.mreza.has(n.slug)}">${esc(n.name)}</button>`).join('')
    : `<span class="wm-empty">${esc(t('net_none'))}</span>`;
}
// the 10 most frequent networks among the points drawn in the visible part of the map
function topNets() {
  if (!ready) return;
  const cnt = new Map();
  let fs = [];
  try { fs = map.queryRenderedFeatures({ layers: [LYR] }); } catch (e) { fs = []; }
  const seen = new Set();
  for (const f of fs) {
    const o = f.properties.o, i = f.properties.i;
    if (!o || seen.has(i)) continue;
    seen.add(i);
    const s = NETS_BY_O.get(o);
    if (s) cnt.set(s, (cnt.get(s) || 0) + 1);
  }
  const top = [...cnt.entries()].sort((a, b) => b[1] - a[1]).slice(0, 10);
  $('wm-top').innerHTML = top.map(([s]) => `<button class="chip" type="button" data-net="${esc(s)}" aria-pressed="${st.mreza.has(s)}">${esc(netName(s))}</button>`).join('') +
    `<button class="chip" type="button" data-net="nepoznata" aria-pressed="${st.mreza.has('nepoznata')}">${esc(t('net_unknown'))}</button>`;
}
const NETS_BY_O = new Map();
// mobile: the filters fold under one button so the map stays on the first screen
$('wm-ft').addEventListener('click', e => {
  const open = fForm.classList.toggle('is-open');
  e.currentTarget.setAttribute('aria-expanded', String(open));
});

// ------------------------------------------------------------------ formatting
const nf = (x, dg = 0) => Number(x).toLocaleString(LOC, { maximumFractionDigits: dg });
let REGION = null;
try { REGION = new Intl.DisplayNames([LANG === 'sr' ? 'sr-Latn' : LANG], { type: 'region' }); } catch (e) { REGION = null; }
const country = cc => { try { return (REGION && cc && REGION.of(cc)) || cc || ''; } catch (e) { return cc || ''; } };
function fmtDate(iso) {
  const [y, m, dd] = String(iso || '').split('-');
  if (!y) return '';
  if (LANG === 'en') return new Date(Date.UTC(+y, +m - 1, +dd || 1)).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  return (dd ? dd + '.' : '') + m + '.' + y + (LANG === 'sr' ? '.' : '');
}
const fmtMonth = ym => {
  if (!ym) return '';
  const [y, m] = ym.split('-');
  if (LANG === 'en') return new Date(Date.UTC(+y, +m - 1, 1)).toLocaleDateString('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  return m + '.' + y + (LANG === 'sr' ? '.' : '');
};
const KW = LANG === 'ru' ? 'кВт' : 'kW';
const CONN = { TYPE2: 'Type 2', TYPE1: 'Type 1', CCS2: 'CCS2', CCS1: 'CCS1', CCS: 'CCS', CHADEMO: 'CHAdeMO', NACS_TESLA: 'NACS (Tesla)', TESLA: 'Tesla',
  SCHUKO: 'Schuko', NEMA: 'NEMA', GBT: 'GB/T', GB_T: 'GB/T', CEE: 'CEE', TYPE3: 'Type 3' };
const connName = c => CONN[String(c).toUpperCase()] || (/^other$/i.test(c) ? t('conn_other') : String(c));

// ------------------------------------------------------------------ card
// G3: ad hoc price of the network in this country (cfg.prices = /assets/world/prices-<hash>.json); never on the pin (RUNBOOK 3.11)
let PR = null, PRV = null;
function loadPrices() {
  if (!cfg.prices) return Promise.resolve(null);
  if (!PR) PR = getJson(cfg.prices).catch(() => ({ nets: {} })).then(v => (PRV = v));
  return PR;
}
const PSYM = { EUR: '€', USD: '$', GBP: '£', SEK: 'kr', NOK: 'kr', DKK: 'kr', CZK: 'Kč', PLN: 'zł', HUF: 'Ft', RON: 'lei', CHF: 'CHF' };
function pmoney(x, c) {
  const d = Math.abs(x) < 0.1 ? 3 : 2, n = Number(x).toLocaleString(LOC, { minimumFractionDigits: d, maximumFractionDigits: d }), s = PSYM[c] || c;
  return LANG === 'en' && (c === 'EUR' || c === 'USD' || c === 'GBP') ? s + n : n + '\u00a0' + s;
}
function priceRow(c, P) {
  if (!P || !P.nets) return '';
  const name = c.net || (cur && cur.props && M.networks[cur.props.o]) || '';
  const e = name && P.nets[c.cc + '|' + name];
  if (!e) return '';
  let wc = 'eur';
  try { wc = localStorage.getItem('bv:wcur') || 'eur'; } catch (err) { /* private mode */ }
  const parts = [['AC', 0, e.ac], ['DC', 1, e.dc], ['HPC', 2, e.hpc]].filter(x => x[2] != null).map(([k, i, v]) => {
    let s = pmoney(v, 'EUR');
    if (wc === 'usd' && P.rates && P.rates.USD) s = '≈\u00a0' + pmoney(v * P.rates.USD, 'USD');
    else if (wc === 'loc' && e.l && e.l[i] != null) s = pmoney(e.l[i], e.cur);
    return `${k} ${esc(s)}`;
  });
  if (!parts.length) return '';
  const u = e.u && e.u[LANG];
  let h = `${parts.join(' · ')} <small>${esc(t('c_price_kwh'))}</small><br><small>${esc(t('c_price_note', { d: fmtDate(e.d) }))}</small>`;
  if (e.old) h += `<br><small class="wm-old">${esc(t('c_price_old'))}</small>`;
  if (u) h += `<br><a href="${esc(u)}">${esc(t('c_price_more'))}</a>`;
  return `<div><dt>${esc(t('c_price'))}</dt><dd>${h}</dd></div>`;
}
const box = $('wm-card');
let cur = null;           // {pid, ll, card}
let marker = null;        // draggable marker of a "wrong location" report
function closeCard() {
  box.classList.remove('is-open');
  box.innerHTML = '';
  cur = null;
  if (marker) { marker.remove(); marker = null; }
  selPoint(null);
  st.id = '';
  writeUrl();
}
function shell(inner) {
  box.innerHTML = `<div class="ccard wm-cc" role="dialog" aria-modal="false" aria-labelledby="wm-ct"><button class="x" type="button" data-close aria-label="${esc(t('close'))}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg></button>${inner}</div>`;
  box.classList.add('is-open');
}
async function openCard(pid, ll, props) {
  if (marker) { marker.remove(); marker = null; }
  cur = { pid, ll, card: null, props };
  st.id = pid;
  writeUrl();
  selPoint(ll);
  shell(`<h2 id="wm-ct">${esc(t('loading'))}</h2><div class="wm-skel" aria-hidden="true"></div>`);
  let c = null;
  let g = '';
  try { const r = await findCard(pid, ll[0], ll[1]); if (r) { c = r.card; g = r.g; } } catch (e) { c = null; }
  try { await loadPrices(); } catch (e) { /* the card works without prices */ }
  if (!cur || cur.pid !== pid) return;
  if (!c) { shell(`<h2 id="wm-ct">${esc(t('c_unnamed'))}</h2><p class="wm-err">${esc(t('card_err'))}</p>`); return; }
  cur.card = c;
  cur.g = g;
  renderCard(c);
}
function confWord(v) { return v >= 70 ? t('conf_hi') : v >= 50 ? t('conf_mid') : t('conf_lo'); }
function navHref(lat, lon) {
  const ll = (+lat).toFixed(6) + ',' + (+lon).toFixed(6);
  if (IS_ANDROID) return 'geo:' + ll + '?q=' + ll;
  if (IS_IOS) return 'https://maps.apple.com/?daddr=' + ll;   // iOS opens no geo: links; Apple Maps, never Google
  return 'https://www.openstreetmap.org/directions?route=%3B' + encodeURIComponent(ll) + '#map=16/' + (+lat).toFixed(5) + '/' + (+lon).toFixed(5);
}
function renderCard(c) {
  const [lon, lat] = cur.ll;
  const title = c.n || c.net || t('c_unnamed');
  const sub = [c.n && c.net ? c.net : '', country(c.cc)].filter(Boolean).join(' · ');
  const pw = c.kw ? `${nf(c.kw, 1)} ${KW} · ${c.dc ? 'DC' : 'AC'}` : (c.p === 7 ? 'DC · ' : c.p === 6 ? 'AC · ' : '') + t('c_power_unk');
  const conn = (c.conn || []).map(([ty, n, kw]) => `${esc(connName(ty))}${n > 1 ? ' ×' + n : ''}${kw ? ' · ' + nf(kw, 1) + ' ' + KW : ''}`).join('<br>');
  const row = (k, v) => (v ? `<div><dt>${esc(k)}</dt><dd>${v}</dd></div>` : '');
  const accKey = 'acc_' + (c.acc || 'unknown');
  const acc = T[accKey] ? t(accKey) : esc(c.acc);
  let h = `<h2 id="wm-ct" translate="no">${esc(title)}</h2>${sub ? `<p class="wm-sub2">${esc(sub)}</p>` : ''}<dl class="wm-dl">`;
  h += row(t('c_power'), esc(pw));
  if (c.more) {
    // Serbia and the region: the regional BlokVolt map has the full card (prices, checks, reports)
    h += row(t('c_conn'), conn) + '</dl>';
    h += `<p class="wm-note2">${esc(t('bv_note'))}</p><div class="wm-acts"><a class="btn sm dark" href="${esc(c.more)}">${esc(t('more'))}</a>` +
      `<a class="btn sm" href="${esc(navHref(lat, lon))}" rel="noopener">${esc(t('nav'))}</a><button class="btn sm" type="button" data-share>${esc(t('share'))}</button></div><p class="wm-copied" role="status" hidden></p>`;
    shell(h);
    return;
  }
  h += row(t('c_conn'), conn);
  h += priceRow(c, PRV);
  h += row(t('c_pts'), c.pts ? esc(nf(c.pts)) : '');
  h += row(t('c_acc'), esc(acc));
  h += row(t('c_lc'), esc(c.lc ? fmtMonth(c.lc) : t('c_lc_none')));
  const v = Math.round(c.conf || 0);
  h += row(t('c_conf'), `<b>${esc(confWord(v))}</b> · ${v}/100 · <a href="${esc(cfg.about)}">${esc(t('how'))}</a><br><small>${esc(t('conf_note'))}</small>`);
  const srcs = (c.src || []).map(s => {
    const m = (M.sources || {})[s.k] || {};
    const nm = esc(m.name || s.k), lic = m.licence ? (m.licence_url ? `<a href="${esc(m.licence_url)}" rel="noopener license">${esc(m.licence)}</a>` : esc(m.licence)) : '';
    return `<li>${s.u ? `<a href="${esc(s.u)}" rel="noopener nofollow">${nm}</a>` : nm}${lic ? ` <span>(${esc(t('licence'))}: ${lic})</span>` : ''}</li>`;
  }).join('');
  h += srcs ? `<div><dt>${esc(t('c_src'))}</dt><dd><ul class="wm-src">${srcs}</ul></dd></div>` : '';
  h += '</dl><div class="wm-acts">';
  h += `<a class="btn sm dark" href="${esc(navHref(lat, lon))}" rel="noopener">${esc(t('nav'))}</a>`;
  h += `<button class="btn sm" type="button" data-share>${esc(t('share'))}</button>`;
  if (cfg.reports_api) h += `<button class="btn sm" type="button" data-report aria-expanded="false">${esc(t('rep'))}</button>`;
  h += '</div><p class="wm-copied" role="status" hidden></p>';
  if (c.osm) h += `<p class="wm-osm"><a href="${esc(c.osm)}" rel="noopener nofollow">${esc(t('osm_fix'))}</a></p>`;
  h += ciBlock(c);
  h += '<div class="wm-rep" id="wm-rep" hidden></div>';
  shell(h);
  ciLoad(cur.pid);
}
box.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b) return;
  if (b.hasAttribute('data-close')) { closeCard(); return; }
  if (b.hasAttribute('data-share')) { share(); return; }
  if (b.hasAttribute('data-report')) { toggleReport(b); return; }
  if (b.hasAttribute('data-rcancel')) { const btn = box.querySelector('[data-report]'); if (btn) toggleReport(btn, false); }
  if (b.hasAttribute('data-ci')) { ciState(b); return; }
  if (b.hasAttribute('data-paid')) { ciPaid(b); return; }
});
d.addEventListener('keydown', e => { if (e.key === 'Escape' && box.classList.contains('is-open') && !$('wm-src').open) closeCard(); });
function shareUrl() {
  const [lon, lat] = cur.ll;
  const u = new URL(location.href);
  u.searchParams.set('id', cur.pid);
  u.hash = '#' + Math.max(15, Math.round(map.getZoom())) + '/' + (+lat).toFixed(5) + '/' + (+lon).toFixed(5);
  return u.toString().replace(/%2C/g, ',');
}
function share() {
  const url = shareUrl(), title = (cur.card && (cur.card.n || cur.card.net)) || t('c_unnamed');
  const done = () => { const p = box.querySelector('.wm-copied'); if (p) { p.textContent = t('copied'); p.hidden = false; } };
  if (navigator.share && IS_TOUCH) { navigator.share({ title, url }).catch(() => {}); return; }
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done, () => prompt(t('share'), url));
  else prompt(t('share'), url);
}

// ------------------------------------------------------------------ "Prijavi grešku" (P1 §2.4, contract §10)
const TYPES = ['ne_postoji', 'ne_radi', 'lokacija', 'snaga', 'nije_javni', 'drugo'];
function toggleReport(btn, force) {
  const r = $('wm-rep');
  const open = force == null ? r.hidden : force;
  btn.setAttribute('aria-expanded', String(open));
  if (!open) { r.hidden = true; r.innerHTML = ''; if (marker) { marker.remove(); marker = null; } return; }
  r.hidden = false;
  r.innerHTML = `<form id="wm-rf" novalidate><fieldset><legend>${esc(t('r_type'))}</legend>${TYPES.map(k =>
    `<label class="wm-radio"><input type="radio" name="type" value="${k}"> ${esc(t('r_' + k))}</label>`).join('')}</fieldset>
<p class="wm-hint" id="wm-loch" hidden>${esc(t('r_loc_hint'))}</p>
<label class="wm-lbl" for="wm-rt">${esc(t('r_text'))}</label><textarea class="input" id="wm-rt" name="text" maxlength="300" rows="3" aria-describedby="wm-rtn"></textarea><small id="wm-rtn">${esc(t('r_text_max'))}</small>
<label class="wm-lbl" for="wm-re">${esc(t('r_email'))}</label><input class="input" id="wm-re" name="email" type="email" autocomplete="email" aria-describedby="wm-reh"><small id="wm-reh">${esc(t('r_email_hint'))}</small>
<div class="wm-hp" aria-hidden="true"><label>Website <input name="hp" type="text" tabindex="-1" autocomplete="off"></label></div>
<p class="wm-rmsg" role="status" aria-live="polite"></p>
<div class="wm-acts"><button class="btn sm dark" type="submit">${esc(t('r_send'))}</button><button class="btn sm" type="button" data-rcancel>${esc(t('r_cancel'))}</button></div></form>`;
  const f = $('wm-rf');
  f.addEventListener('change', e => {
    if (e.target.name !== 'type') return;
    const loc = e.target.value === 'lokacija';
    $('wm-loch').hidden = !loc;
    if (loc && !marker) {
      marker = new maplibregl.Marker({ draggable: true, color: '#2E6BFF' }).setLngLat(cur.ll).addTo(map);
    } else if (!loc && marker) { marker.remove(); marker = null; }
  });
  f.addEventListener('submit', sendReport);
  const first = f.querySelector('input[name="type"]');
  if (first) first.focus();
}
async function sendReport(e) {
  e.preventDefault();
  const f = e.currentTarget, out = f.querySelector('.wm-rmsg'), btn = f.querySelector('button[type="submit"]');
  const type = (f.querySelector('input[name="type"]:checked') || {}).value;
  if (!type) { out.textContent = t('r_need_type'); return; }
  const body = { pid: Number(cur.pid), type, text: f.text.value.trim().slice(0, 300), email: f.email.value.trim(), lang: LANG, hp: f.hp.value };
  // optional hints for /admin/svet/ (K6): the country and the geohash cell whose card file holds the place
  if (cur.card && /^[A-Z]{2}$/.test(cur.card.cc || '')) body.cc = cur.card.cc;
  if (cur.g) body.g = cur.g;
  if (type === 'lokacija') {
    const p = marker ? marker.getLngLat() : { lng: cur.ll[0], lat: cur.ll[1] };
    body.lat = +p.lat.toFixed(6);
    body.lon = +p.lng.toFixed(6);
  }
  if (!body.text) delete body.text;
  if (!body.email) delete body.email;
  btn.disabled = true;
  out.textContent = t('r_sending');
  let r = null;
  try {
    r = await fetch(cfg.reports_api, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), mode: 'cors' });
  } catch (err) {
    out.textContent = t('r_err_net');
    btn.disabled = false;
    return;
  }
  let j = null;
  try { j = await r.json(); } catch (err) { j = null; }
  if (r.ok && j && j.ok) {
    if (marker) { marker.remove(); marker = null; }
    const rep = $('wm-rep');
    rep.innerHTML = `<p class="wm-ok" role="status">${esc(t('r_ok'))}</p>`;
    const b = box.querySelector('[data-report]');
    if (b) { b.disabled = true; b.setAttribute('aria-expanded', 'false'); }
    return;
  }
  out.textContent = r.status === 429 ? t('r_err_limit') : t('r_err');
  btn.disabled = false;
}

// ------------------------------------------------------------------ drivers' check-ins (G6)
// „Radi / Ne radi / Zauzeto“ and „Koliko ste platili“ go to cfg.checkins_api (/api/svet/stanje of blokvolt.rs). With
// checkins_api = "demo" (dev previews: no D1 there) the form works and nothing leaves the browser; empty = no block.
// The price is checked against the network's list price (G3) only to warn the driver; the weekly script decides.
const CI_API = cfg.checkins_api || '', CI_DEMO = CI_API === 'demo';
const CI_STATES = ['radi', 'ne_radi', 'zauzeto'];
const CI_CUR = ['EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RON', 'BGN', 'TRY', 'CAD', 'AUD'];
let ciSent = {};          // pid → true once a state was sent from this page (one a day per place is stored anyway)
function ciCls(c) { return c.kw >= 150 ? 'hpc' : c.dc ? 'dc' : c.kw ? 'ac' : null; }
function ciRef(c) {
  // the network's ad hoc list price for this power class: [EUR, local, currency]
  const name = c.net || (cur && cur.props && M.networks[cur.props.o]) || '';
  const e = PRV && PRV.nets && name && PRV.nets[c.cc + '|' + name];
  if (!e) return null;
  const i = { ac: 0, dc: 1, hpc: 2 }[ciCls(c)];
  if (i == null) return null;
  const eur = [e.ac, e.dc, e.hpc][i] != null ? [e.ac, e.dc, e.hpc][i] : i === 2 ? e.dc : null;
  if (eur == null) return null;
  const loc = e.l ? (e.l[i] != null ? e.l[i] : i === 2 ? e.l[1] : null) : null;
  return { eur, loc, cur: e.cur || 'EUR' };
}
function ciBlock(c) {
  if (!CI_API) return '';
  const btns = CI_STATES.map(k => `<button class="btn sm" type="button" data-ci="${k}">${esc(t('ci_' + k))}</button>`).join('');
  return `<section class="wm-ci" aria-labelledby="wm-cih"><h3 id="wm-cih">${esc(t('ci_h'))}</h3><p class="wm-cis" id="wm-cis" role="status" aria-live="polite">${CI_DEMO ? esc(t('ci_demo_note')) : ''}</p>` +
    `<div class="wm-acts">${btns}</div><p class="wm-acts"><button class="btn sm" type="button" data-paid aria-expanded="false">${esc(t('ci_paid'))}</button></p>` +
    `<div id="wm-pf" hidden></div><details class="wm-rules"><summary>${esc(t('ci_rules_h'))}</summary><p>${esc(t('ci_rules'))}</p><p>${esc(t('ci_privacy'))}</p></details></section>`;
}
const ago = s => {
  const days = Math.max(0, Math.floor((Date.now() / 1000 - s) / 86400));
  try { return new Intl.RelativeTimeFormat(LOC, { numeric: 'auto' }).format(-days, 'day'); } catch (e) { return fmtDate(new Date(s * 1000).toISOString().slice(0, 10)); }
};
async function ciLoad(pid) {
  if (!CI_API || CI_DEMO) return;
  let j = null;
  try { const r = await fetch(CI_API + '?pid=' + encodeURIComponent(pid), { mode: 'cors' }); j = await r.json(); } catch (e) { return; }
  if (!cur || String(cur.pid) !== String(pid) || !j || !j.ok) return;
  const out = $('wm-cis');
  if (!out) return;
  const parts = [];
  if (j.last_ok) parts.push(t('ci_last_ok', { d: ago(j.last_ok) }));
  if (j.last && j.last.s !== 'radi' && (!j.last_ok || j.last.at > j.last_ok)) parts.push(t('ci_last_' + j.last.s, { d: ago(j.last.at) }));
  const n = (j.d30 && (j.d30.radi + j.d30.ne_radi + j.d30.zauzeto)) || 0;
  if (n) parts.push(t('ci_n30', { n: nf(n) }));
  out.textContent = parts.join(' · ');
}
async function ciPost(body) {
  if (CI_DEMO) return { ok: true, demo: true };
  try {
    const r = await fetch(CI_API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), mode: 'cors' });
    let j = null;
    try { j = await r.json(); } catch (e) { j = null; }
    if (r.ok && j && j.ok) return { ok: true };
    return { ok: false, msg: r.status === 429 ? t('ci_err_limit') : t('ci_err') };
  } catch (e) { return { ok: false, msg: t('r_err_net') }; }
}
function ciBase() {
  const c = cur.card, b = { pid: Number(cur.pid), lang: LANG, hp: '' };
  if (/^[A-Z]{2}$/.test(c.cc || '')) b.cc = c.cc;
  if (cur.g) b.g = cur.g;
  const cl = ciCls(c);
  if (cl) b.cls = cl;
  const name = c.net || (cur.props && M.networks[cur.props.o]) || '';
  if (name) b.net = String(name).slice(0, 80);
  return b;
}
async function ciState(btn) {
  const out = $('wm-cis'), s = btn.getAttribute('data-ci');
  if (ciSent[cur.pid]) { out.textContent = t('ci_once'); return; }
  box.querySelectorAll('[data-ci]').forEach(x => { x.disabled = true; });
  out.textContent = t('r_sending');
  const r = await ciPost(Object.assign(ciBase(), { s }));
  if (r.ok) {
    ciSent[cur.pid] = true;
    btn.setAttribute('aria-pressed', 'true');
    out.textContent = r.demo ? t('ci_demo') : t('ci_thanks');
  } else {
    out.textContent = r.msg;
    box.querySelectorAll('[data-ci]').forEach(x => { x.disabled = false; });
  }
}
function ciMonths() {
  const d = new Date(), out = [];
  for (let i = 0; i < 12; i++) {
    const x = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - i, 1)), v = x.toISOString().slice(0, 7);
    out.push(`<option value="${v}">${esc(fmtMonth(v))}</option>`);
  }
  return out.join('');
}
function ciPaid(btn) {
  const f = $('wm-pf');
  const open = f.hidden;
  btn.setAttribute('aria-expanded', String(open));
  if (!open) { f.hidden = true; f.innerHTML = ''; return; }
  const ref = ciRef(cur.card);
  const curs = [...new Set([ref && ref.cur, 'EUR', ...CI_CUR].filter(Boolean))];
  f.hidden = false;
  f.innerHTML = `<form id="wm-pff" novalidate><div class="wm-prow"><label class="wm-lbl" for="wm-pa">${esc(t('ci_amt'))}</label>` +
    `<input class="input" id="wm-pa" name="amt" inputmode="decimal" autocomplete="off" required></div>` +
    `<div class="wm-prow"><label class="wm-lbl" for="wm-pc">${esc(t('ci_cur'))}</label><select class="input" id="wm-pc" name="cur">${curs.map(x => `<option>${esc(x)}</option>`).join('')}</select></div>` +
    `<div class="wm-prow"><label class="wm-lbl" for="wm-pu">${esc(t('ci_unit'))}</label><select class="input" id="wm-pu" name="unit">` +
    ['kwh', 'min', 'session'].map(u => `<option value="${u}">${esc(t('ci_u_' + u))}</option>`).join('') + `</select></div>` +
    `<div class="wm-prow"><label class="wm-lbl" for="wm-pm">${esc(t('ci_month'))}</label><select class="input" id="wm-pm" name="ym">${ciMonths()}</select></div>` +
    `<div class="wm-hp" aria-hidden="true"><label>Website <input name="hp" type="text" tabindex="-1" autocomplete="off"></label></div>` +
    `<p class="wm-rmsg" role="status" aria-live="polite"></p><div class="wm-acts"><button class="btn sm dark" type="submit">${esc(t('r_send'))}</button></div></form>`;
  const form = $('wm-pff');
  form.addEventListener('input', () => { form.dataset.warned = ''; });
  form.addEventListener('submit', ciSendPrice);
  $('wm-pa').focus();
}
// how far a per-kWh price is from the list price: null when it cannot be compared
function ciFar(amt, unit, cu, ref) {
  if (!ref || unit !== 'kwh') return null;
  let base = null;
  if (cu === 'EUR') base = ref.eur;
  else if (cu === ref.cur && ref.loc != null) base = ref.loc;
  else if (cu === 'USD' && PRV && PRV.rates && PRV.rates.USD) base = ref.eur * PRV.rates.USD;
  if (!base) return null;
  const k = amt / base;
  return k < 0.5 || k > 2 ? base : null;
}
async function ciSendPrice(e) {
  e.preventDefault();
  const f = e.currentTarget, out = f.querySelector('.wm-rmsg'), btn = f.querySelector('button[type="submit"]');
  const amt = Number(String(f.amt.value).trim().replace(/\s/g, '').replace(',', '.'));
  if (!isFinite(amt) || amt <= 0 || amt > 100000) { out.textContent = t('ci_need_amt'); return; }
  const unit = f.unit.value, cu = f.cur.value, ym = f.ym.value;
  const ref = ciRef(cur.card), far = ciFar(amt, unit, cu, ref);
  if (far != null && !f.dataset.warned) {
    f.dataset.warned = '1';
    out.textContent = t('ci_far', { p: pmoney(far, cu) });
    return;
  }
  btn.disabled = true;
  out.textContent = t('r_sending');
  const r = await ciPost(Object.assign(ciBase(), { amt, unit, cur: cu, ym, hp: f.hp.value }));
  if (r.ok) {
    $('wm-pf').innerHTML = `<p class="wm-ok" role="status">${esc(r.demo ? t('ci_demo') : t('ci_paid_ok'))}</p>`;
    const b = box.querySelector('[data-paid]');
    if (b) { b.disabled = true; b.setAttribute('aria-expanded', 'false'); }
    return;
  }
  out.textContent = r.msg;
  btn.disabled = false;
}

// ------------------------------------------------------------------ attribution, sources, data date
function attribution() {
  const S = M.sources || {};
  const lic = k => (S[k] && S[k].licence ? ` (${esc(S[k].licence)})` : '');
  const parts = [`${esc(t('attr_map'))}: <a href="https://openfreemap.org" rel="noopener">OpenFreeMap</a> © <a href="https://www.openmaptiles.org/" rel="noopener">OpenMapTiles</a>`,
    `© <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a>${lic('osm') || ' (ODbL)'}`];
  if (S.ocm) parts.push(`<a href="https://openchargemap.org" rel="noopener">Open Charge Map</a>${lic('ocm')}`);
  if (S.geonames) parts.push(`<a href="https://www.geonames.org/" rel="noopener">GeoNames</a>${lic('geonames')}`);
  const n = Object.keys(S).length;
  parts.push(`<button class="lnkbtn" type="button" data-sources>${esc(t('sources_btn'))}${n ? ' (' + n + ')' : ''}</button>`);
  parts.push(`<a href="${esc(cfg.about)}">${esc(t('about'))}</a>`);
  if (cfg.download) parts.push(`<a href="${esc(cfg.download)}">${esc(t('download'))}</a>`);
  parts.push(esc(t('data_date', { d: fmtDate(M.date) })));
  const at = $('wm-attr');
  at.innerHTML = `<span class="wm-attr-full">${parts.join(' · ')}</span><button class="wm-attr-i" type="button" aria-expanded="true" aria-controls="wm-attr" aria-label="${esc(t('attr_show'))}">i</button>`;
  // ≤ 480 px: after 5 seconds the line folds into "(i)" (decision 6, 09.11; L1 §2: not earlier than 5 s); a tap opens it again
  if (window.matchMedia && matchMedia('(max-width: 480px)').matches) {
    setTimeout(() => { at.classList.add('is-min'); at.querySelector('.wm-attr-i').setAttribute('aria-expanded', 'false'); }, 5000);
  }
  $('wm-data').innerHTML = `<p><b>${esc(t('data_date', { d: fmtDate(M.date) }))}</b> · ${esc(t('sources_n', { n: String(n) }))}</p>` +
    `<p><button class="lnkbtn" type="button" data-sources>${esc(t('sources_btn'))}</button> · <a href="${esc(cfg.about)}">${esc(t('about'))}</a>` +
    (cfg.download ? ` · <a href="${esc(cfg.download)}">${esc(t('download'))}</a>` : '') + `</p><p class="wm-small">${esc(t('odbl_note'))}</p>`;
}
function sourcesDialog() {
  const S = M.sources || {};
  const rows = Object.keys(S).sort((a, b) => (a === 'osm' ? -1 : b === 'osm' ? 1 : String(S[a].name).localeCompare(S[b].name))).map(k => {
    const s = S[k];
    const name = s.url ? `<a href="${esc(s.url)}" rel="noopener">${esc(s.name || k)}</a>` : esc(s.name || k);
    const lic = s.licence ? (s.licence_url ? `<a href="${esc(s.licence_url)}" rel="noopener license">${esc(s.licence)}</a>` : esc(s.licence)) : '';
    return `<li><b>${name}</b>${lic ? ' — ' + lic : ''}${s.attribution && s.attribution !== s.name ? `<br><small>${esc(s.attribution)}</small>` : ''}</li>`;
  }).join('');
  $('wm-src-body').innerHTML = `<p>${esc(t('data_date', { d: fmtDate(M.date) }))}</p><ul class="wm-srcl">${rows}</ul><p class="wm-small">${esc(t('odbl_note'))} <a href="${esc(cfg.about)}">${esc(t('about'))}</a></p>`;
  const dl = $('wm-src');
  if (dl.showModal) dl.showModal(); else dl.setAttribute('open', '');
}
d.addEventListener('click', e => {
  const i = e.target.closest('.wm-attr-i');
  if (i) {
    const at = $('wm-attr'), min = at.classList.toggle('is-min');
    i.setAttribute('aria-expanded', String(!min));
    return;
  }
  const b = e.target.closest('[data-sources]');
  if (b && M) sourcesDialog();
});
$('wm-src').addEventListener('click', e => {
  const dl = $('wm-src');
  if (e.target.closest('[data-close]') || e.target === dl) dl.close ? dl.close() : dl.removeAttribute('open');
});

// ------------------------------------------------------------------ ?id= from a shared link
let idTried = false;
function openFromUrl() {
  if (idTried || !st.id) return;
  idTried = true;
  const pid = st.id;
  // a shared link puts the point in the hash (#z/lat/lon): its card file is found from there
  const c = map.getCenter();
  const near = map.queryRenderedFeatures({ layers: [LYR] }).find(f => String(f.properties.i) === pid);
  openCard(pid, near ? near.geometry.coordinates : [c.lng, c.lat], near ? near.properties : null);
}

// ------------------------------------------------------------------ start
readUrl();
paintFilters();
initMap();
// for debugging and scripts/qa/world_map_test.py (read only by tests; nothing on the page depends on it)
window.BVWorldMap = { get map() { return map; }, get ready() { return ready; }, get manifest() { return M; }, state: st, openCard };
async function fitPlace() {
  if (!(st.zemlja || st.grad) || HAD_HASH || !M || !M.places) return;
  let P = null;
  try { P = await getJson(at(M.places)); } catch (e) { return; }
  const c = st.grad && P.city && P.city[st.grad], b = c || (st.zemlja && P.cc && P.cc[st.zemlja]);
  if (!b || b.length < 4 || !map) return;
  const go = () => map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 30, maxZoom: c ? 13 : 9, duration: 0 });
  if (mapLoaded) go(); else map.once('load', go);
}
loadManifest().then(() => {
  NETS.forEach(n => NETS_BY_O.set(n.i, n.slug));
  attribution();
  paintFilters();
  if (map) addLayers();
  fitPlace();
}).catch(() => msg(t('data_err')));
