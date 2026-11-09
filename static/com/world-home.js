/* Search of the world home page (G0): a static index of countries and cities with a page (assets/world/search.json,
   rows [kind, cc, en, sr, ru, local, url_en, url_sr, url_ru]), loaded on the first focus. No tracking, no requests
   while typing. */
(function () {
  const box = document.querySelector('.wh-search');
  if (!box) return;
  const q = box.querySelector('input'), out = box.querySelector('ul');
  const L = { en: 0, sr: 1, ru: 2 }[box.dataset.lang] || 0;
  let rows = null, loading = null;
  const fold = s => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'dj').replace(/ß/g, 'ss').replace(/ł/g, 'l').replace(/ø/g, 'o').replace(/æ/g, 'ae');
  function load() {
    if (!loading) loading = fetch(box.dataset.idx).then(r => r.json()).then(j => {
      rows = j.map(r => ({ r, k: [r[2], r[3], r[4], r[5]].map(fold) }));
      return rows;
    });
    return loading;
  }
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  function country(cc) {
    const c = rows.find(x => x.r[0] === 'c' && x.r[1] === cc);
    return c ? c.r[2 + L] : cc;
  }
  function show() {
    const t = fold(q.value.trim());
    if (t.length < 2 || !rows) { out.innerHTML = ''; return; }
    const hit = [];
    for (const x of rows) {
      let s = -1;
      for (const k of x.k) { if (!k) continue; if (k.startsWith(t)) { s = Math.max(s, 2); } else if (k.includes(' ' + t) || k.includes('-' + t)) { s = Math.max(s, 1); } }
      if (s >= 0) hit.push([s + (x.r[0] === 'c' ? 1 : 0), x]);
    }
    hit.sort((a, b) => b[0] - a[0] || a[1].r[2 + L].localeCompare(b[1].r[2 + L]));
    if (!hit.length) { out.innerHTML = `<li><span>${esc(box.dataset.none)} <a href="${box.dataset.map}">→</a></span></li>`; return; }
    out.innerHTML = hit.slice(0, 8).map(([, x]) => `<li><a href="${x.r[6 + L]}" translate="no">${esc(x.r[2 + L])}` +
      (x.r[0] === 't' ? `<small>${esc(country(x.r[1]))}</small>` : '') + '</a></li>').join('');
  }
  q.addEventListener('focus', load, { once: true });
  q.addEventListener('input', () => (rows ? show() : load().then(show)));
  q.addEventListener('keydown', e => { if (e.key === 'Enter') { const a = out.querySelector('a'); if (a) location.href = a.href; } });
})();
