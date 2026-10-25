/* BlokVolt — map of service points for electric cars (/servisi/). MapLibre GL + OpenFreeMap, the same layout and card as
   /mapa/. Places from /assets/servisi/servisi.json (built from content/servisi/servisi.json): the authorized services of the
   brands that sell electric cars in Serbia, as the importers list them, and the independent services that say on their own
   sites that they work on electric cars. Same fields and rules for every service; no ratings, no order but distance and name.
   The reader's location stays in the browser. Serbian texts of the data are translated on /en/ and /ru/ through the page's
   string table ('tx:<text>'). docs/RUNBOOK.md 3.31. */
import * as maplibregl from '/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs';

const d = document;
const cfg = JSON.parse(d.getElementById('srv-cfg').textContent);
const T = JSON.parse(d.getElementById('bv-i18n').textContent);
const LANG = (d.documentElement.lang || 'sr').slice(0, 2);
const LP = LANG === 'en' || LANG === 'ru' ? '/' + LANG : '';
const LOC = LANG === 'sr' ? 'sr-Latn-RS' : LANG;
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const tr = s => (s && T['tx:' + s]) || s;
const fold = s => String(s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
const CYR = { а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', ђ: 'd', е: 'e', ж: 'z', з: 'z', и: 'i', ј: 'j', к: 'k', л: 'l', љ: 'lj', м: 'm',
  н: 'n', њ: 'nj', о: 'o', п: 'p', р: 'r', с: 's', т: 't', ћ: 'c', у: 'u', ф: 'f', х: 'h', ц: 'c', ч: 'c', џ: 'dz', ш: 's', й: 'j',
  ы: 'y', э: 'e', ю: 'ju', я: 'ja', ё: 'e', щ: 's', ь: '', ъ: '' };
const sfold = s => fold(String(s || '').toLowerCase().replace(/[Ѐ-ӿ]/g, c => (c in CYR ? CYR[c] : c)))
  .replace(/([szc])h/g, '$1').replace(/dj/g, 'd');
const fmt = (n, dg = 0) => Number(n).toLocaleString(LOC, { minimumFractionDigits: dg, maximumFractionDigits: dg });
const track = (e, p) => { try { if (window.bvTrack) window.bvTrack(e, p); } catch (x) { /* never breaks the map */ } };
const svg = p => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + p + '</svg>';
const ICON = {
  x: svg('<path d="M6 6l12 12M18 6 6 18"/>'),
  nav: svg('<path d="M3.5 11 20.5 3.5 13 20.5l-2-7.5-7.5-2Z"/>'),
  ext: svg('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
  flag: svg('<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>'),
  share: svg('<path d="M12 3v12M7 8l5-5 5 5"/><path d="M5 12v7a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-7"/>'),
  phone: svg('<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1Z"/>'),
  wrench: svg('<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'),
  clock: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>')
};

// directions: Apple Maps first on Apple devices, Google Maps elsewhere, Waze always; the app chosen last comes first
// (the same 'bv:nav2' key as the charger map, kept in this browser)
const IS_APPLE = /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent) && !/Android/.test(navigator.userAgent);
const NAV_NAME = { google: 'Google Maps', apple: 'Apple Maps', waze: 'Waze' };
let NAV_PREF = '';
try { NAV_PREF = localStorage.getItem('bv:nav2') || ''; } catch (e) { NAV_PREF = ''; }
const navApps = () => (IS_APPLE ? ['google', 'apple', 'waze'] : ['google', 'waze']);   // Google Maps first everywhere (owner, 25.10.2026)
const navPref = () => (navApps().indexOf(NAV_PREF) >= 0 ? NAV_PREF : navApps()[0]);
function setNavPref(a) {
  if (navApps().indexOf(a) < 0 || a === NAV_PREF) return;
  NAV_PREF = a;
  try { localStorage.setItem('bv:nav2', a); } catch (e) { /* private mode */ }
}
function navUrl(a, s) {
  const ll = s.lat + ',' + s.lon;
  if (a === 'apple') return 'https://maps.apple.com/?daddr=' + ll + '&dirflg=d';
  if (a === 'waze') return 'https://waze.com/ul?ll=' + ll + '&navigate=yes&utm_source=blokvolt';
  return 'https://www.google.com/maps/dir/?api=1&destination=' + ll + '&travelmode=driving&dir_action=navigate';
}
function distKm(a, b) {
  const r = Math.PI / 180, dLa = (b.lat - a.lat) * r, dLo = (b.lon - a.lon) * r;
  const h = Math.sin(dLa / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLo / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
}

// ---------- state ----------
const $list = d.getElementById('slist'), $count = d.getElementById('scount'), $card = d.getElementById('scard');
const $chips = d.getElementById('schips'), $q = d.getElementById('sq'), $brand = d.getElementById('sbrand'), $me = d.getElementById('sme');
const P0 = new URLSearchParams(location.search);
const state = { f: ['o', 'n', 'bat', 'tesla'].indexOf(P0.get('f')) >= 0 ? P0.get('f') : 'all', q: P0.get('q') || '', b: P0.get('marka') || '', bounds: null, lim: 25 };
let ALL = [], BR = {}, map = null, sel = null, me = null, userMove = false, CHECKED = '';

const BAT = ['dijagnostika_baterije', 'popravka_baterije', 'bms'];
function hay(s) {
  if (!s._h) s._h = sfold([s.n, s.g, s.ar, s.a, (s.b || []).join(' '), (s.m || []).join(' '), s.t === 'o' ? T.t_o : T.t_n].join(' '));
  return s._h;
}
function pass(s) {
  if (state.f === 'o' && s.t !== 'o') return false;
  if (state.f === 'n' && s.t !== 'n') return false;
  if (state.f === 'bat' && !(s.s || []).some(x => BAT.indexOf(x) >= 0)) return false;
  if (state.f === 'tesla' && (s.m || []).indexOf('Tesla') < 0) return false;
  if (state.b && (s.b || []).concat(s.m || []).indexOf(state.b) < 0) return false;
  if (state.q) {
    // a word that is a town name means that town ("Niš" must not find "Nissan" elsewhere)
    const q = sfold(state.q).trim(), g = sfold(s.g);
    if (isTown(q)) return g === q;
    const words = q.split(/\s+/).filter(Boolean);
    if (!words.every(w => (isTown(w) ? g === w : hay(s).indexOf(w) >= 0))) return false;
  }
  return true;
}
let TOWNS = null;
function isTown(w) {
  if (!TOWNS && ALL.length) TOWNS = new Set(ALL.map(s => sfold(s.g)));
  return !!TOWNS && TOWNS.has(w);
}
const visible = () => ALL.filter(pass);
// a service whose address could not be placed has no point (pos 'none'): it is in the list, not on the map
const hasPt = s => isFinite(s.lat) && isFinite(s.lon) && s.lat !== null && s.lon !== null;
const inView = s => !state.bounds || (hasPt(s) && s.lat >= state.bounds.s && s.lat <= state.bounds.n && s.lon >= state.bounds.w && s.lon <= state.bounds.e);
const place = s => [s.a, s.ar && s.ar !== s.g ? s.ar : '', s.g].filter(Boolean).join(', ');
const brandsOf = s => (s.t === 'o' ? s.b : s.m) || [];
function sub(s) {
  const kind = s.t === 'o' ? (s.b || []).join(', ') : T.t_n;
  return [kind, s.g + (s.ar && s.ar !== s.g ? ' — ' + s.ar : '')].filter(Boolean).join(' · ');
}

// ---------- list ----------
function renderList() {
  let rows = visible().filter(inView);
  if (me) rows = rows.map(s => (s._d = hasPt(s) ? distKm(me, s) : Infinity, s)).sort((a, b) => a._d - b._d);
  const all = ALL.length;
  const txt = state.bounds ? T.in_view.replace('{n}', rows.length) : (rows.length === all ? T.count_all : T.count).replace('{n}', rows.length).replace('{all}', all);
  $count.innerHTML = esc(txt + (me ? ' · ' + T.sorted_near : '')) + (state.bounds ? ' · <button class="lnkbtn" type="button" data-all>' + esc(T.all_serbia) + '</button>' : '');
  const lim = window.innerWidth <= 900 ? state.lim : Infinity, more = rows.length - lim;
  $list.innerHTML = rows.slice(0, lim).map(s => {
    const dist = me && isFinite(s._d) ? '<span>' + fmt(s._d, s._d < 10 ? 1 : 0) + ' km</span>' : '';
    return '<button class="st sv' + (sel === s ? ' is-on' : '') + '" data-id="' + esc(s.id) + '"><span class="dot sv-' + s.t + '">' + ICON.wrench + '</span>' +
      '<span class="nm"><b>' + esc(s.n) + '</b><span class="sb">' + esc(sub(s)) + '</span></span><span class="pr">' + esc(s.t === 'o' ? T.tag_o : T.tag_n) + dist + '</span></button>';
  }).join('') || '<p class="empty">' + esc(T.none) + '</p>';
  if (more > 0) $list.insertAdjacentHTML('beforeend', '<div class="more"><button class="btn sm" type="button" data-more>' + esc(T.more.replace('{n}', more)) + '</button></div>');
}
$list.addEventListener('click', e => {
  if (e.target.closest('[data-more]')) { state.lim += 25; renderList(); return; }
  const b = e.target.closest('.st');
  if (!b) return;
  const s = ALL.find(x => x.id === b.dataset.id);
  if (s) openCard(s, true);
});
$count.addEventListener('click', e => {
  if (!e.target.closest('[data-all]')) return;
  state.bounds = null;
  if (map) { userMove = false; map.flyTo({ center: cfg.center, zoom: cfg.zoom }); }
  renderList();
});

// ---------- card ----------
function cbox(label, html) { return '<div class="cbox"><span>' + esc(label) + '</span>' + html + '</div>'; }
function telHref(t) { return 'tel:' + String(t).split(/[,;/]| ili /)[0].replace(/[^\d+]/g, ''); }
function openCard(s, fly) {
  sel = s;
  const bi = s.t === 'o' ? (s.b || []).map(b => BR[b]).filter(Boolean) : [];
  let h = '<div class="ccard sv-card" role="dialog" aria-label="' + esc(s.n) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(s.n) + '</h2><p class="addr">' + esc(place(s)) + '</p>' +
    '<p class="sv-kind"><span class="sv-pill sv-' + s.t + '">' + ICON.wrench + esc(s.t === 'o' ? T.t_o : T.t_n) + '</span></p>';
  // other services on the same spot (one auto centre, several firms): a map tap reaches only one of them
  const same = hasPt(s) ? ALL.filter(x => x !== s && hasPt(x) && Math.abs(x.lat - s.lat) < 0.0003 && Math.abs(x.lon - s.lon) < 0.0004) : [];
  if (same.length) h += '<p class="sv-same">' + esc(T.same_spot) + ': ' + same.map(x => '<button type="button" class="lnk" data-same="' + esc(x.id) + '">' + esc(x.n) + '</button>').join(' · ') + '</p>';
  if (s.t === 'o') {
    h += cbox(T.for_brands, '<ul>' + (s.b || []).map(b => '<li><b>' + esc(b) + '</b>' + (BR[b] && BR[b].ev ? '<small>' + esc(T.ev_models) + ': ' + esc(tr(BR[b].ev)) + '</small>' : '') + '</li>').join('') + '</ul>');
    // evs: who says it — 'u' the importer's list, 's' the service's own site
    h += cbox(T.ev_work, s.ev ? '<div>' + esc(s.evs === 's' ? T.firm_says : T.imp_says) + ': ' + esc(tr(s.ev)) + '</div>' : '<small>' + esc(T.ev_none) + '</small>');
  } else {
    if (s.ev) h += cbox(T.ev_work, '<div>' + esc(T.firm_says) + ': ' + esc(tr(s.ev)) + '</div>');
    if ((s.s || []).length) h += cbox(T.services, '<div class="sv-tags">' + s.s.map(x => '<span class="tag">' + esc(T['s_' + x] || x) + '</span>').join('') + '</div>');
    h += cbox(T.makes, (s.m || []).length ? '<div>' + esc(s.m.join(', ')) + '</div>' : '<small>' + esc(T.not_said) + '</small>');
  }
  if (s.oh) h += cbox(T.hours, '<div>' + esc(tr(s.oh)) + '</div>');
  const navs = [navPref()].concat(navApps().filter(a => a !== navPref())), pt = hasPt(s);
  const findUrl = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent([s.n, s.a, s.g].join(', '));
  const fix = LP + '/ispravka/?servis=' + encodeURIComponent(s.id);
  h += '<div class="acts">' +
    (s.tel ? '<a class="btn dark full" href="' + esc(telHref(s.tel)) + '" data-act="call">' + ICON.phone + esc(T.call) + ' ' + esc(s.tel) + '</a>' : '') +
    (s.tel2 ? '<p class="nav-alt">' + esc(T.tel2) + ': <a class="lnk" href="' + esc(telHref(s.tel2)) + '" data-act="call">' + esc(s.tel2) + '</a></p>' : '') +
    (pt ? '<a class="btn' + (s.tel ? '' : ' dark') + ' full" href="' + navUrl(navs[0], s) + '" target="_blank" rel="noopener" data-nav="' + navs[0] + '">' + ICON.nav + esc(T.navigate) + '</a>' +
    '<p class="nav-alt">' + esc(T.nav_in) + ' ' + navs.slice(1).map(a => '<a class="lnk" href="' + navUrl(a, s) + '" target="_blank" rel="noopener" data-nav="' + a + '">' + NAV_NAME[a] + '</a>').join(' · ') + '</p>'
      : '<a class="btn' + (s.tel ? '' : ' dark') + ' full" href="' + findUrl + '" target="_blank" rel="noopener" data-act="find">' + ICON.nav + esc(T.find_addr) + '</a>') +
    (s.web ? '<a class="btn" href="' + esc(s.web) + '" target="_blank" rel="noopener nofollow" data-act="site">' + ICON.ext + esc(T.site) + '</a>' : '') +
    '<button class="btn" type="button" data-share>' + ICON.share + esc(T.share) + '</button>' +
    '<a class="btn' + (s.web ? ' full' : '') + '" href="' + fix + '" data-act="report">' + ICON.flag + esc(T.report) + '</a></div>';
  const srcs = (s.src || []).filter(x => x.u).map(x => '<a href="' + esc(x.u) + '" rel="noopener nofollow">' + esc(tr(x.l)) + '</a>').join(' · ');
  h += '<p class="src">' + esc(T.data) + ': ' + srcs + (CHECKED ? ' · ' + esc(T.checked.replace('{d}', CHECKED)) : '') +
    (s.pos === 'osm' ? '<br>' + esc(T.pos_osm) : s.pos === 'none' ? '<br>' + esc(T.pos_none) : '') + '</p>';
  if (bi.length && bi.some(b => b.u)) h += '<p class="src">' + esc(T.net_of) + ': ' + bi.filter(b => b.u).map(b => '<a href="' + esc(b.u) + '" rel="noopener nofollow">' + esc(b.name) + '</a>').join(' · ') + '</p>';
  $card.innerHTML = h + '</div>';
  $card.classList.add('is-open');
  $card.querySelector('.x').addEventListener('click', closeCard);
  $card.querySelectorAll('[data-same]').forEach(b => b.addEventListener('click', () => {
    const o = ALL.find(x => x.id === b.dataset.same);
    if (o) openCard(o, false);
  }));
  $card.querySelector('.acts').addEventListener('click', e => {
    if (e.target.closest('[data-share]')) { share(s); return; }
    const a = e.target.closest('a');
    if (!a) return;
    if (a.dataset.nav) { setNavPref(a.dataset.nav); track('srv_navigate', { servis: s.id, tip: s.t, app: a.dataset.nav }); }
    else track('srv_' + (a.dataset.act || 'link'), { servis: s.id, tip: s.t });
  });
  track('srv_card_open', { servis: s.id, tip: s.t });
  if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: pt ? [feat(s)] : [] });
  if (fly && map && pt) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 13), speed: 1.4, padding: padding() });
  history.replaceState(null, '', location.pathname + location.search + '#' + s.id);
  renderList();
}
function closeCard() {
  sel = null;
  $card.classList.remove('is-open');
  $card.innerHTML = '';
  if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [] });
  history.replaceState(null, '', location.pathname + location.search);
  renderList();
}
d.addEventListener('keydown', e => { if (e.key === 'Escape' && sel) closeCard(); });
function share(s) {
  const url = location.origin + location.pathname + '#' + encodeURIComponent(s.id);
  const done = how => track('srv_share', { servis: s.id, how });
  if (navigator.share) { navigator.share({ title: s.n, text: s.n + ' — ' + place(s), url }).then(() => done('sheet'), () => {}); return; }
  const b = $card.querySelector('[data-share]');
  const ok = () => { if (b) { b.lastChild.textContent = T.copied; setTimeout(() => { if (b.isConnected) b.lastChild.textContent = T.share; }, 2500); } done('copy'); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(ok, () => prompt(T.share, url));
  else prompt(T.share, url);
}
const padding = () => (window.innerWidth > 900 ? { left: 0, right: 400, top: 0, bottom: 0 } : { top: 0, bottom: 0, left: 0, right: 0 });

// ---------- map ----------
function feat(s) {
  return { type: 'Feature', geometry: { type: 'Point', coordinates: [s.lon, s.lat] }, properties: { id: s.id, t: s.t, n: s.n } };
}
function setData() {
  if (map && map.getSource('sv')) map.getSource('sv').setData({ type: 'FeatureCollection', features: visible().filter(hasPt).map(feat) });
}
function initMap() {
  map = new maplibregl.Map({ container: 'smap', style: cfg.style, center: cfg.center, zoom: cfg.zoom, minZoom: 5, maxZoom: 18,
    attributionControl: false, dragRotate: false, pitchWithRotate: false });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.on('load', () => {
    const zr = (a, b, c, e) => ['interpolate', ['linear'], ['zoom'], 5, a, 8, b, 12, c, 16, e];
    map.addSource('sv', { type: 'geojson', data: { type: 'FeatureCollection', features: visible().filter(hasPt).map(feat) } });
    map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: sel && hasPt(sel) ? [feat(sel)] : [] } });
    map.addSource('me', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    // independent EV services above the authorized ones (fewer, and the reason many readers come)
    map.addLayer({ id: 'sv-pt', type: 'circle', source: 'sv',
      layout: { 'circle-sort-key': ['match', ['get', 't'], 'n', 2, 1] },
      paint: {
        'circle-radius': zr(3.5, 5, 9, 12),
        'circle-color': ['match', ['get', 't'], 'n', '#D9F45B', '#0D111A'],
        'circle-stroke-width': zr(1.2, 1.6, 2.5, 2.5),
        'circle-stroke-color': ['match', ['get', 't'], 'n', '#0D111A', '#FFFFFF']
      } });
    map.addLayer({ id: 'sv-nm', type: 'symbol', source: 'sv', minzoom: 12.5,
      layout: { 'text-field': ['get', 'n'], 'text-font': cfg.font, 'text-size': 11.5, 'text-anchor': 'left', 'text-offset': [1.2, 0], 'text-max-width': 14, 'text-padding': 2 },
      paint: { 'text-color': '#0D111A', 'text-halo-color': '#FFFFFF', 'text-halo-width': 2.2 } });
    map.addLayer({ id: 'sel', type: 'circle', source: 'sel',
      paint: { 'circle-radius': zr(9, 11, 16, 16), 'circle-color': 'rgba(217,244,91,.35)', 'circle-stroke-width': 3, 'circle-stroke-color': '#0D111A' } }, 'sv-pt');
    map.addLayer({ id: 'me-halo', type: 'circle', source: 'me', paint: { 'circle-radius': 22, 'circle-color': 'rgba(46,107,255,.16)' } });
    map.addLayer({ id: 'me-dot', type: 'circle', source: 'me', paint: { 'circle-radius': 7, 'circle-color': '#FFFFFF', 'circle-stroke-width': 4, 'circle-stroke-color': '#2E6BFF' } });
    showMe();
    map.on('moveend', e => {
      if (!e.originalEvent && !userMove) return;
      userMove = false;
      if (map.getZoom() >= 8) {
        const b = map.getBounds();
        state.bounds = { s: b.getSouth(), n: b.getNorth(), w: b.getWest(), e: b.getEast() };
      } else state.bounds = null;
      state.lim = 25;
      renderList();
    });
    // a tap looks at a small box around the finger: one service opens its card, several zoom in on them
    map.on('click', e => {
      const r = window.matchMedia && matchMedia('(pointer: coarse)').matches ? 14 : 8, p = e.point;
      const hits = map.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]], { layers: ['sv-pt'] });
      if (!hits.length) return;
      const ids = new Set(hits.map(f => f.properties.id)), z0 = map.getZoom();
      if (ids.size > 1 && z0 < 14) {
        const b = new maplibregl.LngLatBounds();
        hits.forEach(f => b.extend(f.geometry.coordinates));
        const cam = map.cameraForBounds(b, { padding: 60 });
        userMove = true;
        map.easeTo({ center: b.getCenter(), zoom: Math.min(15, Math.max(z0 + 2, cam && isFinite(cam.zoom) ? cam.zoom : 0)) });
        return;
      }
      let best = hits[0], bd = Infinity;
      hits.forEach(f => {
        const q = map.project(f.geometry.coordinates), dd = (q.x - p.x) ** 2 + (q.y - p.y) ** 2;
        if (dd < bd) { bd = dd; best = f; }
      });
      const s = ALL.find(x => x.id === best.properties.id);
      if (s) openCard(s, false);
    });
    map.on('mouseenter', 'sv-pt', () => { map.getCanvas().style.cursor = 'pointer'; });
    map.on('mouseleave', 'sv-pt', () => { map.getCanvas().style.cursor = ''; });
    if (sel && hasPt(sel)) map.jumpTo({ center: [sel.lon, sel.lat], zoom: 13, padding: padding() });
  });
}
function showMe() {
  if (map && map.getSource('me')) map.getSource('me').setData({ type: 'FeatureCollection', features: me ? [{ type: 'Feature', geometry: { type: 'Point', coordinates: [me.lon, me.lat] }, properties: {} }] : [] });
}
function refresh() { state.lim = 25; setData(); renderList(); }

