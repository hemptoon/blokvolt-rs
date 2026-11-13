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
// TAILS P2.7 (13.11.2026): MapLibre (≈ 1 MB) is imported when the live map starts, not with the page — on a phone the
// first screen is a picture of our points (cfg.poster, the pictures of the home) until the first touch, scroll or key;
// a link with parameters or a view (?grad=, ?mreza=, ?id=, ?zemlja=, #z/lat/lon) and wider screens start at once
const ML_URL = '/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs';
let maplibregl = null;

const d = document;
// read before MapLibre (hash: true) writes its own #z/lat/lon: a link with a view keeps it, zemlja/grad then do not move it
const HAD_HASH = /^#\d/.test(location.hash);
const cfg = JSON.parse(d.getElementById('wm-cfg').textContent);
const T = JSON.parse(d.getElementById('wm-i18n').textContent);
const LANG = cfg.lang;
const LOC = cfg.intl || (LANG === 'sr' ? 'sr-Latn-RS' : LANG === 'ru' ? 'ru-RU' : 'en-GB');   // LANG0: cfg.intl of the other languages
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
// widget for other sites (/embed/map/, G5, RUNBOOK 3.42): cfg.embed = {open, utm}. Two-finger gestures so the host page
// still scrolls, no reports, the card's button opens the place on blokvolt.com; &tema=tamna picks the dark base map.
const EMB = cfg.embed || null;
// HOME3 (11.11.2026): /map/ opens dark; THEME (12.11.2026): it follows the theme of the whole site — the inline scripts of
// base.html and world_map.html have set html[data-theme] and html.wm-dark (?tema= for one link, else the visitor's choice,
// else dark), the switch of the header changes it ("bv-theme", static/com/bvc.js). The widget keeps its own rule (light
// unless &tema=tamna)
let TEMA = EMB ? (/^(tamna|dark)$/.test(new URLSearchParams(location.search).get('tema') || '') ? 'tamna' : '')
  : (d.documentElement.classList.contains('wm-dark') ? 'tamna' : '');
if (TEMA) d.documentElement.classList.add('wm-dark');
const DARK = () => !!(TEMA && cfg.style_dark);

