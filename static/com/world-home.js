/* World home of blokvolt.com (HOME2, 11.11.2026; G0 search kept): search over K3's static index, country tabs, number
   count-up and section reveal (both off with prefers-reduced-motion), "Near me" (asks for the location only on the press),
   and the first screen: the picture of the map is swapped in place for the live map on the first tap, click or key press —
   world-hero-map.js (MapLibre + pmtiles) is imported only then, so it is not part of the start of the page.
   No tracking, no cookies, no requests while typing (the search is world-search.js since SEARCH, 12.11.2026).
   LANG0: numbers are formatted with cfg.intl. */
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
  // SEARCH (12.11.2026): the field of the first screen is one of the places of /assets/world/world-search.js (countries,
  // every city with places, regions, networks and pages, typos, all languages); /?q=… (SearchAction) opens it there.

  // ------------------------------------------------------------ attribution of the first screen (HOME3, L1 §2)
  // "© OpenStreetMap contributors · Sources" in the corner, visible without any action; after 5 s (never earlier) it folds
  // into "ⓘ"; "ⓘ" opens the panel with the map data, the base map, the borders and the data date.
  // THEME (12.11.2026): the panel is a small card of its own above (on phones in the picture: below) the "ⓘ", on the
  // colours of the theme, and never over a button; it closes with "ⓘ" again, Esc, a click elsewhere or a move of the map.
  const at = d.getElementById('wh-attr');
  let attrClose = () => {};
  if (at) {
    const ib = at.querySelector('.wh-attr-i'), more = d.getElementById('wh-attr-more');
    ib.hidden = false;
    setTimeout(() => { if (ib.getAttribute('aria-expanded') !== 'true') at.classList.add('is-min'); }, 5000);
    const setOpen = open => {
      ib.setAttribute('aria-expanded', String(open));
      more.hidden = !open;
      at.classList.toggle('is-open', open);
    };
    attrClose = () => { if (ib.getAttribute('aria-expanded') === 'true') setOpen(false); };
    ib.addEventListener('click', e => { e.stopPropagation(); setOpen(ib.getAttribute('aria-expanded') !== 'true'); });
    d.addEventListener('click', e => { if (!at.contains(e.target)) attrClose(); });
    d.addEventListener('keydown', e => {
      if (e.key === 'Escape' && ib.getAttribute('aria-expanded') === 'true') { setOpen(false); ib.focus(); }
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
  let started = false, heroMod = null, heroMap = null;
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
    import(js).then(m => { heroMod = m; return m.start({ el: live, cfg, center: pic.c, zoom, onMove: setLinks, onMoveStart: attrClose,
      theme: H.getAttribute('data-theme') === 'light' ? 'light' : 'dark', onReady: () => {
      live.hidden = false;
      wrap.dataset.state = 'live';
      status.textContent = '';
    } }); }).then(m => { heroMap = m; }).catch(() => {
      wrap.dataset.state = 'pic';
      status.textContent = cfg.err || '';
      started = false;
    });
    live.hidden = false;
  }
  // THEME: the switch of the header — the picture of the other theme (only now loaded), and the live map restyled
  d.addEventListener('bv-theme', e => {
    const pic = d.getElementById('wh-pic'), t = d.getElementById('wh-pic-' + REG + (e.detail === 'light' ? '-light' : ''));
    if (pic && t) { pic.querySelectorAll('picture').forEach(x => x.remove()); pic.appendChild(t.content.cloneNode(true)); }
    if (heroMod && heroMap) heroMod.restyle(heroMap, e.detail === 'light' ? 'light' : 'dark');
  });
  if (wrap) {
    wrap.addEventListener('click', activate);
    if (go) go.addEventListener('click', e => { e.stopPropagation(); activate(); });
  }
})();
