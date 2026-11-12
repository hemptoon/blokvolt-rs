/* BlokVolt — one search for the whole of blokvolt.com (SEARCH, 12.11.2026; scripts/world_search.py builds the index).
   Countries, every city with charging places, regions, networks and the pages of the site, in the 30 languages of the site,
   with typos. No requests while typing, nothing sent anywhere: the index of the page's language
   (/assets/world/search-<code>.json) loads once, on the first focus.
   - one spelling (the same fold as the build): case, diacritics (ü = u, and the index also has ue), Cyrillic and Greek
     in Latin letters, hyphens and dots = spaces, St/Sankt/Saint = st;
   - a word matches whole (3), as a beginning (2) or with typos (1: one for 4–7 letters, two from 8); every word of the
     query must match (connector words "charging stations in", "Ladestationen", "зарядки в" are dropped first);
   - ranking: a whole name > every word whole > beginnings > typos; then the kind (country > city > network > region >
     page) and the size (places, population), the visitor's region (time zone) and the countries of the page language;
   - "ionity munich", "tesla berlin", "fast chargers vienna": a network and/or a power filter with a place → the map with
     mreza / snaga and grad / zemlja; "prices germany", "how to pay france" → that page.
   UI: ARIA combobox (arrows, Enter, Esc, Tab), groups with an icon, country and count per row, "All results" →
   /search/?q=; recent searches (localStorage, try/catch) and the popular places of the visitor's region when the
   field is empty; "Did you mean", "Search on the map" and "All countries" when nothing is found; full screen on a phone.
   Works in the browser (window.BVWorldSearch, auto-mounts form.bvs / .wh-search / .wd-find / #bvs-map) and in node
   for scripts/qa/world_search_test.mjs (module.exports). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.BVWorldSearch = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---------------------------------------------------------------- one spelling (mirror of world_search.fold)
  var SPEC = { 'ß': 'ss', 'ø': 'o', 'æ': 'ae', 'œ': 'oe', 'đ': 'dj', 'ð': 'd', 'þ': 'th', 'ł': 'l', 'ı': 'i', 'ħ': 'h', 'ŀ': 'l', 'ŧ': 't' };
  var EXP = { 'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'å': 'aa', 'ø': 'oe', 'æ': 'ae' };
  var TR = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ґ': 'g', 'д': 'd', 'ђ': 'dj', 'е': 'e', 'є': 'je', 'ж': 'z', 'з': 'z', 'ѕ': 'dz',
    'и': 'i', 'і': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'љ': 'lj', 'м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz', 'ш': 's', 'щ': 'sc', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'ju', 'я': 'ja',
    'α': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm',
    'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'φ': 'f', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o'
  };
  var ABBR = { st: 'st', sankt: 'st', saint: 'st', ste: 'ste', sainte: 'ste' };
  function fold(s, exp) {
    s = String(s == null ? '' : s).toLowerCase().normalize('NFC');
    if (exp) s = s.replace(/[äöüåøæ]/g, function (c) { return EXP[c]; });
    s = s.replace(/[ßøæœđðþłıħŀŧ]/g, function (c) { return SPEC[c]; });
    s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    s = s.replace(/[Ͱ-ӿ]/g, function (c) { return TR[c] != null ? TR[c] : c; });
    return s.replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function words(s, exp) {
    var w = fold(s, exp);
    return w ? w.split(' ').filter(function (x) { return x.length <= 32; }).map(function (x) { return ABBR[x] || x; }) : [];
  }

  // ---------------------------------------------------------------- Damerau-Levenshtein (optimal string alignment)
  // dist(q, k, max, pre): distance of q to k, or with pre to the closest beginning of k (q is still being typed)
  function dist(a, b, max, pre) {
    var m = a.length, n = pre ? Math.min(b.length, m + max) : b.length;
    if (!pre && Math.abs(m - n) > max) return max + 1;
    if (pre && n < m - max) return max + 1;
    var p2 = null, p1 = new Array(n + 1), cur, i, j, best = max + 1;
    for (j = 0; j <= n; j++) p1[j] = j;
    for (i = 1; i <= m; i++) {
      cur = new Array(n + 1);
      cur[0] = i;
      var rowMin = i;
      for (j = 1; j <= n; j++) {
        var c = a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1;
        var v = Math.min(p1[j] + 1, cur[j - 1] + 1, p1[j - 1] + c);
        if (i > 1 && j > 1 && a.charCodeAt(i - 1) === b.charCodeAt(j - 2) && a.charCodeAt(i - 2) === b.charCodeAt(j - 1)) v = Math.min(v, p2[j - 2] + 1);
        cur[j] = v;
        if (v < rowMin) rowMin = v;
      }
      if (rowMin > max) return max + 1;
      p2 = p1; p1 = cur;
    }
    if (!pre) return p1[n];
    for (j = Math.max(0, m - max); j <= n; j++) if (p1[j] < best) best = p1[j];
    return best;
  }

  // ---------------------------------------------------------------- the index
  // part 1 (search-<code>.json): countries, cities with a page here, networks, regions, pages — dictionary ready-made;
  // part 2 (search-<code>-2.json, loaded right after): the long tail in columns, inverted here
  function load(doc) {
    var I = { doc: doc, items: [], parts: [], stop: new Set(doc.stop || []), mod: {}, mk: new Set(doc.mk || []), cname: {}, curl: {}, creg: {}, region: '' };
    ['fast', 'ultra', 'ac'].forEach(function (k) { (doc.mod && doc.mod[k] || []).forEach(function (w) { I.mod[w] = k; }); });
    doc.items.forEach(function (r) {
      while (r.length < 9) r.push(r.length === 7 ? 0 : null);
      if (r[0] === 'c') { I.cname[r[3]] = r[2]; if (r[5]) I.curl[r[3]] = r[5]; I.creg[r[3]] = r[8]; }
    });
    doc.items.forEach(function (r) { if (r[5] && r[5].charAt(0) === '+') r[5] = (I.curl[r[3]] || '/') + r[5].slice(1); I.items.push(r); });
    I.parts.push({ tok: doc.tok ? doc.tok.split('\n') : [], tp: doc.tp, nm: doc.nm ? doc.nm.split('\n') : [], np: doc.np, dec: true });
    return I;
  }
  function addTail(I, t) {
    var off = I.items.length, prev = 0, tok = new Map(), full = new Map();
    for (var j = 0; j < t.k.length; j++) {
      var k = t.k.charAt(j), id = t.id[j], cc = t.cc.substr(2 * j, 2);
      if (typeof id === 'number') { id += prev; prev = id; }
      var e = t.ex && t.ex[j], u = e && e[1];
      if (u && u.charAt(0) === '+') u = (I.curl[cc] || '/') + u.slice(1);
      I.items.push([k, id, t.lb[j], cc === '--' ? null : cc, e ? e[0] : null, u || null, t.w[j], e ? e[2] || 0 : 0, I.creg[cc] || null]);
      var kwj = t.kw[j], sep = kwj.indexOf('||'), xw = sep >= 0 ? kwj.slice(sep + 2).split(' ') : [];
      var names = (sep >= 0 ? kwj.slice(0, sep) : kwj).split('|'), x = off + j;
      for (var q = 0; q < xw.length; q++) {   // other words of the item (synonyms, its country): never a whole name
        var a0 = tok.get(xw[q]);
        if (!a0) tok.set(xw[q], [2 * x]); else if (a0[a0.length - 1] >> 1 !== x) a0.push(2 * x);
      }
      for (var n = 0; n < names.length; n++) {
        var ws = names[n].split(' '), one = ws.length === 1;
        for (var m = 0; m < ws.length; m++) {
          var v = 2 * x + (one ? 1 : 0), a = tok.get(ws[m]);
          if (!a) tok.set(ws[m], [v]); else if (a[a.length - 1] >> 1 !== x) a.push(v); else if (one) a[a.length - 1] = v;
        }
        if (!one && ws.length <= 5) { var f = ws.join('').slice(0, 48), b = full.get(f); if (!b) full.set(f, [x]); else if (b[b.length - 1] !== x) b.push(x); }
      }
    }
    var tk = Array.from(tok.keys()).sort(), fk = Array.from(full.keys()).sort();
    I.parts.push({ tok: tk, tp: tk.map(function (w) { return tok.get(w); }), nm: fk, np: fk.map(function (w) { return full.get(w); }), dec: false });
    I.bf = null;
    return I;
  }
  function postings(P, arr, i) {
    var d = arr[i];
    if (!P.dec) return d;
    var out = new Array(d.length), x = 0;
    for (var k = 0; k < d.length; k++) { x += d[k]; out[k] = x; }
    return out;
  }
  function lower(list, s) {   // first index with list[i] >= s
    var lo = 0, hi = list.length;
    while (lo < hi) { var mid = (lo + hi) >> 1; if (list[mid] < s) lo = mid + 1; else hi = mid; }
    return lo;
  }
  function buckets(P) {
    if (P.bf) return P.bf;
    var b = {};
    for (var i = 0; i < P.tok.length; i++) { var c = P.tok[i].charAt(0); (b[c] || (b[c] = [])).push(i); }
    return (P.bf = b);
  }
  // words of a part that a query word matches: Map word index → quality (3 whole, 2 beginning, 1 typo)
  function wordHits(P, w, last) {
    var out = new Map(), tok = P.tok, i = lower(tok, w);
    if (tok[i] === w) out.set(i, 3);
    if (w.length >= (last ? 1 : 3)) {
      for (var j = (tok[i] === w ? i + 1 : i); j < tok.length && tok[j].lastIndexOf(w, 0) === 0; j++) out.set(j, 2);
    }
    if (w.length >= 4 && !/^\d+$/.test(w)) {
      var max = w.length >= 8 ? 2 : 1, B = buckets(P), seen = {};
      [w.charAt(0), w.charAt(1)].forEach(function (c) {
        if (seen[c]) return;
        seen[c] = 1;
        var list = B[c] || [];
        for (var k = 0; k < list.length; k++) {
          var t = list[k];
          if (out.has(t)) continue;
          var s = tok[t];
          if (s.length < w.length - max || (!last && s.length > w.length + max)) continue;
          if (dist(w, s, max, false) <= max || (last && s.length > w.length && dist(w, s, max, true) <= max)) out.set(t, 1);
        }
      });
    }
    return out;
  }
  // items a query word matches: Map item → quality (4: the word is a whole name of the item)
  function itemHits(I, w, last) {
    var key = w + '|' + (last ? 1 : 0) + '|' + I.parts.length, hc = I.hc || (I.hc = new Map());
    if (hc.has(key)) return hc.get(key);   // the words already typed are not searched again on the next key
    if (hc.size > 300) hc.clear();
    var res = new Map();
    hc.set(key, res);
    // one letter: only the first file (countries, sections, the largest cities and networks) — the rest is noise there
    (w.length < 2 ? I.parts.slice(0, 1) : I.parts).forEach(function (P) {
      wordHits(P, w, last).forEach(function (q, t) {
        var ids = postings(P, P.tp, t);
        for (var k = 0; k < ids.length; k++) {
          var id = ids[k] >> 1, qq = q === 3 && (ids[k] & 1) ? 4 : q, o = res.get(id) || 0;
          if (qq > o) res.set(id, qq);
        }
      });
    });
    return res;
  }
  function fullHits(I, key, pre) {
    var res = new Map();
    I.parts.forEach(function (P) {
      var i = lower(P.nm, key);
      if (P.nm[i] === key) postings(P, P.np, i).forEach(function (x) { res.set(x, 4); });
      if (pre && key.length >= 4) {
        for (var j = (P.nm[i] === key ? i + 1 : i), n = 0; j < P.nm.length && P.nm[j].lastIndexOf(key, 0) === 0 && n < 400; j++, n++) {
          postings(P, P.np, j).forEach(function (x) { if (!res.has(x)) res.set(x, 2); });
        }
      }
    });
    return res;
  }

  function labelWords(I, id) {
    var c = I.lw || (I.lw = {});
    return c[id] || (c[id] = words(I.items[id][2]));
  }
  var KW = { c: 60, t: 0, n: 0, r: 0, p: 0, q: 0 };
  function boost(I, r) {
    var b = 0;
    if (r[3] && I.mk.has(r[3])) b += 4;
    if (I.region && r[8] === I.region) b += 5;
    return b;
  }
  function parse(I, q) {
    var raw = words(q), toks = raw.filter(function (w) { return !I.stop.has(w); });
    var allStop = !toks.length;
    if (allStop) toks = raw.slice();
    var mods = {}, rest = toks.filter(function (w) { if (I.mod[w]) { mods[I.mod[w]] = 1; return false; } return true; });
    if (rest.length) toks = rest; else mods = {};
    return { raw: raw, toks: toks, mods: mods, allStop: allStop };
  }
  // items matching every word: Map id → {tier, sum}
  function match(I, toks, full, kinds, nx) {
    var acc = null;
    for (var k = 0; k < toks.length; k++) {
      var h = itemHits(I, toks[k], k === toks.length - 1), next = new Map();
      var multi = toks.length > 1, lastW = k === toks.length - 1;
      // the last word may still be growing: whole word and beginning are one tier (the sum keeps whole words first)
      var tierOf = function (q) { return lastW && q === 2 ? 3 : q; };
      var w3 = lastW && toks[k].length <= 3;   // three letters: a whole word or a beginning weigh the same (new = Newark = New Haven)
      if (acc === null) h.forEach(function (q, id) { if (multi && q > 3) q = 3; next.set(id, { tier: tierOf(q), sum: w3 && q === 2 ? 3 : q }); });
      else acc.forEach(function (v, id) { var q = h.get(id); if (q > 3) q = 3; if (q) next.set(id, { tier: Math.min(v.tier, tierOf(q)), sum: v.sum + q }); });
      acc = next;
      if (!acc.size) break;
    }
    acc = acc || new Map();
    if (full) {
      fullHits(I, full, toks.length === 1).forEach(function (q, id) {
        var v = acc.get(id);
        if (q === 4) acc.set(id, { tier: 4, sum: (v ? v.sum : 3 * toks.length) + 1 });
        else if (!v) acc.set(id, { tier: 2, sum: 2 });
      });
    }
    var out = [], short = toks.length === 1 && toks[0].length <= 3;
    acc.forEach(function (v, id) {
      var r = I.items[id];
      if (kinds && kinds.indexOf(r[0]) < 0) return;
      if (r[7] && (nx || toks.length) < 2) return;   // a network page of a country, a price page of a country: with the country only
      // "new": the network NEW is a whole name, but three letters are rather the start of New York, Newark, New Zealand
      var tier = short && v.tier > 3 && r[0] === 'n' ? 3 : v.tier, sc = tier * 1000 + v.sum * 10 + r[6] + boost(I, r);
      if (r[0] === 'p' && v.sum >= 3 * toks.length && toks.every(function (t) { return t.length >= 3; })) sc += r[7] ? 20 : 80;   // a section named by its own word ("cost", "карта"); its country pages less
      out.push({ id: id, r: r, tier: tier, score: sc, v4: v.tier === 4 });
    });
    out.sort(function (a, b) { return b.score - a.score; });
    // the shown name: only the best 80 are looked at (its words cost a fold each)
    var last = toks[toks.length - 1], head = out.slice(0, 80);
    head.forEach(function (x) {
      var lw = labelWords(I, x.id);
      if (x.v4 && x.r[0] !== 'n' && lw.join('') === full) x.score += 40;   // the name of the result as shown here (Niš before Nice/"Nis")
      else if (lw.some(function (w) { return w.lastIndexOf(last, 0) === 0; })) x.score += 15;   // the shown name, not an old or other one (new → Newark before Tallahassee "Newtown")
    });
    head.sort(function (a, b) { return b.score - a.score || (a.r[2] < b.r[2] ? -1 : 1); });
    return head.concat(out.slice(80));
  }
  function mapUrl(I, p) {
    var q = [];
    if (p.mreza) q.push('mreza=' + p.mreza);
    if (p.snaga) q.push('snaga=' + p.snaga);
    if (p.zemlja) q.push('zemlja=' + p.zemlja);
    if (p.grad) q.push('grad=' + p.grad);
    return I.doc.map + (q.length ? '?' + q.join('&') : '') + (p.hash || '');
  }
  // the address of a result: its page, else the map on it
  function href(I, r) {
    if (r[5] && r[5].charAt(0) !== '#') return r[5];
    if (r[0] === 'c') return mapUrl(I, { zemlja: r[1] });
    if (r[0] === 't') return mapUrl(I, { grad: r[1] });
    if (r[0] === 'n') return mapUrl(I, { mreza: String(r[1]).split('@')[0] });
    if (r[0] === 'r') return mapUrl(I, { hash: r[5] });
    return r[5] || I.doc.map;
  }
  // the address of a result on the map itself (the search of /map/ moves the map instead of opening a page)
  function mapHref(I, r) {
    if (r[0] === 'c') return mapUrl(I, { zemlja: r[1] });
    if (r[0] === 't') return mapUrl(I, { grad: r[1] });
    if (r[0] === 'n') return mapUrl(I, { mreza: String(r[1]).split('@')[0] });
    if (r[0] === 'r') return mapUrl(I, { hash: r[5] });
    return null;
  }
  var SNAGA = { fast: 'dc,hpc', ultra: 'hpc', ac: 'ac' };
  // "tesla berlin", "fast chargers vienna", "ionity munich": a network and/or a power filter + a place → the map
  function compound(I, P) {
    var toks = P.toks, best = null, modKey = P.mods.ultra ? 'ultra' : P.mods.fast ? 'fast' : P.mods.ac ? 'ac' : null;
    var good = function (x, ws) { return x && ws.join('').length >= 3 && (x.tier >= 2 || ws.join('').length >= 7) ? x : null; };
    if (P.allStop) return null;
    var place = function (ws) { return good(match(I, ws, ws.join(''), ['c', 't', 'r'])[0], ws); };
    var net = function (ws) { return good(match(I, ws, ws.join(''), ['n']).filter(function (x) { return !x.r[7]; })[0], ws); };
    if (modKey && toks.length) {
      var p0 = place(toks);
      if (p0) best = { net: null, place: p0, score: p0.score };
      else {
        var n0 = net(toks);
        if (n0) best = { net: n0, place: null, score: n0.score };
      }
    }
    for (var s = 1; s < toks.length; s++) {
      var A = toks.slice(0, s), B = toks.slice(s);
      [[A, B], [B, A]].forEach(function (pair) {
        var n = net(pair[0]), p = n && place(pair[1]);
        if (n && p && Math.max(n.tier, p.tier) >= 3) {   // one part may have a typo, not both
          var sc = Math.min(n.tier, p.tier) * 1000 + n.score % 1000 + p.score % 1000;
          if (!best || sc > best.score) best = { net: n, place: p, score: sc };
        }
      });
    }
    if (!best) return null;
    var T = I.doc.T, parts = [], o = {};
    if (best.net) { parts.push(best.net.r[2]); o.mreza = String(best.net.r[1]).split('@')[0]; }
    if (modKey) { parts.push(T[modKey] || modKey); o.snaga = SNAGA[modKey]; }
    if (best.place) {
      var r = best.place.r;
      parts.push(r[2]);
      if (r[0] === 'c') o.zemlja = r[1]; else if (r[0] === 't') o.grad = r[1]; else o.hash = r[5];
    }
    var tier = Math.min(best.net ? best.net.tier : 4, best.place ? best.place.tier : 4);
    return { id: -1, r: ['q', o.mreza || '', parts.join(' · '), best.place ? best.place.r[3] : null, null, mapUrl(I, o), 0, 0],
      tier: tier, score: tier * 1000 + 990, url: mapUrl(I, o), parts: [best.place, best.net].filter(Boolean) };
  }
  function search(I, q, opt) {
    opt = opt || {};
    var P = parse(I, q);
    if (!P.toks.length || P.raw.join('').length < 1) return { list: [], P: P };
    var full = P.raw.join(''), list = match(I, P.toks, full, opt.kinds);
    if (P.toks.join('') !== full) {   // "le mans", "den haag", "los ang", "shell recharge": every word of the query, little ones too
      var seen = new Map();
      list.forEach(function (x) { seen.set(x.id, x); });
      match(I, P.raw, full, opt.kinds, P.toks.length).forEach(function (x) {
        var y = seen.get(x.id);
        if (y) { if (x.score + 300 > y.score) { y.score = x.score + 300; y.tier = Math.max(y.tier, x.tier); } }
        else { x.score += 300; list.push(x); }
      });
      list.sort(function (a, b) { return b.score - a.score; });
    }
    var mods = Object.keys(P.mods).length;
    if (!opt.kinds && (P.toks.length > 1 || mods)) {
      var top = list[0], c = compound(I, P);
      if (c && (mods || !top || c.tier > top.tier)) list.unshift(c);   // nothing answers every word by itself
      else if (c) list.splice(Math.min(3, list.length), 0, c);
      if (c) c.parts.forEach(function (x, k) {   // "tesla berlin": Berlin and Tesla themselves right after the map
        if (!list.some(function (y) { return y.id === x.id; })) list.splice(list.indexOf(c) + 1 + k, 0, x);
      });
    }
    list.forEach(function (x) { if (!x.url) x.url = href(I, x.r); });
    return { list: list, P: P };
  }
  // "Did you mean": every word that matches nothing → the closest word of the dictionary (the one of the largest items)
  function suggest(I, q) {
    var P = parse(I, q), out = [], changed = false;
    for (var k = 0; k < P.toks.length; k++) {
      var w = P.toks[k], best = null, bd = 9, bw = -1;
      if (itemHits(I, w, k === P.toks.length - 1).size) { out.push(w); continue; }
      var max = w.length >= 7 ? 3 : 2;
      I.parts.forEach(function (P) {
        for (var t = 0; t < P.tok.length; t++) {
          var s = P.tok[t];
          if (Math.abs(s.length - w.length) > max) continue;
          var dd = dist(w, s, max, false);
          if (dd > max || dd > bd) continue;
          var ids = postings(P, P.tp, t), wt = 0;
          for (var j = 0; j < ids.length && j < 50; j++) wt = Math.max(wt, I.items[ids[j] >> 1][6]);
          if (dd < bd || wt > bw) { best = s; bd = dd; bw = wt; }
        }
      });
      if (!best) return null;
      out.push(best);
      changed = true;
    }
    return changed ? out.join(' ') : null;
  }

  var API = { fold: fold, words: words, dist: dist, load: load, addTail: addTail, search: search, suggest: suggest, href: href, mapHref: mapHref };
  if (typeof document === 'undefined') return API;

  // ================================================================ the interface
  var d = document, H = d.documentElement;
  var LANG = (H.getAttribute('lang') || 'en').split('-')[0];
  var JS = d.currentScript && d.currentScript.src;
  var BASE = JS ? JS.replace(/world-search\.js.*$/, '') : '/assets/world/';
  var VER = JS && /[?&]v=([\w]+)/.test(JS) ? RegExp.$1 : '';
  var IDX = null, LOADING = null;
  function idxUrl() { return BASE + 'search-' + LANG + '.json' + (VER ? '?v=' + VER : ''); }
  var TAIL = [];   // renders waiting for the second file
  // search-<code>-0.json (≈ 2 KB): the strings and the popular places, so the list opens at once on the first focus
  var SMALL = null, SMALLING = null;
  function getSmall() {
    if (!SMALLING) {
      SMALLING = fetch(BASE + 'search-' + LANG + '-0.json' + (VER ? '?v=' + VER : '')).then(function (r) { return r.ok ? r.json() : null; })
        .then(function (doc) { if (doc) SMALL = { doc: doc, cname: doc.cn || {}, items: [], region: visitorRegion(doc.tz), curl: {} }; return SMALL; })
        .catch(function () { return null; });
    }
    return SMALLING;
  }
  function getIndex(url) {
    if (!LOADING) {
      var u = url || idxUrl();
      LOADING = fetch(u).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (doc) {
        IDX = load(doc);
        IDX.region = visitorRegion(doc.tz);
        IDX.pending = [].concat(doc.tail || []).length;
        // the long tail (cities with no page here, small networks): one file after the other, each added when idle
        (typeof doc.tail === 'string' ? [doc.tail] : doc.tail || []).reduce(function (p, name) {
          return p.then(function () {
            return fetch(u.replace(/[^/?]+(\?.*)?$/, name + (VER ? '?v=' + VER : ''))).then(function (r) { return r.ok ? r.json() : null; }).then(function (t) {
              if (!t) return;
              return new Promise(function (res) {
                var go = function () { addTail(IDX, t); IDX.pending--; TAIL.forEach(function (f) { f(); }); res(); };
                if (window.requestIdleCallback) requestIdleCallback(go, { timeout: 400 }); else setTimeout(go, 0);
              });
            });
          });
        }, Promise.resolve()).catch(function () { /* the first file still answers */ });
        return IDX;
      });
      LOADING.catch(function () { LOADING = null; });
    }
    return LOADING;
  }
  function css() {
    if (d.getElementById('bvs-css')) return;
    var l = d.createElement('link');
    l.id = 'bvs-css'; l.rel = 'stylesheet'; l.href = BASE + 'world-search.css' + (VER ? '?v=' + VER : '');
    d.head.appendChild(l);
  }
  function visitorRegion(tz) {
    var z = '';
    try { z = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { /* old browser */ }
    for (var k in tz || {}) { try { if (new RegExp(tz[k]).test(z)) return k; } catch (e) { /* bad pattern */ } }
    return 'eu';
  }
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var ICON = {
    c: '<path d="M4 21V4m0 0h11l-1.5 4L15 12H4"/>',
    t: '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    n: '<path d="M13 2 5 13h6l-1 9 8-11h-6z"/>',
    r: '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"/><path d="M9 4v14M15 6v14"/>',
    p: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    q: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4-4M11 8v6M8 11h6"/>',
    h: '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>'
  };
  var icon = function (k) { return '<svg class="bvs-k" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + ICON[k] + '</svg>'; };
  var nf = (function () { try { return new Intl.NumberFormat(H.lang || 'en'); } catch (e) { return new Intl.NumberFormat('en'); } })();
  var RECENT = 'bv_search_recent';
  function recent() { try { return (JSON.parse(localStorage.getItem(RECENT) || '{}')[LANG] || []).slice(0, 5); } catch (e) { return []; } }
  function remember(x) {
    try {
      var all = JSON.parse(localStorage.getItem(RECENT) || '{}'), l = (all[LANG] || []).filter(function (y) { return y.u !== x.u; });
      l.unshift(x); all[LANG] = l.slice(0, 5);
      localStorage.setItem(RECENT, JSON.stringify(all));
    } catch (e) { /* private mode: no recent searches */ }
  }
  var GROUP = ['c', 't', 'n', 'r', 'p'];
  var uid = 0;

  function row(I, x, sel) {
    var r = x.r, T = I.doc.T, k = r[0], sub = [];
    if (k === 't' || k === 'r' || (k === 'n' && r[3]) || (k === 'p' && r[3]) || (k === 'q' && r[3])) {
      if (r[3] && I.cname[r[3]] && (k !== 'p' && k !== 'n')) sub.push(esc(I.cname[r[3]]));
    }
    var num = r[4] ? '<span class="bvs-n" title="' + esc(T.places) + '">' + nf.format(r[4]) + '</span>' : '';
    var tag = (!r[5] || r[5].charAt(0) === '#') && k !== 'p' ? '<span class="bvs-tag">' + esc(T.map_tag) + '</span>' : '';
    return '<li role="option" id="' + x.oid + '" class="bvs-o" aria-selected="' + (sel ? 'true' : 'false') + '" data-i="' + x.n + '">' +
      '<a href="' + esc(x.url) + '" tabindex="-1">' + icon(k) + '<span class="bvs-t"><span class="bvs-l" translate="no">' + esc(r[2]) + '</span>' +
      (sub.length ? '<span class="bvs-s">' + sub.join(' · ') + '</span>' : '') + '</span>' + num + tag +
      '<span class="sr-only">, ' + esc(T['k_' + (k === 'q' ? 'n' : k)] || '') + '</span></a></li>';
  }

  function mount(form, opt) {
    opt = opt || {};
    var input = form.querySelector('input[type=search],input[name=q],input');
    if (!input || form.__bvs) return null;
    form.__bvs = true;
    css();
    var id = 'bvs' + (++uid), lb = d.createElement('div'), live = d.createElement('div');
    form.classList.add('bvs-on');
    var pane = d.createElement('div');
    pane.className = 'bvs-pane';
    pane.hidden = true;
    lb.className = 'bvs-list';
    lb.id = id + '-l';
    pane.appendChild(lb);
    live.className = 'sr-only';
    live.setAttribute('role', 'status');
    live.setAttribute('aria-live', 'polite');
    pane.className += ' bvs-float';
    (opt.inline ? form : d.body).appendChild(pane);
    form.appendChild(live);
    var box = input.closest('.wh-sbox, .bvs-box, .wd-sbox') || input;
    function place() {
      if (pane.hidden || !pane.classList.contains('bvs-float')) return;
      var r = box.getBoundingClientRect(), w = Math.min(Math.max(r.width, 300), innerWidth - 16);
      pane.style.left = Math.max(8, Math.min(r.left, innerWidth - w - 8)) + 'px';
      pane.style.top = (r.bottom + 6) + 'px';
      pane.style.width = w + 'px';
      pane.style.maxHeight = Math.max(200, Math.min(560, innerHeight - r.bottom - 14)) + 'px';
    }
    addEventListener('scroll', place, { passive: true, capture: true });
    addEventListener('resize', place, { passive: true });
    var old = form.querySelector('.wh-res, .wd-res-x');
    if (old) old.hidden = true;
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-controls', lb.id);
    input.setAttribute('autocomplete', 'off');
    var opts = [], sel = -1, lastQ = null, mob = function () { return matchMedia('(max-width: 640px)').matches && !opt.inline; };
    var sheet = null;   // phone: the search opens full screen in a sheet of its own (above every layer of the page)
    function setOpen(on) {
      pane.hidden = !on;
      form.classList.toggle('bvs-open', on);
      input.setAttribute('aria-expanded', String(on));
      place();
      if (!on) { input.removeAttribute('aria-activedescendant'); sel = -1; }
    }
    function openSheet() {
      if (!sheet) {
        var T = (IDX || SMALL || { doc: { T: {} } }).doc.T;
        var sh = d.createElement('div');
        sh.className = 'bvs-sheet';
        sh.hidden = true;
        sh.setAttribute('role', 'dialog');
        sh.setAttribute('aria-modal', 'true');
        sh.setAttribute('aria-label', T.label || input.getAttribute('placeholder') || '');
        sh.innerHTML = '<form class="bvs-sf" role="search" action=""><button type="button" class="bvs-back" aria-label="' + esc(T.close || 'Close') +
          '"><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M15 5l-7 7 7 7"/></svg></button>' +
          '<input type="search" autocomplete="off" spellcheck="false" maxlength="80" enterkeyhint="search" placeholder="' + esc(input.getAttribute('placeholder') || T.ph || '') + '"></form>';
        d.body.appendChild(sh);
        var api2 = mount(sh.querySelector('form'), { inline: true, sheet: true, countries: opt.countries, limit: opt.limit, onPick: opt.onPick, idx: opt.idx,
          onClose: function () { closeSheet(); } });
        sheet = { el: sh, api: api2 };
        sh.querySelector('.bvs-back').addEventListener('click', closeSheet);
        sheet.api.input.addEventListener('input', function () { input.value = sheet.api.input.value; });
      }
      sheet.el.hidden = false;
      H.classList.add('bvs-lock');
      sheet.api.input.value = input.value;
      sheet.api.input.focus();
      sheet.api.go();
    }
    function closeSheet() {
      if (!sheet || sheet.el.hidden) return;
      sheet.el.hidden = true;
      H.classList.remove('bvs-lock');
      setOpen(false);
    }
    function render() {
      var I = IDX || SMALL, q = input.value.trim();
      if (!I || (q && !IDX) || (!q && opt.countries && !IDX)) return;
      var T = I.doc.T, html = '', n = 0;
      opts = [];
      lastQ = q;
      if (!q) {
        var rec = opt.countries ? [] : recent(), pop = (I.doc.pop[I.region] || I.doc.pop.eu || []);
        if (!IDX) pop = pop.map(function (r) { return { r: r }; });
        if (rec.length) {
          html += '<div class="bvs-g" role="presentation">' + esc(T.recent) + '</div>';
          rec.forEach(function (x) { var o = { r: [x.k || 'h', '', x.l, x.c || null, null, x.u, 0, 0], url: x.u, n: n++, oid: id + '-o' + opts.length }; opts.push(o); });
        }
        html += '<ul role="presentation">' + opts.map(function (o) { return row(I, o, false); }).join('') + '</ul>';
        if (opt.countries) pop = I.items.map(function (r, i) { return i; }).filter(function (i) { return I.items[i][0] === 'c' && I.items[i][8] === I.region; })
          .sort(function (a, b) { return (I.items[b][4] || 0) - (I.items[a][4] || 0); }).slice(0, 8);
        if (pop.length) {
          var po = pop.map(function (i) { var r = typeof i === 'number' ? I.items[i] : i.r; return { r: r, url: IDX ? href(I, r) : r[5] || mapUrl(I, r[0] === 'c' ? { zemlja: r[1] } : { grad: r[1] }), n: n++, oid: '' }; });
          po.forEach(function (o, k) { o.oid = id + '-o' + (opts.length + k); });
          opts = opts.concat(po);
          html += '<div class="bvs-g" role="presentation">' + esc(T.popular) + '</div><ul role="presentation">' + po.map(function (o) { return row(I, o, false); }).join('') + '</ul>';
        }
        lb.setAttribute('role', 'listbox');
        lb.setAttribute('aria-label', T.label);
        lb.innerHTML = html;
        live.textContent = '';
        setOpen(opts.length > 0);
        return;
      }
      var res = search(I, q, { kinds: opt.countries ? ['c'] : null }), list = res.list.slice(0, opt.limit || 9);
      list.forEach(function (x, k) { x.n = k; x.oid = id + '-o' + k; });
      opts = list.slice();
      if (!list.length && I.pending > 0) { setOpen(false); return; }   // the long tail is still on its way
      if (!list.length) {
        var dym = suggest(I, q);
        html = '<p class="bvs-none">' + esc(T.none.replace('{q}', q)) + '</p>';
        if (dym) html += '<p class="bvs-dym"><button type="button" class="bvs-dymb" data-q="' + esc(dym) + '">' + esc(T.dym).replace('{q}', '<b>' + esc(dym) + '</b>') + '</button></p>';
        html += '<p class="bvs-foot"><a href="' + esc(I.doc.map) + '">' + esc(T.on_map) + '</a><a href="' + esc(I.doc.hub) + '">' + esc(T.countries) + '</a></p>';
        lb.removeAttribute('role');
        lb.innerHTML = html;
        live.textContent = T.n_res.replace('{n}', '0');
        var b = lb.querySelector('.bvs-dymb');
        if (b) b.addEventListener('click', function () { input.value = b.dataset.q; render(); input.focus(); });
        setOpen(true);
        return;
      }
      // groups in the order of their best result, so the first row is the best match
      var order = [];
      list.forEach(function (x) { var g = x.r[0] === 'q' ? 'q' : x.r[0]; if (order.indexOf(g) < 0) order.push(g); });
      opts = [];
      order.forEach(function (g) {
        var xs = list.filter(function (x) { return (x.r[0] === 'q' ? 'q' : x.r[0]) === g; });
        xs.forEach(function (x) { x.n = opts.length; x.oid = id + '-o' + opts.length; opts.push(x); });
        html += '<div class="bvs-g" role="presentation" id="' + id + '-g' + g + '">' + esc(T['g_' + g]) + '</div><ul role="group" aria-labelledby="' + id + '-g' + g + '">' +
          xs.map(function (x) { return row(I, x, false); }).join('') + '</ul>';
      });
      if (!opt.countries) html += '<a class="bvs-more" href="' + esc(I.doc.all) + '?q=' + encodeURIComponent(q) + '">' + esc(T.all) + ' →</a>';
      lb.setAttribute('role', 'listbox');
      lb.setAttribute('aria-label', T.label);
      lb.innerHTML = html;
      live.textContent = T.n_res.replace('{n}', String(res.list.length));
      setOpen(true);
    }
    function mark() {
      lb.querySelectorAll('[role=option]').forEach(function (o, k) { o.setAttribute('aria-selected', String(k === sel)); });
      if (sel >= 0 && opts[sel]) {
        input.setAttribute('aria-activedescendant', opts[sel].oid);
        var el = d.getElementById(opts[sel].oid);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
      } else input.removeAttribute('aria-activedescendant');
    }
    function pick(o, ev) {
      if (!o) return;
      var r = o.r;
      if (r[0] !== 'h') remember({ l: r[2], u: o.url, k: r[0], c: r[3] });
      if (opt.onPick && opt.onPick(o, IDX) === true) { if (ev) ev.preventDefault(); setOpen(false); if (opt.onClose) opt.onClose(); input.blur(); return; }
      location.href = o.url;
    }
    function go() {
      if (IDX) return render();
      getSmall().then(function () { if (!IDX) render(); });
      getIndex(opt.idx).then(render).catch(function () {});
    }
    var warm = function () { getSmall(); getIndex(opt.idx).catch(function () {}); };   // the pointer is on its way to the field
    form.addEventListener('pointerenter', warm, { once: true });
    form.addEventListener('touchstart', warm, { once: true, passive: true });
    TAIL.push(function () { if (!pane.hidden || d.activeElement === input) render(); });
    input.addEventListener('focus', function () {
      if (mob()) { setOpen(false); openSheet(); return; }
      go();
    });
    input.addEventListener('input', function () { sel = -1; go(); });
    input.addEventListener('keydown', function (e) {
      var n = opts.length;
      if (e.key === 'ArrowDown') { if (pane.hidden) go(); else if (n) { sel = (sel + 1) % n; mark(); } e.preventDefault(); }
      else if (e.key === 'ArrowUp') { if (n) { sel = (sel - 1 + n) % n; mark(); } e.preventDefault(); }
      else if (e.key === 'Escape') {
        if (opt.sheet && opt.onClose) { opt.onClose(); e.preventDefault(); }
        else if (!pane.hidden) { setOpen(false); e.preventDefault(); } else if (input.value) { input.value = ''; }
      }
      else if (e.key === 'Tab') setOpen(false);
      else if (e.key === 'Enter') {
        e.preventDefault();
        if (sel >= 0 && opts[sel]) return pick(opts[sel], e);
        if (opt.page) return submit();
        var q = input.value.trim();
        if (!q) return;
        (IDX ? Promise.resolve(IDX) : getIndex(opt.idx)).then(function () { render(); if (opts[0] && lastQ === q) pick(opts[0], e); else if (q) location.href = IDX.doc.all + '?q=' + encodeURIComponent(q); });
      }
    });
    function submit() { if (opt.page) opt.page(input.value.trim()); }
    form.addEventListener('submit', function (e) { e.preventDefault(); if (opt.page) return submit(); var q = input.value.trim(); if (q) location.href = (IDX ? IDX.doc.all : (opt.all || '/search/')) + '?q=' + encodeURIComponent(q); });
    lb.addEventListener('mousedown', function (e) { e.preventDefault(); });   // keep the focus in the field
    lb.addEventListener('click', function (e) {
      var li = e.target.closest('[role=option]');
      if (!li) return;
      var o = opts[+li.dataset.i];
      if (o && opt.onPick) { e.preventDefault(); pick(o, e); }
      else if (o && o.r[0] !== 'h') remember({ l: o.r[2], u: o.url, k: o.r[0], c: o.r[3] });
    });
    d.addEventListener('click', function (e) { if (!form.contains(e.target) && !pane.contains(e.target)) setOpen(false); });
    input.addEventListener('blur', function () { setTimeout(function () { if (!opt.sheet && !form.contains(d.activeElement) && !pane.contains(d.activeElement)) setOpen(false); }, 150); });
    if (opt.autofocus) input.focus();
    return { render: render, input: input, go: go };
  }

  // the page of all results (/search/?q=)
  function page(form) {
    var out = d.getElementById('bvs-all'), hint = d.getElementById('bvs-hint'), input = form.querySelector('input');
    var q0 = new URLSearchParams(location.search).get('q') || '';
    input.value = q0.slice(0, 80);
    var draw = function (q) {
      if (!IDX) return;
      var I = IDX, T = I.doc.T;
      if (history.replaceState) history.replaceState(null, '', location.pathname + (q ? '?q=' + encodeURIComponent(q) : ''));
      if (!q) { out.innerHTML = ''; hint.hidden = false; return; }
      hint.hidden = true;
      var res = search(I, q), html = '';
      if (!res.list.length && I.pending > 0) return;
      if (!res.list.length) {
        var dym = suggest(I, q);
        html = '<p class="bvs-none">' + esc(T.none.replace('{q}', q)) + '</p>' + (dym ? '<p class="bvs-dym"><a href="?q=' + encodeURIComponent(dym) + '">' + esc(T.dym).replace('{q}', '<b>' + esc(dym) + '</b>') + '</a></p>' : '');
      } else {
        html += '<p class="bvs-cnt">' + esc(T.n_res.replace('{n}', String(res.list.length))) + '</p>';
        var order = [];
        res.list.forEach(function (x) { var g = x.r[0]; if (order.indexOf(g) < 0) order.push(g); });
        order.forEach(function (g) {
          var xs = res.list.filter(function (x) { return x.r[0] === g; }).slice(0, 60);
          html += '<section class="bvs-sec"><h2>' + esc(T['g_' + g]) + '</h2><ul class="bvs-ul">' + xs.map(function (x, k) { x.n = k; x.oid = 'bvsa-' + g + k; return row(I, x, false).replace('role="option"', '').replace('tabindex="-1"', ''); }).join('') + '</ul></section>';
        });
      }
      html += '<p class="bvs-foot"><a href="' + esc(I.doc.map) + '">' + esc(T.on_map) + '</a><a href="' + esc(I.doc.hub) + '">' + esc(T.countries) + '</a></p>';
      out.innerHTML = html;
    };
    var api = mount(form, { inline: true, page: function (q) { setTimeout(function () { var p = form.querySelector('.bvs-pane'); if (p) p.hidden = true; }, 0); draw(q); } });
    getIndex(form.dataset.idx).then(function () { draw(input.value.trim()); });
    TAIL.push(function () { draw(input.value.trim()); });
    return api;
  }

  function auto() {
    d.querySelectorAll('form.bvs[data-mode=page]').forEach(page);
    d.querySelectorAll('form.wh-search, form.bvs:not([data-mode=page])').forEach(function (f) {
      var o = { idx: f.dataset.idx && /search-/.test(f.dataset.idx) ? f.dataset.idx : null };
      if (f.dataset.mode === 'map') o.onPick = function (x, I) {   // /map/: world-map.js moves the map ("bvs-pick")
        var m = x.r[0] === 'q' ? x.url : mapHref(I, x.r);
        if (!m) return false;
        var ev = new CustomEvent('bvs-pick', { detail: { map: m, r: x.r }, cancelable: true });
        d.dispatchEvent(ev);
        return ev.defaultPrevented;
      };
      var api = mount(f, o), pq = new URLSearchParams(location.search).get('q');
      if (api && pq && f.classList.contains('wh-search')) { api.input.value = pq.slice(0, 80); getIndex(o.idx).then(api.render); }   // /?q= (SearchAction)
    });
    d.querySelectorAll('.wd-find').forEach(function (f) { mount(f, { countries: true, limit: 8 }); });
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', auto); else auto();
  API.mount = mount;
  API.index = getIndex;
  API.cold = function () { if (IDX) { IDX.hc = null; IDX.lw = null; } };   // tests: forget the words searched so far
  API.ready = function () { return !!(IDX && IDX.pending === 0); };   // every file of the index is in (tests)
  return API;
});
