/* BlokVolt — "Mapa za vaš sajt" (/mapa-za-vas-sajt/, RUNBOOK 3.40): the widget configurator. Builds the widget's
   address and the iframe code from the form, shows the live preview (the widget itself, same origin) and copies the
   code. Nothing is sent or stored. The code's texts follow the widget's language, not the page's (vz-cfg). */
(function () {
  'use strict';
  var d = document, root = d.querySelector('[data-vz]');
  if (!root) return;
  var C = JSON.parse(d.getElementById('vz-cfg').textContent);
  var f = root.querySelector('.vz-form'), frame = root.querySelector('[data-vz-frame]'), code = root.querySelector('[data-vz-code]');
  var stage = root.querySelector('[data-vz-stage]'), okMsg = root.querySelector('[data-vz-ok]'), copyBtn = root.querySelector('[data-vz-copy]');
  var llErr = d.getElementById('vz-ll-e'), llIn = d.getElementById('vz-ll');
  var PAGE_LANG = (d.documentElement.lang || 'sr').slice(0, 2);
  var lastSrc = '', timer = 0, H = 560, PC = 1000, box = root.querySelector('[data-vz-scale]');

  // the widget's language starts as the page's language
  var lr = f.querySelector('input[name=jezik][value="' + PAGE_LANG + '"]');
  if (lr) lr.checked = true;

  function val(n) { var e = f.elements[n]; if (!e) return ''; if (e.type === 'checkbox') return e.checked; return e.value || (e.length ? [].filter.call(e, function (x) { return x.checked; }).map(function (x) { return x.value; })[0] || '' : ''); }
  function radio(n) { var x = f.querySelector('input[name=' + n + ']:checked'); return x ? x.value : ''; }
  // "45.2551, 19.8452", "45,2551 19,8452", "45.2551 19.8452" → [lat, lon]; null when it is not a point near Serbia
  function parseLL(s) {
    var m = String(s || '').trim().match(/^(-?\d{1,2}(?:[.,]\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:[.,]\d+)?)$/);
    if (!m) return null;
    var a = parseFloat(m[1].replace(',', '.')), b = parseFloat(m[2].replace(',', '.'));
    if (!(a >= 39 && a <= 48.5 && b >= 13 && b <= 24.5)) return null;
    return [Math.round(a * 1e5) / 1e5, Math.round(b * 1e5) / 1e5];
  }
  function state() {
    return { tip: radio('tip'), pogled: val('pogled'), grad: val('grad'), ll: parseLL(llIn.value), llRaw: llIn.value.trim(),
      naziv: (val('naziv') || '').trim().slice(0, 40), filter: val('filter'), ok: val('ok'), jezik: radio('jezik') || 'sr', visina: +radio('visina') || 560 };
  }
  function path(s) { return (s.jezik === 'sr' ? '' : '/' + s.jezik) + '/embed/' + (s.tip === 'cene' ? 'cene' : 'mapa') + '/'; }
  function query(s) {
    if (s.tip === 'cene') return '';
    var q = [];
    if (s.pogled === 'grad' && s.grad) q.push('grad=' + encodeURIComponent(s.grad));
    if (s.pogled === 'mesto' && s.ll) {
      q.push('mesto=' + s.ll[0] + ',' + s.ll[1]);
      if (s.naziv) q.push('naziv=' + encodeURIComponent(s.naziv));
    }
    if (s.filter && s.filter.indexOf('net:') === 0) q.push('mreza=' + encodeURIComponent(s.filter.slice(4)));
    else if (s.filter === 'fast' || s.filter === 'free') q.push('f=' + s.filter);
    if (s.ok) q.push('ok=1');
    return q.length ? '?' + q.join('&') : '';
  }
  function attr(x) { return String(x).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
  function makeCode(s) {
    var L = C.txt[s.jezik] || C.txt.sr, map = s.tip !== 'cene';
    var src = C.site + path(s) + query(s);
    var link = C.site + (s.jezik === 'sr' ? '' : '/' + s.jezik) + (map ? '/mapa/' : '/javno-punjenje/');
    return '<iframe src="' + attr(src) + '" title="' + attr(map ? L.title_map : L.title_cene) + '" width="100%" height="' + s.visina + '"' +
      ' style="border:1px solid #E2E4DF;border-radius:14px;max-width:100%" loading="lazy"' + (map ? ' allow="geolocation"' : '') +
      ' referrerpolicy="strict-origin-when-cross-origin"></iframe>\n' +
      '<p style="margin:6px 0 0;font:13px/1.4 system-ui,sans-serif;color:#5C6270">' + attr(L.src) + ' <a href="' + attr(link) + '">' + attr(map ? L.link_map : L.link_cene) + '</a></p>';
  }
  function paint() {
    var s = state(), map = s.tip !== 'cene';
    // the map's own step is shown only for the map; the later steps keep their numbers in order
    root.querySelector('[data-vz-map]').hidden = !map;
    root.querySelector('[data-vz-n]').textContent = map ? '3' : '2';
    root.querySelector('[data-vz-cn]').textContent = map ? '4' : '3';
    [].forEach.call(root.querySelectorAll('[data-vz-if]'), function (el) { el.hidden = el.getAttribute('data-vz-if') !== s.pogled; });
    var bad = map && s.pogled === 'mesto' && !s.ll;
    llErr.hidden = !(bad && s.llRaw);
    llIn.setAttribute('aria-invalid', bad && s.llRaw ? 'true' : 'false');
    code.value = makeCode(s);
    frame.setAttribute('height', s.visina);
    H = s.visina;
    fit();
    okMsg.hidden = true;
    var src = path(s) + query(s);
    if (src !== lastSrc) {
      clearTimeout(timer);
      timer = setTimeout(function () { lastSrc = src; frame.src = src; }, lastSrc ? 350 : 0);
    }
  }
  f.addEventListener('submit', function (e) { e.preventDefault(); });
  f.addEventListener('input', paint);
  f.addEventListener('change', paint);

  // preview width: the host page on a computer (the widget drawn at 1000 px and scaled down to the stage, so the wide
  // layout shows as it will on a real page) or on a phone (real width)
  function fit() {
    var tel = stage.classList.contains('is-tel'), w = box.clientWidth || 1;
    var k = tel || w >= PC ? 1 : w / PC;
    frame.style.width = tel || w >= PC ? '100%' : PC + 'px';
    frame.style.height = H + 'px';
    frame.style.transform = k < 1 ? 'scale(' + k + ')' : '';
    box.style.height = Math.round(H * k) + 'px';
  }
  // only a change of the width counts (the height is ours: reacting to it could loop with the page's scrollbar)
  var lastW = 0;
  function onSize() { var w = box.clientWidth; if (Math.abs(w - lastW) > 1) { lastW = w; fit(); } }
  // on a phone the preview starts at the phone's width
  if (window.matchMedia && matchMedia('(max-width: 700px)').matches) {
    var tr = root.querySelector('.vz-dev input[value=tel]');
    if (tr) { tr.checked = true; stage.classList.add('is-tel'); }
  }
  if (window.ResizeObserver) new ResizeObserver(onSize).observe(box); else window.addEventListener('resize', onSize);
  root.querySelector('.vz-dev').addEventListener('change', function (e) {
    stage.classList.toggle('is-tel', e.target.value === 'tel');
    fit();
  });

  function copied() {
    okMsg.hidden = false;
    var lbl = copyBtn.querySelector('span'), t = lbl.textContent;
    lbl.textContent = C.copied[PAGE_LANG] || C.copied.sr;
    setTimeout(function () { lbl.textContent = t; }, 2200);
    if (window.bvTrack) window.bvTrack('widget_code_copy', { widget: radio('tip'), lang: radio('jezik'), view: val('pogled'), filter: val('filter') });
  }
  copyBtn.addEventListener('click', function () {
    code.focus();
    code.select();
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(code.value).then(copied, function () { try { if (d.execCommand('copy')) copied(); } catch (e) { /* the code stays selected */ } });
    else { try { if (d.execCommand('copy')) copied(); } catch (e) { /* the code stays selected */ } }
  });
  code.addEventListener('focus', function () { code.select(); });
  paint();
})();
