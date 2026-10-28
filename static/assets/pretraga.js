/* BlokVolt site search (docs/RUNBOOK.md 3.8). One engine for /pretraga/ and the suggestions under the home search box.
   The index is /assets/search[-en|-ru].json (build.py → build_search), the ranking is MiniSearch (/assets/vendor/, MIT):
   BM25 over title, URL words, section, headings, description and the start of the text, with typos (fuzzy) and word
   beginnings (prefix). On top of it, for Serbian and its readers:
   - one spelling: case, diacritics (č = c, đ = dj) and Cyrillic do not matter („Нови Сад“ = „novi sad“);
   - a light stemmer per language, so „subvencije“ finds „subvencija“ and „tesla“ never matches „test“;
   - words that mean the same thing on this site (content/data/pretraga.json → syn: volbox = wallbox);
   - words that carry no meaning in a query are skipped (stop: za, i, u, kako…);
   - „Možda ste mislili“: a word that is on no page is corrected to the nearest word of a title or heading;
   - page kinds weigh differently: guides and data before firms, news a little lower and lower with age.
   Works in the browser (window.BVSearch) and in node for scripts/qa/pretraga_test.mjs (module.exports). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.BVSearch = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---------------------------------------------------------------- one spelling
  var CYR = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'ђ': 'dj', 'е': 'e', 'ё': 'e', 'ж': 'z', 'з': 'z', 'и': 'i', 'й': 'j', 'ј': 'j',
    'к': 'k', 'л': 'l', 'љ': 'lj', 'м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c',
    'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz', 'ш': 's', 'щ': 'sc', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e',
    'ю': 'ju', 'я': 'ja', 'і': 'i', 'ї': 'ji', 'є': 'je', 'ґ': 'g'
  };
  var HAS_CYR = /[Ѐ-ӿ]/;
  function translit(s) { return String(s || '').toLowerCase().replace(/[Ѐ-ӿ]/g, function (c) { return CYR[c] != null ? CYR[c] : c; }); }
  // lower case, Cyrillic to Latin (unless keepCyr: the Russian pages keep Russian words), đ = dj, no diacritics
  function norm(s, keepCyr) {
    s = String(s == null ? '' : s).toLowerCase();
    if (keepCyr) s = s.replace(/[ђјљњћџ]/g, function (c) { return CYR[c]; }).replace(/ё/g, 'е');
    else s = translit(s);
    return s.replace(/đ/g, 'dj').normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/й/g, 'и');
  }
  var SPLIT = /[^a-z0-9а-я]+/;
  function words(s, keepCyr) { return norm(s, keepCyr).split(SPLIT).filter(Boolean); }

  // ---------------------------------------------------------------- light stemmers (one ending, the stem keeps 4 letters)
  var END = {
    sr: ['ovima', 'evima', 'ijama', 'ama', 'ima', 'ega', 'emu', 'omu', 'oga', 'ih', 'im', 'om', 'em', 'og', 'oj', 'a', 'e', 'i', 'o', 'u'],
    // й is folded to и first (norm), so -ий/-ый/-ой/-ей are written -ии/-ыи/-ои/-еи
    ru: ['иями', 'ями', 'ами', 'ого', 'его', 'ому', 'ему', 'ыми', 'ими', 'иеи', 'ие', 'ия', 'ии', 'ыи', 'ои', 'еи', 'ая', 'яя', 'ое',
      'ее', 'ые', 'ую', 'юю', 'ом', 'ем', 'ам', 'ям', 'ах', 'ях', 'ов', 'ев', 'ть', 'а', 'я', 'ы', 'и', 'у', 'ю', 'е', 'о', 'ь']
  };
  function cut(w, list) {
    if (w.length < 5) return w;
    for (var i = 0; i < list.length; i++) {
      var e = list[i];
      if (w.length - e.length >= 4 && w.slice(-e.length) === e) return w.slice(0, -e.length);
    }
    return w;
  }
  function stemEn(w) {
    if (w.length < 5) return w;
    if (/ies$/.test(w)) return w.slice(0, -3) + 'y';
    if (/(ss|us)$/.test(w)) return w;
    if (/(sh|ch|x|z|s)es$/.test(w)) return w.slice(0, -2);
    if (/s$/.test(w)) return w.slice(0, -1);
    return w;
  }
  function stem(w, lang) {
    if (/^\d/.test(w)) return w;
    if (/[а-я]/.test(w)) return cut(w, END.ru);
    return lang === 'en' ? stemEn(w) : cut(w, END.sr);
  }

  // ---------------------------------------------------------------- Damerau-Levenshtein, stops early past `max`
  function dist(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var m = a.length, n = b.length, d = [], i, j;
    for (i = 0; i <= m; i++) { d[i] = [i]; }
    for (j = 1; j <= n; j++) d[0][j] = j;
    for (i = 1; i <= m; i++) {
      var best = max + 1;
      for (j = 1; j <= n; j++) {
        var c = a[i - 1] === b[j - 1] ? 0 : 1;
        var v = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c);
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, d[i - 2][j - 2] + 1);
        d[i][j] = v;
        if (v < best) best = v;
      }
      if (best > max) return max + 1;
    }
    return d[m][n];
  }

  // page kinds (build.py → kind_of): how much a page of that kind weighs against the others
  // katalog: /elektricni-automobili/, the page for „električni automobili“ and „gde kupiti električni auto“
  // model: /elektricni-automobili/<brand>/<model>/, a little under its brand page (a brand name finds the brand first)
  var KIND = { katalog: 1.45, vodic: 1.35, podaci: 1.3, alat: 1.3, javno: 1.2, mreza: 1.2, marka: 1.2, model: 1.15, grad: 1.25, mesto: 1.1, hub: 1.1, firma: 1, pomoc: 1,
    vest: 0.8, strana: 0.6, pregled: 0.5, home: 0.45 };
  var FIELDS = ['t', 'sl', 's', 'h', 'd', 'b'];
  var BOOST = { t: 5, sl: 3, s: 1.5, h: 2, d: 2, b: 1 };

  /* docs: the index (array of {u, t, d, s, h, b, k, dt}); cfg: {lang, syn, stop, today: 'YYYY-MM-DD'} */
  function create(MiniSearch, docs, cfg) {
    cfg = cfg || {};
    var lang = cfg.lang || 'sr', keepCyr = lang === 'ru';
    var stop = {};
    ((cfg.stop || {})[lang] || []).concat(lang === 'sr' ? [] : (cfg.stop || {}).sr || []).forEach(function (w) { stop[norm(w, keepCyr)] = 1; });
    var tok = function (s) { return words(s, keepCyr); };
    var proc = function (w) { return stop[w] ? null : stem(w, lang); };
    var today = cfg.today ? Date.parse(cfg.today) : Date.now();

    // synonyms: normalized member -> the group's members (normalized)
    var syn = {};
    (cfg.syn || []).forEach(function (g) {
      var ms = g.map(function (w) { return words(w, keepCyr).join(' '); }).filter(Boolean);
      ms.forEach(function (m) { syn[m] = ms; });
    });

    // vocabulary for „Možda ste mislili“: words of titles, URLs, sections, headings and descriptions (count and how a
    // title writes them); every word and stem of the pages, to know whether a query word exists at all
    var top = {}, surface = {}, all = {}, stems = {};
    var docsIx = docs.map(function (x, i) {
      var sl = String(x.u || '').split('?')[0].replace(/\/$/, '').split('/').pop().replace(/\.html$/, '');
      var o = { id: i, t: x.t || '', sl: sl.replace(/-/g, ' ') + ' ' + sl.replace(/-/g, ''), s: x.s || '', h: x.h || '', d: x.d || '', b: x.b || '',
        k: x.k || '', dt: x.dt || '' };
      FIELDS.forEach(function (f) {
        tok(o[f]).forEach(function (w) {
          all[w] = 1; stems[stem(w, lang)] = 1;
          if (f !== 'b' && w.length >= 4 && !/^\d+$/.test(w)) top[w] = (top[w] || 0) + 1;
        });
      });
      String(o.t).split(/[\s,.:;()„“"«»—–/]+/).forEach(function (w) { var n = norm(w, keepCyr); if (n && !surface[n]) surface[n] = w; });
      return o;
    });

    function boostDoc(id, term, f) {
      var k = KIND[f && f.k] || 1;
      if (f && f.k === 'vest' && f.dt) {
        var age = (today - Date.parse(f.dt)) / 864e5;
        k *= age < 60 ? 1 : age < 180 ? 0.85 : 0.7;
      }
      return k;
    }
    var ms = new MiniSearch({
      fields: FIELDS, storeFields: ['k', 'dt'], idField: 'id',
      tokenize: tok, processTerm: proc,
      searchOptions: { tokenize: tok, processTerm: proc, boost: BOOST, boostDocument: boostDoc, weights: { fuzzy: 0.35, prefix: 0.5 } }
    });
    ms.addAll(docsIx);

    var known = function (w) { return !!(all[w] || stems[stem(w, lang)] || syn[w]); };
    function fix(w) {
      if (w.length < 5 || /\d/.test(w) || known(w)) return null;
      var max = w.length >= 8 ? 2 : 1, best = null, bd = max + 1, bn = 0;
      var tries = [w];
      if (keepCyr && HAS_CYR.test(w)) tries.push(translit(w));
      tries.forEach(function (q) {
        for (var v in top) {
          if (Math.abs(v.length - q.length) > max) continue;
          var k = dist(q, v, max);
          if (k <= max && (k < bd || (k === bd && top[v] > bn))) { best = v; bd = k; bn = top[v]; }
        }
      });
      return best;
    }

    // the query as user words (stop words out, unless nothing else is left), two-word synonyms kept together
    function parse(q) {
      var ws = words(q, keepCyr), out = [];
      var kept = ws.filter(function (w) { return !stop[w]; });
      if (!kept.length) kept = ws;
      for (var i = 0; i < kept.length; i++) {
        var two = i + 1 < kept.length ? kept[i] + ' ' + kept[i + 1] : '';
        if (two && syn[two]) { out.push(two); i++; } else out.push(kept[i]);
      }
      return out;
    }
    // one OR group per user word: the word (and on the Russian pages its Latin spelling, for brand names) at full weight,
    // its synonyms at a third, so a page with the typed word stays ahead and many synonyms never add up to more than it
    var leaf = function (v) { return v.indexOf(' ') > 0 ? { combineWith: 'AND', queries: [v] } : v; };
    // (a phrase synonym names the same thing exactly — „ночной тариф“ = „низкий тариф“ — so it keeps most of the weight)
    var SYN_W = function () { return 0.35; }, PHRASE_W = function () { return 0.8; };
    function group(w, last, suggest) {
      var main = [w];
      if (keepCyr && HAS_CYR.test(w)) main.push(translit(w));
      var others = (syn[w] || []).filter(function (v) { return main.indexOf(v) < 0; });
      // a typed word that is on no page („volbox“) is only another spelling: its synonyms then count fully
      if (others.length && w.indexOf(' ') < 0 && !all[w] && !stems[stem(w, lang)]) {
        main = main.concat(others.filter(function (v) { return v.indexOf(' ') < 0; }));
        others = others.filter(function (v) { return v.indexOf(' ') > 0; });
      }
      var one = others.filter(function (v) { return v.indexOf(' ') < 0; }), many = others.filter(function (v) { return v.indexOf(' ') > 0; });
      var qs = main.map(leaf);
      if (one.length) qs.push({ combineWith: 'OR', boostTerm: SYN_W, queries: one });
      if (many.length) qs.push({ combineWith: 'OR', boostTerm: PHRASE_W, queries: many.map(leaf) });
      var node = { combineWith: 'OR', queries: qs };
      if (suggest && last) node.prefix = function (t) { return t.length >= 2; };
      return node;
    }
    function run(ws, suggest) {
      if (!ws.length) return [];
      var opts = {
        prefix: function (t) { return t.length >= 4; },
        fuzzy: function (t) { return t.length >= 8 ? 2 : t.length >= 5 ? 1 : false; }
      };
      var groups = ws.map(function (w, i) { return group(w, i === ws.length - 1, suggest); });
      var r = ms.search({ combineWith: 'AND', queries: groups }, opts);
      if (!r.length && ws.length > 1) {
        // no page has every word: pages with more of the words first, and with three or more words at least two of them
        var sets = ws.map(function (w) {
          var set = {};
          [w].concat(syn[w] || [], keepCyr && HAS_CYR.test(w) ? [translit(w)] : []).forEach(function (v) {
            tok(v).forEach(function (t) { var x = proc(t); if (x) set[x] = 1; });
          });
          return set;
        });
        var need = ws.length >= 3 ? 2 : 1;
        var or = ms.search({ combineWith: 'OR', queries: groups }, opts).map(function (x) {
          var m = 0;
          sets.forEach(function (set) { if (x.queryTerms.some(function (t) { return set[t]; })) m++; });
          x.m = m;
          return x;
        });
        var some = or.filter(function (x) { return x.m >= need; });
        r = (some.length ? some : or).sort(function (a, b) { return b.m - a.m || b.score - a.score; });
      }
      return r;
    }

    /* search(q, {suggest}) → {hits: [{doc, score, terms}], words, fixed: {from, to} | null, maybe: 'query' | null}
       fixed: no page had the typed words, the results are for the corrected ones; maybe: there were results, but a word
       is on no page, so the corrected query is offered as a link */
    function search(q, o) {
      o = o || {};
      var ws = parse(q);
      var r = run(ws, o.suggest), fixed = null, maybe = null;
      var corr = ws.map(function (w) { return w.indexOf(' ') < 0 ? fix(w) : null; });
      if (corr.some(Boolean)) {
        var ws2 = ws.map(function (w, i) { return corr[i] || w; });
        var by = {};
        ws.forEach(function (w, i) { if (corr[i]) by[w] = surface[corr[i]] || corr[i]; });
        // the query as typed, with only the corrected words replaced („kako da punm auto“ → „kako da punim auto“)
        var shown = String(q).trim().split(/(\s+)/).map(function (t) { var n = words(t, keepCyr).join(' '); return by[n] || t; }).join('');
        var r2 = run(ws2, o.suggest);
        if (!r.length && r2.length) { r = r2; fixed = { from: q.trim(), to: shown }; ws = ws2; }
        else if (r.length && r2.length && r2[0].id !== r[0].id) maybe = shown;   // only when the correction changes the answer
      }
      return {
        hits: r.map(function (x) { return { doc: docs[x.id], score: x.score, terms: x.terms }; }),
        words: ws, fixed: fixed, maybe: maybe
      };
    }

    // <mark> around the words of a text that the result matched (by stem, so „punjača“ marks „Punjači“)
    function mark(text, terms, esc) {
      var set = {};
      (terms || []).forEach(function (t) { set[t] = 1; });
      return String(text || '').split(/(\s+)/).map(function (part) {
        if (!part.trim()) return part;
        var w = words(part, keepCyr), hit = false;
        for (var i = 0; i < w.length && !hit; i++) {
          var s = stem(w[i], lang);
          if (set[s]) hit = true;
          else for (var t in set) if (t.length >= 3 && s.indexOf(t) === 0) { hit = true; break; }
        }
        return hit ? '<mark>' + esc(part) + '</mark>' : esc(part);
      }).join('');
    }

    return { search: search, mark: mark, size: docs.length, parse: parse, known: known };
  }

  return { create: create, norm: norm, words: words, stem: stem, translit: translit, dist: dist };
});