// ------------------------------------------------------------------ state <-> URL
const SNAGA = ['ac', 'dc', 'hpc', 'nepoznato'];
const IZVOR = { drz: 1, zaj: 2, mre: 4, bv: 8 };
const PCODES = { ac: [1, 2], dc: [3, 4], hpc: [5], nepoznato: [0, 6, 7] };
// HOME3: the full map shows every place of the layer by default ("Public only" is one tap, ?pristup=javni); the widget keeps "javni"
const DEF_PR = EMB ? 'javni' : 'svi';
const st = { snaga: new Set(SNAGA), mreza: new Set(), p: 40, pristup: DEF_PR, izvor: new Set(Object.keys(IZVOR)), zemlja: '', grad: '', id: '' };
function readUrl() {
  const q = new URLSearchParams(location.search);
  const list = (k, ok) => (q.get(k) || '').split(',').map(x => x.trim().toLowerCase()).filter(x => x && (!ok || ok.includes(x)));
  const sn = list('snaga', SNAGA);
  if (sn.length) st.snaga = new Set(sn);
  st.mreza = new Set(list('mreza').map(slug).filter(Boolean));
  const p = +q.get('p');
  st.p = [40, 50, 70].includes(p) ? p : 40;
  st.pristup = q.get('pristup') === 'svi' ? 'svi' : q.get('pristup') === 'javni' ? 'javni' : DEF_PR;
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
  if (st.pristup !== DEF_PR) q.set('pristup', st.pristup);
  if (st.izvor.size !== 4) q.set('izvor', Object.keys(IZVOR).filter(x => st.izvor.has(x)).join(','));
  if (st.zemlja) q.set('zemlja', st.zemlja);
  if (st.grad) q.set('grad', st.grad);
  if (st.id) q.set('id', st.id);
  if (EMB) { if (TEMA) q.set('tema', TEMA); }
  else if ((TEMA || 'svetla') !== (cfg.theme || 'svetla')) q.set('tema', TEMA || 'svetla');
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
  // "Public only": a = 0 (public*), the number of manifest.counts.public (HOME3); the widget keeps its old rule
  // (public and unknown access, P1 §2.2)
  if (st.pristup === 'javni') f.push(EMB ? ['!=', ['get', 'a'], 1] : ['==', ['get', 'a'], 0]);
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
// K7: small zooms show the even grain of the tiles (z0–5 thinned by spacing, z6–9 thinner still, all points from z10):
// tiny dots without a ring, slightly transparent; AC points are dark there (a white dot without a ring is invisible on the
// base map) and turn white with the dark ring by zoom 8. From zoom 10 the sizes are the ones before K7.
const zrl = (big, x, y) => ['interpolate', ['linear'], ['zoom'], ...[2, 5, 8, 10, 12, 16].flatMap((z, k) => [z, ['case', big, x[k], y[k]]])];
const P_LOW = ['match', ['get', 'p'], [3, 4, 5], '#0D111A', 7, '#5C6270', 0, '#8A909B', '#2B3240'];
const restricted = ['==', ['get', 'a'], 1];
// HOME3 dark map: zoomed out every place is a lime light (the picture of the home); from zoom 8 the types — AC light grey,
// DC lime, 150 kW+ a larger lime point with a light ring, unknown power grey
const D_COLOR = ['match', ['get', 'p'], [3, 4], '#D9F45B', 5, '#E9FF8A', 7, '#7E8696', 0, '#8A909B', '#E4E8EF'];
const D_STROKE = ['match', ['get', 'p'], [3, 4], '#0B0F17', 5, '#F6FFD2', '#AEB5C2'];
const D_LOW = ['match', ['get', 'p'], 5, '#F4FFD2', [3, 4], '#D9F45B', '#A9BC45'];
// places that are not public draw as a ring (no fill) from zoom 8: access not confirmed in the colour of the type,
// customers only / private in orange; zoomed out they are smaller, fainter dots
const notPub = ['!=', ['get', 'a'], 0];
const RING_UNK_L = ['match', ['get', 'p'], [3, 4, 5], '#4E6410', [0, 6, 7], '#5C6270', '#0D111A'];
const RING_UNK_D = ['match', ['get', 'p'], [3, 4, 5], '#D9F45B', [0, 6, 7], '#9AA1AD', '#E4E8EF'];
const RING_RES_L = '#C2410C', RING_RES_D = '#FF9B71';
function pointPaint() {
  const dk = DARK(), big = ['==', ['get', 'p'], 5];
  if (EMB) return {   // the widget draws as before HOME3 (G5): restricted places faded, no rings
    'circle-radius': zrl(big, [1.8, 3, 4.5, 7, 9, 12.5], [1.5, 2.5, 3.5, 5.7, 7.5, 11]),
    'circle-color': ['interpolate', ['linear'], ['zoom'], 5, P_LOW, 8, P_COLOR],
    'circle-stroke-color': P_STROKE,
    'circle-stroke-width': zrl(big, [0, 0.6, 1.2, 2.4, 3, 3.2], [0, 0.4, 0.8, 1.6, 2, 2.4]),
    'circle-opacity': ['interpolate', ['linear'], ['zoom'], 2, ['case', restricted, 0.35, 0.7], 5, ['case', restricted, 0.4, 0.85], 7, ['case', restricted, 0.45, 1]],
    'circle-stroke-opacity': ['case', restricted, 0.55, 1]
  };
  const ring = ['case', restricted, dk ? RING_RES_D : RING_RES_L, dk ? RING_UNK_D : RING_UNK_L];
  return {
    // dark: smaller points zoomed out, so the lime reads as lights, not as one patch (HOME3 7)
    'circle-radius': dk ? zrl(big, [1.2, 1.9, 3.6, 7, 9, 12.5], [0.9, 1.4, 2.8, 5.7, 7.5, 11]) : zrl(big, [1.8, 3, 4.5, 7, 9, 12.5], [1.5, 2.5, 3.5, 5.7, 7.5, 11]),
    'circle-color': dk ? ['interpolate', ['linear'], ['zoom'], 6, D_LOW, 8.5, D_COLOR] : ['interpolate', ['linear'], ['zoom'], 5, P_LOW, 8, P_COLOR],
    'circle-stroke-color': ['case', notPub, ring, dk ? D_STROKE : P_STROKE],
    'circle-stroke-width': ['interpolate', ['linear'], ['zoom'], ...[2, 5, 8, 10, 12, 16].flatMap((z, k) => [z, ['case', notPub,
      [0, 0, 1.6, 2.2, 2.6, 3][k], ['case', big, [0, 0.6, 1.2, 2.4, 3, 3.2][k], [0, 0.4, 0.8, 1.6, 2, 2.4][k]]]])],
    // a "grid" of thinned tiles zoomed out is softened by lower opacity there (HOME2 note, HOME3 7)
    'circle-opacity': ['interpolate', ['linear'], ['zoom'], 2, ['case', notPub, 0.3, dk ? 0.75 : 0.7], 5, ['case', notPub, 0.4, 0.85],
      7, ['case', notPub, 0.35, 1], 8.5, ['case', notPub, 0, 1]],
    'circle-stroke-opacity': ['interpolate', ['linear'], ['zoom'], 7, ['case', notPub, 0.6, 1], 8.5, 1]
  };
}
// FIX1: the base-map labels (cities, countries) sit above the points and get a strong halo, so they stay readable
// over dense areas without hiding any point; names follow the page language (cfg.lang), then Latin, then local.
function labelName(l) {
  if (l === 'en') return ['coalesce', ['get', 'name:en'], ['get', 'name_en'], ['get', 'name:latin'], ['get', 'name']];
  if (l === 'sr') return ['coalesce', ['get', 'name:sr-Latn'], ['get', 'name:hr'], ['get', 'name:latin'], ['get', 'name']];
  if (l === 'nb') return ['coalesce', ['get', 'name:nb'], ['get', 'name:no'], ['get', 'name:latin'], ['get', 'name']];
  return ['coalesce', ['get', 'name:' + l], ['get', 'name:latin'], ['get', 'name']];
}
// HOME3: the dark base map in the colours of the home picture (content/world/config.json → map_theme.dark_paint). The style
// JSON of OpenFreeMap is fetched once and recoloured before MapLibre draws it, so the dark map never flashes black.
let darkJson = null;
async function darkStyle() {
  if (!darkJson) {
    const j = await getJson(cfg.style_dark);
    const P = (!EMB && cfg.dark_paint) || {};
    (j.layers || []).forEach(l => { if (P[l.id]) l.paint = Object.assign({}, l.paint || {}, P[l.id]); });
    darkJson = j;
  }
  return darkJson;
}
const DARK_BG = { version: 8, sources: {}, layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#111621' } }] };
let realStyle = false;   // true once a base map (not the plain dark ground) has been handed to MapLibre
function useStyle() {
  if (!DARK()) { realStyle = true; map.setStyle(cfg.style); return; }
  darkStyle().then(j => { realStyle = true; map.setStyle(j); })
    .catch(() => { TEMA = ''; realStyle = true; map.setStyle(cfg.style); });   // the page stays dark; only the base map is light
}
function paintDark() {
  if (EMB || !DARK() || !cfg.dark_paint) return;
  for (const id in cfg.dark_paint) {
    if (!map.getLayer(id)) continue;
    for (const k in cfg.dark_paint[id]) { try { map.setPaintProperty(id, k, cfg.dark_paint[id][k]); } catch (e) { /* not in this style */ } }
  }
}
function styleLabels() {
  const dark = DARK(), name = labelName(LANG);
  (map.getStyle().layers || []).forEach(l => {
    if (l.type !== 'symbol' || l['source-layer'] !== 'place') return;
    const ctry = /^label_country/.test(l.id), soft = l.id === 'label_state' || l.id === 'label_other';
    const set = (k, v, lay) => { try { (lay ? map.setLayoutProperty : map.setPaintProperty).call(map, l.id, k, v); } catch (e) { /* layer without that property */ } };
    set('text-field', name, true);
    set('text-halo-color', dark ? 'rgba(11,15,23,0.95)' : 'rgba(255,255,255,0.95)');
    set('text-halo-width', ctry ? 2.4 : 2);
    set('text-halo-blur', 0.3);
    set('text-color', dark ? (soft ? '#B8BDC7' : '#F4F3EE') : (soft ? '#3A404C' : '#0D111A'));
    if (ctry) { set('text-transform', 'uppercase', true); set('text-letter-spacing', 0.08, true); }
  });
}
function addLayers() {
  if (!M || !mapLoaded || map.getSource(SRC)) return;
  // points go under the first label layer of the base map; the selection ring stays on top of everything
  const before = ((map.getStyle().layers || []).find(l => l.type === 'symbol') || {}).id;
  paintDark();
  styleLabels();
  map.addSource(SRC, { type: 'vector', url: 'pmtiles://' + at(M.tiles), attribution: '' });
  if (DARK() && !EMB) {   // the glow of the home picture, zoomed out only
    map.addLayer({ id: 'wm-glow', type: 'circle', source: SRC, 'source-layer': 'sites', maxzoom: 9, filter: pFilter(),
      paint: { 'circle-color': '#4A5C12', 'circle-blur': 1, 'circle-radius': ['interpolate', ['linear'], ['zoom'], 2, 2, 5, 3.5, 8, 7],
        'circle-opacity': ['interpolate', ['linear'], ['zoom'], 2, 0.16, 7, 0.22, 9, 0] } }, before);
  }
  map.addLayer({
    id: LYR, type: 'circle', source: SRC, 'source-layer': 'sites', filter: pFilter(),
    // public places are drawn above the rings of the others; inside each group 150 kW+ on top
    layout: { 'circle-sort-key': EMB ? ['match', ['get', 'p'], 5, 4, [3, 4], 3, [1, 2], 2, 7, 1, 0] : ['+', ['case', notPub, 0, 10], ['match', ['get', 'p'], 5, 4, [3, 4], 3, [1, 2], 2, 7, 1, 0]] },
    paint: pointPaint()
  }, before);
  // max kW inside the point from zoom 12, as on /mapa/ (tile attribute k; a point without k simply has no number)
  map.addLayer({
    id: 'wm-kw', type: 'symbol', source: SRC, 'source-layer': 'sites', minzoom: 12, filter: kwFilter(),
    layout: { 'text-field': ['to-string', ['get', 'k']], 'text-font': cfg.font, 'text-size': 10, 'text-allow-overlap': true, 'text-ignore-placement': true,
      'symbol-sort-key': ['match', ['get', 'p'], 5, 4, [3, 4], 3, [1, 2], 2, 7, 1, 0] },
    paint: EMB ? { 'text-color': ['match', ['get', 'p'], [3, 4, 5], '#D9F45B', 7, '#FFFFFF', [0, 6], '#5C6270', '#0D111A'],
      'text-opacity': ['case', ['==', ['get', 'a'], 1], 0.6, 1] } : { 'text-color': DARK() ? ['case', notPub, ['case', restricted, RING_RES_D, '#E4E8EF'], ['match', ['get', 'p'], [3, 4, 5], '#0B0F17', 7, '#FFFFFF', [0, 6], '#0B0F17', '#0B0F17']]
        : ['case', notPub, ['case', restricted, RING_RES_L, '#0D111A'], ['match', ['get', 'p'], [3, 4, 5], '#D9F45B', 7, '#FFFFFF', [0, 6], '#5C6270', '#0D111A']] }
  }, before);
  map.addSource('wm-sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
  map.addLayer({ id: 'wm-sel', type: 'circle', source: 'wm-sel',
    paint: { 'circle-radius': zr(8, 10, 15, 18), 'circle-color': 'rgba(217,244,91,.35)', 'circle-stroke-width': 3, 'circle-stroke-color': DARK() && !EMB ? '#F6FFD2' : '#0D111A' } });
  ready = true;
  map.once('idle', () => { topNets(); if (st.id) openFromUrl(); });
}
function kwFilter() {
  const f = pFilter();
  return f === true ? ['has', 'k'] : ['all', ['has', 'k'], f];
}
function applyFilter() {
  if (ready) { map.setFilter(LYR, pFilter()); map.setFilter('wm-kw', kwFilter()); if (map.getLayer('wm-glow')) map.setFilter('wm-glow', pFilter()); }
  writeUrl();
  paintFilters();
}
function selPoint(c) {
  const s = map && map.getSource('wm-sel');
  if (s) s.setData({ type: 'FeatureCollection', features: c ? [{ type: 'Feature', properties: {}, geometry: { type: 'Point', coordinates: c } }] : [] });
}

async function initMap(view) {
  try {
    maplibregl = await import(ML_URL);
    if (!window.pmtiles) await new Promise((ok, no) => { const s = d.querySelector('script[src*="pmtiles"]'); if (!s) return no(); s.addEventListener('load', ok); s.addEventListener('error', no); });
  } catch (e) {
    msg(t('no_map'));
    return;
  }
  const proto = new window.pmtiles.Protocol();
  maplibregl.addProtocol('pmtiles', proto.tile);
  try {
    map = new maplibregl.Map({
      container: 'map', style: DARK() ? DARK_BG : cfg.style, center: (view || cfg).center, zoom: (view || cfg).zoom, minZoom: 1.5, maxZoom: 18, hash: true,
      attributionControl: false, dragRotate: false, pitchWithRotate: false, cooperativeGestures: !!EMB
    });
  } catch (e) {
    msg(t('no_map'));
    return;
  }
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  if (DARK()) useStyle(); else realStyle = true;
  // the first real base map counts as loaded (HOME3: the dark style arrives a moment after the plain dark ground)
  // (every new base map — the theme toggle too — gets the points again; addLayers() does nothing when they are there)
  map.on('style.load', () => {
    if (!realStyle || !map.getStyle().layers.some(l => l.type !== 'background')) return;
    mapLoaded = true;
    if (!map.getSource(SRC)) { ready = false; addLayers(); if (cur && cur.ll) selPoint(cur.ll); }
  });
  map.on('load', () => { if (realStyle) { mapLoaded = true; addLayers(); } });
  map.on('click', e => tap(e.point));
  map.on('mousemove', e => {
    if (!ready) return;
    const r = 6, hit = map.queryRenderedFeatures([[e.point.x - r, e.point.y - r], [e.point.x + r, e.point.y + r]], { layers: [LYR] });
    map.getCanvas().style.cursor = hit.length ? 'pointer' : '';
  });
  let tm = 0;
  map.on('moveend', () => { clearTimeout(tm); tm = setTimeout(topNets, 350); });
  map.on('movestart', e => { if (e.originalEvent && attrIsOpen()) attrOpen(false); });   // THEME: a move closes the "ⓘ" card
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
  const n = (st.snaga.size !== 4) + st.mreza.size + (st.p !== 40) + (st.pristup !== DEF_PR) + (st.izvor.size !== 4);
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
    st.snaga = new Set(SNAGA); st.mreza.clear(); st.p = 40; st.pristup = DEF_PR; st.izvor = new Set(Object.keys(IZVOR));
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
  if (LANG === 'en' || cfg.intl) return new Date(Date.UTC(+y, +m - 1, +dd || 1)).toLocaleDateString(cfg.intl || 'en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  return (dd ? dd + '.' : '') + m + '.' + y + (LANG === 'sr' ? '.' : '');
}
const fmtMonth = ym => {
  if (!ym) return '';
  const [y, m] = ym.split('-');
  if (LANG === 'en' || cfg.intl) return new Date(Date.UTC(+y, +m - 1, 1)).toLocaleDateString(cfg.intl || 'en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' });
  return m + '.' + y + (LANG === 'sr' ? '.' : '');
};
const KW = LANG === 'ru' || LANG === 'uk' || LANG === 'bg' ? 'кВт' : 'kW';
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
  // HOME3: a place that is not public says so at the top of its card, in the colour of its ring on the map
  const accCls = /^public/.test(c.acc || '') ? '' : /^(restricted|private)/.test(c.acc || '') ? 'res' : 'unk';
  let h = `<h2 id="wm-ct" translate="no">${esc(title)}</h2>${sub ? `<p class="wm-sub2">${esc(sub)}</p>` : ''}` +
    (accCls && !c.more ? `<p class="wm-accb wm-accb-${accCls}"><i class="wm-sw sw-acc-${accCls}" aria-hidden="true"></i>${esc(acc)}</p>` : '') + '<dl class="wm-dl">';
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
  if (EMB) h += `<a class="btn sm" href="${esc(fullUrl(cur.pid))}" target="_blank" rel="noopener">${esc(t('emb_open'))}</a>`;
  else h += `<button class="btn sm" type="button" data-share>${esc(t('share'))}</button>`;
  if (cfg.reports_api && !EMB) h += `<button class="btn sm" type="button" data-report aria-expanded="false">${esc(t('rep'))}</button>`;
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
// the same view and filters on the full map of blokvolt.com, with the host site as utm_source (widget only)
function fullUrl(pid) {
  const u = new URL(EMB.open, location.href), q = new URLSearchParams(location.search);
  q.delete('tema');
  if (pid) q.set('id', pid); else q.delete('id');
  q.set('utm_source', HOST || 'widget'); q.set('utm_medium', 'widget'); q.set('utm_campaign', EMB.utm || 'world-map');
  u.search = q.toString().replace(/%2C/g, ',');
  if (map) { const c = map.getCenter(); u.hash = '#' + Math.round(map.getZoom() * 100) / 100 + '/' + c.lat.toFixed(5) + '/' + c.lng.toFixed(5); }
  return u.toString();
}
let HOST = '';
try { HOST = d.referrer ? new URL(d.referrer).hostname.replace(/^www\./, '').slice(0, 80) : ''; } catch (e) { HOST = ''; }
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
  if (EMB) { attributionEmb(); return; }
  // HOME3: one short line in the corner, "© OpenStreetMap contributors · Sources", visible without any action (L1 §2,
  // OSMF guidelines); 5 s after the start it folds into "ⓘ" (never earlier); "ⓘ" opens a panel with the map data, the
  // base map, the data date and the number of sources. The widget keeps its own line (G5).
  const S = M.sources || {};
  const lic = k => (S[k] && S[k].licence ? ` (${esc(S[k].licence)})` : '');
  const n = nSources();
  const at = $('wm-attr');
  const short = `© <a href="https://www.openstreetmap.org/copyright" rel="noopener">${esc(t('attr_osm'))}</a>` +
    (EMB ? '' : ` · <a href="${esc(cfg.sources || cfg.about)}">${esc(t('attr_sources'))}</a>`);
  const parts = [`${esc(t('attr_data'))}: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a>${lic('osm') || ' (ODbL)'}` +
    (S.ocm ? ` · <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a>${lic('ocm')}` : '') +
    (S.geonames ? ` · <a href="https://www.geonames.org/" rel="noopener">GeoNames</a>${lic('geonames')}` : ''),
    `${esc(t('attr_map'))}: <a href="https://openfreemap.org" rel="noopener">OpenFreeMap</a> © <a href="https://www.openmaptiles.org/" rel="noopener">OpenMapTiles</a>`,
    `${esc(t('data_date', { d: fmtDate(M.date) }))} · ${esc(t('sources_n', { n: nf(n) }))} · <button class="lnkbtn" type="button" data-sources>${esc(t('sources_btn'))}</button>`];
  at.innerHTML = `<span class="wm-attr-full">${short}</span><span class="wm-attr-more" id="wm-attr-more">${parts.join('<br>')}</span>` +
    `<button class="wm-attr-i" type="button" aria-expanded="false" aria-controls="wm-attr-more" aria-label="${esc(t('attr_show'))}">i</button>`;
  let opened = false;
  const fold = () => { if (!opened) at.classList.add('is-min'); };
  setTimeout(() => {
    if (EMB && !(window.matchMedia && matchMedia('(max-width: 480px)').matches)) return;
    fold();
  }, 5000);
  const c = M.counts || {};
  $('wm-data').innerHTML = (c.sites ? `<p class="wm-count"><b>${esc(t('count_line', { n: nf(c.sites), m: nf(c.public || 0) }))}</b></p>` : '') +
    `<p><button class="lnkbtn" type="button" data-sources>${esc(t('sources_btn'))}</button> · <a href="${esc(cfg.about)}">${esc(t('about'))}</a>` +
    (cfg.download ? ` · <a href="${esc(cfg.download)}">${esc(t('download'))}</a>` : '') + `</p><p class="wm-small">${esc(t('odbl_note'))}</p>`;
}
// one number of sources everywhere (HOME3 12): the publishers of the layer — Open Charge Map counts once, the data
// providers inside it (manifest keys "ocm:<id>") are listed in the dialog but not counted again (as on /sources/)
function nSources() { return Object.keys((M && M.sources) || {}).filter(k => !k.startsWith('ocm:')).length; }
function attributionEmb() {   // the widget keeps its G5 line (unchanged by HOME3)
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
  $('wm-src-body').innerHTML = `<p>${esc(t('data_date', { d: fmtDate(M.date) }))} · ${esc(t('sources_n', { n: nf(nSources()) }))}</p><ul class="wm-srcl">${rows}</ul><p class="wm-small">${esc(t('odbl_note'))} <a href="${esc(cfg.about)}">${esc(t('about'))}</a></p>`;
  const dl = $('wm-src');
  if (dl.showModal) dl.showModal(); else dl.setAttribute('open', '');
}
// THEME (12.11.2026): the "ⓘ" card closes with "ⓘ" again, Esc, a click elsewhere or a move of the map (as on the home)
function attrOpen(open) {
  const at = $('wm-attr'), i = at && at.querySelector('.wm-attr-i');
  if (!at || !i || EMB) return;
  at.classList.toggle('is-open', open);
  at.classList.toggle('is-min', !open);
  i.setAttribute('aria-expanded', String(open));
}
const attrIsOpen = () => { const at = $('wm-attr'); return !!(at && at.classList.contains('is-open')); };
d.addEventListener('keydown', e => {
  if (e.key === 'Escape' && attrIsOpen()) { attrOpen(false); const i = $('wm-attr').querySelector('.wm-attr-i'); if (i) i.focus(); }
});
d.addEventListener('click', e => {
  const i = e.target.closest('.wm-attr-i');
  if (i) {
    if (EMB) {
      const at = $('wm-attr'), open = !at.classList.contains('is-open');
      at.classList.toggle('is-open', open);
      at.classList.toggle('is-min', !open);
      i.setAttribute('aria-expanded', String(open));
    } else attrOpen(!attrIsOpen());
    return;
  }
  if (attrIsOpen() && !e.target.closest('#wm-attr')) attrOpen(false);
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
  // a point merged into another by the weekly build (manifest.redirects: old pid → kept pid): an old shared link opens the kept one
  const to = M && M.redirects && M.redirects[st.id];
  const pid = to ? String(to) : st.id;
  // a shared link puts the point in the hash (#z/lat/lon): its card file is found from there
  const c = map.getCenter();
  const near = map.queryRenderedFeatures({ layers: [LYR] }).find(f => String(f.properties.i) === pid);
  openCard(pid, near ? near.geometry.coordinates : [c.lng, c.lat], near ? near.properties : null);
}

// ------------------------------------------------------------------ widget: links back and one view count a load
function embedInit() {
  d.querySelectorAll('[data-emb-full]').forEach(a => {
    const go = () => { a.href = fullUrl(cur && cur.pid); };
    go();
    a.addEventListener('pointerdown', go);
    a.addEventListener('focus', go);
  });
  // the view count (host name only, no cookie): only when the API is set — empty until "релиз G5" (demo mode)
  if (EMB.views && HOST !== location.hostname.replace(/^www\./, '')) {
    const body = JSON.stringify({ h: HOST, k: 'map', l: LANG });
    try {
      if (!(navigator.sendBeacon && navigator.sendBeacon(EMB.views, new Blob([body], { type: 'text/plain' }))))
        fetch(EMB.views, { method: 'POST', body, mode: 'cors', keepalive: true }).catch(() => {});
    } catch (e) { /* a widget never fails because of the count */ }
  }
}

// ------------------------------------------------------------------ light / dark map (HOME3; THEME: the switch of the header)
function paintTheme() {
  const b = $('wm-theme');   // HOME3's own button is gone (THEME): the header's switch does it for the whole site
  if (!b) return;
  if (EMB || !cfg.style_dark) { b.hidden = true; return; }
  b.setAttribute('aria-pressed', String(!!TEMA));
  b.querySelector('span').textContent = TEMA ? b.dataset.light : b.dataset.dark;
}
function setTheme(x) {
  TEMA = x === 'tamna' ? 'tamna' : '';
  d.documentElement.classList.toggle('wm-dark', !!TEMA);
  writeUrl();
  paintTheme();
  if (!map) return;
  ready = false;
  useStyle();   // the points come back in the 'style.load' handler of initMap()
}
if (!EMB) d.addEventListener('bv-theme', e => setTheme(e.detail === 'dark' ? 'tamna' : 'svetla'));

// ------------------------------------------------------------------ poster → live map (TAILS P2.7)
function startMap() {
  const P = $('wm-poster'), pic = cfg.poster;
  const plain = !location.search.replace(/^\?/, '') && !HAD_HASH;
  if (EMB || !P || !pic || !plain || !matchMedia('(max-width: 720px)').matches) {
    if (P) P.hidden = true;
    initMap();
    return;
  }
  let go = false;
  const evs = ['pointerdown', 'touchstart', 'keydown', 'wheel'];
  const start = () => {
    if (go) return;
    go = true;
    evs.forEach(x => d.removeEventListener(x, start, true));
    window.removeEventListener('scroll', start);
    // the live map opens exactly where the picture is: same centre, zoom scaled like object-fit: cover
    const el = $('map'), W = el.clientWidth || pic.w, H = el.clientHeight || pic.h;
    initMap({ center: pic.c, zoom: pic.z + Math.log2(Math.max(W / pic.w, H / pic.h)) }).then(() => {
      if (!map) { P.hidden = true; return; }
      map.once('idle', () => { P.classList.add('is-gone'); setTimeout(() => { P.hidden = true; }, 300); });
    });
  };
  evs.forEach(x => d.addEventListener(x, start, { capture: true, passive: true }));
  window.addEventListener('scroll', start, { passive: true });
}

// ------------------------------------------------------------------ start
readUrl();
paintTheme();
paintFilters();
startMap();
if (EMB) embedInit();
// for debugging and scripts/qa/world_map_test.py (read only by tests; nothing on the page depends on it)
window.BVWorldMap = { get map() { return map; }, get ready() { return ready; }, get manifest() { return M; }, state: st, openCard };
// SEARCH (12.11.2026): the site search above the filters (world-search.js) — a place, a network or "ionity munich" chosen
// there moves this map (and sets the network / power filter) instead of opening another page; pages still open
d.addEventListener('bvs-pick', e => {
  if (!map || EMB) return;
  const u = new URL(e.detail.map, location.href), q = u.searchParams;
  e.preventDefault();
  if (q.get('mreza')) st.mreza = new Set(q.get('mreza').split(',').map(slug).filter(Boolean));
  if (q.get('snaga')) st.snaga = new Set(q.get('snaga').split(',').filter(x => SNAGA.includes(x)));
  st.zemlja = (q.get('zemlja') || '').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2);
  st.grad = (q.get('grad') || '').replace(/\D/g, '');
  applyFilter();
  paintFilters();
  const h = /^#([\d.]+)\/(-?[\d.]+)\/(-?[\d.]+)/.exec(u.hash);
  if (h) map.flyTo({ zoom: +h[1], center: [+h[3], +h[2]], duration: 900 });
  else if (st.zemlja || st.grad) flyPlace();
});
async function flyPlace() {
  let P = null;
  try { P = await getJson(at(M.places)); } catch (e) { return; }
  const c = st.grad && P.city && P.city[st.grad], b = c || (st.zemlja && P.cc && P.cc[st.zemlja]);
  if (b && b.length >= 4) map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 30, maxZoom: c ? 13 : 9, duration: 900 });
}
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
