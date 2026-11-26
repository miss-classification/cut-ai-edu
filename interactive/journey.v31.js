/* Guided transitions and learner observations; all model responses are recorded. */
(() => {
  'use strict';
  const q = s => document.querySelector(s);
  const qa = s => [...document.querySelectorAll(s)];
  let referenceKind = 'snow';
  const evidence = {
    snow: {base:'snow-reference', ratio:'960 / 608', label:'Recorded and generated snow', source:'Boreas · matched location', caption:'The same location, recorded in another season', description:'Top left: sunny source. Top right: depth-guided generation. Bottom left: edge-guided generation. Bottom right: real snow.', inspectTitle:'Inspect snow appearance',inspect:'Compare the road surface, distant visibility, vegetation, and illumination.',limitTitle:'Account for the different day',limit:'Locations were matched using camera poses. Traffic, foliage, viewpoint, and timing differ, so the real clip is an appearance reference rather than a pixel-aligned target.',question:'Can this real snowy drive verify every generated car and lane?',feedback:'The real drive was recorded on another day. It helps assess snow appearance, but different traffic and viewpoints prevent direct verification of every generated object.'},
    prompt:{base:'prompt-test',ratio:'960 / 226',label:'Generic and scene-aware prompts',source:'GOOSE · depth control · seed 101',caption:'Change the request while preserving the material',description:'Left: source. Center: generic drought prompt. Right: scene-aware drought prompt.',inspectTitle:'Follow the asphalt',inspect:'Inspect whether the surface remains asphalt as the surrounding snow and vegetation change.',limitTitle:'Keep the inference narrow',limit:'This example compares 2 prompts on one clip and seed. It does not establish that scene-aware prompts always improve quality.',question:'Does this one example prove that scene-aware prompts always work?',feedback:'One clip and seed support a local comparison. More scenes, seeds, and independent review are needed to assess reliability.'}
  };
  qa('[data-evidence]').forEach(button => button.addEventListener('click', () => {
    referenceKind = button.dataset.evidence;
    const e = evidence[referenceKind], v = q('#referenceVideo');
    v.pause();v.src=`research-media/${e.base}.mp4`;v.poster=`research-media/${e.base}.jpg`;v.style.aspectRatio=e.ratio;v.setAttribute('aria-label',e.description);v.load();
    for(const [field,id] of Object.entries({label:'referenceLabel',source:'referenceSource',caption:'referenceCaption',description:'referenceDescription',inspectTitle:'referenceInspectTitle',inspect:'referenceInspect',limitTitle:'referenceLimitTitle',limit:'referenceLimit',question:'referenceQuestion'})) q(`#${id}`).textContent=e[field];
    q('#referenceDownload').href=`research-media/${e.base}.mp4`;
    q('#promptDetails').hidden=referenceKind!=='prompt';
    q('#referenceFeedback').textContent='';
    qa('[data-reference-answer]').forEach(b=>b.setAttribute('aria-pressed','false'));
    qa('[data-evidence]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
  }));
  qa('[data-reference-answer]').forEach(button=>button.addEventListener('click',()=>{
    qa('[data-reference-answer]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    q('#referenceFeedback').textContent=(button.dataset.referenceAnswer==='no'?'Correct. ':'Reconsider the evidence. ')+evidence[referenceKind].feedback;
  }));
  let reviewCase='hood';
  qa('[data-case]').forEach(button=>button.addEventListener('click',()=>{
    reviewCase=button.dataset.case;
    q('#predictionQuestion').textContent=reviewCase==='day'?'Does the output satisfy night with rain?':'Does the frost transformation preserve the foreground?';
    q('#predictionFeedback').textContent='Make your own assessment, then compare it with the recorded responses.';
    qa('[data-prediction]').forEach(b=>b.setAttribute('aria-pressed','false'));
  }));
  qa('[data-prediction]').forEach(button=>button.addEventListener('click',()=>{
    qa('[data-prediction]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    const messages={retain:'Assessment recorded. Name the visual evidence that supports keeping this candidate.',reject:'Assessment recorded. Identify the requested change or preservation requirement that failed.',uncertain:'Assessment recorded. Specify what additional evidence would resolve the uncertainty.'};
    q('#predictionFeedback').textContent=messages[button.dataset.prediction]+' Now reveal the model’s responses.';
  }));
  if('IntersectionObserver' in window){
    const links=qa('.journey-nav a');
    const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{
      if(entry.isIntersecting){links.forEach(a=>{const on=a.getAttribute('href')===`#${entry.target.id}`;a.classList.toggle('current',on);if(on)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}
    }),{rootMargin:'-18% 0px -58% 0px',threshold:0});
    links.forEach(a=>{const target=q(a.getAttribute('href'));if(target)observer.observe(target);});
  }
})();

(() => {
  'use strict';
  const q=s=>document.querySelector(s);
  document.querySelectorAll('[data-demo-gate]').forEach(button=>button.addEventListener('click',()=>{
    const allExcluded=Number(button.dataset.demoGate)===97;
    document.querySelectorAll('[data-demo-gate]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
    q('#gateDemoReason').textContent=allExcluded?'All 3 street-fidelity values are below 97. Every candidate is excluded.':'Take 07 is excluded before scoring. Takes 03 and 04 remain eligible.';
    q('#gateDemoResult').textContent=allExcluded?'Retain none':'Take 04';
    q('#gateDemoResultNote').textContent=allExcluded?'There is no eligible candidate to rank.':'The balanced illustrative rubric ranks Take 04 above Take 03.';
  }));
  const annotations=window.CUT_FOG_ANNOTATIONS;
  if(!annotations)return;
  const select=q('#scoreExample');
  function inspectScores(changeMedia=false){
    const n=Number(select.value||4);const row=annotations.find(x=>x.n===n);
    q('#scoreObservation').textContent=row.observation;
    q('#scoreRationale').textContent=row.rationale;
    const a=Number(q('#fogWeight').value),b=Number(q('#structureWeight').value),c=Number(q('#stabilityWeight').value),sum=a+b+c;
    q('#scoreFormula').textContent=sum?`(${row.intensity} × ${a} + ${row.structure} × ${b} + ${row.stability} × ${c}) ÷ ${sum} = ${((row.intensity*a+row.structure*b+row.stability*c)/sum).toFixed(1)}`:'All weights are zero, so no weighted ranking is defined.';
    if(changeMedia){const video=q('#scoreExampleVideo');video.pause();video.src=`media/directors_cut_take${String(n).padStart(2,'0')}.mp4`;video.poster=`media/posters/take-${String(n).padStart(2,'0')}.jpg`;video.load();}
  }
  select.addEventListener('change',()=>inspectScores(true));
  document.querySelectorAll('[data-judge-weight]').forEach(input=>input.addEventListener('input',()=>inspectScores()));
  document.querySelectorAll('[data-judge-preset]').forEach(button=>button.addEventListener('click',()=>inspectScores()));
  inspectScores();
})();
