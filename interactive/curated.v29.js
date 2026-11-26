/* Selected comparisons use supplied media. No model scoring runs in this viewer. */
(() => {
  'use strict';
  const entries = window.CUT_CURATED;
  const panel = document.querySelector('#selected-comparisons');
  if (!entries || !panel) return;
  const q = selector => panel.querySelector(selector);
  const groups = [...panel.querySelectorAll('[data-curated-group]')];
  const video = q('#curatedVideo');
  const choices = q('#curatedChoices');
  let group = 'terrain';
  let current = entries.find(item => item.group === group);
  const paused = () => document.documentElement.classList.contains('motion-paused') ||
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function updateMedia() {
    const wasPlaying = !video.paused;
    video.pause();
    video.src = `${current.base}.mp4`;
    video.poster = `${current.base}.jpg`;
    video.style.aspectRatio = current.ratio;
    video.setAttribute('aria-label', `${current.title}. Recorded source on the left and generated variant on the right. ${current.description}`);
    video.load();
    q('#curatedTitle').textContent = current.title;
    q('#curatedDescription').textContent = current.description;
    q('#curatedMeta').textContent = `${current.dataset} · seed ${current.seed}`;
    q('#curatedPreserve').textContent = current.preserve;
    q('#curatedInspect').textContent = current.inspect;
    q('#curatedAuthor').textContent = current.attribution;
    q('#curatedSource').href = current.source_url;
    q('#curatedLicense').href = current.license_url;
    q('#curatedLicense').textContent = current.license;
    q('#curatedDownload').href = `${current.base}.mp4`;
    q('#curatedError').hidden = true;
    choices.querySelectorAll('button').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.curatedClip === current.id));
    });
    if (wasPlaying && panel.open && !paused()) video.play().catch(() => {});
  }

  function renderChoices() {
    choices.replaceChildren();
    entries.filter(item => item.group === group).forEach(item => {
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.curatedClip = item.id;
      button.textContent = item.label;
      button.setAttribute('aria-pressed', String(item.id === current.id));
      button.addEventListener('click', () => { current = item; updateMedia(); });
      choices.append(button);
    });
  }

  groups.forEach(button => button.addEventListener('click', () => {
    group = button.dataset.curatedGroup;
    current = entries.find(item => item.group === group);
    groups.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    renderChoices();
    updateMedia();
  }));
  panel.addEventListener('toggle', () => {
    q('.curated-open-label').textContent = panel.open ? 'Close comparisons' : 'Open comparisons';
    if (!panel.open) video.pause();
    else if (!paused()) video.play().catch(() => {});
  });
  q('#curatedReplay').addEventListener('click', () => {
    video.currentTime = 0;
    video.play().catch(() => {});
  });
  video.addEventListener('error', () => { q('#curatedError').hidden = false; });
  renderChoices();
  // Keep the initial source unloaded until the viewer is opened or playback is requested.
})();
