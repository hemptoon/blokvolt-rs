/* BlokVolt — map of public chargers (/mapa/). MapLibre GL + OpenFreeMap; stations from
   /assets/map/punjaci.json (OSM + OCM, ODbL), prices from /assets/map/cene.json (ours). */
import * as maplibregl from '/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs';

const d = document;
const cfg = JSON.parse(d.getElementById('map-cfg').textContent);
const T = JSON.parse(d.getElementById('bv-i18n').textContent);
const LANG = (d.documentElement.lang || 'sr').slice(0, 2);
const fold = s => (s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmt = (n, dg = 0) => Number(n).toLocaleString(LANG === 'sr' ? 'sr-Latn-RS' : LANG, { minimumFractionDigits: dg, maximumFractionDigits: dg });
const CONN = { ccs2: 'CCS2', ccs1: 'CCS1', chademo: 'CHAdeMO', type2: 'Type 2', type1: 'Type 1', tesla: 'Tesla', schuko: T.schuko, cee: 'CEE', other: T.other };
const ICON = {
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  nav: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 11 20.5 3.5 13 20.5l-2-7.5-7.5-2Z"/></svg>',
  ext: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
  flag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4M5 4h11l-2 4 2 4H5"/></svg>'
};

let ST = [], NETS = {}, map, me = null, sel = null, city = null;
const state = { q: '', f: 'all', bounds: null, lim: 20 };
let userMove = false;
const $list = d.getElementById('mlist'), $count = d.getElementById('mcount'), $card = d.getElementById('mcard');
const $q = d.getElementById('mq'), $chips = d.getElementById('mchips'), $me = d.getElementById('mme');

// ---------- data ----------
function isFree(s) {
  const n = NETS[s.net];
  if (!n || !n.free) return false;
  if (!n.free_where) return true;
  const hay = fold([s.n, s.a, s.t].join(' '));
  return n.free_where.some(w => hay.indexOf(w) >= 0);
}
// state motorway chargers carry the official status (s.ps): none working now = 'off'
function isOff(s) { return !!s.ps && !s.ps.l.some(l => l[2] === 1); }
function kind(s) {
  if (isOff(s)) return 'off';
  if (isFree(s)) return 'free';
  return (s.dc || 0) > 0 ? 'dc' : 'ac';
}
function netOf(s) { return NETS[s.net] || null; }
function netName(s) { const n = netOf(s); return n ? n.name : (s.opn || ''); }
function title(s) { return s.n || (netName(s) ? netName(s) : T.charger); }
function place(s) { return s.a || (s.t ? T.near.replace('{t}', s.t) : ''); }
function power(s) { return s.dc || s.ac || 0; }

function price(s) {
  let n = netOf(s);
  if (!n) return { kind: 'none', text: T.p_unknown };
  if (n.via && NETS[n.via]) n = NETS[n.via];
  if (n.free) return isFree(s) ? { kind: 'free', text: T.p_free, note: n.free_note || '', date: n.date || '' } : { kind: 'none', text: n.note || T.p_unknown };
  const hay = fold(s.n + ' ' + s.a);
  const cur = s.dc ? 'dc' : 'ac', P = power(s);
  const fits = t => t.cur === cur && (t.lo == null || (P >= t.lo - 5 && P <= t.hi + 5));
  const all = (n.tiers || []).concat(n.places || []);
  const exact = all.filter(t => t.where.some(w => hay.indexOf(w) >= 0));
  const ex = exact.filter(fits)[0] || (exact.length === 1 ? exact[0] : null);
  const receipt = (n.receipts || []).filter(r => r.where.some(w => hay.indexOf(w) >= 0));
  if (ex) return { kind: 'exact', t: ex, receipt, note: n.note };
  if (s.net === 'chargego' || n === NETS.chargego) {
    const tiers = (n.tiers || []).filter(t => t.cur === cur);
    const t = tiers.filter(fits)[0];
    if (t) return { kind: 'tier', t, receipt, note: n.note };
    if (cur === 'dc' && tiers.length && P) {
      const lower = tiers.filter(x => x.hi <= P).pop(), upper = tiers.filter(x => x.lo >= P)[0];
      if (lower && upper) return { kind: 'range', lo: lower, hi: upper, note: n.note };
    }
  }
  const same = (n.tiers || []).filter(t => t.cur === cur);
  if (same.length) return { kind: 'seen', list: same, note: n.note };
  return { kind: 'none', text: n.note || T.p_unknown };
}
function priceShort(s) {
  if (isOff(s)) return { t: T.off, cls: 'off' };
  const p = price(s);
  if (p.kind === 'free') return { t: T.free, cls: 'free' };
  if (p.kind === 'exact' || p.kind === 'tier') return { t: p.t.label, cls: '' };
  if (p.kind === 'range') return { t: fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + T.per_min, cls: '' };
  return { t: '', cls: '' };
}

// ---------- filters ----------
function match(s) {
  const f = state.f;
  if (f === 'fast' && !((s.dc || 0) >= 50)) return false;
  if (f === 'ac' && !(s.ac || s.c.some(c => c[1] !== 'dc'))) return false;
  if (f === 'free' && kind(s) !== 'free') return false;
  if (f.indexOf('net:') === 0 && s.net !== f.slice(4)) return false;
  if (state.q) {
    const hay = s._q || (s._q = fold([s.n, s.a, s.t, netName(s), s.opn].join(' ')));
    for (const w of fold(state.q).split(/\s+/).filter(Boolean)) if (hay.indexOf(w) < 0) return false;
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
function renderList() {
  let rows = visible().filter(inView);
  const ref = me || city;
  if (ref) rows = rows.map(s => (s._d = distKm(ref, s), s)).sort((a, b) => a._d - b._d);
  const txt = state.bounds ? T.in_view.replace('{n}', rows.length) : (rows.length === ST.length ? T.count_all : T.count).replace('{n}', rows.length).replace('{all}', ST.length);
  $count.innerHTML = esc(txt + (ref ? ' · ' + T.sorted_near : '')) + (state.bounds ? ' · <button class="lnkbtn" type="button" data-all>' + esc(T.all_serbia) + '</button>' : '');
  const lim = window.innerWidth <= 900 ? state.lim : Infinity, more = rows.length - lim;
  const html = rows.slice(0, lim).map(s => {
    const k = kind(s), ps = priceShort(s), pw = power(s);
    const sub = [netName(s), place(s)].filter(Boolean).join(' · ');
    const dist = ref ? '<span>' + fmt(s._d, s._d < 10 ? 1 : 0) + ' km</span>' : '';
    return '<button class="st' + (sel === s ? ' is-on' : '') + '" data-id="' + esc(s.id) + '"><span class="dot ' + k + '">' + (pw ? Math.round(pw) : '') + '</span>' +
      '<span class="nm"><b>' + esc(title(s)) + '</b><span class="sb">' + esc(sub) + '</span></span><span class="pr ' + ps.cls + '">' + esc(ps.t) + dist + '</span></button>';
  }).join('');
  $list.innerHTML = (html || '<p class="empty">' + esc(T.none) + '</p>') + (more > 0 ? '<div class="more"><button class="btn sm" type="button" data-more>' + esc(T.more.replace('{n}', more)) + '</button></div>' : '');
}

// ---------- card ----------
function connLine(c) {
  const [type, cur, kw, n] = c;
  return (CONN[type] || type) + ' · ' + cur.toUpperCase() + (kw ? ' · ' + fmt(kw, kw % 1 ? 1 : 0) + ' kW' : '') + (n > 1 ? ' × ' + n : '');
}
function priceHtml(s) {
  const p = price(s);
  let h = '<div class="cbox"><span>' + esc(T.price) + '</span>';
  if (p.kind === 'free') {
    h += '<div class="price free">' + esc(T.p_free) + '</div>' + (p.note ? '<small>' + esc(p.note) + '</small>' : '');
  } else if (p.kind === 'exact' || p.kind === 'tier') {
    const t = p.t;
    h += '<div class="price">' + esc(t.label) + '</div>';
    if (t.extra) h += '<small>' + esc(t.extra) + '</small>';
    h += '<small>' + esc(p.kind === 'exact' ? T.p_exact : T.p_tier.replace('{c}', t.charger)) + ' · ' + esc(t.date) + (t.src ? ' · ' + esc(t.src) : '') + '</small>';
    (p.receipt || []).slice(0, 2).forEach(r => { h += '<small>' + esc(T.p_receipt.replace('{l}', r.label).replace('{k}', fmt(r.kwh))) + '</small>'; });
  } else if (p.kind === 'range') {
    h += '<div class="price">' + fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + esc(T.per_min) + '</div>';
    h += '<small>' + esc(T.p_range.replace('{a}', p.lo.charger).replace('{b}', p.hi.charger)) + ' · ' + esc(p.lo.date) + '</small>';
  } else if (p.kind === 'seen') {
    h += '<div>' + esc(T.p_seen) + '</div><ul>' + p.list.slice(0, 3).map(t => '<li><b>' + esc(t.label) + '</b> — ' + esc(t.charger) + (t.extra ? ', ' + esc(t.extra) : '') + '</li>').join('') + '</ul>';
    h += '<small>' + esc(p.note || '') + ' · ' + esc(p.list[0].date) + '</small>';
  } else {
    h += '<div>' + esc(p.text) + '</div>';
  }
  if (p.note && (p.kind === 'exact' || p.kind === 'tier' || p.kind === 'range')) h += '<small>' + esc(p.note) + '</small>';
  const idle = cfg.idle && cfg.idle[(netOf(s) && netOf(s).via) || s.net];
  if (idle && p.kind !== 'free' && p.kind !== 'none') h += '<small>' + esc(T.idle.replace('{x}', idle)) + '</small>';
  return h + '</div>';
}
function statusHtml(s) {
  if (!s.ps) return '';
  const li = s.ps.l.map(l => '<li class="' + (l[2] === 1 ? 'ok' : 'no') + '"><i></i><span>' + esc([l[0], l[1]].filter(Boolean).join(' · ')) +
    ' · <b>' + esc(l[2] === 1 ? T.st_ok : T.st_off) + '</b>' + (l[3] && T['st_' + l[3]] ? ' (' + esc(T['st_' + l[3]]) + ')' : '') + '</span></li>').join('');
  return '<div class="cbox"><span>' + esc(T.status) + '</span><ul class="stl">' + li + '</ul><small>' + esc(T.st_src.replace('{d}', s.ps.d)) + '</small></div>';
}
function openCard(s, fly) {
  sel = s;
  const n = netOf(s);
  const logo = n && n.logo ? '<span class="lg w' + (n.logo_dark ? ' dark' : '') + '"><img src="' + esc(n.logo) + '" alt=""></span>' : '<span class="lg w mono" aria-hidden="true">' + esc((netName(s) || '?').slice(0, 2).toUpperCase()) + '</span>';
  const netLine = netName(s) ? '<div class="net">' + logo + '<div><b>' + esc(netName(s)) + '</b><span>' + esc(n && n.page ? T.net_known : (s.opn && !n ? T.operator : T.net_unknown)) + '</span></div></div>' : '';
  const conns = s.c.length ? '<div class="cbox"><span>' + esc(T.conn) + '</span><ul>' + s.c.map(c => '<li>' + esc(connLine(c)) + '</li>').join('') + '</ul></div>' : '';
  const acc = s.acc === 'customers' ? '<div class="cbox"><span>' + esc(T.access) + '</span><div>' + esc(T.customers) + '</div></div>' : '';
  const nav = 'https://www.google.com/maps/dir/?api=1&destination=' + s.lat + ',' + s.lon;
  const site = n && n.page ? n.page : (n && n.site ? n.site : '');
  const mail = 'mailto:hello@blokvolt.com?subject=' + encodeURIComponent(T.mail_subj + ': ' + title(s)) + '&body=' + encodeURIComponent(T.mail_body + '\n\n' + title(s) + ' (' + s.id + ')\n' + location.origin + location.pathname + '#' + s.id);
  const SRC = { ocm: 'Open Charge Map', osm: 'OpenStreetMap', ps: 'JP Putevi Srbije' };
  const srcs = s.src.filter(x => x.u).map(x => '<a href="' + esc(x.u) + '" rel="noopener nofollow">' + (SRC[x.d] || x.d) + '</a>' + (x.upd ? ' (' + esc(x.upd) + ')' : '')).join(' · ');
  $card.innerHTML = '<div class="ccard" role="dialog" aria-label="' + esc(title(s)) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(title(s)) + '</h2><p class="addr">' + esc(place(s)) + '</p>' + netLine + priceHtml(s) + statusHtml(s) + conns + acc +
    '<div class="acts"><a class="btn dark full" href="' + nav + '" target="_blank" rel="noopener">' + ICON.nav + esc(T.navigate) + '</a>' +
    (site ? '<a class="btn" href="' + esc(site) + '"' + (site[0] === '/' ? '' : ' target="_blank" rel="noopener"') + '>' + ICON.ext + esc(n && n.page ? T.about_net : T.site) + '</a>' : '') +
    '<a class="btn' + (site ? '' : ' full') + '" href="' + mail + '">' + ICON.flag + esc(T.report) + '</a></div>' +
    '<p class="src">' + esc(T.data) + ': ' + srcs + '</p></div>';
  $card.classList.add('is-open');
  $card.querySelector('.x').addEventListener('click', closeCard);
  if (map && map.getSource('sel')) map.getSource('sel').setData({ type: 'FeatureCollection', features: [feat(s)] });
  if (fly && map) map.flyTo({ center: [s.lon, s.lat], zoom: Math.max(map.getZoom(), 13), speed: 1.4, padding: padding() });
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
function padding() {
  return window.innerWidth > 900 ? { left: 0, right: 400, top: 0, bottom: 0 } : { top: 0, bottom: 0, left: 0, right: 0 };
}

// ---------- map ----------
function feat(s) {
  return { type: 'Feature', id: s._i, geometry: { type: 'Point', coordinates: [s.lon, s.lat] }, properties: { id: s.id, k: kind(s), p: Math.round(power(s)) || '' } };
}
function data() { return { type: 'FeatureCollection', features: visible().map(feat) }; }
function refresh() {
  state.lim = 20;
  if (map && map.getSource('st')) map.getSource('st').setData(data());
  renderList();
}
function initMap() {
  map = new maplibregl.Map({
    container: 'map', style: cfg.style, center: [20.9, 44.1], zoom: 6.3, minZoom: 5, maxZoom: 18,
    attributionControl: false, cooperativeGestures: false, dragRotate: false, pitchWithRotate: false
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
  map.on('load', () => {
    map.addSource('st', { type: 'geojson', data: data(), cluster: true, clusterRadius: 42, clusterMaxZoom: 11 });
    map.addSource('sel', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    const font = cfg.font;
    map.addLayer({ id: 'cl', type: 'circle', source: 'st', filter: ['has', 'point_count'],
      paint: { 'circle-color': '#0D111A', 'circle-radius': ['step', ['get', 'point_count'], 15, 10, 19, 30, 24], 'circle-stroke-width': 3, 'circle-stroke-color': 'rgba(217,244,91,.55)' } });
    map.addLayer({ id: 'cl-n', type: 'symbol', source: 'st', filter: ['has', 'point_count'],
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': font, 'text-size': 13, 'text-allow-overlap': true },
      paint: { 'text-color': '#FFFFFF' } });
    map.addLayer({ id: 'pt', type: 'circle', source: 'st', filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 6, 12, 9, 16, 12],
        'circle-color': ['match', ['get', 'k'], 'dc', '#0D111A', 'free', '#D9F45B', 'off', '#E3E5E9', '#FFFFFF'],
        'circle-stroke-width': 2.5,
        'circle-stroke-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#8A909B', '#0D111A']
      } });
    map.addLayer({ id: 'pt-kw', type: 'symbol', source: 'st', filter: ['!', ['has', 'point_count']], minzoom: 12,
      layout: { 'text-field': ['get', 'p'], 'text-font': font, 'text-size': 10, 'text-allow-overlap': true },
      paint: { 'text-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#5C6270', '#0D111A'] } });
    map.addLayer({ id: 'sel', type: 'circle', source: 'sel',
      paint: { 'circle-radius': 16, 'circle-color': 'rgba(217,244,91,.35)', 'circle-stroke-width': 3, 'circle-stroke-color': '#0D111A' } }, 'pt');
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
function setChip(f) {
  state.f = f;
  [].forEach.call($chips.querySelectorAll('.chip'), c => c.setAttribute('aria-pressed', c.dataset.f === f ? 'true' : 'false'));
  refresh();
}
$chips.addEventListener('click', e => { const c = e.target.closest('.chip'); if (c) setChip(c.dataset.f); });
$count.addEventListener('click', e => {
  if (!e.target.closest('[data-all]')) return;
  state.bounds = null; me = null; city = null;
  if (map) map.flyTo({ center: [20.9, 44.1], zoom: 6.3 });
  renderList();
});
let qt;
$q.addEventListener('input', () => { clearTimeout(qt); qt = setTimeout(() => { state.q = $q.value.trim(); refresh(); }, 120); });
$list.addEventListener('click', e => {
  if (e.target.closest('[data-more]')) { state.lim += 30; renderList(); return; }
  const b = e.target.closest('.st'); if (b) { const s = ST.find(x => x.id === b.dataset.id); if (s) openCard(s, true); }
});
d.addEventListener('keydown', e => { if (e.key === 'Escape' && sel) closeCard(); });
$me.addEventListener('click', () => {
  if (!navigator.geolocation) return;
  $me.disabled = true;
  navigator.geolocation.getCurrentPosition(pos => {
    me = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    state.bounds = null;
    $me.disabled = false;
    if (map) map.flyTo({ center: [me.lon, me.lat], zoom: 11 });
    renderList();
  }, () => { $me.disabled = false; alertNote(T.no_location); }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 });
});
function alertNote(msg) { $count.textContent = msg; }

// ?mreza=<net> ?grad=<city> ?q=<text> ?f=fast|ac|free and #<station id>; applied before the map loads,
// so the list is right even when the map tiles cannot be loaded
function fromUrl() {
  const p = new URLSearchParams(location.search);
  const net = p.get('mreza'), g = p.get('grad'), q = p.get('q'), f = p.get('f');
  if (q) { $q.value = q; state.q = q; }
  const c = g && cfg.cities[g];
  if (c) city = { lat: c[0], lon: c[1] };
  if (net && $chips.querySelector('[data-f="net:' + net + '"]')) setChip('net:' + net);
  else if (net) { state.q = state.q || net.replace(/-/g, ' '); refresh(); }
  else if (f && $chips.querySelector('[data-f="' + f + '"]')) setChip(f);
  else refresh();
  const id = decodeURIComponent(location.hash.slice(1));
  if (id) { const s = ST.find(x => x.id === id); if (s) openCard(s, false); }
}

Promise.all([fetch(cfg.stations).then(r => r.json()), fetch(cfg.prices).then(r => r.json())]).then(([a, b]) => {
  ST = a.stations; NETS = b.nets;
  ST.forEach((s, i) => { s._i = i; });
  fromUrl();
  try { initMap(); } catch (e) { d.getElementById('map').classList.add('is-off'); }
}).catch(() => { $count.textContent = T.load_err; });
