/* Country directory of blokvolt.com (HOME3, 11.11.2026) — the home and the hub (templates/com2/world__dir.html).
   Regions become ARIA tabs (a strip that scrolls by itself on a phone, never the page); the visitor's region is opened
   first — from the time zone only (the same table as the picture of the first screen, content/world/regions.json), no
   location request; without JS every region shows with its heading. "Find a country" filters every region at once,
   by the name in the page's language, in English or in the country's own language, without accents. No requests. */
(function () {
  const d = document;
  const fold = s => (s || '').toLowerCase().replace(/đ/g, 'dj').replace(/ß/g, 'ss').replace(/ł/g, 'l').replace(/ø/g, 'o')
    .replace(/æ/g, 'ae').replace(/ı/g, 'i').normalize('NFD').replace(/[̀-ͯ]/g, '');
  function region(root) {
    const h = d.documentElement.getAttribute('data-dr');
    if (h) return h;
    let z = '';
    try { z = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { /* old browser */ }
    let T = {};
    try { T = JSON.parse(root.dataset.tz || '{}'); } catch (e) { T = {}; }
    for (const k in T) { try { if (new RegExp(T[k]).test(z)) return k; } catch (e) { /* bad pattern */ } }
    return 'eu';
  }
  d.querySelectorAll('.wd').forEach(root => {
    const tl = root.querySelector('.wd-tabs');
    const tabs = [...tl.querySelectorAll('[role=tab]')];
    const pans = [...root.querySelectorAll('.wd-pan')];
    const pick = (t, focus) => {
      tabs.forEach(x => {
        const on = x === t;
        x.setAttribute('aria-selected', String(on));
        x.tabIndex = on ? 0 : -1;
        const p = d.getElementById(x.getAttribute('aria-controls'));
        if (p) p.hidden = !on;
      });
      if (focus) t.focus();
      // keep the chosen tab in view inside its own strip (the page itself never scrolls sideways)
      const l = t.offsetLeft - tl.offsetLeft, r = l + t.offsetWidth;
      if (l < tl.scrollLeft || r > tl.scrollLeft + tl.clientWidth) tl.scrollLeft = Math.max(0, l - 24);
    };
    tl.hidden = false;
    root.classList.add('is-tabs');
    tabs.forEach(t => t.addEventListener('click', () => pick(t)));
    tl.addEventListener('keydown', e => {
      const i = tabs.indexOf(d.activeElement);
      if (i < 0) return;
      const n = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : null;
      if (n === null) return;
      e.preventDefault();
      pick(tabs[(n + tabs.length) % tabs.length], true);
    });
    const r0 = region(root);
    pick(tabs.find(t => t.dataset.r === r0) || tabs[0]);
    // ---------------------------------------------------------- find a country
    const box = root.querySelector('.wd-find'), q = box && box.querySelector('input');
    const res = root.querySelector('.wd-res'), none = box && box.querySelector('.wd-none');
    if (!q || !res) return;
    box.hidden = false;
    const items = [];
    const seen = new Set();
    pans.forEach(p => p.querySelectorAll('.wd-az li[data-k]').forEach(li => {
      if (seen.has(li.dataset.cc)) return;
      seen.add(li.dataset.cc);
      items.push({ li, k: li.dataset.k.split(' ') });
    }));
    const run = () => {
      const s = fold(q.value.trim());
      if (!s) {
        res.hidden = true;
        res.innerHTML = '';
        none.hidden = true;
        tl.hidden = false;
        const t = tabs.find(x => x.getAttribute('aria-selected') === 'true') || tabs[0];
        pans.forEach(p => { p.hidden = p.id !== t.getAttribute('aria-controls'); });
        return;
      }
      const hit = items.filter(x => x.k.some(k => k.startsWith(s) || k.includes(' ' + s) || k.includes('-' + s)));
      hit.sort((a, b) => fold(a.li.textContent).localeCompare(fold(b.li.textContent)));
      res.innerHTML = '';
      hit.forEach(x => res.appendChild(x.li.cloneNode(true)));
      res.hidden = !hit.length;
      none.hidden = !!hit.length;
      tl.hidden = true;
      pans.forEach(p => { p.hidden = true; });
    };
    q.addEventListener('input', run);
    q.addEventListener('keydown', e => {
      if (e.key === 'Enter') { const a = res.querySelector('a'); if (a) { e.preventDefault(); location.href = a.href; } }
      else if (e.key === 'Escape') { q.value = ''; run(); }
    });
  });
})();
