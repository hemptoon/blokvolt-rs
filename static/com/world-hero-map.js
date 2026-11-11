/* Live map of the first screen of the world home (HOME2, 11.11.2026). Imported by world-home.js only on the first tap,
   click or key press on the picture, so MapLibre (≈ 1 MB) never loads with the page. It looks like the picture it replaces
   (scripts/world_hero.py): the same dark ground, the same Natural Earth lines (/assets/world/hero/borders.json) and lime
   points — now from the PMTiles of the world map (layer `sites`, contract v1 §3), opened at the picture's own view.
   HOME3 (11.11.2026): the ground is the dark base map of /map/ (OpenFreeMap "dark" recoloured with cfg.dark_paint — the
   colours of the picture), so picture → live map → /map/ look the same; its labels fade in only from zoom 5 (the picture has
   none). If that style cannot load, the Natural Earth lines of HOME2 are the ground. Filters and the cards are on the full
   map (/map/); a tap on a point opens it there (?id=), and from zoom 7 a button offers the full map at the same view.
   Attribution stays on screen (L1 §2). */
let pmLoaded = null;
function loadPm(src) {
  if (window.pmtiles) return Promise.resolve();
  if (!pmLoaded) pmLoaded = new Promise((ok, no) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = ok;
    s.onerror = no;
    document.head.appendChild(s);
  });
  return pmLoaded;
}
async function getJson(u) {
  const r = await fetch(u, { mode: 'cors' });
  if (!r.ok) throw new Error(r.status + ' ' + u);
  return r.json();
}

function loadCss(href) {
  if (document.querySelector(`link[href="${href}"]`)) return;
  const l = document.createElement('link');
  l.rel = 'stylesheet';
  l.href = href;
  document.head.appendChild(l);
}

export async function start(o) {
  const { el, cfg } = o;
  loadCss(cfg.lib.replace(/maplibre-gl\.mjs$/, 'maplibre-gl.css'));
  const [ml] = await Promise.all([import(cfg.lib), loadPm(cfg.pmtiles)]);
  const base = cfg.data_base.replace(/\/?$/, '/');
  const at = u => (/^https?:\/\//.test(u) ? u : base + u);
  const latest = await getJson(base + 'latest.json');
  const M = await getJson(at(latest.manifest));
  const proto = new window.pmtiles.Protocol();
  ml.addProtocol('pmtiles', proto.tile);
  const points = [
    { id: 'glow', type: 'circle', source: 'wm', 'source-layer': 'sites',
      // the tiles are thinned on a regular grid zoomed out (K7): a faint, small glow, so the grid does not read as a carpet
      paint: { 'circle-color': '#4A5C12', 'circle-blur': 1, 'circle-opacity': ['interpolate', ['linear'], ['zoom'], 2, 0.16, 6, 0.22, 9, 0.3],
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 2, 2, 5, 3.5, 8, 7, 12, 14] } },
    { id: 'pt', type: 'circle', source: 'wm', 'source-layer': 'sites',
      paint: { 'circle-color': ['match', ['get', 'p'], 5, '#F4FFD2', '#D9F45B'],
        'circle-opacity': ['interpolate', ['linear'], ['zoom'], 2, 0.75, 6, 0.95],
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 2, 0.55, 5, 1, 8, 2.4, 12, 5.5] } }
  ];
  const wm = { type: 'vector', url: 'pmtiles://' + at(M.tiles), attribution: '' };
  let style = null;
  if (cfg.style_dark) {
    try {
      const j = await getJson(cfg.style_dark);
      const P = cfg.dark_paint || {};
      j.layers.forEach(l => {
        if (P[l.id]) l.paint = Object.assign({}, l.paint || {}, P[l.id]);
        if (l.id === 'boundary_state') l.paint = Object.assign({}, l.paint || {}, { 'line-opacity': ['interpolate', ['linear'], ['zoom'], 4.6, 0, 5.4, 1] });
        if (l.type === 'symbol') {   // no labels on the picture: they come in from zoom 5, light on the dark ground
          l.paint = Object.assign({}, l.paint || {}, { 'text-opacity': ['interpolate', ['linear'], ['zoom'], 4.6, 0, 5.4, 1],
            'icon-opacity': ['interpolate', ['linear'], ['zoom'], 4.6, 0, 5.4, 1] });
          if (l['source-layer'] === 'place') Object.assign(l.paint, { 'text-color': '#F4F3EE', 'text-halo-color': 'rgba(11,15,23,0.95)', 'text-halo-width': 2 });
        }
      });
      const k = j.layers.findIndex(l => l.type === 'symbol');
      j.sources.wm = wm;
      j.layers.splice(k < 0 ? j.layers.length : k, 0, ...points);
      style = j;
    } catch (e) { style = null; }
  }
  if (!style) style = {
    version: 8,
    sources: {
      ne: { type: 'geojson', data: cfg.borders, attribution: '' },
      wm
    },
    layers: [
      { id: 'bg', type: 'background', paint: { 'background-color': '#111621' } },
      { id: 'coast', type: 'line', source: 'ne', filter: ['==', ['get', 'k'], 'c'], paint: { 'line-color': '#96A0B6', 'line-opacity': 0.32, 'line-width': 0.8 } },
      { id: 'border', type: 'line', source: 'ne', filter: ['==', ['get', 'k'], 'b'], paint: { 'line-color': '#96A0B6', 'line-opacity': 0.42, 'line-width': 0.8 } },
      ...points
    ]
  };
  const map = new ml.Map({
    container: el, style, center: o.center, zoom: o.zoom, minZoom: 1.2, maxZoom: 13,
    attributionControl: false, dragRotate: false, pitchWithRotate: false, keyboard: true, fadeDuration: 0
  });
  map.touchZoomRotate.disableRotation();
  map.addControl(new ml.NavigationControl({ showCompass: false }), 'top-right');
  map.getCanvas().setAttribute('aria-label', cfg.label || 'Map');
  const report = () => o.onMove && o.onMove(map.getZoom(), map.getCenter());
  map.on('moveend', report);
  map.once('idle', () => { report(); o.onReady && o.onReady(); map.getCanvas().focus({ preventScroll: true }); });
  map.on('error', e => { if (!map.loaded() && o.onError) o.onError(e); });
  const hit = p => map.queryRenderedFeatures([[p.x - 8, p.y - 8], [p.x + 8, p.y + 8]], { layers: ['pt'] });
  map.on('mousemove', e => { map.getCanvas().style.cursor = hit(e.point).length ? 'pointer' : ''; });
  map.on('click', e => {
    const f = hit(e.point)[0];
    if (!f) return;
    const [lon, lat] = f.geometry.coordinates;
    location.href = `${cfg.map}?id=${encodeURIComponent(f.properties.i)}#${Math.max(13, map.getZoom()).toFixed(2)}/${lat.toFixed(5)}/${lon.toFixed(5)}`;
  });
  return map;
}
