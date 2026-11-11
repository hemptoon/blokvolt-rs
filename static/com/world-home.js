/* World home of blokvolt.com (HOME2, 11.11.2026; G0 search kept): search over K3's static index, country tabs, number
   count-up and section reveal (both off with prefers-reduced-motion), "Near me" (asks for the location only on the press),
   and the first screen: the picture of the map is swapped in place for the live map on the first tap, click or key press —
   world-hero-map.js (MapLibre + pmtiles) is imported only then, so it is not part of the start of the page.
   No tracking, no cookies, no requests while typing (the index loads once, on the first focus).
   LANG0: another language loads search-index-<code>.json (doc.langs = en, sr, ru, <code>; item[8] = the name in that
   language) and formats numbers with cfg.intl. */
(function () {
  const d = document, H = d.documentElement;
  const cfgEl = d.getElementById('wh-cfg');
  const cfg = cfgEl ? JSON.parse(cfgEl.textContent) : {};
  const REG = H.getAttribute('data-hr') || 'eu';
  const RM = H.classList.contains('wh-rm');
  const LOC = cfg.intl || { en: 'en-GB', sr: 'sr-Latn-RS', ru: 'ru-RU' }[cfg.lang] || 'en-GB';
  const VIEW = { na: '#3.2/41/-98', ap: '#2.6/12/112' };   // the directory's tabs: world-dir.js (HOME3)
  const nf = new Intl.NumberFormat(LOC);
  const done = new WeakSet();
  const mapLinks = () => d.querySelectorAll('a[data-map]');
  // links into the full map open on the visitor's region (Europe is the map's own default)
  if (VIEW[REG]) mapLinks().forEach(a => { a.href = a.getAttribute('href').split('#')[0] + VIEW[REG]; });

  // ------------------------------------------------------------ search
  const box = d.querySelector('.wh-search');
  if (box) {
    const q = box.querySelector('input'), out = box.querySelector('ul');
    let L = { en: 0, sr: 1, ru: 2 }[box.dataset.lang] || 0;
    let rows = null, loading = null, sel = -1;
    const nm = r => (L > 2 ? r[8] || r[2] : r[2 + L]);
    const fold = s => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/đ/g, 'dj').replace(/ß/g, 'ss').replace(/ł/g, 'l').replace(/ø/g, 'o').replace(/æ/g, 'ae');
    const load = () => {
      if (!loading) loading = fetch(box.dataset.idx).then(r => r.json()).then(j => {
        const i = (j.langs || []).indexOf(box.dataset.lang);
        if (i > 2) L = i;
        rows = j.items.map(r => ({ r, u: r[6][L] || r[6][0], k: [r[8], r[2], r[3], r[4], ...(r[5] || [])].map(fold) }));
        return rows;
      });
      return loading;
    };
    const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const country = cc => { const c = rows.find(x => x.r[0] !== 't' && x.r[1] === cc); return c ? nm(c.r) : cc; };
    const show = () => {
      const t = fold(q.value.trim());
      sel = -1;
      if (t.length < 2 || !rows) { out.innerHTML = ''; q.setAttribute('aria-expanded', 'false'); return; }
      const hit = [];
      for (const x of rows) {
        let s = -1;
        for (const k of x.k) { if (!k) continue; if (k.startsWith(t)) s = Math.max(s, 2); else if (k.includes(' ' + t) || k.includes('-' + t)) s = Math.max(s, 1); }
        if (s >= 0 && x.u) hit.push([s + (x.r[0] !== 't' ? 1 : 0) + (x.r[7] || 0) / 1e6, x]);
      }
      hit.sort((a, b) => b[0] - a[0] || nm(a[1].r).localeCompare(nm(b[1].r)));
      q.setAttribute('aria-expanded', 'true');
      if (!hit.length) { out.innerHTML = `<li><span>${esc(box.dataset.none)} <a href="${box.dataset.map}">→</a></span></li>`; return; }
      out.innerHTML = hit.slice(0, 8).map(([, x]) => `<li><a href="${x.u}" translate="no">${esc(nm(x.r))}` +
        (x.r[0] === 't' ? `<small>${esc(country(x.r[1]))}</small>` : '') + '</a></li>').join('');
    };
    const mark = () => out.querySelectorAll('a').forEach((a, i) => a.setAttribute('aria-selected', String(i === sel)));
    q.addEventListener('focus', load, { once: true });
    q.addEventListener('input', () => (rows ? show() : load().then(show)));
    q.addEventListener('keydown', e => {
      const items = out.querySelectorAll('a');
      if (e.key === 'ArrowDown' && items.length) { sel = (sel + 1) % items.length; mark(); e.preventDefault(); }
      else if (e.key === 'ArrowUp' && items.length) { sel = (sel - 1 + items.length) % items.length; mark(); e.preventDefault(); }
      else if (e.key === 'Escape') { out.innerHTML = ''; }
    });
    box.addEventListener('submit', e => {
      e.preventDefault();
      const items = out.querySelectorAll('a'), a = items[Math.max(sel, 0)];
      if (a && a.textContent !== '→') location.href = a.href;
      else if (q.value.trim().length >= 2) load().then(() => { show(); const b = out.querySelector('li > a'); location.href = b ? b.href : box.dataset.map; });
    });
    d.addEventListener('click', e => { if (!box.contains(e.target)) out.innerHTML = ''; });
    // SearchAction of the home page: /?q=…
    const pq = new URLSearchParams(location.search).get('q');
    if (pq) { q.value = pq.slice(0, 80); load().then(show); }
  }

  // ------------------------------------------------------------ attribution of the first screen (HOME3, L1 §2)
  // "© OpenStreetMap contributors · Sources" in the corner, visible without any action; after 5 s (never earlier) it folds
  // into "ⓘ"; "ⓘ" opens the panel with the map data, the base map, the borders and the data date
  const at = d.getElementById('wh-attr');
  if (at) {
    const ib = at.querySelector('.wh-attr-i'), more = d.getElementById('wh-attr-more');
    ib.hidden = false;
    setTimeout(() => { if (ib.getAttribute('aria-expanded') !== 'true') at.classList.add('is-min'); }, 5000);
    ib.addEventListener('click', e => {
      e.stopPropagation();
      const open = ib.getAttribute('aria-expanded') !== 'true';
      ib.setAttribute('aria-expanded', String(open));
      more.hidden = !open;
      at.classList.toggle('is-min', !open);
    });
  }

  // ------------------------------------------------------------ count-up and reveal
  function count(root) {
    if (RM || !root) return;
    root.querySelectorAll('.wh-num[data-n]').forEach(el => {
      if (done.has(el) || !root.closest('.wh-rv.in')) return;   // (HOME3: the directory numbers do not count up)
      done.add(el);
      const to = +el.dataset.n, txt = el.textContent, t0 = performance.now(), dur = 900;
      const step = now => {
        const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        el.textContent = k < 1 ? nf.format(Math.round(to * e)) : txt;
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  }
  // reveal on scroll: a section shows once its top is in the viewport, or once it has been scrolled past (a jump to an
  // anchor or the end never leaves a section hidden)
  if (!RM) {
    H.classList.add('wh-anim');
    const secs = [...d.querySelectorAll('.wh-rv')];
    let ticking = false;
    const sweep = () => {
      ticking = false;
      const lim = innerHeight * 0.92;
      for (const s of secs) {
        if (s.classList.contains('in') || s.getBoundingClientRect().top > lim) continue;
        s.classList.add('in');
        s.querySelectorAll('.wh-pan:not([hidden])').forEach(count);
      }
    };
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(sweep); } }, { passive: true });
    addEventListener('resize', sweep, { passive: true });
    sweep();
  }

  // ------------------------------------------------------------ near me (location only on the press)
  const near = d.getElementById('wh-near');
  if (near) near.addEventListener('click', () => {
    const fail = () => {
      let p = d.getElementById('wh-near-err');
      if (!p) { p = d.createElement('p'); p.id = 'wh-near-err'; p.className = 'wh-near-err'; p.setAttribute('role', 'status'); near.parentNode.after(p); }
      p.textContent = cfg.near_err || '';
    };
    if (!navigator.geolocation) return fail();
    navigator.geolocation.getCurrentPosition(p => {
      location.href = `${cfg.map}#12/${p.coords.latitude.toFixed(4)}/${p.coords.longitude.toFixed(4)}`;
    }, fail, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 });
  });

  // ------------------------------------------------------------ first screen: picture → live map
  const wrap = d.getElementById('wh-map'), live = d.getElementById('wh-live'), go = d.getElementById('wh-go');
  const status = d.getElementById('wh-status'), more = d.getElementById('wh-more'), full = d.getElementById('wh-full');
  const js = d.currentScript && d.currentScript.dataset.mapJs;
  let started = false;
  function activate(e) {
    if (started || !wrap || !js) return;
    if (e && e.target && e.target.closest && e.target.closest('a,.wh-attr')) return;
    started = true;
    wrap.dataset.state = 'loading';
    status.textContent = status.dataset.loading;
    const shape = matchMedia('(max-width: 720px)').matches ? 't' : 'w';
    const pic = cfg.pics[REG][shape];
    const W = wrap.clientWidth, Hh = wrap.clientHeight;
    const zoom = pic.z + Math.log2(Math.max(W / pic.w, Hh / pic.h));
    const setLinks = (z, c) => {
      const h = `#${z.toFixed(2)}/${c.lat.toFixed(4)}/${c.lng.toFixed(4)}`;
      [full, more].forEach(a => { if (a) a.href = a.getAttribute('href').split('#')[0] + h; });
      if (more) more.hidden = z < 7;
    };
    import(js).then(m => m.start({ el: live, cfg, center: pic.c, zoom, onMove: setLinks, onReady: () => {
      live.hidden = false;
      wrap.dataset.state = 'live';
      status.textContent = '';
    } })).catch(() => {
      wrap.dataset.state = 'pic';
      status.textContent = cfg.err || '';
      started = false;
    });
    live.hidden = false;
  }
  if (wrap) {
    wrap.addEventListener('click', activate);
    if (go) go.addEventListener('click', e => { e.stopPropagation(); activate(); });
  }
})();
