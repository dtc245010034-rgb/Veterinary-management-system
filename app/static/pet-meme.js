/* Pet Meme Edition: friendly reactions on login and all sub-pages. */
(function () {
  'use strict';
  if (window.__petMemeEdition) return;
  window.__petMemeEdition = true;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var photos = [
    {src:'/static/images/cat-middle-finger.png', alt:'Meme mèo giơ ngón giữa cực bựa', caption:'Tâm trạng khi deadline dí 💀'},
    {src:'/static/images/tiger-meme.png', alt:'Meme hổ ngồi tạo dáng hài hước', caption:'Tôi sau khi xem đúng một video gym 🐯'},
    {src:'/static/images/shocked-cat.png', alt:'Meme mèo mắt trợn ngạc nhiên', caption:'Khi nhớ ra mai phải nộp bài 😳'}
  ];
  function make(tag, cls) { var e=document.createElement(tag); if(cls)e.className=cls; return e; }
  function addMemeWall() {
    var main=document.querySelector('main');
    if(!main || document.querySelector('.meme-login-layout') || main.querySelector('.meme-sticker-wall')) return;
    var wall=make('section','meme-sticker-wall'); wall.setAttribute('aria-label','Meme thú cưng giải trí');
    photos.slice(0,4).forEach(function(p){
      var card=make('article','meme-sticker'), img=make('img'), cap=make('span');
      img.src=p.src; img.alt=p.alt; img.loading='lazy'; cap.textContent=p.caption;
      card.appendChild(img); card.appendChild(cap); wall.appendChild(card);
    });
    var heading=make('h2'); heading.textContent='Meme hết cứu 🐾💀';
    var sub=make('p','phu'); sub.textContent='Ba chiếc meme đúng tâm trạng, xem xong nhớ quay lại xử lý lịch hẹn nha sen.';
    main.appendChild(heading); main.appendChild(sub); main.appendChild(wall);
  }
  function addBubble() {
    if(document.querySelector('.meme-login-layout') || document.querySelector('.meme-global-bubble')) return;
    var bubble=make('aside','meme-global-bubble'); bubble.setAttribute('aria-label','Meme thú cưng ngẫu nhiên');
    var img=make('img'), text=make('div'), strong=make('strong'), caption=make('span'), close=make('button');
    var item=photos[Math.floor(Math.random()*photos.length)]; img.src=item.src; img.alt=item.alt;
    strong.textContent='Pet mood'; caption.textContent=item.caption; text.appendChild(strong); text.appendChild(caption);
    close.type='button'; close.setAttribute('aria-label','Đóng meme'); close.textContent='×';
    close.addEventListener('click',function(){bubble.remove();});
    bubble.appendChild(img); bubble.appendChild(text); bubble.appendChild(close); document.body.appendChild(bubble);
  }
  function paws(e) {
    if(reduce || !e.target.closest('button, .chinh, .lien-ket')) return;
    var paw=make('span','meme-paw'); paw.textContent=['🐾','✨','💖'][Math.floor(Math.random()*3)];
    paw.style.left=(e.clientX||window.innerWidth/2)+'px'; paw.style.top=(e.clientY||window.innerHeight/2)+'px'; document.body.appendChild(paw);
    window.setTimeout(function(){paw.remove();},850);
  }
  function init(){addMemeWall();addBubble();document.addEventListener('click',paws);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();

/* Cat spins with a playful "ui a ui a" sound-effect caption on navigation. */
(function () {
  'use strict';
  if (window.__petNavigationCat) return;
  window.__petNavigationCat = true;
  var overlay;
  function createOverlay() {
    if (overlay) return overlay;
    overlay = document.createElement('div');
    overlay.className = 'pet-navigation-spin';
    overlay.setAttribute('aria-hidden', 'true');
    var img = document.createElement('img');
    img.src = '/static/images/shocked-cat.png';
    img.alt = '';
    var label = document.createElement('span');
    label.textContent = 'UI A UI A UI A 🐈';
    overlay.appendChild(img);
    overlay.appendChild(label);
    document.body.appendChild(overlay);
    return overlay;
  }
  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.target === '_blank' || link.hasAttribute('download')) return;
    var url;
    try { url = new URL(link.href, window.location.href); } catch (_) { return; }
    if (url.origin !== window.location.origin || url.href === window.location.href || url.hash && url.pathname === window.location.pathname && url.search === window.location.search) return;
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    event.preventDefault();
    var layer = createOverlay();
    layer.classList.add('is-active');
    window.setTimeout(function () { window.location.href = url.href; }, 520);
  }, true);
})();