/* ---------------------------------------------------------------- the page: /pretraga/ and the home suggestions */
(function () {
  'use strict';
  if (typeof document === 'undefined' || typeof window === 'undefined' || !window.BVSearch) return;
  var d = document, B = window.BVSearch;
  var L = (d.documentElement.lang || 'sr').slice(0, 2), PRE = (L === 'en' || L === 'ru') ? '/' + L : '';
  var cfgEl = d.getElementById('s-cfg');
  if (!cfgEl) return;
  var CFG = JSON.parse(cfgEl.textContent);
  var T = {};
  try { T = JSON.parse((d.getElementById('bv-i18n') || {}).textContent || '{}'); } catch (e) {}
  var tr = function (v) { return (v && typeof v === 'object' && !Array.isArray(v)) ? (v[L] || v.sr) : v; };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var Q = tr(T.q) || ['„', '“'];
  var quote = function (s) { return Q[0] + s + Q[1]; };
  function pl(n, f) {
    if (!Array.isArray(f)) return f;
    var l = n % 10, l2 = n % 100;
    if (L === 'en') return n === 1 ? f[0] : f[2];
    return (l === 1 && l2 !== 11) ? f[0] : ((l >= 2 && l <= 4 && (l2 < 12 || l2 > 14)) ? f[1] : f[2]);
  }

  // the engine, built once: MiniSearch and the index come on first use
  var ENGINE = null, LOADING = null;
  function loadScript(src) {
    return new Promise(function (ok, no) {
      if (window.MiniSearch) return ok();
      var s = d.createElement('script'); s.src = src; s.async = true; s.onload = function () { ok(); }; s.onerror = no;
      d.head.appendChild(s);
    });
  }
  function engine() {
    if (ENGINE) return Promise.resolve(ENGINE);
    if (LOADING) return LOADING;
    LOADING = Promise.all([loadScript(CFG.lib), fetch(CFG.index[PRE ? L : 'sr']).then(function (r) { if (!r.ok) throw new Error('index'); return r.json(); })])
      .then(function (a) {
        ENGINE = B.create(window.MiniSearch, a[1], { lang: L, syn: CFG.syn, stop: CFG.stop, today: CFG.today });
        ENGINE.docs = a[1];
        return ENGINE;
      });
    LOADING.catch(function () { LOADING = null; });
    return LOADING;
  }

  // what people search: the query (no IP, no cookie; RUNBOOK 3.8), once per query and page view; n = pages found,
  // c = position of the opened result. The server folds it per day and keeps it 90 days.
  var SENT = {};
  function logq(q, n, extra) {
    q = String(q || '').trim();
    if (q.length < 2) return;
    var key = q.toLowerCase() + '|' + (extra && extra.c ? 'c' : '');
    if (SENT[key]) return;
    SENT[key] = 1;
    var body = JSON.stringify(Object.assign({ q: q.slice(0, 80), l: L, n: n, w: location.pathname === PRE + '/' ? 'home' : 'page' }, extra || {}));
    try {
      if (navigator.sendBeacon && navigator.sendBeacon('/api/pretraga', new Blob([body], { type: 'text/plain' }))) return;
    } catch (e) {}
    try { fetch('/api/pretraga', { method: 'POST', body: body, keepalive: true, headers: { 'content-type': 'text/plain' } }).catch(function () {}); } catch (e) {}
  }
  function hitHtml(h, eng, i) {
    var x = h.doc;
    return '<a class="hit" href="' + esc(x.u) + '" data-i="' + i + '">' + (x.s ? '<small>' + esc(x.s) + '</small>' : '') +
      '<b>' + eng.mark(x.t, h.terms, esc) + '</b>' + (x.d ? '<span>' + esc(x.d) + '</span>' : '') + '</a>';
  }

  // ------------------------------------------------------------ /pretraga/
  var page = d.getElementById('s-results');
  if (page) (function () {
    var input = d.getElementById('q'), out = page, status = d.getElementById('s-status'), more = d.getElementById('s-more');
    var ask = d.getElementById('s-ask'), sim = d.getElementById('s-sim'), simList = d.getElementById('s-sim-list');
    var timer = null, idle = null, last = null, SM_OFF = !CFG.smisao;
    function show(el, on) { if (el) el.hidden = !on; }

    // pages close in meaning (RUNBOOK 3.8b): asked only when the words found little or the query reads like a question
    var smTimer = null, smSeq = 0;
    function smisao(q, res) {
      show(sim, false);
      if (SM_OFF || !sim) return;
      var few = res.hits.length < 3, long = res.words.length >= 3;
      if (!few && !long) return;
      clearTimeout(smTimer);
      var seq = ++smSeq;
      smTimer = setTimeout(function () {
        fetch('/api/smisao?l=' + L + '&q=' + encodeURIComponent(q.slice(0, 160))).then(function (r) { return r.json(); }).then(function (j) {
          if (seq !== smSeq) return;
          if (!j || !j.ok) { if (j && j.error === 'off') SM_OFF = true; return; }
          var shown = {};
          res.hits.slice(0, 30).forEach(function (h) { shown[h.doc.u] = 1; });
          var by = {};
          ENGINE.docs.forEach(function (x) { by[x.u] = x; });
          var rows = (j.hits || []).map(function (h) { return by[PRE + h.u]; })
            .filter(function (x) { return x && !shown[x.u]; }).slice(0, 5);
          if (!rows.length) return;
          simList.innerHTML = rows.map(function (x, i) {
            return hitHtml({ doc: x, terms: [] }, ENGINE, 100 + i);
          }).join('');
          show(sim, true);
          if (!res.hits.length) { show(ask, false); }
        }, function () {});
      }, 450);
    }

    function render(q, res) {
      var hits = res.hits, n = hits.length;
      var head = '';
      if (!q) {
        status.textContent = String(tr(T.hint) || '').replace('{n}', ENGINE.size);
      } else if (n) {
        head = n + ' ' + pl(n, tr(T.found)) + ' ' + quote(res.fixed ? res.fixed.to : q);
        status.innerHTML = esc(head) + (res.fixed ? ' <span class="s-fix">' + esc(String(tr(T.fixed) || '').replace('{q}', quote(res.fixed.from))) + '</span>' : '') +
          (res.maybe ? ' <span class="s-fix">' + esc(tr(T.maybe) || '') + ' <a href="?q=' + encodeURIComponent(res.maybe) + '" data-maybe>' + esc(res.maybe) + '</a>?</span>' : '');
      } else {
        status.textContent = String(tr(T.none) || '').replace('{q}', q);
      }
      out.innerHTML = hits.slice(0, 30).map(function (h, i) { return hitHtml(h, ENGINE, i); }).join('') +
        (n > 30 ? '<p class="s-cap">' + esc(String(tr(T.cap) || '').replace('{n}', n)) + '</p>' : '');
      show(out, n > 0);
      show(more, !q || n < 3);
      show(ask, !!q && n < 3);
      if (ask && q) { var f = ask.querySelector('[name=upit]'); if (f) f.value = q; }
      smisao(q, res);
    }
    function run(push) {
      var q = input.value.trim();
      if (!ENGINE) return;
      var res = q ? ENGINE.search(q) : { hits: [], words: [], fixed: null, maybe: null };
      last = { q: q, n: res.hits.length, fixed: res.fixed };
      render(q, res);
      if (history.replaceState) history.replaceState(null, '', PRE + '/pretraga/' + (q ? '?q=' + encodeURIComponent(q) : ''));
      clearTimeout(idle);
      if (q) idle = setTimeout(function () { logq(q, res.hits.length, res.fixed ? { f: res.fixed.to } : null); }, push ? 0 : 2500);
    }
    status.textContent = tr(T.loading) || '';
    engine().then(function () {
      var p = new URLSearchParams(location.search).get('q');
      if (p) input.value = p;
      run(!!p);
    }, function () { status.textContent = tr(T.down) || ''; show(more, true); });
    input.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(function () { run(false); }, 120); });
    input.form.addEventListener('submit', function (e) { e.preventDefault(); run(true); input.blur(); });
    d.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a');
      if (!a) return;
      if (a.hasAttribute('data-maybe')) { e.preventDefault(); input.value = a.textContent; run(true); return; }
      var i = a.getAttribute('data-i');
      if (i != null && last && last.q) logq(last.q, last.n, { c: +i + 1 });
    });

    // „Niste našli šta tražite?“ → /api/zahtev, kind pretraga (the owner's bot shows it in the BlokVolt topic)
    var form = ask && ask.querySelector('form'), t0 = Date.now();
    if (form) form.addEventListener('submit', function (e) {
      e.preventDefault();
      var msg = function (k) { [].forEach.call(ask.querySelectorAll('[data-m]'), function (m) { m.hidden = m.getAttribute('data-m') !== k; }); };
      var txt = form.querySelector('textarea').value.trim();
      if (!txt) { form.querySelector('textarea').focus(); return; }
      var btn = form.querySelector('[type=submit]'); btn.disabled = true;
      fetch('/api/zahtev', { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ kind: 'pretraga', slug: PRE + '/pretraga/', data: { poruka: txt, upit: (form.querySelector('[name=upit]') || {}).value || '', jezik: L },
          hp: form.elements.website ? form.elements.website.value : '', t: Date.now() - t0 }) })
        .then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }, function () { return { ok: false, status: r.status }; }); })
        .then(function (j) {
          btn.disabled = false;
          if (j.ok) { msg('poslato'); form.hidden = true; if (window.bvTrack) window.bvTrack('form_sent', { form: 'pretraga' }); }
          else msg(j.status === 429 ? 'limit' : 'greska');
        }, function () { btn.disabled = false; msg('greska'); });
    });
  })();

  // ------------------------------------------------------------ suggestions under the home search box
  var hq = d.getElementById('home-q');
  if (hq) (function () {
    var form = hq.form, box = null, items = [], cur = -1, timer = null, lastQ = '';
    hq.setAttribute('role', 'combobox');
    hq.setAttribute('aria-autocomplete', 'list');
    hq.setAttribute('aria-expanded', 'false');
    hq.setAttribute('aria-controls', 'home-sug');
    function place() {
      if (!box) return;
      var r = hq.getBoundingClientRect();
      box.style.left = (r.left + window.scrollX) + 'px';
      box.style.top = (r.bottom + window.scrollY + 6) + 'px';
      box.style.width = r.width + 'px';
    }
    function close() {
      if (box) box.hidden = true;
      hq.setAttribute('aria-expanded', 'false');
      hq.removeAttribute('aria-activedescendant');
      cur = -1;
    }
    function ensure() {
      if (box) return box;
      box = d.createElement('div');
      box.id = 'home-sug'; box.className = 'sug'; box.setAttribute('role', 'listbox'); box.hidden = true;
      box.setAttribute('aria-label', tr(T.sug_label) || '');
      d.body.appendChild(box);
      box.addEventListener('mousedown', function (e) { e.preventDefault(); });   // keep the focus in the box
      box.addEventListener('click', function (e) {
        var a = e.target.closest('a');
        if (a && a.getAttribute('data-i') != null && lastQ) logq(lastQ, items.length, { c: +a.getAttribute('data-i') + 1 });
      });
      window.addEventListener('resize', place);
      return box;
    }
    function paint(q) {
      var res = ENGINE.search(q, { suggest: true });
      var hits = res.hits.slice(0, 6);
      items = hits;
      lastQ = q;
      ensure();
      var all = PRE + '/pretraga/?q=' + encodeURIComponent(q);
      var html = '';
      if (res.fixed) html += '<p class="sug-fix">' + esc(String(tr(T.sug_fixed) || '').replace('{q}', quote(res.fixed.to))) + '</p>';
      html += hits.map(function (h, i) {
        var x = h.doc;
        return '<a id="sug-' + i + '" role="option" aria-selected="false" class="sug-i" href="' + esc(x.u) + '" data-i="' + i + '"><b>' + ENGINE.mark(x.t, h.terms, esc) + '</b>' +
          (x.s ? '<small>' + esc(x.s) + '</small>' : '') + '</a>';
      }).join('');
      if (!hits.length) html += '<p class="sug-none">' + esc(String(tr(T.sug_none) || '').replace('{q}', q)) + '</p>';
      html += '<a id="sug-all" role="option" aria-selected="false" class="sug-all" href="' + esc(all) + '">' + esc(String(tr(T.sug_all) || '').replace('{q}', quote(q))) + '</a>';
      box.innerHTML = html;
      cur = -1;
      place();
      box.hidden = false;
      hq.setAttribute('aria-expanded', 'true');
    }
    function update() {
      var q = hq.value.trim();
      if (q.length < 2) { close(); return; }
      engine().then(function () { if (hq.value.trim() === q && d.activeElement === hq) paint(q); }, function () {});
    }
    function move(k) {
      if (!box || box.hidden) return;
      var opts = box.querySelectorAll('[role=option]'), n = opts.length;
      if (!n) return;
      cur += k;                                   // -1 = back in the input, then the options, and round again
      if (cur > n - 1) cur = -1;
      if (cur < -1) cur = n - 1;
      [].forEach.call(opts, function (o, i) { o.setAttribute('aria-selected', i === cur ? 'true' : 'false'); });
      if (cur >= 0) hq.setAttribute('aria-activedescendant', opts[cur].id); else hq.removeAttribute('aria-activedescendant');
    }
    hq.addEventListener('focus', function () { engine().catch(function () {}); if (hq.value.trim().length >= 2) update(); });
    hq.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(update, 90); });
    hq.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Escape') { close(); }
      else if (e.key === 'Enter' && box && !box.hidden && cur >= 0) {
        var o = box.querySelectorAll('[role=option]')[cur];
        if (o) { e.preventDefault(); if (o.getAttribute('data-i') != null) logq(lastQ, items.length, { c: cur + 1 }); location.href = o.getAttribute('href'); }
      }
    });
    hq.addEventListener('blur', function () { setTimeout(close, 150); });
    form.addEventListener('submit', function () { close(); });
  })();
})();
