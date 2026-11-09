/* BlokVolt — world widget configurator (/map-for-your-site/ …) and the "Request access" form of /developers/ (G5,
   RUNBOOK 3.41). The configurator only builds an address and an <iframe> code; nothing is stored or sent from it.
   The request form posts to data-api (the blokvolt.rs worker, /api/svet/zahtev); empty data-api = preview (demo). */
(function () {
  'use strict';
  var d = document;
  // ---------------------------------------------------------------- configurator
  var cfgEl = d.getElementById('wz-cfg');
  if (cfgEl) {
    var C = JSON.parse(cfgEl.textContent), f = d.getElementById('wz-form'), fr = d.getElementById('wz-frame');
    var code = d.getElementById('wz-code'), ok = d.getElementById('wz-ok'), bad = d.getElementById('wz-vbad');
    var esc = function (s) { return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); };
    // a pasted link of the full map (any language) gives grad / id-free filters and the #z/lat/lon view
    var mapPaths = Object.keys(C.map).map(function (k) { return C.map[k]; });
    function fromView(v) {
      if (!v) return { ok: true };
      var u;
      try { u = new URL(v, C.site); } catch (e) { return { ok: false }; }
      var site = new URL(C.site);
      var sameHost = u.hostname.replace(/^www\./, '') === site.hostname.replace(/^www\./, '') || /\.pages\.dev$/.test(u.hostname) || u.hostname === location.hostname;
      if (!sameHost || mapPaths.indexOf(u.pathname) < 0) return { ok: false };
      var g = (u.searchParams.get('grad') || '').replace(/\D/g, ''), z = (u.searchParams.get('zemlja') || '').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2);
      var h = /^#\d+(\.\d+)?\/-?\d+(\.\d+)?\/-?\d+(\.\d+)?$/.test(u.hash) ? u.hash : '';
      return { ok: true, grad: g, zemlja: z, hash: h };
    }
    function build() {
      var fd = new FormData(f), lang = fd.get('lang') || C.lang, q = [];
      var view = fromView(String(fd.get('view') || '').trim());
      bad.hidden = view.ok;
      var zemlja = fd.get('zemlja') || view.zemlja || '';
      if (zemlja) q.push('zemlja=' + encodeURIComponent(zemlja));
      if (view.grad) q.push('grad=' + view.grad);
      if (fd.get('mreza')) q.push('mreza=' + encodeURIComponent(fd.get('mreza')));
      var sn = fd.getAll('snaga');
      if (sn.length && sn.length < 4) q.push('snaga=' + sn.join(','));
      if (fd.get('tema')) q.push('tema=' + fd.get('tema'));
      var path = C.embed[lang] + (q.length ? '?' + q.join('&') : '') + (view.hash || '');
      var h = Math.max(300, Math.min(1200, parseInt(fd.get('h'), 10) || 520));
      var src = C.site + path, title = C.frame_title[lang];
      code.value = '<iframe src="' + esc(src) + '" title="' + esc(title) + '" width="100%" height="' + h + '" style="border:0;max-width:100%" loading="lazy" allow="geolocation"></iframe>\n' +
        '<p style="font:12px/1.4 sans-serif;margin:4px 0 0">' + esc(C.src[lang]) + ' <a href="' + esc(C.site + C.map[lang]) + '">' + esc(C.link[lang]) + '</a></p>';
      // the preview loads from this site (the same page on a preview host), not from the production address
      if (fr.getAttribute('src') !== path) fr.setAttribute('src', path);
      fr.style.height = h + 'px';
      ok.textContent = '';
    }
    var tm = 0;
    f.addEventListener('input', function () { clearTimeout(tm); tm = setTimeout(build, 250); });
    f.addEventListener('change', build);
    f.addEventListener('submit', function (e) { e.preventDefault(); });
    // at least one power class stays on
    f.addEventListener('click', function (e) {
      var c = e.target.closest('input[name=snaga]');
      if (c && !c.checked && !f.querySelectorAll('input[name=snaga]:checked').length) c.checked = true;
    });
    d.getElementById('wz-copy').addEventListener('click', function () {
      var done = function () { ok.textContent = C.copied; };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(code.value).then(done, function () { code.select(); });
      else { code.select(); try { d.execCommand('copy'); done(); } catch (e) { /* the text stays selected */ } }
    });
    build();
  }
  // ---------------------------------------------------------------- request form
  var rf = d.getElementById('dv-form');
  if (rf) {
    var t0 = Date.now(), out = d.getElementById('dv-msg');
    rf.addEventListener('submit', function (e) {
      e.preventDefault();
      var api = rf.getAttribute('data-api'), fd = new FormData(rf);
      var email = String(fd.get('email') || '').trim(), msg = String(fd.get('poruka') || '').trim();
      if (!email || !msg || !rf.elements.email.checkValidity()) { out.textContent = rf.getAttribute('data-need'); return; }
      if (!api) { out.textContent = rf.getAttribute('data-demo'); return; }
      var btn = rf.querySelector('button[type=submit]');
      btn.disabled = true;
      fetch(api, { method: 'POST', mode: 'cors', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({
        kind: 'api', slug: location.pathname, lang: rf.getAttribute('data-lang'), email: email, hp: fd.get('website') || '', t: Date.now() - t0,
        data: { ime: String(fd.get('ime') || ''), sajt: String(fd.get('sajt') || ''), poruka: msg } }) })
        .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || !j.ok) throw new Error(j.error || r.status); }); })
        .then(function () { out.textContent = rf.getAttribute('data-ok'); rf.reset(); }, function () { out.textContent = rf.getAttribute('data-err'); })
        .then(function () { btn.disabled = false; });
    });
  }
})();
