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
  // the tokens of the account and newsletter links (?prijava=, ?t=) never reach the analytics, not even from a page
  // captured before it took them out of the address bar: every URL-like property of every event (and the page address
  // in session replay) loses them
  function scrubUrl(u) {
    if (typeof u !== 'string' || !/^(https?:\/\/|\/)/i.test(u) || !/[?&](t|prijava)=/.test(u)) return u;   // URLs and paths only
    try {
      var x = new URL(u, location.href);
      x.searchParams.delete('t');
      x.searchParams.delete('prijava');
      return /^https?:/i.test(u) ? x.href : x.pathname + x.search + x.hash;
    } catch (e) { return u.replace(/([?&])(t|prijava)=[^&#]*&?/g, '$1').replace(/[?&](#|$)/, '$1'); }
  }
  function scrubProps(p) {
    if (!p || typeof p !== 'object') return p;
    Object.keys(p).forEach(function (k) { if (typeof p[k] === 'string') p[k] = scrubUrl(p[k]); });
    if (Array.isArray(p.$snapshot_data)) {
      p.$snapshot_data.forEach(function (s) { if (s && s.data && typeof s.data.href === 'string') s.data.href = scrubUrl(s.data.href); });
    }
    return p;
  }
  window.bvTrack.scrub = scrubProps;                     // for the tests (scripts/qa/nalog_ui_test.py)
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
      before_send: function (ev) { if (ev) { scrubProps(ev.properties); scrubProps(ev.$set); scrubProps(ev.$set_once); } return ev; },
      sanitize_properties: function (props) { return scrubProps(props); },   // posthog-js before before_send existed
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
  // only on pages that declare the web app (www.blokvolt.rs); blokvolt.com uses this script without a service worker
  if ('serviceWorker' in navigator && d.querySelector('link[rel="manifest"]') && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
    window.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () {}); });
  }
  d.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('[data-bv-app-download]')) window.bvTrack('app_download', { platform: 'android' });
  }, true);
  // ads (docs/RUNBOOK.md 3.26): a booked ad disappears the day after its last day even without a new build;
  // a click is counted as ad_click (no personal data), the advertiser sees it by the utm tag.
  // No ads in the apps: bv.css hides them in standalone display; this also covers an app opened in a browser tab
  // (start URLs carry ?src=android / ?src=pwa, remembered for the tab) and an ad whose dates have passed.
  (function () {
    var app = d.referrer.indexOf('android-app://') === 0;
    try {
      if (/[?&]src=(android|pwa)(&|$)/.test(location.search)) sessionStorage.setItem('bv-app', '1');
      app = app || sessionStorage.getItem('bv-app') === '1';
    } catch (e) { /* storage blocked: the CSS rule still applies */ }
    var t = new Date(), iso = t.getFullYear() + '-' + ('0' + (t.getMonth() + 1)).slice(-2) + '-' + ('0' + t.getDate()).slice(-2);
    [].forEach.call(d.querySelectorAll('.oglas[data-do]'), function (el) {
      if (app || iso < el.getAttribute('data-od') || iso > el.getAttribute('data-do')) el.hidden = true;
      el.addEventListener('click', function (e) {
        if (e.target.closest && e.target.closest('a[href]')) window.bvTrack('ad_click', { ad: el.getAttribute('data-id') || '' });
      });
    });
  })();
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
    } else if (where && /^\/[\w\/.-]{0,120}$/.test(p.get('stranica') || '')) {
      where.value = location.origin + p.get('stranica');    // "Prijavite grešku u tekstu" on the help pages
      if (what && what.querySelector('option[value=tekst]')) what.value = 'tekst';
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
      data.jezik = (d.documentElement.lang || 'sr').slice(0, 2);   // the language to answer in (sr, en, ru)
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

  // "Moj nalog" in the header (only with site.json → accounts.enabled): a dot while someone is signed in in this browser.
  // bv_in=1 is only a hint for the static pages; the session itself is the HttpOnly cookie bv_s (docs/RUNBOOK.md 3.27).
  var accLink = d.querySelector('[data-bv-acc]');
  if (accLink && /(?:^|;\s*)bv_in=1(?:;|$)/.test(d.cookie)) accLink.classList.add('is-in');

  // Nedeljni pregled (newsletter) sign-up: /pregled/ and the boxes under the news, /vesti/ and /javno-punjenje/ (only with
  // site.json → pregled.enabled). Posts to /api/posta/prijava; the answer always looks the same, whether or not the address
  // was already signed up. The texts are in the form (translated with the page); this only shows and hides them.
  [].forEach.call(d.querySelectorAll('form[data-bv-pregled]'), function (f) {
    var t0 = Date.now(), inp = f.querySelector('input[type=email]'), btn = f.querySelector('[type=submit]');
    function show(k, email) {
      [].forEach.call(f.querySelectorAll('[data-m]'), function (m) {
        m.hidden = m.getAttribute('data-m') !== k;
        var e = m.querySelector('[data-email]');
        if (e && email) e.textContent = email;
      });
    }
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = inp.value.trim();
      if (email.length > 120 || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) { show('email'); inp.focus(); return; }
      btn.disabled = true;
      show('');
      // the server refuses a form sent faster than a person types (under 1,5 s): wait the rest instead
      setTimeout(function () {
        fetch('/api/posta/prijava', { method: 'POST', headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ email: email, lang: LANG, topics: f.getAttribute('data-topics') || undefined, src: location.pathname.slice(0, 80),
            hp: f.elements.website ? f.elements.website.value : '', t: Date.now() - t0 }) })
          .then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }, function () { return { ok: false, status: r.status }; }); })
          .then(function (j) {
            btn.disabled = false;
            if (j.ok) { show('ok', email); inp.value = ''; window.bvTrack('newsletter_signup', { src: location.pathname.slice(0, 80) }); }
            else show(j.error === 'email' ? 'email' : j.status === 429 ? 'limit' : 'off');
          }, function () { btn.disabled = false; show('net'); });
      }, Math.max(0, 1600 - (Date.now() - t0)));
    });
  });

  // help pages (/pomoc/): "Da li vam je ovo pomoglo?" — the vote goes to /api/zahtev (kind pomoc, no name or e-mail);
  // after "Ne" an optional note. The texts are in the page (translated with it); this only shows and hides them.
  [].forEach.call(d.querySelectorAll('[data-helpful]'), function (box) {
    var t0 = Date.now(), page = location.pathname, form = box.querySelector('form');
    function msg(k) { [].forEach.call(box.querySelectorAll('[data-m]'), function (m) { m.hidden = m.getAttribute('data-m') !== k; }); }
    function send(data) {
      return fetch('/api/zahtev', { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ kind: 'pomoc', slug: page, data: data, hp: form && form.elements.website ? form.elements.website.value : '', t: Date.now() - t0 }) })
        .then(function (r) { return r.ok; }, function () { return false; });
    }
    box.addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('[data-v]');
      if (!b) return;
      var v = b.getAttribute('data-v');
      box.classList.add('done');
      window.bvTrack('help_vote', { vote: v });
      send({ v: v }).then(function (ok) {
        if (!ok) return msg('greska');
        msg(v);
        if (v === 'ne' && form) form.querySelector('textarea').focus({ preventScroll: true });
      });
    });
    if (form) form.addEventListener('submit', function (e) {
      e.preventDefault();
      var txt = form.querySelector('textarea').value.trim();
      if (!txt) return msg('poslato');
      form.querySelector('[type=submit]').disabled = true;
      send({ v: 'komentar', poruka: txt }).then(function (ok) { msg(ok ? 'poslato' : 'greska'); });
    });
  });

  // help hub: the search box filters the questions on the page
  var hq = d.querySelector('[data-help-filter]');
  if (hq) {
    var fold = function (x) { return (x || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd'); };
    hq.addEventListener('input', function () {
      var q = fold(hq.value).split(/\s+/).filter(Boolean), shown = 0;
      [].forEach.call(d.querySelectorAll('[data-help-item]'), function (a) {
        var t = fold(a.textContent), ok = q.every(function (w) { return t.indexOf(w) >= 0; });
        a.hidden = !ok;
        if (ok && a.classList.contains('row')) shown++;
      });
      [].forEach.call(d.querySelectorAll('.sec[id], .help-top'), function (s) {
        var sec = s.classList.contains('help-top') ? s.parentNode : s;
        sec.hidden = ![].some.call(s.querySelectorAll('[data-help-item]'), function (a) { return !a.hidden; });
      });
      var none = d.querySelector('.help-none');
      if (none) none.hidden = shown > 0;
    });
  }

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

/* Visit counter (07.10.2026, RUNBOOK 3.16): one request per page view to our own counter (Cloudflare Worker
   evolako-bot, database in the EU), so the founders see exact numbers of people. No cookies and nothing stored in the
   browser for readers; sent: the page path (no query string), the referring site's host name, utm_source/medium/
   campaign and the page language. The counter turns IP + browser into an anonymous fingerprint that changes every day
   and does not keep the IP. Not sent from automated browsers (navigator.webdriver: our QA) or other hosts
   (pages.dev previews). ?tim=1 marks this browser as the team's own ('evo_tim' in localStorage, ?tim=0 removes it). */
(function () {
  try {
    var L = location, h = L.hostname;
    if (!/^(www\.)?(blokvolt|evolako)\.rs$/.test(h) || navigator.webdriver) return;
    var s = L.search, K = 'evo_tim', t = 0;
    try {
      if (/[?&]tim=1(&|$)/.test(s)) localStorage.setItem(K, '1');
      if (/[?&]tim=0(&|$)/.test(s)) localStorage.removeItem(K);
      t = localStorage.getItem(K) ? 1 : 0;
    } catch (e) { /* storage blocked */ }
    var r = '';
    try { r = document.referrer ? new URL(document.referrer).hostname : ''; } catch (e) { r = ''; }
    var q = new URLSearchParams(s), g = function (k) { return (q.get(k) || '').slice(0, 60); };
    var b = JSON.stringify({ h: h, p: L.pathname, r: r, t: t, us: g('utm_source'), um: g('utm_medium'), uc: g('utm_campaign'),
      l: (document.documentElement.lang || '').slice(0, 2) });
    var u = 'https://evolako-bot.mr-smekhov.workers.dev/s/p';
    // fetch, not sendBeacon: Brave's Shields drop cross-site beacons ("ping" requests) silently (checked 07.10.2026)
    if (window.fetch) fetch(u, { method: 'POST', body: b, keepalive: true, mode: 'no-cors', credentials: 'omit' }).catch(function () {});
    else if (navigator.sendBeacon) navigator.sendBeacon(u, b);
  } catch (e) { /* never break the page */ }
})();

/* EV fleet counter (10.10.2026, RUNBOOK 3.30): the estimate of electric cars in Serbia grows by itself.
   data-evc = "anchor|anchor_date|rate per day|step hours|max days": the value at the end of anchor_date (MUP fleet +
   new registrations by SAUVD) plus the average daily growth, counted in whole steps and for at most max_days. */
(function () {
  function fmt(n, t) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, t || '.'); }
  function run() {
    var els = document.querySelectorAll('[data-evc]');
    for (var i = 0; i < els.length; i++) {
      var p = (els[i].getAttribute('data-evc') || '').split('|');
      if (p.length < 5) continue;
      var t0 = Date.parse(p[1] + 'T23:59:59Z');
      if (isNaN(t0)) continue;
      var h = Math.max(0, Math.min((Date.now() - t0) / 3600000, +p[4] * 24));
      var steps = Math.floor(h / +p[3]);
      var v = Math.floor(+p[0] + +p[2] * steps * +p[3] / 24);
      if (v > 0) els[i].textContent = fmt(v, els[i].getAttribute('data-evc-t'));
    }
  }
  try { run(); setInterval(run, 600000); } catch (e) { /* never break the page */ }
})();
