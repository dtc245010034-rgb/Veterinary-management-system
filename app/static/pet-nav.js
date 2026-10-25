/* PET NAV — menu dropdown + chuyển trang nhẹ.
 * Chỉ dùng opacity/transform (chạy trên GPU), không blur, không overlay toàn màn hình. */
(function () {
  'use strict';
  var doc = document;
  var body = doc.body;
  if (!body) return;

  var reduceMotion = !!(window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* ---------- Dropdown ---------- */
  var menu = doc.getElementById('pet-menu');
  var btn = doc.getElementById('pet-menu-btn');
  var list = doc.getElementById('pet-menu-list');

  function isOpen() { return menu && menu.classList.contains('is-open'); }
  function setOpen(open, focusBtn) {
    if (!menu || !btn) return;
    menu.classList.toggle('is-open', open);
    btn.setAttribute('aria-expanded', String(open));
    if (!open && focusBtn) btn.focus();
  }

  if (menu && btn && list) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      setOpen(!isOpen());
    });

    doc.addEventListener('click', function (e) {
      if (isOpen() && !menu.contains(e.target)) setOpen(false);
    });

    doc.addEventListener('keydown', function (e) {
      if (!isOpen()) return;
      if (e.key === 'Escape') { setOpen(false, true); return; }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        var items = Array.prototype.slice.call(list.querySelectorAll('a[href], button'));
        if (!items.length) return;
        e.preventDefault();
        var i = items.indexOf(doc.activeElement);
        i = e.key === 'ArrowDown' ? (i + 1) % items.length
                                  : (i <= 0 ? items.length - 1 : i - 1);
        items[i].focus();
      }
    });

    /* Đánh dấu trang hiện tại + hiện tên trang trên nút menu */
    var path = window.location.pathname.replace(/\/+$/, '') || '/';
    var best = null;
    list.querySelectorAll('a[href]').forEach(function (a) {
      var p = a.getAttribute('href').replace(/\/+$/, '') || '/';
      if (p === path || (p !== '/' && path.indexOf(p + '/') === 0)) {
        if (!best || p.length > best.p.length) best = { a: a, p: p };
      }
    });
    if (best) {
      best.a.setAttribute('aria-current', 'page');
      var label = btn.querySelector('.pet-menu-label');
      if (label) label.textContent = best.a.textContent.trim();
    }
  }

  /* ---------- Chuyển trang: fade ngắn rồi đi tiếp ---------- */
  var navigating = false;
  doc.addEventListener('click', function (event) {
    if (navigating) return;
    var link = event.target && event.target.closest
      ? event.target.closest('a[href]') : null;
    if (!link) return;
    if (event.defaultPrevented) return;
    if (event.button && event.button !== 0) return;
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (link.target && link.target !== '_self') return;
    if (link.hasAttribute('download') || link.hasAttribute('data-no-transition')) return;

    var url;
    try { url = new URL(link.href, window.location.href); } catch (_) { return; }
    if (url.origin !== window.location.origin) return;
    if (url.pathname === window.location.pathname &&
        url.search === window.location.search) return;

    if (reduceMotion) return;          // đi thẳng, không trì hoãn
    event.preventDefault();
    navigating = true;
    setOpen(false);
    body.classList.add('pet-leaving');
    window.setTimeout(function () { window.location.assign(url.href); }, 130);
  });

  window.addEventListener('pageshow', function () {
    navigating = false;
    body.classList.remove('pet-leaving');
  });
})();
