/* BlokVolt — "Moj BlokVolt" (/nalog/) and the pages the newsletter's e-mails link to (/pregled/potvrda/,
   /pregled/odjava/). No dependencies, like bv.js. The account lives on the server (/api/nalog/*, /api/posta/*, see
   worker/_worker.js); these static pages only show it. The session is the HttpOnly cookie bv_s; bv_in=1 (readable)
   only says that someone is signed in in this browser. Favourites and "Imam Teslu" are also kept in localStorage
   ('bv:fav', 'bv:tesla', as on the map), so the map works offline and without an account; 'bv:fav-owner' says which
   account the list belongs to (a short hash from the server), so the lists of two people on one browser are never
   joined. Signing out and deleting the account remove all three. The sign-up forms of the newsletter (/pregled/ and
   the boxes under the news) are handled by bv.js. Texts: <script id="bv-i18n">. docs/RUNBOOK.md 3.27. */
(function () {
  'use strict';
  var d = document;
  var T = {}, CFG = {};
  try { T = JSON.parse(d.getElementById('bv-i18n').textContent); } catch (e) { T = {}; }
  try { CFG = JSON.parse((d.getElementById('nl-cfg') || {}).textContent || '{}'); } catch (e) { CFG = {}; }
  var API = CFG.api || '/api';
  var LANG = (d.documentElement.lang || 'sr').slice(0, 2);
  var LOC = LANG === 'sr' ? 'sr-Latn-RS' : LANG === 'en' ? 'en-GB' : LANG;   // British English on this site
  var LP = LANG === 'en' || LANG === 'ru' ? '/' + LANG : '';
  var PAGE = d.body.getAttribute('data-nl') || '';
  var T0 = Date.now();
  var STAR = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 3.6l2.55 5.17 5.7.83-4.13 4.02.98 5.68L12 16.62l-5.1 2.68.98-5.68L3.75 9.6l5.7-.83L12 3.6Z"/></svg>';

  function $(id) { return d.getElementById(id); }
  function all(sel, root) { return [].slice.call((root || d).querySelectorAll(sel)); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function track(e, p) { try { if (window.bvTrack) window.bvTrack(e, p || {}); } catch (x) { /* analytics never breaks the page */ } }
  function fmtDate(t) { return new Date(t * 1000).toLocaleDateString(LOC, { day: 'numeric', month: 'numeric', year: 'numeric' }); }
  function num(n) { return Number(n).toLocaleString(LOC, { maximumFractionDigits: 1 }); }
  // one call to the API → the answer plus {status: the HTTP status}; status 0 = no connection. A subscription's own
  // "status" of the answer (pending / on / off) is kept as {state}.
  function api(method, path, body) {
    var o = { method: method, credentials: 'same-origin', headers: {} };
    if (body) { o.headers['content-type'] = 'application/json'; o.body = JSON.stringify(body); }
    return fetch(API + path, o).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        j = j || {};
        if (j.status !== undefined) j.state = j.status;
        j.status = r.status;
        return j;
      });
    }, function () { return { ok: false, status: 0 }; });
  }
  // the server refuses forms sent faster than a person types (under 1,5 s after the page opened): wait the rest
  function afterTyping(fn) { setTimeout(fn, Math.max(0, 1600 - (Date.now() - T0))); }
  function errText(j) {
    if (!j.status) return T.err_net;
    if (j.error === 'email') return T.err_mail;
    if (j.error === 'tries') return T.err_tries;
    if (j.status === 429) return T.err_limit;
    if (j.error === 'code') return T.err_code;
    if (j.error === 'topics') return T.err_topics;
    return j.status >= 500 ? T.err_off : (T.err_save || T.err_off);
  }
  function msg(el, text) { if (el) { el.textContent = text || ''; el.hidden = !text; } }
  var toastT = null;
  function toast(text) {
    var t = $('nl-toast');
    if (!t || !text) return;
    t.textContent = text;
    t.hidden = false;
    clearTimeout(toastT);
    toastT = setTimeout(function () { t.hidden = true; }, 2800);
  }
  function hinted() { return /(?:^|;\s*)bv_in=1(?:;|$)/.test(d.cookie); }
  function dropHint() { d.cookie = 'bv_in=; Max-Age=0; Path=/; SameSite=Lax' + (location.protocol === 'https:' ? '; Secure' : ''); }
  // localStorage, as on the map (in a private window it may be missing: then this visit only)
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  function localFavs() {
    try { return (JSON.parse(lsGet('bv:fav') || '[]') || []).filter(function (x) { return typeof x === 'string'; }).slice(0, 300); } catch (e) { return []; }
  }
  function saveLocalFavs(a) { lsSet('bv:fav', JSON.stringify(a.slice(0, 300))); }
  // signed out or deleted: this browser keeps nothing of the account
  function forgetLocal() { ['bv:fav', 'bv:tesla', 'bv:fav-owner'].forEach(function (k) { try { localStorage.removeItem(k); } catch (e) { /* private mode */ } }); }
  // the plural form of the page language: 'one' | 'few' | 'many' (Serbian and Russian have all three, English two)
  function plural(n) {
    var c = 'other';
    try { c = new Intl.PluralRules(LOC).select(n); } catch (e) { c = n === 1 ? 'one' : 'other'; }
    return c === 'one' ? 'one' : c === 'few' ? 'few' : 'many';
  }
  function uniq(a) { var s = {}; return a.filter(function (x) { return s[x] ? false : (s[x] = 1); }); }
  function sameSet(a, b) { if (a.length !== b.length) return false; var s = {}; a.forEach(function (x) { s[x] = 1; }); return b.every(function (x) { return s[x]; }); }
  function shows(root, attr, key) { all('[' + attr + ']', root).forEach(function (el) { el.hidden = el.getAttribute(attr) !== key; }); }
  function topicsOf(root) { return all('input[type=checkbox][value]', root).filter(function (c) { return c.checked; }).map(function (c) { return c.value; }); }

  // ---------------------------------------------------------------- stations (names for favourites and reports)
  // the map's own files, loaded once and only when needed: Serbia (+ the networks' lists and our checked facts), and
  // the neighbouring countries only when an id is not among them
  var ST = null, ST_RG = null, SUM = null;
  function getJson(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }
  function stations(ids) {
    if (!ST) {
      ST = Promise.all([getJson(CFG.stations), getJson(CFG.nets).catch(function () { return {}; }), getJson(CFG.extra).catch(function () { return {}; })]).then(function (r) {
        var by = Object.create(null);
        (r[0].stations || []).concat(r[1].add || []).forEach(function (s) { by[s.id] = s; });
        [r[1], r[2]].forEach(function (L) {
          Object.keys(L.upd || {}).forEach(function (id) {
            var s = by[id], u = L.upd[id];
            if (s) Object.keys(u).forEach(function (k) { if (k !== 'src') s[k] = u[k]; });
          });
        });
        return { ok: true, by: by };
      }, function () { return { ok: false, by: Object.create(null) }; });
    }
    return ST.then(function (S) {
      if (!S.ok || !CFG.region || ids.every(function (id) { return S.by[id]; })) return S;
      if (!ST_RG) {
        ST_RG = getJson(CFG.region).then(function (rg) {
          (rg.stations || []).forEach(function (s) { if (!S.by[s.id]) S.by[s.id] = s; });
          return S;
        }, function () { return S; });
      }
      return ST_RG;
    });
  }
  // drivers' reports per station (the map's /api/stanice): the last status and when
  function summaries() {
    if (!SUM) SUM = getJson(API + '/stanice').then(function (j) { return (j && j.st) || {}; }, function () { return {}; });
    return SUM;
  }
  function cleanName(n) { return (n || '').replace(/^charge\s*&\s*go\s*[-–:]?\s*/i, '').replace(/^BS\s+(?=gazprom|nis|evoil)/i, '').trim(); }
  function netName(s) { return s.cc ? (s.nn || s.opn || '') : ((CFG.names || {})[s.net] || s.opn || ''); }
  function title(s) { return cleanName(s.n) || netName(s) || (s.a ? s.a.split(',')[0] : T.charger); }
  function power(s) { return s.dc ? 'DC ' + num(s.dc) + ' kW' : s.ac ? 'AC ' + num(s.ac) + ' kW' : ''; }
  // Radi / Prijavljen kvar from a driver's report of the last 30 days or our check; the state chargers' official list
  function chip(s, c) {
    if (s.ps && s.ps.l && !s.ps.l.some(function (l) { return l[2] === 1; })) return ['bad', T.st_off];
    if (c && c.s && c.t && Date.now() / 1000 - c.t < 30 * 86400) return c.s === 'ok' || c.s === 'problem' ? ['ok', T.st_ok] : ['bad', T.st_bad];
    if (s.v && s.v.s === 'prob') return ['bad', T.st_bad];
    return null;
  }
  function mapLink(id) { return LP + '/mapa/#' + encodeURIComponent(id); }

  if (PAGE === 'nalog') nalog();
  else if (PAGE === 'potvrda') potvrda();
  else if (PAGE === 'odjava') odjava();

  // ================================================================ /nalog/
  function nalog() {
    var html = d.documentElement, email = '', optIn = false, timer = null, busy = false, ACC = null;
    var fMail = $('nl-f-mail'), fCode = $('nl-f-code'), fLink = $('nl-f-link'), inMail = $('nl-mail'), inCode = $('nl-code');
    var msgTop = $('nl-msg-top'), msgMail = $('nl-msg-mail'), msgCode = $('nl-msg-code'), msgLink = $('nl-msg-link');

    function view(inside) { html.classList.toggle('nl-in', inside); }
    // which card of the sign-in: 'mail' (the address), 'code' (the six digits) or 'link' (the button of the mail's link)
    function step(which) {
      fMail.hidden = which !== 'mail';
      fCode.hidden = which !== 'code';
      fLink.hidden = which !== 'link';
    }
    // signed out: the form; the server says whether it can send mail at all (RESEND_API_KEY)
    function ready() {
      view(false);
      step('mail');
      api('GET', '/nalog/status').then(function (j) {
        var b = fMail.querySelector('[type=submit]');
        b.disabled = j.status === 200 && j.mail === false;
        if (b.disabled) msg(msgMail, T.err_off);
      });
    }
    // the session ended on the server (expired, signed out on another device, account deleted)
    function lost() {
      dropHint();
      ACC = null;
      ready();
      msg(msgTop, T.err_auth);
    }
    function fail(j) {
      if (j.status === 401) return lost();
      toast(errText(j));
    }

    // ---- start: the one-click link from the mail, a session, or the sign-in form
    var q = new URLSearchParams(location.search), link = q.get('prijava');
    if (link) {
      // the token must not stay in the address bar, the history or a shared link
      history.replaceState(null, '', location.pathname + location.hash);
      linkCard(link);
    } else if (hinted()) {
      api('GET', '/nalog/ja').then(function (j) {
        if (j.ok) return signedIn(j, false);
        if (j.status === 401) dropHint();
        ready();
        if (j.status !== 401) msg(msgTop, errText(j));
      });
    } else ready();

    // ---- the link from the mail: a card with one button. Opening the page spends nothing (mail scanners open links, and
    // some run the scripts too); it only asks which address the link is for. The button signs in.
    function linkCard(token) {
      var who = fLink.querySelector('[data-nl-link]'), btn = fLink.querySelector('[type=submit]');
      view(false);
      step('link');
      api('POST', '/nalog/link', { token: token, peek: true }).then(function (j) {
        if (j.ok) { who.textContent = j.email_masked; return; }
        if (j.status === 400) { ready(); msg(msgTop, T.err_link); return; }   // used or older than 15 minutes
        who.parentNode.hidden = true;                                       // no answer: the button may still work
      });
      fLink.addEventListener('submit', function (e) {
        e.preventDefault();
        if (btn.disabled) return;
        btn.disabled = true;
        msg(msgLink, '');
        api('POST', '/nalog/link', { token: token }).then(function (j) {
          btn.disabled = false;
          if (j.ok) { track('account_sign_in', { how: 'link' }); signedIn(j, true); return; }
          if (j.status === 400) { ready(); msg(msgTop, T.err_link); return; }
          msg(msgLink, errText(j));
        });
      });
    }

    // ---- step 1: the address
    fMail.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = inMail.value.trim();
      if (v.length > 120 || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) { msg(msgMail, T.err_mail); inMail.focus(); return; }
      email = v;
      optIn = !!($('nl-optin') && $('nl-optin').checked);
      sendCode(fMail.querySelector('[type=submit]'), msgMail, function () {
        all('#nl-f-code [data-nl-email]').forEach(function (el) { el.textContent = email; });
        step('code');
        inCode.value = '';
        msg(msgCode, '');
        countdown();
        inCode.focus();
      });
    });
    function sendCode(btn, box, done) {
      if (busy) return;
      busy = true;
      btn.disabled = true;
      msg(box, '');
      msg(msgTop, '');
      afterTyping(function () {
        api('POST', '/nalog/kod', { email: email, lang: LANG, opt_in: optIn, hp: fMail.elements.website.value, t: Date.now() - T0 }).then(function (j) {
          busy = false;
          btn.disabled = false;
          if (j.ok) done(); else msg(box, errText(j));
        });
      });
    }
    // "Pošaljite ponovo" after 60 seconds
    function countdown() {
      var left = 60, b = $('nl-resend'), w = $('nl-wait');
      clearInterval(timer);
      b.disabled = true;
      function tick() {
        if (left <= 0) { clearInterval(timer); b.disabled = false; w.textContent = ''; return; }
        w.textContent = T.wait.replace('{s}', left) + ' ';
        left--;
      }
      tick();
      timer = setInterval(tick, 1000);
    }
    $('nl-resend').addEventListener('click', function () {
      sendCode($('nl-resend'), msgCode, function () { countdown(); inCode.value = ''; inCode.focus(); });
    });
    $('nl-change').addEventListener('click', function () {
      clearInterval(timer);
      step('mail');
      msg(msgCode, '');
      inMail.focus();
      inMail.select();
    });

    // ---- step 2: the code (six digits; pasted "123 456" or "Kod: 123456" works; sent by itself at the sixth digit)
    inCode.setAttribute('aria-describedby', 'nl-code-sent');
    fCode.querySelector('.nl-sent').id = 'nl-code-sent';
    inCode.addEventListener('input', function () {
      var v = inCode.value.replace(/\D/g, '').slice(0, 6);
      if (v !== inCode.value) inCode.value = v;
      if (v.length === 6) submitCode();
    });
    fCode.addEventListener('submit', function (e) { e.preventDefault(); submitCode(); });
    var codeBusy = false;
    function submitCode() {
      var v = inCode.value.replace(/\D/g, ''), btn = fCode.querySelector('[type=submit]');
      if (codeBusy) return;
      if (v.length !== 6) { msg(msgCode, T.err_code); inCode.focus(); return; }
      codeBusy = true;
      btn.disabled = true;
      msg(msgCode, '');
      api('POST', '/nalog/potvrdi', { email: email, code: v }).then(function (j) {
        codeBusy = false;
        btn.disabled = false;
        if (j.ok) { track('account_sign_in', { how: 'code' }); signedIn(j, true); return; }
        msg(msgCode, errText(j));
        if (j.error === 'tries') { clearInterval(timer); $('nl-resend').disabled = false; $('nl-wait').textContent = ''; }
        inCode.focus();
        inCode.select();
      });
    }

    // ---- signed in
    function signedIn(j, fresh) {
      ACC = j;
      clearInterval(timer);
      msg(msgTop, '');
      view(true);
      all('[data-nl-email]').forEach(function (el) { el.textContent = j.user.email; el.classList.remove('nl-sk-t'); });
      $('nl-since').textContent = j.user.created_at ? T.since.replace('{d}', fmtDate(j.user.created_at)) : '';
      $('nl-export').href = API + '/nalog/izvoz';
      // this browser follows the account: "Imam Teslu" for the map, the display currency (assets/valuta.js) and the
      // favourites (syncFavs)
      lsSet('bv:tesla', j.user.tesla ? '1' : '0');
      if (window.bvFxAccount) window.bvFxAccount(j.user);
      syncFavs(j);
      fillCar(j.user);
      fillPregled(j.sub);
      loadReports();
      if (fresh) $('nl-h1').focus();
    }

    // ---- 1. favourites
    // The list of this browser and the account's: kept by the same account (bv:fav-owner) → joined; kept by another
    // account → replaced by this account's, never mixed; kept before any sign-in and holding stations the account does
    // not have → the reader decides (#nl-ask): add them to the account, or not.
    function syncFavs(j) {
      var key = j.user.owner, owner = lsGet('bv:fav-owner'), local = localFavs(), acc = j.favs || [];
      var extra = local.filter(function (x) { return acc.indexOf(x) < 0; });
      if (!owner && extra.length) { renderFavs(acc); askFavs(local, acc, key); return; }
      adoptFavs(owner === key ? uniq(acc.concat(local)).slice(0, 300) : acc.slice(), acc, key);
    }
    function adoptFavs(favs, acc, key) {
      $('nl-ask').hidden = true;
      saveLocalFavs(favs);
      lsSet('bv:fav-owner', key);
      if (!sameSet(favs, acc)) {
        api('POST', '/nalog/omiljeni', { replace: favs }).then(function (r) {
          if (!r.ok) return;
          ACC.favs = r.favs;
          saveLocalFavs(r.favs);
          renderFavs(r.favs);
        });
      }
      renderFavs(favs);
    }
    function askFavs(local, acc, key) {
      var box = $('nl-ask');
      $('nl-ask-t').textContent = (T['fav_ask_' + plural(local.length)] || T.fav_ask_many).replace('{n}', local.length);
      box.hidden = false;
      $('nl-ask-yes').onclick = function () {
        adoptFavs(uniq(acc.concat(local)).slice(0, 300), acc, key);
        toast(T.saved);
        $('nl-fav-h').focus();
      };
      $('nl-ask-no').onclick = function () { adoptFavs(acc.slice(), acc, key); $('nl-fav-h').focus(); };
    }
    function renderFavs(ids) {
      var box = $('nl-favs'), none = $('nl-favs-none');
      d.querySelector('[data-nl-favn]').textContent = ids.length ? '(' + ids.length + ')' : '';
      if (!ids.length) { box.innerHTML = ''; box.hidden = true; none.hidden = false; box.removeAttribute('aria-busy'); return; }
      box.hidden = false;
      none.hidden = true;
      Promise.all([stations(ids), summaries()]).then(function (r) {
        var S = r[0], sum = r[1];
        // a station that left the map is dropped quietly, as on the map
        var gone = S.ok ? ids.filter(function (id) { return !S.by[id]; }) : [];
        if (gone.length) {
          api('POST', '/nalog/omiljeni', { remove: gone }).then(function (j) { if (j.ok) { ACC.favs = j.favs; saveLocalFavs(j.favs); } });
          ids = ids.filter(function (id) { return S.by[id]; });
          d.querySelector('[data-nl-favn]').textContent = ids.length ? '(' + ids.length + ')' : '';
        }
        box.innerHTML = ids.map(function (id) { return favRow(S.by[id] || { id: id, n: T.charger + ' ' + id, c: [] }, sum[id]); }).join('');
        box.removeAttribute('aria-busy');
        if (!ids.length) { box.hidden = true; none.hidden = false; }
      });
    }
    function favRow(s, c) {
      var ch = chip(s, c), sub = [netName(s), power(s)].filter(Boolean).join(' · ');
      return '<div class="nl-st" data-id="' + esc(s.id) + '"><div class="nl-st-t"><b>' + esc(title(s)) + '</b>' + (sub ? '<span>' + esc(sub) + '</span>' : '') + '</div>' +
        (ch ? '<span class="nl-chip ' + ch[0] + '">' + esc(ch[1]) + '</span>' : '<span class="nl-chip-no"></span>') +
        '<a class="btn sm" href="' + esc(mapLink(s.id)) + '">' + esc(T.on_map) + '</a>' +
        '<button class="nl-star" type="button" aria-label="' + esc(T.fav_del + ': ' + title(s)) + '" title="' + esc(T.fav_del) + '">' + STAR + '</button></div>';
    }
    $('nl-favs').addEventListener('click', function (e) {
      var b = e.target.closest && e.target.closest('.nl-star');
      if (!b) return;
      var row = b.closest('.nl-st'), id = row.getAttribute('data-id');
      b.disabled = true;
      api('POST', '/nalog/omiljeni', { remove: [id] }).then(function (j) {
        if (!j.ok) { b.disabled = false; return fail(j); }
        ACC.favs = j.favs;
        saveLocalFavs(localFavs().filter(function (x) { return x !== id; }));
        var next = row.nextElementSibling || row.previousElementSibling;
        row.remove();
        d.querySelector('[data-nl-favn]').textContent = j.favs.length ? '(' + j.favs.length + ')' : '';
        if (!j.favs.length) { $('nl-favs').hidden = true; $('nl-favs-none').hidden = false; }
        (next && next.querySelector('.nl-star') || $('nl-fav-h')).focus();
        track('favourite_remove', { station: id, total: j.favs.length, where: 'nalog' });
      });
    });

    // ---- 2. the car
    var fCar = $('nl-f-car'), model = $('nl-model');
    function fillCar(u) {
      var car = u.car || '', known = !!car && all('option', model).some(function (o) { return o.value === car && o.value !== '*'; });
      model.value = !car ? '' : known ? car : '*';
      $('nl-other').value = known ? '' : car;
      $('nl-other-w').hidden = model.value !== '*';
      all('[name=dc]', fCar).forEach(function (r) { r.checked = r.value === u.dc; });
      $('nl-tesla').checked = !!u.tesla;
      $('nl-city').value = u.city || '';
    }
    model.addEventListener('change', function () {
      $('nl-other-w').hidden = model.value !== '*';
      if (model.value === '*') $('nl-other').focus();
    });
    fCar.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = fCar.querySelector('[type=submit]'), dc = fCar.querySelector('[name=dc]:checked');
      var car = model.value === '*' ? $('nl-other').value.trim() : model.value;
      btn.disabled = true;
      api('POST', '/nalog/podesavanja', { car: car.slice(0, 80), dc: dc ? dc.value : '', tesla: $('nl-tesla').checked, city: $('nl-city').value }).then(function (j) {
        btn.disabled = false;
        if (!j.ok) return fail(j);
        ACC.user = j.user;
        lsSet('bv:tesla', j.user.tesla ? '1' : '0');
        fillCar(j.user);
        toast(T.saved);
        track('account_settings', { car: !!j.user.car, dc: j.user.dc || '', tesla: !!j.user.tesla, city: j.user.city || '' });
      });
    });

    // ---- 3. the newsletter (only with site.json → pregled.enabled)
    var pg = d.querySelector('.nl-s-pg'), pgOn = $('nl-pg-on');
    function fillPregled(sub) {
      if (!pg) return;
      var st = sub ? sub.status : 'off';
      pgOn.checked = st === 'on';
      shows($('nl-pg-st'), 'data-st', st);
      var topics = sub && sub.topics.length ? sub.topics : ['vesti', 'cene', 'punjaci'];
      all('#nl-pg-topics input', pg).forEach(function (c) { c.checked = topics.indexOf(c.value) >= 0; });
      all('[name=freq]', pg).forEach(function (r) { r.checked = r.value === ((sub && sub.freq) || 'w'); });
      $('nl-pg-lang').value = (sub && sub.lang) || (ACC && ACC.user.lang) || LANG;
      all('fieldset, select', pg).forEach(function (el) { el.disabled = !pgOn.checked; });
    }
    if (pg) {
      pg.addEventListener('change', function (e) {
        var topics = topicsOf($('nl-pg-topics'));
        if (!topics.length) { e.target.checked = true; toast(T.err_topics); return; }
        var fr = pg.querySelector('[name=freq]:checked');
        api('POST', '/nalog/pregled', { on: pgOn.checked, topics: topics, freq: fr ? fr.value : 'w', lang: $('nl-pg-lang').value }).then(function (j) {
          if (!j.ok) { fillPregled(ACC.sub); return fail(j); }
          if (e.target === pgOn) track(pgOn.checked ? 'newsletter_on' : 'newsletter_off', { where: 'nalog' });
          ACC.sub = j.sub;
          fillPregled(j.sub);
          toast(T.saved);
        });
      });
    }

    // ---- 4. reports and photos sent while signed in
    function loadReports() {
      var box = $('nl-ci'), none = $('nl-ci-none');
      api('GET', '/nalog/doprinosi').then(function (j) {
        if (!j.ok) { box.removeAttribute('aria-busy'); box.innerHTML = ''; return j.status === 401 ? lost() : msg(none, errText(j)); }
        var items = (j.checkins || []).map(function (c) { return { st: c.st, at: c.at, c: c }; })
          .concat((j.photos || []).map(function (p) { return { st: p.st, at: p.at, p: p }; }))
          .sort(function (a, b) { return b.at - a.at; }).slice(0, 60);
        if (!items.length) { box.innerHTML = ''; box.hidden = true; none.hidden = false; box.removeAttribute('aria-busy'); return; }
        stations(items.map(function (x) { return x.st; })).then(function (S) {
          box.hidden = false;
          none.hidden = true;
          box.innerHTML = items.map(function (it) { return reportRow(it, S.by[it.st]); }).join('');
          box.removeAttribute('aria-busy');
        });
      });
    }
    function checkState(cs) { return cs === 'ok' ? ['ok', T.cs_ok] : cs === 'pending' ? ['wait', T.cs_pending] : ['bad', T.cs_hidden]; }
    function stars(r) { return '<span class="sb5" role="img" aria-label="' + esc(T.stars.replace('{r}', r)) + '">' + '★★★★★'.slice(0, r) + '<i>' + '★★★★★'.slice(r) + '</i></span>'; }
    function reportRow(it, s) {
      var name = s ? title(s) : T.gone, what, state = null;
      if (it.c) {
        what = '<span class="rv-s ' + esc(it.c.s) + '">' + esc(T['ci_' + it.c.s] || it.c.s) + '</span>' + (it.c.r ? stars(it.c.r) : '');
        if (it.c.cs && it.c.cs !== 'none') state = checkState(it.c.cs);
      } else {
        what = '<span class="rv-s">' + esc(T.photo) + '</span>';
        state = checkState(it.p.status === 'no' ? 'hidden' : it.p.status);
      }
      return '<div class="nl-ci"><div class="nl-st-t">' + (s ? '<a href="' + esc(mapLink(it.st)) + '"><b>' + esc(name) + '</b></a>' : '<b>' + esc(name) + '</b>') +
        '<span class="nl-ci-m">' + what + '<time datetime="' + new Date(it.at * 1000).toISOString() + '">' + fmtDate(it.at) + '</time></span></div>' +
        (state ? '<span class="nl-chip ' + state[0] + '">' + esc(state[1]) + '</span>' : '') + '</div>';
    }

    // ---- 5. the account: sign out (here or everywhere), delete
    function signOut(everywhere) {
      api('POST', '/nalog/odjava', everywhere ? { all: true } : {}).then(function (j) {
        if (!j.ok && j.status !== 401) return toast(errText(j));
        dropHint();
        forgetLocal();
        ACC = null;
        ready();
        toast(T.signed_out);
        $('nl-h1').focus();
        track('account_sign_out', { all: !!everywhere });
      });
    }
    $('nl-out').addEventListener('click', function () { signOut(false); });
    $('nl-out-all').addEventListener('click', function () { signOut(true); });
    var dlg = $('nl-dlg');
    function closeDlg() { if (dlg.close) dlg.close(); else dlg.removeAttribute('open'); }
    $('nl-del').addEventListener('click', function () {
      if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
      $('nl-del-no').focus();
    });
    $('nl-del-no').addEventListener('click', function () { closeDlg(); $('nl-del').focus(); });
    $('nl-del-yes').addEventListener('click', function () {
      var b = this;
      b.disabled = true;
      api('POST', '/nalog/obrisi', { confirm: 'OBRISI' }).then(function (j) {
        b.disabled = false;
        closeDlg();
        if (!j.ok) return fail(j);
        dropHint();
        forgetLocal();
        ACC = null;
        ready();
        toast(T.deleted);
        $('nl-h1').focus();
        track('account_delete', {});
      });
    });
  }

  // The token of a newsletter link (?t=…, and &teme=1 on /pregled/odjava/): read once, then taken out of the address
  // bar, so it is not in the history, a shared or copied link, a screenshot or the analytics. It stays for this tab
  // (sessionStorage), so a reload still works.
  function linkToken() {
    var q = new URLSearchParams(location.search), t = q.get('t') || '', teme = q.get('teme') === '1';
    if (q.has('t')) {
      try { sessionStorage.setItem('bv:pg-t', t); } catch (e) { /* private mode: this page view only */ }
      history.replaceState(null, '', location.pathname + location.hash);
    } else {
      try { t = sessionStorage.getItem('bv:pg-t') || ''; } catch (e) { t = ''; }
    }
    return { t: /^[0-9a-f]{32}$/.test(t) ? t : '', teme: teme };
  }

  // ================================================================ /pregled/potvrda/?t=… (the link in the confirmation mail)
  // Opening the page only reads the state (mail scanners open links, and some run the scripts too); the sign-up is
  // confirmed by the button "Potvrđujem prijavu".
  function potvrda() {
    var box = d.querySelector('.pg-state'), t = linkToken().t, prefs = box.querySelector('[data-nl-prefs]');
    if (!t) return shows(box, 'data-s', 'bad');
    function done() { shows(box, 'data-s', 'ok'); }
    // "Izaberite teme i učestalost": the token goes into the address only at the click (that page takes it out again)
    if (prefs) prefs.addEventListener('click', function (e) {
      e.preventDefault();
      location.href = prefs.getAttribute('href').split('?')[0] + '?t=' + t + '&teme=1';
    });
    api('GET', '/posta/stanje?t=' + t).then(function (j) {
      if (!j.ok) {
        if (j.status === 404) return shows(box, 'data-s', 'bad');
        shows(box, 'data-s', 'err');
        return msg(box.querySelector('[data-s=err]'), errText(j));
      }
      if (j.state === 'off') return shows(box, 'data-s', 'bad');            // unsubscribed since: sign up again
      if (j.state === 'on') return done();                                  // confirmed already
      all('[data-nl-email]', box).forEach(function (el) { el.textContent = j.email_masked; });
      shows(box, 'data-s', 'ask');
    });
    $('pg-yes').addEventListener('click', function () {
      var b = this;
      b.disabled = true;
      api('POST', '/posta/potvrdi', { token: t }).then(function (j) {
        b.disabled = false;
        if (j.ok) { done(); track('newsletter_confirm', {}); return; }
        if (j.status === 400 || j.status === 404) return shows(box, 'data-s', 'bad');
        toast(errText(j));
      });
    });
  }

  // ================================================================ /pregled/odjava/?t=… (unsubscribe, monthly, topics)
  function odjava() {
    var box = d.querySelector('.pg-state'), lt = linkToken(), t = lt.t, form = $('pg-f-teme');
    if (!t) return shows(box, 'data-s', 'bad');
    api('GET', '/posta/stanje?t=' + t).then(function (j) {
      if (!j.ok) {
        if (j.status === 404) return shows(box, 'data-s', 'bad');
        shows(box, 'data-s', 'err');
        return msg(box.querySelector('[data-s=err]'), errText(j));
      }
      show(j);
      if (lt.teme && j.state !== 'off') {                                  // the subscription's state, not the HTTP status
        $('pg-teme').open = true;
        $('pg-teme').scrollIntoView({ block: 'start' });
      }
    });
    function show(j) {
      all('[data-nl-email]', box).forEach(function (el) { el.textContent = j.email_masked; });
      if (j.state === 'off') return shows(box, 'data-s', 'off');
      shows(box, 'data-s', 'on');
      shows(box.querySelector('.pg-st'), 'data-st', j.state === 'pending' ? 'pending' : j.freq === 'm' ? 'm' : 'on');
      $('pg-month').hidden = j.freq === 'm';
      all('input[type=checkbox]', form).forEach(function (c) { c.checked = j.topics.indexOf(c.value) >= 0; });
      all('[name=freq]', form).forEach(function (r) { r.checked = r.value === j.freq; });
      $('pg-lang').value = j.lang || LANG;
    }
    $('pg-off').addEventListener('click', function () {
      var b = this;
      b.disabled = true;
      api('POST', '/posta/odjava', { token: t }).then(function (j) {
        b.disabled = false;
        if (!j.ok) return toast(errText(j));
        shows(box, 'data-s', 'off');
        $('pg-again').focus();
        track('newsletter_off', { where: 'odjava' });
      });
    });
    $('pg-month').addEventListener('click', function () {
      api('POST', '/posta/podesavanja', { token: t, freq: 'm' }).then(function (j) {
        if (!j.ok) return toast(errText(j));
        show(j);
        toast(T.monthly);
        track('newsletter_monthly', {});
      });
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var topics = topicsOf(form), fr = form.querySelector('[name=freq]:checked');
      if (!topics.length) return toast(T.err_topics);
      api('POST', '/posta/podesavanja', { token: t, topics: topics, freq: fr ? fr.value : 'w', lang: $('pg-lang').value }).then(function (j) {
        if (!j.ok) return toast(errText(j));
        show(j);
        toast(T.saved);
      });
    });
    // "Predomislili ste se? Prijavite se ponovo": a new confirmation mail to the same address
    $('pg-again').addEventListener('click', function () {
      var b = this;
      b.disabled = true;
      afterTyping(function () {
        api('POST', '/posta/prijava', { token: t, lang: LANG, src: location.pathname.slice(0, 80), t: Date.now() - T0 }).then(function (j) {
          b.disabled = false;
          if (!j.ok) return toast(errText(j));
          shows(box, 'data-s', 'again');
          track('newsletter_signup', { src: 'odjava' });
        });
      });
    });
  }
})();
