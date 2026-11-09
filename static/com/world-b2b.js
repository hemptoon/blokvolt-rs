// G10 "Data for business" (blokvolt.com): the request form. Posts to blokvolt.rs /api/zahtev (kind "b2b") as a CORS
// simple request (text/plain, no preflight); data-api="" (previews) = demo mode, nothing is sent.
(function () {
  var f = document.querySelector('form[data-b2b-form]');
  if (!f) return;
  var t0 = Date.now(), api = f.getAttribute('data-api') || '';
  function show(cls) { [].forEach.call(f.querySelectorAll('.f-msg'), function (m) { m.hidden = !m.classList.contains(cls); }); }
  f.addEventListener('submit', function (e) {
    e.preventDefault();
    var bad = [].filter.call(f.querySelectorAll('[required]'), function (el) {
      return el.type === 'checkbox' ? !el.checked : el.type === 'email' ? !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim()) : !el.value.trim();
    });
    if (bad.length) { show('f-need'); bad[0].focus(); return; }
    var data = {}, email = '';
    [].forEach.call(f.elements, function (el) {
      if (!el.name || el.name === 'website') return;
      if (el.type === 'checkbox') { if (el.checked) data[el.name] = true; return; }
      if (el.name === 'email') { email = el.value.trim(); return; }
      if (el.value.trim()) data[el.name] = el.value.trim();
    });
    data.jezik = (document.documentElement.lang || 'en').slice(0, 2);
    data.sajt = location.host;
    if (!api) { show('f-demo'); return; }
    var btn = f.querySelector('[type=submit]');
    btn.disabled = true;
    fetch(api, { method: 'POST', mode: 'cors', headers: { 'content-type': 'text/plain;charset=UTF-8' },
      body: JSON.stringify({ kind: 'b2b', slug: location.pathname.slice(0, 80), data: data, email: email,
        hp: f.elements.website ? f.elements.website.value : '', t: Date.now() - t0 }) })
      .then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }, function () { return { ok: false, status: r.status }; }); })
      .then(function (j) {
        btn.disabled = false;
        if (j.ok) { show('f-ok'); f.reset(); btn.hidden = true; } else show(j.status === 429 ? 'f-limit' : 'f-err');
      }, function () { btn.disabled = false; show('f-err'); });
  });
})();
