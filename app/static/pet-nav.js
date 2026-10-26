/* PET NAV — menu dropdown.
 * Chuyển trang dùng View Transitions của trình duyệt (CSS), không còn trì hoãn 130ms. */
(function () {
  'use strict';
  var doc = document;
  if (!doc.body) return;

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

  /* Chuyển trang: KHÔNG chặn click, KHÔNG trì hoãn điều hướng.
   * Hiệu ứng mờ dần do trình duyệt đảm nhiệm qua `@view-transition { navigation: auto; }`
   * trong pet-motion.css. Trình duyệt chưa hỗ trợ thì chuyển trang bình thường. */
})();
