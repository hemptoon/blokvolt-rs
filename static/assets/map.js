/* BlokVolt — map of public chargers (/mapa/). MapLibre GL + OpenFreeMap; stations from
   /assets/map/punjaci.json (OSM + OCM, ODbL) completed with /assets/map/mreze.json (the networks' own lists),
   prices from /assets/map/cene.json (ours), drivers' reports, ratings and photos from /api (Cloudflare D1). */
import * as maplibregl from '/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs';

const d = document;
const cfg = JSON.parse(d.getElementById('map-cfg').textContent);
const T = JSON.parse(d.getElementById('bv-i18n').textContent);
const LANG = (d.documentElement.lang || 'sr').slice(0, 2);
const LOC = LANG === 'sr' ? 'sr-Latn-RS' : LANG;
const fold = s => (s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
// notes from the price data and idle fees, translated on /en/ and /ru/ through the page's string table
const tr = s => (s && T['tx:' + s]) || s;
const fmt = (n, dg = 0) => Number(n).toLocaleString(LOC, { minimumFractionDigits: dg, maximumFractionDigits: dg });
const CONN = { ccs2: 'CCS2', ccs1: 'CCS1', chademo: 'CHAdeMO', type2: 'Type 2', type1: 'Type 1', tesla: 'Tesla', schuko: T.schuko, cee: 'CEE', other: T.other };
const svg = p => '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + p + '</svg>';
const ICON = {
  x: svg('<path d="M6 6l12 12M18 6 6 18"/>'),
  nav: svg('<path d="M3.5 11 20.5 3.5 13 20.5l-2-7.5-7.5-2Z"/>'),
  ext: svg('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>'),
  flag: svg('<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>'),
  ok: svg('<path d="M20 6 9 17l-5-5"/>'),
  warn: svg('<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4M12 17.5v.01"/>'),
  cam: svg('<path d="M4 8h3l2-3h6l2 3h3v11H4V8Z"/><circle cx="12" cy="13" r="3.5"/>')
};
const ST_LABEL = { ok: T.ci_ok, problem: T.ci_problem, broken: T.ci_broken, missing: T.ci_missing };

let ST = [], NETS = {}, CI = {}, map, me = null, sel = null, city = null, opened = 0;
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
// v.s: ok = on a network's own list or checked by hand; nep = only in the open databases; prob = recent reports that it does not work
function ver(s) { return (s.v && s.v.s) || 'nep'; }
// state motorway chargers carry the official status (s.ps): none working now = 'off'
function isOff(s) { return (!!s.ps && !s.ps.l.some(l => l[2] === 1)) || ver(s) === 'prob'; }
function kind(s) {
  if (isOff(s)) return 'off';
  if (isFree(s)) return 'free';
  return (s.dc || 0) > 0 ? 'dc' : 'ac';
}
function netOf(s) { return NETS[s.net] || null; }
function netName(s) { const n = netOf(s); return n ? n.name : (s.opn || ''); }
// a station without a name is called by its network, else by its street
function title(s) { return s.n || netName(s) || (s.a ? s.a.split(',')[0] : T.charger); }
function place(s) {
  const near = s.t ? T.near.replace('{t}', s.t) : '';
  if (!s.n && !netName(s) && s.a) return s.a.split(',').slice(1).join(',').trim() || near;
  return s.a || near;
}
function power(s) { return s.dc || s.ac || 0; }

function price(s) {
  let n = netOf(s);
  if (!n) return { kind: 'none', text: T.p_unknown };
  if (n.via && NETS[n.via]) n = NETS[n.via];
  if (n.free) return isFree(s) ? { kind: 'free', text: T.p_free, note: tr(n.free_note) || '', date: n.date || '' } : { kind: 'none', text: tr(n.note) || T.p_unknown };
  const hay = fold(s.n + ' ' + s.a);
  const cur = s.dc ? 'dc' : 'ac', P = power(s);
  const fits = t => t.cur === cur && (t.lo == null || (P >= t.lo - 5 && P <= t.hi + 5));
  const all = (n.tiers || []).concat(n.places || []);
  const exact = all.filter(t => t.where.some(w => hay.indexOf(w) >= 0));
  const ex = exact.filter(fits)[0] || (exact.length === 1 ? exact[0] : null);
  const receipt = (n.receipts || []).filter(r => r.where.some(w => hay.indexOf(w) >= 0));
  if (ex) return { kind: 'exact', t: ex, receipt, note: tr(n.note) };
  if (s.net === 'chargego' || n === NETS.chargego) {
    const tiers = (n.tiers || []).filter(t => t.cur === cur);
    const t = tiers.filter(fits)[0];
    if (t) return { kind: 'tier', t, receipt, note: tr(n.note) };
    if (cur === 'dc' && tiers.length && P) {
      const lower = tiers.filter(x => x.hi <= P).pop(), upper = tiers.filter(x => x.lo >= P)[0];
      if (lower && upper) return { kind: 'range', lo: lower, hi: upper, note: tr(n.note) };
    }
  }
  const same = (n.tiers || []).filter(t => t.cur === cur);
  if (same.length) return { kind: 'seen', list: same, note: tr(n.note) };
  return { kind: 'none', text: tr(n.note) || T.p_unknown };
}
function priceShort(s) {
  if (isOff(s)) return { t: ver(s) === 'prob' ? T.v_prob_t : T.off, cls: 'off' };
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
  if (f === 'ok' && ver(s) !== 'ok') return false;
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
  const ref = me || city;
  if (ref) rows = rows.map(s => (s._d = distKm(ref, s), s)).sort((a, b) => a._d - b._d);
  const txt = state.bounds ? T.in_view.replace('{n}', rows.length) : (rows.length === ST.length ? T.count_all : T.count).replace('{n}', rows.length).replace('{all}', ST.length);
  $count.innerHTML = esc(txt + (ref ? ' · ' + T.sorted_near : '')) + (state.bounds ? ' · <button class="lnkbtn" type="button" data-all>' + esc(T.all_serbia) + '</button>' : '');
  const lim = window.innerWidth <= 900 ? state.lim : Infinity, more = rows.length - lim;
  const html = rows.slice(0, lim).map(s => {
    const k = kind(s), ps = priceShort(s), pw = power(s);
    const sub = [netName(s), place(s)].filter(Boolean).join(' · ') + rating(s);
    const dist = ref ? '<span>' + fmt(s._d, s._d < 10 ? 1 : 0) + ' km</span>' : '';
    return '<button class="st' + (sel === s ? ' is-on' : '') + (ver(s) === 'nep' ? ' is-nep' : '') + '" data-id="' + esc(s.id) + '"><span class="dot ' + k + '">' + (pw ? Math.round(pw) : '') + '</span>' +
      '<span class="nm"><b>' + esc(title(s)) + badge(s) + '</b><span class="sb">' + esc(sub) + '</span></span><span class="pr ' + ps.cls + '">' + esc(ps.t) + dist + '</span></button>';
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
    if (t.extra) h += '<small>' + esc(tr(t.extra)) + '</small>';
    h += '<small>' + esc(p.kind === 'exact' ? T.p_exact : T.p_tier.replace('{c}', t.charger)) + ' · ' + esc(t.date) + (t.src ? ' · ' + esc(tr(t.src)) : '') + '</small>';
    (p.receipt || []).slice(0, 2).forEach(r => { h += '<small>' + esc(T.p_receipt.replace('{l}', tr(r.label)).replace('{k}', fmt(r.kwh))) + '</small>'; });
  } else if (p.kind === 'range') {
    h += '<div class="price">' + fmt(p.lo.v, 2) + '–' + fmt(p.hi.v, 2) + ' ' + esc(T.per_min) + '</div>';
    h += '<small>' + esc(T.p_range.replace('{a}', p.lo.charger).replace('{b}', p.hi.charger)) + ' · ' + esc(p.lo.date) + '</small>';
  } else if (p.kind === 'seen') {
    h += '<div>' + esc(T.p_seen) + '</div><ul>' + p.list.slice(0, 3).map(t => '<li><b>' + esc(t.label) + '</b> — ' + esc(t.charger) + (t.extra ? ', ' + esc(tr(t.extra)) : '') + '</li>').join('') + '</ul>';
    h += '<small>' + esc(p.note || '') + ' · ' + esc(p.list[0].date) + '</small>';
  } else {
    h += '<div>' + esc(p.text) + '</div>';
  }
  if (p.note && (p.kind === 'exact' || p.kind === 'tier' || p.kind === 'range')) h += '<small>' + esc(p.note) + '</small>';
  const idle = cfg.idle && cfg.idle[(netOf(s) && netOf(s).via) || s.net];
  if (idle && p.kind !== 'free' && p.kind !== 'none') h += '<small>' + esc(T.idle.replace('{x}', tr(idle))) + '</small>';
  return h + '</div>';
}
function statusHtml(s) {
  if (!s.ps) return '';
  const li = s.ps.l.map(l => '<li class="' + (l[2] === 1 ? 'ok' : 'no') + '"><i></i><span>' + esc([l[0], l[1]].filter(Boolean).join(' · ')) +
    ' · <b>' + esc(l[2] === 1 ? T.st_ok : T.st_off) + '</b>' + (l[3] && T['st_' + l[3]] ? ' (' + esc(T['st_' + l[3]]) + ')' : '') + '</span></li>').join('');
  return '<div class="cbox"><span>' + esc(T.status) + '</span><ul class="stl">' + li + '</ul><small>' + esc(T.st_src.replace('{d}', s.ps.d)) + '</small></div>';
}
const VBY = () => ({ cg: T.v_cg, rm: T.v_rm, te: T.v_te, ps: T.v_ps, g: T.v_g });
function verHtml(s) {
  const v = s.v || { s: 'nep', g: 'g_none' };
  if (v.s === 'ok') {
    const by = (v.by || []).map(b => VBY()[b]).filter(Boolean).join('; ');
    return '<p class="vf">' + ICON.ok + '<span><b>' + esc(T.v_ok) + '</b> ' + esc(by) + (v.d ? ' · ' + esc(v.d) : '') + '</span></p>';
  }
  const why = v.s === 'prob' ? T.v_prob : (v.g === 'test' ? T.v_test : v.g === 'g_old' ? T.v_old : T.v_none);
  return '<div class="vf-warn' + (v.s === 'prob' ? ' no' : '') + '"><b>' + ICON.warn + esc(v.s === 'prob' ? T.v_prob_t : T.v_nep) + '</b><p>' + esc(why) + '</p><small>' + esc(T.v_checked.replace('{d}', v.d || '')) + '</small></div>';
}
function openCard(s, fly) {
  sel = s;
  opened = Date.now();
  const n = netOf(s);
  const logo = n && n.logo ? '<span class="lg w' + (n.logo_dark ? ' dark' : '') + '"><img src="' + esc(n.logo) + '" alt=""></span>' : '<span class="lg w mono" aria-hidden="true">' + esc((netName(s) || '?').slice(0, 2).toUpperCase()) + '</span>';
  const netLine = netName(s) ? '<div class="net">' + logo + '<div><b>' + esc(netName(s)) + '</b><span>' + esc(n && n.page ? T.net_known : (s.opn && !n ? T.operator : T.net_unknown)) + '</span></div></div>' : '';
  const conns = s.c.length ? '<div class="cbox"><span>' + esc(T.conn) + '</span><ul>' + s.c.map(c => '<li>' + esc(connLine(c)) + '</li>').join('') + '</ul></div>' : '';
  const acc = s.acc === 'customers' ? '<div class="cbox"><span>' + esc(T.access) + '</span><div>' + esc(T.customers) + '</div></div>' : '';
  const nav = 'https://www.google.com/maps/dir/?api=1&destination=' + s.lat + ',' + s.lon;
  const site = n && n.page ? n.page : (n && n.site ? n.site : '');
  const fix = '/ispravka/?stanica=' + encodeURIComponent(s.id);
  const SRC = { ocm: 'Open Charge Map', osm: 'OpenStreetMap', ps: 'JP Putevi Srbije', cg: 'Charge&GO', rm: T.src_rm, te: 'Tesla' };
  const srcs = s.src.filter(x => x.u).map(x => '<a href="' + esc(x.u) + '" rel="noopener nofollow">' + esc(SRC[x.d] || x.d) + '</a>' + (x.upd ? ' (' + esc(x.upd) + ')' : '')).join(' · ');
  $card.innerHTML = '<div class="ccard" role="dialog" aria-label="' + esc(title(s)) + '"><button class="x" type="button" aria-label="' + esc(T.close) + '">' + ICON.x + '</button>' +
    '<h2>' + esc(title(s)) + '</h2><p class="addr">' + esc(place(s)) + '</p>' + verHtml(s) + netLine + priceHtml(s) + statusHtml(s) + conns + acc +
    '<div class="acts"><a class="btn dark full" href="' + nav + '" target="_blank" rel="noopener">' + ICON.nav + esc(T.navigate) + '</a>' +
    (site ? '<a class="btn" href="' + esc(site) + '"' + (site[0] === '/' ? '' : ' target="_blank" rel="noopener"') + '>' + ICON.ext + esc(n && n.page ? T.about_net : T.site) + '</a>' : '') +
    '<a class="btn' + (site ? '' : ' full') + '" href="' + fix + '">' + ICON.flag + esc(T.report) + '</a></div>' +
    rvHtml(s) +
    '<p class="src">' + esc(T.data) + ': ' + srcs + '</p></div>';
  $card.classList.add('is-open');
  $card.querySelector('.x').addEventListener('click', closeCard);
  rvBind(s);
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
  if (!c || !c.n) return '<p class="rv-empty">' + esc(T.rv_empty) + '</p>';
  return '<div class="rv-sum">' + (c.a ? '<b>' + fmt(c.a, 1) + '</b>' + starBar(c.a) + '<span>' + esc(T.ratings.replace('{n}', c.nr)) + '</span>' : '') +
    (c.s ? '<span class="rv-last ' + esc(c.s) + '">' + esc(T.last_report) + ': <b>' + esc(ST_LABEL[c.s] || c.s) + '</b>, ' + esc(ago(c.t)) + '</span>' : '') + '</div>';
}
function rvHtml(s) {
  if (!cfg.api) return '';
  const starsIn = [1, 2, 3, 4, 5].map(i => '<button type="button" data-r="' + i + '" aria-label="' + i + '/5" aria-pressed="false">★</button>').join('');
  return '<div class="cbox rv"><span>' + esc(T.rv_title) + '</span><div class="rv-top">' + rvSum(s) + '</div>' +
    '<p class="rv-q">' + esc(T.rv_q) + '</p><div class="rv-btns">' +
    ['ok', 'problem', 'broken', 'missing'].map(k => '<button type="button" class="chip" data-ci="' + k + '" aria-pressed="false">' + esc(ST_LABEL[k]) + '</button>').join('') + '</div>' +
    '<form class="rv-form" hidden novalidate><div class="rv-stars" role="group" aria-label="' + esc(T.rv_rate) + '"><span>' + esc(T.rv_rate) + '</span>' + starsIn + '</div>' +
    '<label class="sr-only" for="rv-c">' + esc(T.rv_comment) + '</label><textarea class="input" id="rv-c" maxlength="500" rows="3" placeholder="' + esc(T.rv_comment_ph) + '"></textarea>' +
    '<label class="sr-only" for="rv-n">' + esc(T.rv_name) + '</label><input class="input" id="rv-n" maxlength="40" autocomplete="nickname" placeholder="' + esc(T.rv_name) + '">' +
    '<input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">' +
    '<div class="rv-row"><button class="btn dark sm" type="submit">' + esc(T.rv_send) + '</button><button class="btn sm" type="button" data-cancel>' + esc(T.rv_cancel) + '</button></div>' +
    '<small>' + esc(T.rv_rules) + ' <a href="/pravila-objavljivanja/">' + esc(T.rv_rules_link) + '</a></small></form>' +
    '<p class="rv-msg" role="status" aria-live="polite"></p><div class="rv-list"></div>' +
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
  fetch(cfg.api + '/stanica/' + encodeURIComponent(s.id)).then(r => r.ok ? r.json() : null).then(j => {
    if (!j || !j.ok || sel !== s) return;
    CI[s.id] = { a: j.avg, nr: j.nr, n: j.n, s: j.items[0] && j.items[0].s, t: j.items[0] && j.items[0].at, f: j.photos.length };
    box.querySelector('.rv-top').innerHTML = rvSum(s);
    box.querySelector('.rv-list').innerHTML = rvItems(j);
    box.querySelector('.rv-thumbs').innerHTML = j.photos.map(p => '<button class="rv-th" type="button" data-full="' + cfg.api + '/foto/' + p.id + '.jpg"><img src="' + cfg.api + '/foto/' + p.id + '.jpg?v=t" alt="' + esc(p.cap || T.photo_alt) + '" loading="lazy" width="96" height="72"></button>').join('');
  }).catch(() => {});
}
function post(url, body, isForm) {
  return fetch(url, isForm ? { method: 'POST', body } : { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) })
    .then(r => r.json().catch(() => ({ ok: false })).then(j => (j.status = r.status, j)));
}
function errText(j) { return j.status === 429 ? T.rv_limit : T.rv_err; }
function rvBind(s) {
  const box = $card.querySelector('.rv');
  if (!box) return;
  const form = box.querySelector('.rv-form'), msg = box.querySelector('.rv-msg');
  let status = '', r = 0;
  box.querySelector('.rv-btns').addEventListener('click', e => {
    const b = e.target.closest('[data-ci]');
    if (!b) return;
    status = b.dataset.ci;
    box.querySelectorAll('[data-ci]').forEach(x => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
    form.hidden = false;
    msg.textContent = '';
    form.querySelector('textarea').focus({ preventScroll: true });
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
      hp: form.querySelector('.hp').value, t: Date.now() - opened, lang: LANG
    }).then(j => {
      btn.disabled = false;
      if (!j.ok) { msg.textContent = errText(j); return; }
      form.hidden = true;
      form.reset(); r = 0;
      msg.textContent = j.pending ? T.rv_thanks_pending : T.rv_thanks;
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
    shrink(f).then(p => {
      const fd = new FormData();
      fd.append('foto', p.big, 'foto.jpg');
      fd.append('thumb', p.th, 'thumb.jpg');
      fd.append('w', p.w); fd.append('h', p.h); fd.append('t', Date.now() - opened); fd.append('hp', '');
      return post(cfg.api + '/stanica/' + encodeURIComponent(s.id) + '/foto', fd, true);
    }).then(j => { note.textContent = j.ok ? T.photo_thanks : errText(j); }).catch(() => { note.textContent = T.photo_bad; });
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
  fetch(cfg.api + '/stanice').then(r => r.ok ? r.json() : null).then(j => {
    if (!j || !j.ok) return;
    CI = j.st || {};
    renderList();
  }).catch(() => {});
}

// ---------- map ----------
function feat(s) {
  const v = ver(s), p = Math.round(power(s)) || '';
  return { type: 'Feature', id: s._i, geometry: { type: 'Point', coordinates: [s.lon, s.lat] }, properties: { id: s.id, k: kind(s), v, p: v === 'nep' ? p + '?' : p } };
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
    const nep = ['==', ['get', 'v'], 'nep'];
    map.addLayer({ id: 'cl', type: 'circle', source: 'st', filter: ['has', 'point_count'],
      paint: { 'circle-color': '#0D111A', 'circle-radius': ['step', ['get', 'point_count'], 15, 10, 19, 30, 24], 'circle-stroke-width': 3, 'circle-stroke-color': 'rgba(217,244,91,.55)' } });
    map.addLayer({ id: 'cl-n', type: 'symbol', source: 'st', filter: ['has', 'point_count'],
      layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': font, 'text-size': 13, 'text-allow-overlap': true },
      paint: { 'text-color': '#FFFFFF' } });
    map.addLayer({ id: 'pt', type: 'circle', source: 'st', filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 6, 6, 12, 9, 16, 12],
        'circle-color': ['match', ['get', 'k'], 'dc', '#0D111A', 'free', '#D9F45B', 'off', '#E3E5E9', '#FFFFFF'],
        'circle-opacity': ['case', nep, 0.5, 1],
        'circle-stroke-width': 2.5,
        'circle-stroke-opacity': ['case', nep, 0.55, 1],
        'circle-stroke-color': ['match', ['get', 'k'], 'dc', '#D9F45B', 'off', '#8A909B', '#0D111A']
      } });
    map.addLayer({ id: 'pt-kw', type: 'symbol', source: 'st', filter: ['!', ['has', 'point_count']], minzoom: 12,
      layout: { 'text-field': ['to-string', ['get', 'p']], 'text-font': font, 'text-size': 10, 'text-allow-overlap': true },
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
d.addEventListener('keydown', e => { if (e.key === 'Escape' && sel && !d.querySelector('.lb')) closeCard(); });
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

// ?mreza=<net> ?grad=<city> ?q=<text> ?f=fast|ac|free|ok and #<station id>; applied before the map loads,
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

const getJson = u => fetch(u).then(r => { if (!r.ok) throw new Error(u); return r.json(); });
Promise.all([getJson(cfg.stations), getJson(cfg.nets).catch(() => ({ upd: {}, add: [] })), getJson(cfg.prices)]).then(([a, m, b]) => {
  ST = a.stations;
  // the networks' own lists: their connectors and names for the stations they confirm, and the stations the open data lacks
  ST.forEach(s => {
    const u = m.upd && m.upd[s.id];
    if (!u) return;
    Object.keys(u).forEach(k => { if (k !== 'src') s[k] = u[k]; });
    s.src = s.src.concat(u.src || []);
  });
  ST = ST.concat(m.add || []);
  ST.sort((x, y) => (!x.n - !y.n) || fold(x.n).localeCompare(fold(y.n)) || (x.id < y.id ? -1 : 1));
  NETS = b.nets;
  ST.forEach((s, i) => { s._i = i; });
  fromUrl();
  loadSummaries();
  try { initMap(); } catch (e) { d.getElementById('map').classList.add('is-off'); }
}).catch(() => { $count.textContent = T.load_err; });
