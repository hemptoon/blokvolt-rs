/* BlokVolt vodiči — static build (Cloudflare Pages) */
(function(){
 var nav=document.querySelector('.v3-nav'),btn=document.querySelector('.v3-burger');
 if(nav&&btn){
  btn.addEventListener('click',function(){var o=nav.classList.toggle('is-open');btn.setAttribute('aria-expanded',o?'true':'false');});
  [].slice.call(nav.querySelectorAll('.v3-links a')).forEach(function(a){a.addEventListener('click',function(){nav.classList.remove('is-open');btn.setAttribute('aria-expanded','false');});});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){nav.classList.remove('is-open');btn.setAttribute('aria-expanded','false');}});
 }
})();
/* smooth in-page anchors */
(function(){
 document.addEventListener('click',function(e){
  var a=e.target.closest('a[href^="#"]'); if(!a) return; var id=a.getAttribute('href').slice(1); if(!id) return; var t=document.getElementById(id); if(!t) return; e.preventDefault();
  var from=window.scrollY, to=t.getBoundingClientRect().top+window.scrollY-90;
  var d=Math.min(700,Math.max(320,Math.abs(to-from)*0.14)), s=performance.now();
  function step(n){var p=Math.min(1,(n-s)/d); var ease=1-Math.pow(1-p,3); window.scrollTo(0,from+(to-from)*ease); if(p<1)requestAnimationFrame(step);}
  requestAnimationFrame(step); history.replaceState(null,'','#'+id);
 },true);
})();
/* copy e-mail button (footer) */
(function(){
 [].slice.call(document.querySelectorAll('.copy-email-button')).forEach(function(b){
  function copy(e){e.preventDefault();var m=b.getAttribute('data-copy-email');if(m&&navigator.clipboard){navigator.clipboard.writeText(m).then(function(){b.setAttribute('data-copy-button','copied');});}else{location.href='mailto:'+m;}}
  b.addEventListener('click',copy);
  b.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' ')copy(e);});
  b.addEventListener('mouseleave',function(){b.removeAttribute('data-copy-button');b.blur();});
  b.addEventListener('blur',function(){b.removeAttribute('data-copy-button');});
 });
})();
/* article system v2: reading progress, active rail item, copy buttons, reveal */
(function(){
var d=document,W=window;
var bar=d.createElement('div');bar.className='bva-prog';d.body.appendChild(bar);
function prog(){var h=d.documentElement,s=W.scrollY||h.scrollTop,m=h.scrollHeight-h.clientHeight;bar.style.transform='scaleX('+(m>0?Math.min(1,s/m):0)+')';}
W.addEventListener('scroll',prog,{passive:true});W.addEventListener('resize',prog);prog();
var links=[].slice.call(d.querySelectorAll('.bva-toc a')),secs=[];
links.forEach(function(a){var id=(a.getAttribute('href')||'').split('#')[1];var el=id&&d.getElementById(id);if(el)secs.push({el:el,a:a});});
function act(){var y=W.scrollY+150,cur=null;secs.forEach(function(s){if(s.el.getBoundingClientRect().top+W.scrollY<=y)cur=s;});secs.forEach(function(s){s.a.classList.toggle('is-active',s===cur);});}
W.addEventListener('scroll',act,{passive:true});act();
[].slice.call(d.querySelectorAll('.bva-doc')).forEach(function(doc){
 var CL=(d.documentElement.lang||'sr').slice(0,2),CT={sr:['Kopiraj tekst','Kopirano ✓'],en:['Copy text','Copied ✓'],ru:['Скопировать текст','Скопировано ✓']}[CL]||['Kopiraj tekst','Kopirano ✓'];
 var b=d.createElement('button');b.type='button';b.className='bva-copy';b.textContent=CT[0];
 b.addEventListener('click',function(){var t=[].map.call(doc.querySelectorAll('h4,p,li'),function(n){return n.innerText.trim();}).filter(Boolean).join('\n\n');
  if(W.navigator.clipboard){W.navigator.clipboard.writeText(t).then(function(){b.textContent=CT[1];setTimeout(function(){b.textContent=CT[0];},1800);});}});
 doc.insertBefore(b,doc.firstChild);});
if(!W.matchMedia('(prefers-reduced-motion: reduce)').matches){
 var els=[].slice.call(d.querySelectorAll('.bva .w3 > *')).filter(function(el){return el.getBoundingClientRect().top>W.innerHeight;});
 els.forEach(function(el){el.classList.add('bva-r');});
 function reveal(){if(!els.length)return;var h=W.innerHeight*0.94;els=els.filter(function(el){if(el.getBoundingClientRect().top<h){el.classList.add('in');return false;}return true;});}
 W.addEventListener('scroll',reveal,{passive:true});
 W.addEventListener('resize',reveal);W.addEventListener('hashchange',function(){setTimeout(reveal,50);});reveal();
}
})();
