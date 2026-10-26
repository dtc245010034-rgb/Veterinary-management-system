/* Pet Meme Edition: friendly reactions on login and all sub-pages. */
(function () {
  'use strict';
  if (window.__petMemeEdition) return;
  window.__petMemeEdition = true;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var photos = [
    {src:'/static/images/cat-middle-finger.webp', alt:'Meme mèo giơ ngón giữa cực bựa', caption:'Tâm trạng khi deadline dí 💀'},
    {src:'/static/images/tiger-meme.webp', alt:'Meme hổ ngồi tạo dáng hài hước', caption:'Tôi sau khi xem đúng một video gym 🐯'},
    {src:'/static/images/shocked-cat.webp', alt:'Meme mèo mắt trợn ngạc nhiên', caption:'Khi nhớ ra mai phải nộp bài 😳'}
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
  function init(){addMemeWall();addBubble();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
