/* BlokVolt — small site script: menu, language switcher, list filters. No dependencies. */
(function () {
  var d = document;

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
      var k = kind === 'firma' ? (data.vrsta === 'mreza' ? 'mreza' : 'firma') : (data.sta === 'stanica' || data.sta === 'novi-punjac' ? 'stanica' : 'ispravka');
      var btn = f.querySelector('[type=submit]');
      btn.disabled = true;
      fetch('/api/zahtev', { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ kind: k, slug: slug, data: data, email: email, hp: f.elements.website ? f.elements.website.value : '', t: Date.now() - t0 }) })
        .then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }, function () { return { ok: false, status: r.status }; }); })
        .then(function (j) {
          btn.disabled = false;
          if (j.ok) { show('f-ok'); f.reset(); btn.hidden = true; }
          else show(j.status === 429 ? 'f-limit' : 'f-err');
        }, function () { btn.disabled = false; show('f-err'); });
    });
  });

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
  });
})();
