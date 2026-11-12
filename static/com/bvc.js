/* THEME (12.11.2026): the light/dark switch of every .com page (templates/com2/_header.html, [data-theme-sw]). The theme itself
   is set before the first paint by the inline script of base.html (html[data-theme], localStorage bv_theme, dark by default);
   here: the switches show it, a press changes it and remembers it, and the page hears it ("bv-theme" on document: the map). */
(function () {
  var d = document, H = d.documentElement, K = 'bv_theme';
  function cur() { return H.getAttribute('data-theme') === 'light' ? 'light' : 'dark'; }
  function show() {
    var on = cur() === 'dark' ? 'true' : 'false', b = d.querySelectorAll('[data-theme-sw]'), i;
    for (i = 0; i < b.length; i++) b[i].setAttribute('aria-checked', on);
  }
  function set(t, keep) {
    t = t === 'light' ? 'light' : 'dark';
    if (keep !== false) { try { localStorage.setItem(K, t); } catch (e) {} }
    if (t === cur()) { show(); return; }
    H.setAttribute('data-theme', t);
    var m = d.querySelector('meta[name=theme-color]');
    if (m) m.content = t === 'light' ? '#FFFFFF' : '#0B0F17';
    show();
    try { d.dispatchEvent(new CustomEvent('bv-theme', { detail: t })); } catch (e) {}
  }
  window.bvTheme = { get: cur, set: set };
  d.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-theme-sw]');
    if (b) set(cur() === 'dark' ? 'light' : 'dark');
  });
  // another tab changed it: follow
  addEventListener('storage', function (e) { if (e.key === K && (e.newValue === 'light' || e.newValue === 'dark')) set(e.newValue, false); });
  show();
})();
/* POLISH (12.11.2026): the phone menu of the header (bv.js opens it: .hd-nav.is-open, burger aria-expanded) — while it is open
   the page under it does not scroll, the focus goes into it and stays between the menu and the burger, Esc, a tap outside
   and the browser's Back close it (Back does not leave the page). bv.js is shared with blokvolt.rs and stays as it is. */
(function () {
  var d = document, H = d.documentElement, nav = d.querySelector('.hd-nav'), bur = d.querySelector('.burger');
  if (!nav || !bur || !window.MutationObserver) return;
  var pushed = false, byPop = false;
  function isOpen() { return bur.getAttribute('aria-expanded') === 'true'; }
  function items() { return [].filter.call(nav.querySelectorAll('a[href],button'), function (x) { return x.offsetParent !== null; }); }
  function close() { if (isOpen()) bur.click(); }
  new MutationObserver(function () {
    if (isOpen()) {
      H.classList.add('bv-menu-open');
      var it = items(); if (it[0]) it[0].focus({ preventScroll: true });
      try { history.pushState({ bvMenu: 1 }, ''); pushed = true; } catch (e) {}
    } else {
      H.classList.remove('bv-menu-open');
      if (pushed && !byPop) { pushed = false; try { if (history.state && history.state.bvMenu) history.back(); } catch (e) {} }
      pushed = false; byPop = false;
    }
  }).observe(bur, { attributes: true, attributeFilter: ['aria-expanded'] });
  addEventListener('popstate', function () { if (isOpen()) { byPop = true; close(); } });
  nav.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('a[href]')) { pushed = false; } });
  d.addEventListener('keydown', function (e) {
    if (!isOpen() || e.key !== 'Tab') return;
    var it = items(), all = it.concat([bur]), i = all.indexOf(d.activeElement);
    if (i < 0) { e.preventDefault(); all[0].focus(); return; }
    var n = e.shiftKey ? (i - 1 + all.length) % all.length : (i + 1) % all.length;
    e.preventDefault(); all[n].focus();
  });
  d.addEventListener('click', function (e) { if (isOpen() && !e.target.closest('.hd')) close(); }, true);
})();
/* POLISH (12.11.2026): a table or chart wider than the screen says so — the right edge fades and "↔" shows above it until the
   reader has scrolled to the end (com.css .tw-more / .tw-end / .tw-hint). */
