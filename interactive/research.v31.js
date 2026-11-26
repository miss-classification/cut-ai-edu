/* Offline playback and evidence controls. No model calls or analytics. */
(() => {
  'use strict';
  const data = window.CUT_RESEARCH;
  if (!data) return;
  const one = (s, root = document) => root.querySelector(s);
  const all = (s, root = document) => [...root.querySelectorAll(s)];
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let labPaused = reduced.matches;
  const paused = () => labPaused || document.documentElement.classList.contains('motion-paused');
  const play = video => {
    if (paused()) return;
    video.play().catch(() => {});
  };
  function changeVideo(video, base, label, posterExt='jpg') {
    video.pause();
    video.src = `${base}.mp4`;
    video.poster = `${base}.${posterExt}`;
    video.setAttribute('aria-label', label);
    video.load();
  }
  function selectButton(buttons, selected, key) {
    buttons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset[key] === selected)));
  }
  all('[data-showcase]').forEach(root => {
    const video = one('[data-showcase-video]', root);
    const buttons = all('[data-clip]', root);
    buttons.forEach(button => button.addEventListener('click', () => {
      const clip = data.clips.find(c => c.id === button.dataset.clip);
      const wasPlaying = !video.paused;
      selectButton(buttons, clip.id, 'clip');
      changeVideo(video, clip.base, `${clip.dataset}: ${clip.title}. ${clip.description}`);
      video.style.aspectRatio = clip.ratio || '960 / 318';
      one('[data-clip-title]', root).textContent = clip.title;
      one('[data-clip-description]', root).textContent = clip.description;
      one('[data-clip-meta]', root).textContent = `${clip.dataset} · ${typeof clip.seed === "number" ? `seed ${clip.seed}` : "seeds on panel labels"} · ${clip.license}`;
      one('[data-clip-inspect]', root).textContent = clip.inspect;
      one('[data-clip-limit]', root).textContent = clip.limit;
      one('[data-clip-download]', root).href = `${clip.base}.mp4`;
      if (wasPlaying) play(video);
    }));
    one('[data-replay]', root).addEventListener('click', () => {
      video.currentTime = 0;
      // An explicit replay request is allowed even when ambient motion is paused.
      video.play().catch(() => {});
    });
  });
  const pauseButton = one('#labPause');
  if (pauseButton) {
    const updatePause = () => {
      document.documentElement.classList.toggle('cut-lab-paused', labPaused);
      pauseButton.textContent = labPaused ? 'Resume motion' : 'Pause motion';
      pauseButton.setAttribute('aria-pressed', String(labPaused));
      if (labPaused) all('video').forEach(v => v.pause());
    };
    pauseButton.addEventListener('click', () => { labPaused = !labPaused; updatePause(); });
    reduced.addEventListener('change', e => {labPaused = e.matches; updatePause();});
    updatePause();
  }
  // Preview the showcase once when it enters view; respect reduced motion and pause controls.
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) entry.target.pause();
      else if (entry.target.hasAttribute('data-showcase-video') && !entry.target.dataset.previewStarted && !paused()) {
        entry.target.dataset.previewStarted = 'true';
        play(entry.target);
      }
    }), {threshold: 0.05});
    all('.cut-player video').forEach(v => observer.observe(v));
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) all('.cut-player video').forEach(v => v.pause());
  });
  // Prevent several research clips from competing for attention.
  all('.cut-player video').forEach(v => v.addEventListener('play', () => {
    all('.cut-player video').forEach(other => { if (other !== v) other.pause(); });
  }));
  let currentCase = data.cases.find(c=>c.id==='hood');
  const caseVideo = one('#caseVideo');
  if (caseVideo) {
    const reveal = one('#revealJudge');
    const results = one('#judgeResults');
    function applyGates() {
      const reasons = [];
      if (one('#objectGate').checked && currentCase.objectFailure) reasons.push('unrequested foreground object');
      if (one('#weatherGate').checked && currentCase.weatherFailure) reasons.push('requested nighttime lighting missing');
      const result = one('#gateResult');
      result.dataset.blocked = String(reasons.length > 0);
      result.textContent = reasons.length ? `Excluded by the selected rule: ${reasons.join('; ')}.` :
        (one('#objectGate').checked || one('#weatherGate').checked ? 'No selected rule excludes this example. Further review is still required.' : 'Review required. No exclusion rules are active.');
    }
    function updateCase() {
      selectButton(all('[data-case]'), currentCase.id, 'case');
      one('#caseTitle').textContent = (currentCase.id==='day'?'Case 2: night rain':'Case 1: frost at dawn');
      one('#caseDescription').textContent = (currentCase.id==='day'?'Inspect the light on the road and in the trees.':'Follow the foreground from the first frame to the last.');
      one('#caseMeta').textContent = `GOOSE · seed ${currentCase.seed} · CC BY-SA 4.0`;
      one('#blindScore').textContent = `${currentCase.blind.overall} / 5`;
      one('#structureScore').textContent = `${currentCase.paired.structure_preserved} / 5`;
      one('#conditionScore').textContent = `${currentCase.paired.condition_achieved} / 5`;
      const quote = one('#judgeQuote');
      const hood = currentCase.id === 'hood';
      const wording = hood ? 'blue and pink striped hood of the car' : 'the scene is still bright and appears to be daytime, not night';
      quote.replaceChildren(document.createTextNode(`“${wording}”`));
      const cite = document.createElement('cite');
      cite.textContent = `Listed under ${hood ? 'added_objects' : 'contradictions'} in the paired response.`;
      quote.append(cite);
      one('#caseInterpretation').textContent = hood ? 'The paired review names the new hood but still gives structure 5/5. A rule against invented foreground objects would reject this clip.' : 'The road looks wet. Only the paired review checks the requested time of day and flags the daylight.';
      one('#blindJSON').textContent = JSON.stringify(currentCase.blind, null, 2);
      one('#pairedJSON').textContent = JSON.stringify(currentCase.paired, null, 2);
      applyGates();
    }
    all('[data-case]').forEach(button => button.addEventListener('click', () => {
      currentCase = data.cases.find(c => c.id === button.dataset.case);
      selectButton(all('[data-case]'), currentCase.id, 'case');
      changeVideo(caseVideo, 'studio-media/case-'+currentCase.id+'.v31', currentCase.id==='day'?'Requested edit: night rain. Source on the left.':'Requested edit: frost at dawn. Source on the left.','png');
      results.hidden = true;
      reveal.setAttribute('aria-expanded', 'false');
      reveal.textContent = 'Reveal recorded judgment';
      updateCase();
    }));
    reveal.addEventListener('click', () => {
      results.hidden = !results.hidden;
      reveal.setAttribute('aria-expanded', String(!results.hidden));
      reveal.textContent = results.hidden ? 'Reveal recorded judgment' : 'Hide recorded judgment';
    });
    all('.cut-gates input').forEach(el => el.addEventListener('change', applyGates));
    changeVideo(caseVideo, 'studio-media/case-'+currentCase.id+'.v31', currentCase.id==='day'?'Requested edit: night rain. Source on the left.':'Requested edit: frost at dawn. Source on the left.','png');
    updateCase();
  }
  const schedule = one('#actorSchedule');
  if (schedule) {
    function showActors(count) {
      const point = data.scaling.find(x => x.num_actors === count);
      selectButton(all('[data-actors]'), String(count), 'actors');
      schedule.replaceChildren();
      for (let i = 0; i < count; i++) {
        const row = document.createElement('div'); row.className = 'cut-worker';
        const label = document.createElement('span'); label.textContent = `GPU ${i+1}`;
        const jobs = document.createElement('div');
        jobs.setAttribute('aria-label', `${24/count} illustrative requests`);
        for (let j=0; j<24/count; j++) {
          const block = document.createElement('i'); block.className = 'cut-task';
          block.style.setProperty('--delay', `${j * 0.045}s`); block.setAttribute('aria-hidden', 'true');
          jobs.append(block);
        }
        row.append(label,jobs); schedule.append(row);
      }
      const seconds = Math.round(point.wall_s);
      one('#batchTime').textContent = `${Math.floor(seconds/60)} min ${seconds%60} s`;
      one('#batchSpeed').textContent = `${(data.scaling[0].wall_s/point.wall_s).toFixed(2)}×`;
      one('#requestTime').textContent = `${point.per_request_child_s_median.toFixed(2)} s`;
    }
    all('[data-actors]').forEach(b => b.addEventListener('click', () => showActors(Number(b.dataset.actors))));
    showActors(8);
  }
})();
