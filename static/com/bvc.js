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
