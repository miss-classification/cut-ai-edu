(() => {
  'use strict';
  const card = document.getElementById('paint-the-trail');
  if (!card) return;
  const toggle = card.querySelector('[data-trail-toggle]');
  const external = card.querySelector('[data-trail-external]');
  const panel = card.querySelector('[data-trail-panel]');
  const mount = card.querySelector('[data-trail-frame]');
  const status = card.querySelector('[data-trail-status]');
  const fallback = card.querySelector('[data-trail-fallback]');
  const help = card.querySelector('[data-trail-help]');
  const gallery = document.getElementById('selected-comparisons');
  const offline = 'You are offline. The recorded comparisons below are available in this lesson.';
  let frame = null;

  function note(message) {
    status.textContent = message;
    status.hidden = !message;
    fallback.hidden = !frame && navigator.onLine !== false;
    help.hidden = !frame;
  }
  function close(message = '') {
    if (frame) frame.remove();
    frame = null;
    panel.hidden = true;
    toggle.textContent = 'Explore gallery here';
    toggle.setAttribute('aria-expanded', 'false');
    note(message);
  }
  function open() {
    if (navigator.onLine === false) { note(offline); return; }
    if (frame) return;
    card.closest('#new-worlds')?.querySelectorAll('video').forEach(video => video.pause());
    frame = document.createElement('iframe');
    frame.title = 'Paint the Trail: gallery of weather comparisons';
    frame.setAttribute('allow', 'fullscreen');
    frame.setAttribute('allowfullscreen', '');
    frame.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
    frame.src = external.href;
    panel.hidden = false;
    mount.append(frame);
    toggle.textContent = 'Close gallery';
    toggle.setAttribute('aria-expanded', 'true');
    note('');
  }
  toggle.addEventListener('click', () => frame ? close() : open());
  toggle.hidden = false;
  card.querySelector('[data-trail-offline]').addEventListener('click', () => {
    close();
    if (gallery) {
      gallery.open = true;
      gallery.querySelector('summary')?.focus({preventScroll: true});
    }
  });
  window.addEventListener('offline', () => close(offline));
  window.addEventListener('online', () => note(''));
  window.addEventListener('pagehide', () => close());
  window.addEventListener('hashchange', () => {
    if (frame && !['#paint-the-trail', '#new-worlds'].includes(location.hash)) close();
  });
  document.getElementById('motionToggle')?.addEventListener('click', () => {
    if (frame && document.documentElement.classList.contains('motion-paused')) {
      close('Gallery closed. You can reopen it when you want to continue.');
    }
  });
  if (navigator.onLine === false) note(offline);
})();
