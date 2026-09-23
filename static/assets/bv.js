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
})();
