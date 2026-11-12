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
