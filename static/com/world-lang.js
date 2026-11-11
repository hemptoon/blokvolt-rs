/* blokvolt.com, world layer (LANG0): the language menu for many languages and the language hint.
   - The menu (templates/com2/_header.html, LANGMENU) lists every language by its native name, A–Z; this script puts the
     languages of the browser on top, adds the keyboard (arrows, Home/End, letters, Escape) — bv.js opens and closes it.
   - Hint strip: on the first visit, when the browser's first language is a language of the site, the page is shown in
     another one and this page exists in that language (no data-up), a thin strip offers it. Never a redirect.
     Closing it is remembered in localStorage "bv:langhint" (try/catch: private mode, blocked storage). */
(function () {
  'use strict';
  var d = document, menu = d.querySelector('[data-lang-menu]'), btn = d.querySelector('[data-lang-toggle]');
  if (!menu || !btn || !menu.querySelector('a[data-lang]')) return;
  var items = [].slice.call(menu.querySelectorAll('a[data-lang]'));
  var nav = [].slice.call(navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''])
    .map(function (x) { return String(x || '').toLowerCase(); });
  function code(tag) {               // browser tag → code of the site: de-AT → de, no / nn → nb
    var p = tag.split('-')[0];
    return p === 'no' || p === 'nn' ? 'nb' : p;
  }
  function rank(c) {
    for (var i = 0; i < nav.length; i++) if (code(nav[i]) === c) return i;
    return -1;
  }
  // 1. the browser's languages on top, in the browser's order, then the rest A–Z (as built)
  var mine = items.filter(function (a) { return rank(a.getAttribute('data-lang')) >= 0; })
    .sort(function (a, b) { return rank(a.getAttribute('data-lang')) - rank(b.getAttribute('data-lang')); });
  if (mine.length && mine.length < items.length) {
    for (var i = mine.length - 1; i >= 0; i--) menu.insertBefore(mine[i].parentNode, menu.firstChild);
    mine[mine.length - 1].parentNode.className += ' lang-sep';
    items = [].slice.call(menu.querySelectorAll('a[data-lang]'));
  }
  // 2. keyboard
  function focusAt(i) { items[(i + items.length) % items.length].focus(); }
  function close(back) {
    if (menu.hasAttribute('hidden')) return;
    menu.setAttribute('hidden', '');
    btn.setAttribute('aria-expanded', 'false');
    if (back) btn.focus();
  }
  btn.addEventListener('click', function () {
    if (!menu.hasAttribute('hidden')) {
      var on = menu.querySelector('a.is--on') || items[0];
      setTimeout(function () { on.focus(); }, 0);
    }
  });
  btn.addEventListener('keydown', function (e) {
    if ((e.key === 'ArrowDown' || e.key === 'ArrowUp') && menu.hasAttribute('hidden')) { e.preventDefault(); btn.click(); }
  });
  menu.addEventListener('keydown', function (e) {
    var i = items.indexOf(d.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); focusAt(i + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); focusAt(i - 1); }
    else if (e.key === 'Home') { e.preventDefault(); focusAt(0); }
    else if (e.key === 'End') { e.preventDefault(); focusAt(items.length - 1); }
    else if (e.key === 'Escape') { e.preventDefault(); close(true); }
    else if (e.key === 'Tab') { close(false); }
    else if (e.key.length === 1 && /\S/.test(e.key)) {   // type-ahead: the next language whose name starts with the letter
      var k = e.key.toLowerCase();
      for (var j = 1; j <= items.length; j++) {
        var a = items[(i + j) % items.length];
        if (a.textContent.trim().toLowerCase().indexOf(k) === 0) { a.focus(); break; }
      }
    }
  });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(true); });
  // 3. hint strip
  var seen = null;
  try { seen = localStorage.getItem('bv:langhint'); } catch (e) { seen = '1'; }
  if (seen || !nav[0]) return;
  var cur = menu.querySelector('a.is--on'), want = code(nav[0]);
  if (!cur || cur.getAttribute('data-lang') === want) return;
  var t = items.filter(function (a) { return a.getAttribute('data-lang') === want; })[0];
  if (!t || t.hasAttribute('data-up') || !t.getAttribute('data-hint')) return;
  var bar = d.createElement('div');
  bar.className = 'lang-hint';
  var a = d.createElement('a');
  a.href = t.href; a.lang = t.lang; a.hreflang = t.getAttribute('hreflang') || t.lang; a.textContent = t.getAttribute('data-hint') + ' →';
  var x = d.createElement('button');
  x.type = 'button'; x.className = 'lang-hint-x'; x.textContent = '×';
  x.setAttribute('aria-label', cur.getAttribute('data-close') || 'Close');
  x.addEventListener('click', function () {
    try { localStorage.setItem('bv:langhint', '1'); } catch (e) { /* storage blocked: the strip comes back next time */ }
    bar.parentNode.removeChild(bar);
  });
  bar.appendChild(a); bar.appendChild(x);
  var skip = d.querySelector('.skip');
  d.body.insertBefore(bar, skip ? skip.nextSibling : d.body.firstChild);
})();
