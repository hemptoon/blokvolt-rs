/* BlokVolt — widgets for other sites (/embed/…, RUNBOOK 3.40). The map itself is map.js (cfg.embed); this file only
   runs the narrow layout's list sheet and names the host site in the links back to blokvolt.rs (utm_source).
   Nothing is stored and nothing is sent from here. */
(function () {
  'use strict';
  var d = document, body = d.body;
  var host = '';
  try { host = d.referrer ? new URL(d.referrer).hostname.replace(/^www\./, '').slice(0, 60) : ''; } catch (e) { host = ''; }
  // the signature and attribution links say which site the reader came from
  [].forEach.call(d.querySelectorAll('[data-emb-full]'), function (a) {
    if (host) a.href = a.href.replace('utm_source=vidzet', 'utm_source=' + encodeURIComponent(host));
  });

  var btn = d.querySelector('[data-emb-list]'), sheet = d.getElementById('emb-sheet'), list = d.getElementById('mlist');
  if (!btn || !sheet) return;
  var narrow = window.matchMedia('(max-width: 699.98px)');
  function setOpen(on, focus) {
    body.classList.toggle('emb-list-open', on);
    btn.setAttribute('aria-expanded', on ? 'true' : 'false');
    if (on && focus) { var x = sheet.querySelector('[data-emb-close]'); if (x) x.focus({ preventScroll: true }); }
    if (!on && focus) btn.focus({ preventScroll: true });
  }
  btn.addEventListener('click', function () { setOpen(!body.classList.contains('emb-list-open'), true); });
  sheet.querySelector('[data-emb-close]').addEventListener('click', function () { setOpen(false, true); });
  // a charger picked in the list: its card replaces the sheet (map.js opens the card)
  if (list) list.addEventListener('click', function (e) { if (narrow.matches && e.target.closest('.st')) setOpen(false, false); });
  d.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && body.classList.contains('emb-list-open') && !d.querySelector('.card-ov.is-open')) setOpen(false, true);
  });
  // the wide layout always shows the list
  narrow.addEventListener('change', function () { if (!narrow.matches) setOpen(false, false); });

  // "Lista · 23": the number of chargers the list holds now (the first number of map.js's count line)
  var count = d.getElementById('mcount'), lbl = btn.querySelector('span');
  if (count && lbl && window.MutationObserver) {
    var base = lbl.textContent;
    new MutationObserver(function () {
      var m = (count.textContent || '').match(/\d[\d.,\s]*/);
      lbl.innerHTML = '';
      lbl.appendChild(d.createTextNode(base));
      if (m) { var n = d.createElement('span'); n.className = 'n'; n.textContent = ' ' + m[0].trim(); lbl.appendChild(n); }
    }).observe(count, { childList: true, characterData: true, subtree: true });
  }
})();
