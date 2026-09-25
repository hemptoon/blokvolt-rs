/* BlokVolt — small site script: menu, language switcher, list filters, usage events. No dependencies. */
(function () {
  var d = document;

  // ---------- usage events ----------
  // window.bvTrack(name, props) is the one entry point for the site and the map (and later the apps, which use the
  // same event names). Events go to PostHog (EU cloud) only when content/data/site.json -> analytics.posthog_key is
  // set; the build then adds <script id="bv-an">. Without it every call is a no-op. Page views are counted
  // separately by Cloudflare Web Analytics (no cookies).
  // Modes: cookieless for everyone (nothing written to the browser); with analytics.consent the page also shows a
  // banner, and a reader who allows the cookie is measured with cookies and session replay (inputs masked) from the
  // next page on. The choice is kept in localStorage 'bv:consent' ('yes' / 'no'). Do Not Track or Global Privacy
  // Control: nothing is sent and no banner is shown.
  var AN = null, anQ = [], anReady = false, CK = 'bv:consent';
  try { var anEl = d.getElementById('bv-an'); AN = anEl ? JSON.parse(anEl.textContent) : null; } catch (e) { AN = null; }
  var optOut = navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true;
  if (AN && (!AN.key || navigator.webdriver || optOut)) AN = null;    // automated browsers (tests) are not counted
  var PAGE = (d.body && d.body.getAttribute('data-page')) || '';
  var LANG = (d.documentElement.lang || 'sr').slice(0, 2);
  function consent() { try { return localStorage.getItem(CK); } catch (e) { return null; } }
  window.bvTrack = function (name, props) {
    if (!AN) return;
    var p = {};
    for (var k in props || {}) p[k] = props[k];
    p.lang = LANG;
    if (PAGE) p.page = PAGE;
    if (anReady && window.posthog && window.posthog.capture) window.posthog.capture(name, p); else if (anQ.length < 50) anQ.push([name, p]);
  };
  function wipeAnalyticsStorage() {
    try { Object.keys(localStorage).forEach(function (k) { if (/^(ph_|__ph)/.test(k)) localStorage.removeItem(k); }); } catch (e) {}
    try { Object.keys(sessionStorage).forEach(function (k) { if (/^(ph_|__ph)/.test(k)) sessionStorage.removeItem(k); }); } catch (e) {}
    var host = location.hostname.replace(/^www\./, '');
    d.cookie.split(';').forEach(function (c) {
      var n = c.split('=')[0].trim();
      if (/^ph_/.test(n)) { d.cookie = n + '=; Max-Age=0; path=/'; d.cookie = n + '=; Max-Age=0; path=/; domain=.' + host; }
    });
  }
  function loadAnalytics() {
    var ph = window.posthog = window.posthog || [];
    if (ph.__SV) return;
    ph.__SV = 1;
    var cookies = AN.consent && consent() === 'yes';
    var cfg = {
      api_host: AN.host, ui_host: AN.ui, capture_pageview: true, capture_pageleave: true, autocapture: true, respect_dnt: true,
      disable_surveys: true, advanced_disable_feature_flags: true,
      loaded: function (inst) { anReady = true; anQ.splice(0).forEach(function (e) { inst.capture(e[0], e[1]); }); }
    };
    if (cookies) {
      cfg.persistence = 'localStorage+cookie'; cfg.person_profiles = 'identified_only';
      cfg.disable_session_recording = false; cfg.session_recording = { maskAllInputs: true };
    } else {
      cfg.cookieless_mode = 'always'; cfg.person_profiles = 'never'; cfg.disable_session_recording = true;
      if (AN.consent) wipeAnalyticsStorage();          // left over from an earlier 'yes' that was withdrawn
    }
    ph._i = [[AN.key, cfg, 'posthog']];
    var s = d.createElement('script');
    s.async = true; s.crossOrigin = 'anonymous'; s.src = AN.assets + '/static/array.js';
    d.head.appendChild(s);
  }
  if (AN) {
    var later = function () { (window.requestIdleCallback || function (f) { setTimeout(f, 1200); })(loadAnalytics); };
    if (d.readyState === 'complete') later(); else window.addEventListener('load', later);
  }
  // consent banner (only with analytics.consent): shown until the reader chooses; the privacy policy can reopen it
  var banner = d.getElementById('bv-consent');
  if (banner && AN && AN.consent) {
    if (consent() !== 'yes' && consent() !== 'no') banner.hidden = false;
    banner.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-consent]');
      if (!b) return;
      var v = b.getAttribute('data-consent');
      try { localStorage.setItem(CK, v); } catch (err) {}
      if (v === 'no') wipeAnalyticsStorage();
      banner.hidden = true;
      window.bvTrack('consent_choice', { choice: v });
    });
  }
  d.addEventListener('click', function (e) {
    var r = e.target.closest && e.target.closest('[data-bv-consent-reset]');
    if (!r) return;
    try { localStorage.removeItem(CK); } catch (err) {}
    wipeAnalyticsStorage();
    location.reload();                                   // start again without cookies; the banner shows
  });
  // offline support and the Android app (TWA): a small service worker, network first (static/sw.js)
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
    window.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () {}); });
  }
  d.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('[data-bv-app-download]')) window.bvTrack('app_download', { platform: 'android' });
  }, true);
  // links out: firm and network sites, phone numbers, e-mail addresses; language switch
  d.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var h = a.getAttribute('href') || '';
    if (a.hasAttribute('data-bv-lang')) { window.bvTrack('language_switch', { to: a.getAttribute('data-bv-lang') }); return; }
    if (h.indexOf('tel:') === 0) window.bvTrack('contact_phone', {});
    else if (h.indexOf('mailto:') === 0) window.bvTrack('contact_email', { to: h.slice(7).split('?')[0] });
    else if (/^https?:/.test(h) && a.hostname && a.hostname !== location.hostname) window.bvTrack('outbound_click', { host: a.hostname.replace(/^www\./, ''), url: h.slice(0, 200) });
  }, true);
  // calculators: one event per page view, on the first change
  var calcSeen = false;
  function calcUsed(e) {
    if (calcSeen || !(e.target.closest && e.target.closest('form.calc'))) return;
    calcSeen = true;
    window.bvTrack('calculator_used', { calculator: location.pathname.indexOf('racun-u-zgradi') >= 0 ? 'zgrada' : 'troskovi' });
  }
  d.addEventListener('input', calcUsed, true);
  d.addEventListener('change', calcUsed, true);

  // mobile menu
  var nav = d.querySelector('.hd-nav'), burger = d.querySelector('.burger');
  if (nav && burger) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { nav.classList.remove('is-open'); burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  // language menu
  var lt = d.querySelector('[data-lang-toggle]'), lm = d.querySelector('[data-lang-menu]');
  if (lt && lm) {
    lt.addEventListener('click', function (e) {
      e.stopPropagation();
      var hidden = lm.hasAttribute('hidden');
      if (hidden) lm.removeAttribute('hidden'); else lm.setAttribute('hidden', '');
      lt.setAttribute('aria-expanded', hidden ? 'true' : 'false');
    });
    d.addEventListener('click', function (e) {
      if (!lm.hasAttribute('hidden') && !lm.contains(e.target)) { lm.setAttribute('hidden', ''); lt.setAttribute('aria-expanded', 'false'); }
    });
  }

  // fold: case- and diacritics-insensitive text for search ("cacak" finds "Čačak")
  function fold(s) {
    return (s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
  }
  window.bvFold = fold;

  // list filters: <div data-filter-list> with [data-f-q], [data-f-sel=name], chips [data-f-chip="name:value"],
  // rows [data-row] carrying data-q (text) and data-<name> (space-separated values)
  [].forEach.call(d.querySelectorAll('[data-filter-list]'), function (box) {
    var rows = [].slice.call(box.querySelectorAll('[data-row]'));
    var q = box.querySelector('[data-f-q]');
    var sels = [].slice.call(box.querySelectorAll('[data-f-sel]'));
    var chips = [].slice.call(box.querySelectorAll('[data-f-chip]'));
    var count = box.querySelector('[data-f-count]');
    var empty = box.querySelector('[data-f-empty]');
    var groups = box.querySelectorAll('[data-f-group]');
    var state = {};
    var params = new URLSearchParams(location.search);
    sels.forEach(function (s) { var n = s.getAttribute('data-f-sel'); if (params.get(n)) s.value = params.get(n); });
    chips.forEach(function (c) {
      var kv = c.getAttribute('data-f-chip').split(':');
      if (params.get(kv[0]) === kv[1]) { chips.forEach(function (o) { if (o.getAttribute('data-f-chip').split(':')[0] === kv[0]) o.setAttribute('aria-pressed', 'false'); }); c.setAttribute('aria-pressed', 'true'); }
    });
    if (q && params.get('q')) q.value = params.get('q');

    function apply() {
      var words = fold(q ? q.value : '').split(/\s+/).filter(Boolean);
      state = {};
      sels.forEach(function (s) { if (s.value) state[s.getAttribute('data-f-sel')] = s.value; });
      chips.forEach(function (c) { if (c.getAttribute('aria-pressed') === 'true') { var kv = c.getAttribute('data-f-chip').split(':'); if (kv[1]) state[kv[0]] = kv[1]; } });
      var n = 0;
      rows.forEach(function (r) {
        var ok = true, hay = r.getAttribute('data-q') || '';
        for (var i = 0; i < words.length && ok; i++) if (hay.indexOf(words[i]) < 0) ok = false;
        for (var k in state) if (ok) { var vals = (r.getAttribute('data-' + k) || '').split(' '); if (vals.indexOf(state[k]) < 0) ok = false; }
        r.hidden = !ok; if (ok) n++;
      });
      [].forEach.call(groups, function (g) { g.hidden = !g.querySelector('[data-row]:not([hidden])'); });
      if (count) count.textContent = count.getAttribute('data-tpl').replace('{n}', n).replace('{all}', rows.length);
      if (empty) empty.hidden = n > 0;
    }
    if (q) q.addEventListener('input', apply);
    sels.forEach(function (s) { s.addEventListener('change', apply); });
    chips.forEach(function (c) {
      c.addEventListener('click', function () {
        var name = c.getAttribute('data-f-chip').split(':')[0];
        chips.forEach(function (o) { if (o.getAttribute('data-f-chip').split(':')[0] === name) o.setAttribute('aria-pressed', 'false'); });
        c.setAttribute('aria-pressed', 'true');
        apply();
      });
    });
    apply();
  });

  // forms that post to /api/zahtev (corrections, companies): fields by name; ?firma= ?operator= ?stanica= prefill the page field
  [].forEach.call(d.querySelectorAll('form[data-bv-form]'), function (f) {
    var t0 = Date.now(), kind = f.getAttribute('data-bv-form');
    var p = new URLSearchParams(location.search), slug = p.get('firma') || p.get('operator') || p.get('mreza') || p.get('stanica') || '';
    var what = f.querySelector('select[name=sta]'), where = f.querySelector('[name=gde],[name=stranica]');
    if (what && p.get('stanica')) what.value = 'stanica';
    else if (what && (p.get('operator') || p.get('mreza'))) what.value = 'mreza';
    if (kind === 'firma' && (p.get('operator') || p.get('mreza'))) { var ko = f.querySelector('[name=vrsta]'); if (ko) ko.value = 'mreza'; }
    if (where && slug) {
      where.value = p.get('stanica') ? location.origin + '/mapa/#' + slug : location.origin + (p.get('firma') ? '/firme/' : '/javno-punjenje/') + slug + '/';
    }
    function show(cls) {
      [].forEach.call(f.querySelectorAll('.f-msg'), function (m) { m.hidden = !m.classList.contains(cls); });
    }
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var bad = [].filter.call(f.querySelectorAll('[required]'), function (el) { return el.type === 'checkbox' ? !el.checked : !el.value.trim(); });
      if (bad.length) { show('f-need'); bad[0].focus(); return; }
      var data = {}, email = '';
      [].forEach.call(f.elements, function (el) {
        if (!el.name || el.name === 'website') return;
        if (el.type === 'checkbox') { if (el.checked) data[el.name] = true; return; }
        if (el.name === 'email') { email = el.value.trim(); return; }
        if (el.value.trim()) data[el.name] = el.value.trim();
      });
      var k = kind === 'firma' ? (data.vrsta === 'mreza' ? 'mreza' : 'firma') : (data.sta === 'stanica' || data.sta === 'novi-punjac' ? 'stanica' : 'ispravka');
      var btn = f.querySelector('[type=submit]');
      btn.disabled = true;
      fetch('/api/zahtev', { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ kind: k, slug: slug, data: data, email: email, hp: f.elements.website ? f.elements.website.value : '', t: Date.now() - t0 }) })
        .then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }, function () { return { ok: false, status: r.status }; }); })
        .then(function (j) {
          btn.disabled = false;
          if (j.ok) { show('f-ok'); f.reset(); btn.hidden = true; window.bvTrack('form_sent', { form: k }); }
          else show(j.status === 429 ? 'f-limit' : 'f-err');
        }, function () { btn.disabled = false; show('f-err'); });
    });
  });

  // YouTube behind a click: the iframe (youtube-nocookie.com) is created only when the reader presses play
  d.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.yt-play');
    if (!b) return;
    var id = b.getAttribute('data-yt');
    if (!/^[\w-]{6,20}$/.test(id)) return;
    var f = d.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0&modestbranding=1';
    var tt = b.querySelector('.yt-t');
    f.title = tt ? tt.textContent : 'YouTube';
    f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    f.setAttribute('allowfullscreen', '');
    f.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
    f.className = 'yt-frame';
    b.replaceWith(f);
    window.bvTrack('video_play', { video: id });
  });
})();
