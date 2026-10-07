/* BlokVolt — display currency (RSD / EUR / USD). docs/RUNBOOK.md 3.29, VALUTA_SPEC_2026-10-06.
   The core is /assets/fx.js (FxCore, shared with evolako.rs — never edit one copy only). This file: the instance, the
   switcher next to the language menu (in the burger menu on narrow phones), the price markup of the page (data-rsd, written
   by build.py / scripts/valuta.py and by the calculators), the footnote, and the account of "Moj BlokVolt".
   Default RSD always: with RSD nothing on the page changes. EUR / USD only by the reader's choice (switcher or ?cur=),
   kept in localStorage 'bv:cur' and, for a signed-in reader, in the account. The rate: /api/kurs (the worker), else the
   constants in fx.js. Every converted sum is a reference sum: "≈ 0,49 €/kWh · 58 RSD/kWh".
   Pages: window.bvFx is the instance (map.js uses it); window.bvFxAccount(user) is called by nalog.js after sign-in. */
(function () {
  var d = document;
  if (!window.FxCore || window.bvFx) return;
  var LANG = (d.documentElement.lang || 'sr').slice(0, 2);
  LANG = LANG === 'en' || LANG === 'ru' ? LANG : 'sr';

  // texts: SR master in the page (<script id="bv-fx-i18n">), EN/RU from the translation memory (scripts/i18n.py)
  var S = null;
  try { S = JSON.parse(d.getElementById('bv-fx-i18n').textContent); } catch (e) { S = null; }
  if (S) {
    var TX = window.FxCore.TX;
    if (S.label) TX.label[LANG] = S.label;
    if (S.note) TX.note.blokvolt[LANG] = S.note;
    if (S.title) TX.title[LANG] = S.title;
    if (S.RSD && S.EUR && S.USD) TX.names[LANG] = { RSD: S.RSD, EUR: S.EUR, USD: S.USD };
  }

  var signedIn = function () { return /(?:^|;\s*)bv_in=1(?:;|$)/.test(d.cookie); };
  var applying = false;          // the account's value is being applied: not a choice to send back
  // numLang 'au' (only scan reads it, and only the map scans): the map writes its own numbers in the page's format
  // ("1,530 RSD" on /en/, "1 530" on /ru/) next to price-data texts in Serbian format ("1.000 RSD/sat"); a separator
  // followed by exactly three digits is thousands, by one or two a decimal comma or point (no RSD price has 3 decimals)
  var fx = window.bvFx = window.FxCore.create({
    brand: 'blokvolt', key: 'bv:cur', ratesUrl: '/api/kurs', numLang: 'au',
    lang: function () { return d.documentElement.lang; },
    track: function (name, props) { if (!applying && window.bvTrack) window.bvTrack(name, props); }
  });
  var cur = fx.get();

  // ---- the switcher: <span class="hd-cur" data-fx-slot> in the header, <div class="hd-cur-m" data-fx-slot="m"> in the menu
  [].forEach.call(d.querySelectorAll('[data-fx-slot]'), function (slot) {
    var sel = fx.switcher({ className: 'fx-sel' });
    if (slot.getAttribute('data-fx-slot') === 'm') {
      var id = 'fx-sel-m';
      sel.id = id;
      var lab = slot.querySelector('label');
      if (lab) lab.setAttribute('for', id);
    }
    slot.appendChild(sel);
    slot.hidden = false;
  });

  // ---- the footnote: once, at the end of the page's main content, only with EUR / USD and only where sums are converted
  var main = d.getElementById('main');
  var note = null;
  function hasSums() { return !!(main && main.querySelector('[data-rsd],[data-rsd-lo],[data-fx-page]')); }
  function footnote() {
    var show = fx.get() !== 'RSD' && hasSums();
    if (!show) { if (note) note.hidden = true; return; }
    if (!note) {
      note = d.createElement('p');
      note.className = 'note fx-note';
      note.setAttribute('data-fx-note', '');
      var upd = main.querySelectorAll('p.upd');
      var anchor = upd.length ? upd[upd.length - 1] : null;
      if (anchor) anchor.parentNode.insertBefore(note, anchor);
      else (main.querySelector('.map-below') || main.querySelector('.wrap.main') || main).appendChild(note);
    }
    note.textContent = fx.note();
    note.hidden = false;
  }

  function paint() {
    fx.render(d);
    footnote();
  }
  paint();
  fx.on(function (c) {
    var changed = c !== cur;
    cur = c;
    paint();
    // a signed-in reader keeps the choice in the account (the same place as the car and "Imam Teslu"); fire and forget
    if (changed && !applying && signedIn()) {
      fetch('/api/nalog/podesavanja', { method: 'POST', credentials: 'same-origin', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ valuta: c }) }).catch(function () {});
    }
  });

  // ---- "Moj BlokVolt": on sign-in (and whenever /nalog/ loads the account) the account's choice is applied; an account
  // that never chose takes this browser's choice when it is not RSD
  window.bvFxAccount = function (user) {
    if (!user) return;
    var v = String(user.valuta || '').toUpperCase();
    if (v === 'RSD' || v === 'EUR' || v === 'USD') {
      if (v !== fx.get()) { applying = true; try { fx.set(v); } finally { applying = false; } }
    } else if (fx.get() !== 'RSD' && signedIn()) {
      fetch('/api/nalog/podesavanja', { method: 'POST', credentials: 'same-origin', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ valuta: fx.get() }) }).catch(function () {});
    }
  };
})();
