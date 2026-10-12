/* PET UI — dark/light theme, pet-photo hero, small joyful interactions. */
(function () {
  'use strict';
  if (window.__petUIReady) return;
  window.__petUIReady = true;

  var root = document.documentElement;
  var storageKey = 'pet-ui-theme';
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function getTheme() {
    try { return localStorage.getItem(storageKey) || 'light'; }
    catch (_) { return 'light'; }
  }
  function setTheme(theme) {
    root.setAttribute('data-theme', theme);
    var buttons = document.querySelectorAll('.pet-theme-toggle');
    buttons.forEach(function (button) {
      var dark = theme === 'dark';
      button.setAttribute('aria-label', dark ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối');
      button.setAttribute('title', dark ? 'Chuyển sang nền sáng' : 'Chuyển sang nền tối');
      button.innerHTML = '<span class="theme-icon" aria-hidden="true">' + (dark ? '☀️' : '🌙') + '</span><span>' + (dark ? 'Nền sáng' : 'Nền tối') + '</span>';
    });
  }
  setTheme(getTheme());

  function addThemeButton() {
    var header = document.querySelector('.thanh-dieu-huong');
    if (document.querySelector('.pet-theme-toggle')) return;
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'pet-theme-toggle';
    button.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      setTheme(next);
      try { localStorage.setItem(storageKey, next); } catch (_) {}
    });
    var userArea = document.querySelector('.pet-account-float') || (header && header.querySelector('.nguoi-dung'));
    if (userArea) userArea.insertBefore(button, userArea.firstChild);
    else if (header) header.appendChild(button);
    else { button.classList.add('pet-theme-floating'); document.body.appendChild(button); }
    setTheme(root.getAttribute('data-theme') || getTheme());
  }


  function revealCards() {
    if (reduceMotion || !('IntersectionObserver' in window)) return;
    var cards = document.querySelectorAll('.the-lien-ket');
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('pet-card-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    cards.forEach(function (card, index) {
      card.style.transitionDelay = (Math.min(index, 7) * 45) + 'ms';
      card.classList.add('pet-card-reveal');
      observer.observe(card);
    });
  }

  function addPawClick() {
    if (reduceMotion) return;
    document.addEventListener('click', function (event) {
      var target = event.target.closest && event.target.closest('button, .the-lien-ket');
      if (!target || target.classList.contains('pet-theme-toggle')) return;
      var paw = document.createElement('span');
      paw.className = 'pet-click-paw';
      paw.textContent = ['🐾', '✨', '💚'][Math.floor(Math.random() * 3)];
      paw.style.left = event.clientX + 'px';
      paw.style.top = event.clientY + 'px';
      document.body.appendChild(paw);
      window.setTimeout(function () { paw.remove(); }, 850);
    }, { passive: true });
  }

  function init() {
    addThemeButton();
    revealCards();
    addPawClick();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