(function () {
  var d = document, box = d.querySelectorAll('.tw,.wp-fig');
  if (!box.length) return;
  function mark(b) {
    var more = b.scrollWidth > b.clientWidth + 2, end = b.scrollLeft + b.clientWidth >= b.scrollWidth - 4;
    b.classList.toggle('tw-more', more); b.classList.toggle('tw-end', more && end);
    var h = b.previousElementSibling;
    if (more && !(h && h.classList.contains('tw-hint'))) {
      h = d.createElement('div'); h.className = 'tw-hint'; h.setAttribute('aria-hidden', 'true'); h.innerHTML = '<span>↔</span>';
      b.parentNode.insertBefore(h, b);
    }
    if (h && h.classList.contains('tw-hint')) h.hidden = !more || end;
  }
  [].forEach.call(box, function (b) { mark(b); b.addEventListener('scroll', function () { mark(b); }, { passive: true }); });
  var t = 0;
  addEventListener('resize', function () { clearTimeout(t); t = setTimeout(function () { [].forEach.call(box, mark); }, 150); });
})();
/* POLISH (12.11.2026): the world footer (templates/com2/_wfooter.html). Phones (< 720 px): the four groups of links are
   accordions, closed (without JS they stay open); wider: plain columns that do not fold. The word "volt" gets its charger
   lights (ft-lights.webp) only when the footer comes within ~800 px of the screen, after the picture has loaded — before that
   and without it the letters are solid lime. */
(function () {
  var d = document, f = d.querySelector('.wft') || d.querySelector('.wft-loc');
  if (!f) return;
  var cols = f.querySelectorAll('.wft-col'), mq = window.matchMedia ? matchMedia('(max-width:719px)') : null, i;
  function lay() {
    var narrow = mq && mq.matches;
    for (i = 0; i < cols.length; i++) {
      if (narrow) cols[i].removeAttribute('open'); else cols[i].setAttribute('open', '');
      var s = cols[i].querySelector('summary');
      if (s) { if (narrow) s.removeAttribute('tabindex'); else s.setAttribute('tabindex', '-1'); }
    }
  }
  lay();
  if (mq) { if (mq.addEventListener) mq.addEventListener('change', lay); else if (mq.addListener) mq.addListener(lay); }
  f.addEventListener('click', function (e) {
    var s = e.target.closest && e.target.closest('.wft-col>summary');
    if (s && !(mq && mq.matches)) e.preventDefault();
  });
  // the language list closes on Esc and on a click elsewhere
  var lang = f.querySelector('.wft-lang');
  if (lang) {
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && lang.open) { lang.open = false; var s = lang.querySelector('summary'); if (s) s.focus(); } });
    d.addEventListener('click', function (e) { if (lang.open && !lang.contains(e.target)) lang.open = false; });
  }
  var w = f.querySelector('.wft-word[data-lights]');
  if (!w || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (en) {
    if (!en[0].isIntersecting) return;
    io.disconnect();
    var url = w.getAttribute('data-lights'), img = new Image();
    img.onload = function () { w.style.setProperty('--wft-lights', 'url("' + url + '")'); w.classList.add('is-lit'); };
    img.src = url;
  }, { rootMargin: '800px 0px' });
  io.observe(w);
})();
/* blokvolt.com visit counter, as on .rs (RUNBOOK 3.16); ?tim=1/0 = team */
(function () {
  try {
  var L = location, h = L.hostname, s = L.search, K = 'evo_tim', t = 0, r = '';
  if (!/^(www\.)?blokvolt\.com$/.test(h) || navigator.webdriver || !window.fetch) return;
  try {
    if (/[?&]tim=1(&|$)/.test(s)) localStorage.setItem(K, '1');
    if (/[?&]tim=0(&|$)/.test(s)) localStorage.removeItem(K);
    t = localStorage.getItem(K) ? 1 : 0;
  } catch (e) {}
  try { r = document.referrer ? new URL(document.referrer).hostname : ''; } catch (e) {}
  var q = new URLSearchParams(s), g = function (k) { return (q.get(k) || '').slice(0, 60); };
  fetch('https://evolako-bot.mr-smekhov.workers.dev/s/p', { method: 'POST', keepalive: true, mode: 'no-cors',
    credentials: 'omit', body: JSON.stringify({ h: h, p: L.pathname, r: r, t: t, us: g('utm_source'),
    um: g('utm_medium'), uc: g('utm_campaign'), l: (document.documentElement.lang || '').slice(0, 2) }) })
    .catch(function () {});
  } catch (e) {}
})();
