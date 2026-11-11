/* blokvolt.com price pages (G3): currency switch EUR (default) / USD / local. Every price is a
   <span class="pz" data-e="EUR" [data-l="local" data-c="GBP"] data-u="/kWh">; EUR is in the HTML, so the page reads
   without this script. The choice is kept in localStorage "bv:wcur" (also read by the world map card). */
(function () {
  'use strict';
  var FX = window.WP_FX || { usd: 0, lang: 'en' };
  var L = FX.lang, DEC = FX.dec || (L === 'en' ? '.' : ','), TH = FX.thou || (L === 'en' ? ',' : L === 'sr' ? '.' : ' ');   // LANG0: dec/thou of other languages
  var SYM = { EUR: '€', USD: '$', GBP: '£', SEK: 'kr', NOK: 'kr', DKK: 'kr', CZK: 'Kč', PLN: 'zł', HUF: 'Ft', RON: 'lei', CHF: 'CHF' };
  function num(x, d) {
    var s = Math.abs(x).toFixed(d).split('.');
    s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, TH);
    return (x < 0 ? '−' : '') + s.join(DEC);
  }
  function money(x, c) {
    var d = Math.abs(x) < 0.1 ? 3 : 2;
    if (c === 'HUF' && Math.abs(x) >= 10) d = 0;
    var n = num(x, d), s = SYM[c] || c;
    return L === 'en' && (c === 'EUR' || c === 'USD' || c === 'GBP') ? s + n : n + ' ' + s;
  }
  // LANG0: FX.def = "loc" — the page of an own country in its own language opens in the local currency (built so)
  function get() { try { return localStorage.getItem('bv:wcur') || FX.def || 'eur'; } catch (e) { return FX.def || 'eur'; } }
  function set(v) { try { localStorage.setItem('bv:wcur', v); } catch (e) { /* private mode */ } }
  function apply(cur) {
    var spans = document.querySelectorAll('.pz'), i, el, e, u, out;
    for (i = 0; i < spans.length; i++) {
      el = spans[i]; e = parseFloat(el.getAttribute('data-e')); u = el.getAttribute('data-u') || '';
      if (cur === 'usd' && FX.usd) out = '≈ ' + money(e * FX.usd, 'USD');
      else if (cur === 'loc' && el.hasAttribute('data-l')) out = money(parseFloat(el.getAttribute('data-l')), el.getAttribute('data-c'));
      else if (cur === 'loc' && document.querySelector('[data-wcur="loc"]')) {
        // a price in EUR on a page of a non-euro country: convert with the rate the page carries
        var r = parseFloat(document.body.getAttribute('data-locrate') || '0'), c = document.body.getAttribute('data-loccur');
        out = r && c ? '≈ ' + money(e * r, c) : money(e, 'EUR');
      } else out = money(e, 'EUR');
      el.textContent = out + u;
    }
    var bs = document.querySelectorAll('[data-wcur]');
    for (i = 0; i < bs.length; i++) bs[i].setAttribute('aria-pressed', String(bs[i].getAttribute('data-wcur') === cur));
    var notes = document.querySelectorAll('.wp-fxn');
    for (i = 0; i < notes.length; i++) notes[i].hidden = cur === 'eur';
  }
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('[data-wcur]');
    if (!b) return;
    var v = b.getAttribute('data-wcur');
    set(v); apply(v);
  });
  var c = get();
  if (c === 'loc' && !document.querySelector('[data-wcur="loc"]')) c = 'eur';
  if (c !== (FX.def || 'eur')) apply(c);
})();