// ---------- controls ----------
function paintChips() {
  [].forEach.call($chips.querySelectorAll('.chip'), c => c.setAttribute('aria-pressed', c.dataset.f === state.f ? 'true' : 'false'));
}
$chips.addEventListener('click', e => {
  const c = e.target.closest('.chip');
  if (!c) return;
  state.f = c.dataset.f;
  track('srv_filter', { filter: state.f, marka: state.b });
  paintChips();
  refresh();
});
if ($brand) $brand.addEventListener('change', () => {
  state.b = $brand.value;
  track('srv_filter', { filter: state.f, marka: state.b });
  refresh();
});
let qT = 0;
$q.addEventListener('input', () => {
  clearTimeout(qT);
  qT = setTimeout(() => { state.q = $q.value.trim(); state.bounds = null; refresh(); }, 150);
});
$me.addEventListener('click', () => {
  if (!navigator.geolocation) { $count.textContent = T.no_location; return; }
  $me.disabled = true;
  navigator.geolocation.getCurrentPosition(pos => {
    me = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    state.bounds = null;
    $me.disabled = false;
    track('srv_near_me', { ok: true });
    showMe();
    if (map) map.flyTo({ center: [me.lon, me.lat], zoom: 10 });
    renderList();
  }, () => { $me.disabled = false; $count.textContent = T.no_location; track('srv_near_me', { ok: false }); },
  { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
});

// the list by city under the map: a name opens the card on the map
d.addEventListener('click', e => {
  const a = e.target.closest && e.target.closest('a[data-sv]');
  if (!a) return;
  const s = ALL.find(x => x.id === a.dataset.sv);
  if (!s) return;
  e.preventDefault();
  const w = d.querySelector('.map-app');
  if (w) w.scrollIntoView({ behavior: 'smooth', block: 'start' });
  openCard(s, true);
  track('srv_city_list', { servis: s.id });
});
window.addEventListener('hashchange', () => {
  const s = ALL.find(x => x.id === decodeURIComponent(location.hash.slice(1)));
  if (s && s !== sel) openCard(s, true);
});

if (P0.get('qa') === '1') { window.bvSrvQa = () => map; window.bvSrvQaVis = () => visible().map(x => x.t); }    // scripts/qa/servisi_ui_test.py

// ---------- start ----------
fetch(cfg.data).then(r => r.json()).then(j => {
  CHECKED = j.checked || '';
  BR = j.brands || {};
  // the list order is the name (or the distance with „Blizu mene“), nothing else (RUNBOOK 3.31)
  ALL = (j.p || []).slice().sort((a, b) => a.n.localeCompare(b.n, 'sr') || a.g.localeCompare(b.g, 'sr'));
  if ($brand) {
    const have = new Set();
    ALL.forEach(s => brandsOf(s).forEach(b => have.add(b)));
    const opts = [...have].sort((a, b) => a.localeCompare(b, 'sr'));
    $brand.insertAdjacentHTML('beforeend', opts.map(b => '<option value="' + esc(b) + '">' + esc(b) + '</option>').join(''));
    if (state.b && have.has(state.b)) $brand.value = state.b; else state.b = '';
  }
  if (state.q) $q.value = state.q;
  paintChips();
  const id = decodeURIComponent(location.hash.slice(1));
  const s0 = id && ALL.find(x => x.id === id);
  if (s0) sel = s0;
  renderList();
  initMap();
  if (s0) openCard(s0, false);
}).catch(() => { $count.textContent = T.load_err; });
