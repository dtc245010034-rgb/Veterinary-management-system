/* Pet Meme Edition: meme thú cưng, MẶC ĐỊNH BẬT. Nút ở góc dưới trái bật/tắt, lựa chọn nhớ trong localStorage. */
(function () {
  'use strict';
  if (window.__petMemeEdition) return;
  window.__petMemeEdition = true;
  var KHOA = 'petMeme';
  var photos = [
    {src:'/static/images/cat-middle-finger.webp', alt:'Meme mèo giơ ngón giữa cực bựa', caption:'Tâm trạng khi deadline dí 💀'},
    {src:'/static/images/tiger-meme.webp', alt:'Meme hổ ngồi tạo dáng hài hước', caption:'Tôi sau khi xem đúng một video gym 🐯'},
    {src:'/static/images/shocked-cat.webp', alt:'Meme mèo mắt trợn ngạc nhiên', caption:'Khi nhớ ra mai phải nộp bài 😳'}
  ];
  function make(tag, cls) { var e=document.createElement(tag); if(cls)e.className=cls; return e; }
  // Chỉ khi người dùng đã bấm tắt ('off') mới tắt. localStorage có thể ném lỗi (chế độ riêng tư, chặn dữ liệu trang):
  // khi đó giữ lựa chọn trong biến `tam` để nút vẫn bấm tắt được trong trang hiện tại.
  var tam = null;
  function dangBat() {
    if (tam !== null) return tam;
    try { return localStorage.getItem(KHOA) !== 'off'; } catch(e) { return true; }
  }
  function ghiNho(bat) { tam = bat; try { localStorage.setItem(KHOA, bat?'on':'off'); } catch(e) {} }

  function addMemeWall() {
    var main=document.querySelector('main');
    // Trang `giua-man-hinh` (lỗi, đăng ký, đặt mật khẩu…) chỉ có đúng một thẻ ở giữa: chèn khối meme vào đó làm thẻ bị ép sang trái.
    if(!main || main.classList.contains('giua-man-hinh') || main.querySelector('.meme-khoi')) return;
    var khoi=make('section','meme-khoi'), wall=make('section','meme-sticker-wall');
    wall.setAttribute('aria-label','Meme thú cưng giải trí');
    photos.forEach(function(p){
      var card=make('article','meme-sticker'), img=make('img'), cap=make('span');
      img.src=p.src; img.alt=p.alt; img.loading='lazy'; cap.textContent=p.caption;
      card.appendChild(img); card.appendChild(cap); wall.appendChild(card);
    });
    var heading=make('h2'); heading.textContent='Meme hết cứu 🐾💀';
    var sub=make('p','phu'); sub.textContent='Ba chiếc meme đúng tâm trạng, xem xong nhớ quay lại xử lý lịch hẹn nha sen.';
    khoi.appendChild(heading); khoi.appendChild(sub); khoi.appendChild(wall); main.appendChild(khoi);
  }
  function addBubble() {
    if(document.querySelector('.meme-global-bubble')) return;
    var bubble=make('aside','meme-global-bubble'); bubble.setAttribute('aria-label','Meme thú cưng ngẫu nhiên');
    var img=make('img'), text=make('div'), strong=make('strong'), caption=make('span'), close=make('button');
    var item=photos[Math.floor(Math.random()*photos.length)]; img.src=item.src; img.alt=item.alt;
    strong.textContent='Pet mood'; caption.textContent=item.caption; text.appendChild(strong); text.appendChild(caption);
    close.type='button'; close.setAttribute('aria-label','Đóng meme'); close.textContent='×';
    close.addEventListener('click',function(){bubble.remove();});
    bubble.appendChild(img); bubble.appendChild(text); bubble.appendChild(close); document.body.appendChild(bubble);
  }
  function xoaMeme() {
    var ds=document.querySelectorAll('.meme-khoi, .meme-global-bubble');
    for(var i=0;i<ds.length;i++) ds[i].remove();
  }
  function addNut() {
    var nut=make('button','meme-toggle'); nut.type='button';
    function ve(){ var bat=dangBat(); nut.setAttribute('aria-pressed', bat?'true':'false'); nut.textContent='🐾 Meme: '+(bat?'Bật':'Tắt'); }
    nut.addEventListener('click',function(){
      var bat=!dangBat(); ghiNho(bat);
      if(bat){addMemeWall();addBubble();} else {xoaMeme();}
      ve();
    });
    ve(); document.body.appendChild(nut);
  }
  function init(){ addNut(); if(dangBat()){addMemeWall();addBubble();} }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
