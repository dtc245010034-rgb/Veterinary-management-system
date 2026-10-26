/* PET MOTION — đồng bộ chuyển động với trang đăng nhập (templates/_dang_nhap_moi.html).
 *
 * Chỉ THÊM hiệu ứng; không chặn, không sửa dữ liệu, không vô hiệu hóa nút,
 * không gọi preventDefault. Mọi chức năng cũ (form, điều hướng, theme, chat AI…)
 * chạy y như trước. Nếu tệp này lỗi/không tải được, trang vẫn dùng bình thường.
 */
(function () {
  'use strict';
  if (window.__petMotion) return;
  window.__petMotion = true;

  var doc = document;
  var root = doc.documentElement;
  var reduceMotion = !!(window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var finePointer = !!(window.matchMedia &&
    window.matchMedia('(hover: hover) and (pointer: fine)').matches);

  function el(tag, cls) {
    var e = doc.createElement(tag);
    if (cls) e.className = cls;
    return e;
  }
  function rnd(min, max) { return min + Math.random() * (max - min); }

  /* ------------------------------------------------------------------
   * 1. Nền: quầng sáng + sao nhấp nháy + bụi bay + ánh sáng đuổi con trỏ
   * ------------------------------------------------------------------ */
  var ambient = null;
  function buildBackground() {
    if (doc.querySelector('.pm-bg') || !doc.body) return;

    var bg = el('div', 'pm-bg');
    bg.setAttribute('aria-hidden', 'true');

    bg.appendChild(el('div', 'pm-glow pm-glow-a'));
    bg.appendChild(el('div', 'pm-glow pm-glow-b'));

    // Sao: 1–1.5px, trễ pha ngẫu nhiên như các .star của trang đăng nhập
    var stars = el('div', 'pm-stars');
    var starCount = window.innerWidth < 600 ? 6 : 12;
    for (var i = 0; i < starCount; i++) {
      var s = el('span', 'pm-star');
      var size = Math.random() < 0.3 ? 1.5 : (Math.random() < 0.5 ? 1 : 2);
      s.style.width = size + 'px';
      s.style.height = size + 'px';
      s.style.left = rnd(1, 99).toFixed(1) + '%';
      s.style.top = rnd(1, 99).toFixed(1) + '%';
      s.style.animationDelay = rnd(0, 3).toFixed(2) + 's';
      s.style.animationDuration = rnd(2.4, 3.8).toFixed(2) + 's';
      stars.appendChild(s);
    }
    bg.appendChild(stars);

    // Bụi sáng bay lên (dustFloat 4s)
    var dustCount = window.innerWidth < 600 ? 2 : 4;
    for (var j = 0; j < dustCount; j++) {
      var d = el('span', 'pm-dust');
      var ds = rnd(1.8, 2.8);
      d.style.width = ds + 'px';
      d.style.height = ds + 'px';
      d.style.left = rnd(4, 96).toFixed(1) + '%';
      d.style.top = rnd(8, 92).toFixed(1) + '%';
      d.style.background = (j % 2 === 0) ? 'var(--pm-dust-a)' : 'var(--pm-dust-b)';
      d.style.animationDelay = rnd(0, 4).toFixed(2) + 's';
      bg.appendChild(d);
    }

    if (finePointer && !reduceMotion) {
      ambient = el('div', 'pm-ambient');
      bg.appendChild(ambient);
    }

    doc.body.insertBefore(bg, doc.body.firstChild);
  }

  /* Ánh sáng nền đuổi theo con trỏ (nội suy 0.22 như renderBeam của trang đăng nhập).
     Vòng lặp chỉ chạy khi còn cần di chuyển → không tốn CPU lúc đứng yên. */
  var pos = { x: -400, y: -400 };
  var target = { x: -400, y: -400 };
  var ticking = false;
  function frame() {
    pos.x += (target.x - pos.x) * 0.3;
    pos.y += (target.y - pos.y) * 0.3;
    if (ambient) {
      // transform chạy trên GPU: không phải vẽ lại gradient toàn màn hình mỗi khung hình
      ambient.style.transform = 'translate3d(' + pos.x.toFixed(1) + 'px,' + pos.y.toFixed(1) + 'px,0)';
    }
    if (Math.abs(target.x - pos.x) > 0.5 || Math.abs(target.y - pos.y) > 0.5) {
      window.requestAnimationFrame(frame);
    } else {
      ticking = false;
    }
  }
  function onPointer(x, y) {
    if (!ambient) return;
    if (pos.x < -300) { pos.x = x; pos.y = y; }   // lần đầu: không trượt từ góc màn hình
    target.x = x;
    target.y = y;
    if (!ticking) { ticking = true; window.requestAnimationFrame(frame); }
  }
  if (finePointer && !reduceMotion) {
    doc.addEventListener('mousemove', function (e) { onPointer(e.clientX, e.clientY); }, { passive: true });
  }

  /* ------------------------------------------------------------------
   * 2. Toast: trượt từ phải với lò xo (showToast của trang đăng nhập)
   * ------------------------------------------------------------------ */
  var toastNode = null;
  var toastTimer = null;
  function ensureToast() {
    if (toastNode) return toastNode;
    toastNode = el('div');
    toastNode.id = 'pm-toast';
    toastNode.setAttribute('role', 'status');
    toastNode.setAttribute('aria-live', 'polite');
    var icon = el('div', 'pm-toast-icon');
    icon.setAttribute('aria-hidden', 'true');
    var msg = el('span', 'pm-toast-msg');
    toastNode.appendChild(icon);
    toastNode.appendChild(msg);
    doc.body.appendChild(toastNode);
    return toastNode;
  }
  function showToast(message, type) {
    if (!message || !doc.body) return;
    var t = ensureToast();
    type = type || 'info';
    t.classList.remove('is-success', 'is-error');
    if (type === 'success') t.classList.add('is-success');
    if (type === 'error') t.classList.add('is-error');
    t.querySelector('.pm-toast-icon').textContent =
      type === 'success' ? '✓' : (type === 'error' ? '!' : 'i');
    t.querySelector('.pm-toast-msg').textContent = message;
    // reflow để hiệu ứng chạy lại nếu toast đang hiển thị
    void t.offsetWidth;
    t.classList.add('is-show');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () { t.classList.remove('is-show'); }, 3200);
  }
  window.PetMotion = { toast: showToast };

  // Thông báo từ máy chủ: giữ nguyên dòng chữ trong trang, chỉ thêm toast như trang đăng nhập
  function toastServerMessages() {
    var err = doc.querySelector('.loi[role="alert"]');
    var ok = doc.querySelector('.thanh-cong[role="status"]');
    if (err && err.textContent.trim()) showToast(err.textContent.trim().replace(/\s+/g, ' '), 'error');
    else if (ok && ok.textContent.trim()) showToast(ok.textContent.trim().replace(/\s+/g, ' '), 'success');
  }

  /* ------------------------------------------------------------------
   * 3. Gửi form: spinner trong nút + toast "Đang xử lý…"
   *    - KHÔNG disabled, KHÔNG đổi chữ, KHÔNG preventDefault → dữ liệu form
   *      (kể cả name/value của nút bấm) được gửi nguyên vẹn.
   * ------------------------------------------------------------------ */
  var busyButtons = [];
  function clearBusy() {
    busyButtons.forEach(function (b) {
      b.classList.remove('pm-loading');
      b.removeAttribute('aria-busy');
    });
    busyButtons = [];
  }
  doc.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;                         // form do JS riêng xử lý (chat AI…)
    var form = e.target;
    if (!form || form.tagName !== 'FORM') return;
    if (form.id === 'pet-ai-form') return;
    if (form.target && form.target !== '_self') return;     // mở tab mới: không treo spinner
    var method = (form.getAttribute('method') || 'get').toLowerCase();
    if (method !== 'post') return;                          // form tìm kiếm GET: giữ nhẹ nhàng

    var btn = e.submitter || form.querySelector('button[type="submit"], button:not([type])');
    if (btn && btn.tagName === 'BUTTON') {
      btn.classList.add('pm-loading');
      btn.setAttribute('aria-busy', 'true');
      busyButtons.push(btn);
    }
    showToast('Đang xử lý...', 'info');
    // Phòng trường hợp phản hồi là tệp tải về (trang không chuyển) → tự gỡ spinner
    window.setTimeout(clearBusy, 12000);
  });
  window.addEventListener('pageshow', clearBusy);           // nút Back: khôi phục nút

  /* ------------------------------------------------------------------ */
  function init() {
    buildBackground();
    window.setTimeout(toastServerMessages, 250);
  }
  if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
