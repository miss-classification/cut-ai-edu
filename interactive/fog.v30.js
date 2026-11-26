const takes=[
 {n:1,seed:2025,file:'directors_cut_take01.mp4',note:'stable, conservative'},
 {n:2,seed:7319,file:'directors_cut_take02.mp4',note:'atmospheric, pink cast'},
 {n:3,seed:18427,file:'directors_cut_take03.mp4',note:'sharp, weak fog'},
 {n:4,seed:29063,file:'directors_cut_take04.mp4',note:'balanced, coherent'},
 {n:5,seed:41851,file:'directors_cut_take05.mp4',note:'stable, conservative'},
 {n:6,seed:57203,file:'directors_cut_take06.mp4',note:'clean, lighter fog'},
 {n:7,seed:70439,file:'directors_cut_take07.mp4',note:'dramatic smoke-like plume'},
 {n:8,seed:91873,file:'directors_cut_take08.mp4',note:'strong mood, light bloom'}
];
const budgetNotes={1:'N=1 gives one candidate to inspect. It can still be rejected.',2:'With 2 candidates you can compare the same request across seeds.',4:'At N = 4, look for fog that leaves the street readable.',8:'The pool doubles. The judge works harder, but the top-ranked result may stay.'};
let budget=1,selected=null,allPlaying=false;
const grid=document.querySelector('#takeGrid');

const episodeButtons=[...document.querySelectorAll('[data-episode-target]')];
const episodePanels=[...document.querySelectorAll('.story-beat')];
const introMotionQuery=window.matchMedia('(prefers-reduced-motion: reduce)');
let introTimer=null;
let motionPaused=introMotionQuery.matches;
let introAuto=false;
let introInView=true;
function stopIntroAuto(){introAuto=false;clearTimeout(introTimer);document.querySelector('.lean-episodes').classList.add('user-controlled')}
function setMotionPaused(paused){
 motionPaused=paused;
 document.documentElement.classList.toggle('motion-paused',paused);
 const toggle=document.querySelector('#motionToggle');
 toggle.setAttribute('aria-pressed',String(paused));
 toggle.textContent=paused?'Resume motion':'Pause motion';
 if(paused){
  stopIntroAuto();
  document.querySelectorAll('video').forEach(video=>video.pause());
  allPlaying=false;
  document.querySelector('#playAll').textContent='▶ Play all';
  return;
 }
 syncEpisodeVideos();
 ['#heroVideoA','#heroVideoB'].forEach(id=>{const v=document.querySelector(id),b=v.getBoundingClientRect();if(b.top<window.innerHeight&&b.bottom>0)v.play().catch(()=>{})});
 const judge=document.querySelector('#judgeVideo');
 if(!document.querySelector('#selector').classList.contains('hidden'))judge.play().catch(()=>{});

}
function scheduleIntro(targetId){
 clearTimeout(introTimer);
 if(!introAuto||!introInView)return;
 const index=episodePanels.findIndex(panel=>panel.id===targetId);
 if(index<episodePanels.length-1)introTimer=setTimeout(()=>activateEpisode(episodePanels[index+1].id),9000);
}
function syncEpisodeVideos(){
 episodePanels.forEach(panel=>panel.querySelectorAll('[data-episode-video]').forEach(video=>{
  const shouldPlay=!panel.hidden&&introInView&&!motionPaused;
  shouldPlay?video.play().catch(()=>{}):video.pause();
 }));
}
function activateEpisode(targetId,moveFocus=false){
 episodeButtons.forEach(button=>{
  const active=button.dataset.episodeTarget===targetId;
  button.setAttribute('aria-selected',String(active));
  button.tabIndex=active?0:-1;
 });
 episodePanels.forEach(panel=>{
  const active=panel.id===targetId;
  panel.hidden=!active;
  panel.querySelectorAll('[data-episode-video]').forEach(video=>{
   video.playbackRate=Number(video.dataset.loopSpeed||1);
   const shouldPlay=active&&introInView&&!motionPaused;
   shouldPlay?video.play().catch(()=>{}):video.pause();
  });
 });
 const panel=document.querySelector(`#${targetId}`);
 if(moveFocus){
  panel.focus({preventScroll:true});
  document.querySelector('.lean-episodes').scrollIntoView({behavior:'smooth',block:'start'});
 }
 scheduleIntro(targetId);
}
episodeButtons.forEach((button,index)=>{
 button.addEventListener('click',()=>{stopIntroAuto();activateEpisode(button.dataset.episodeTarget)});
 button.addEventListener('keydown',event=>{
  if(!['ArrowLeft','ArrowRight'].includes(event.key))return;
  event.preventDefault();
  stopIntroAuto();
  const direction=event.key==='ArrowRight'?1:-1;
  const next=episodeButtons[(index+direction+episodeButtons.length)%episodeButtons.length];
  next.focus();
  activateEpisode(next.dataset.episodeTarget);
 });
});
document.querySelectorAll('[data-next-episode]').forEach(button=>button.addEventListener('click',()=>{stopIntroAuto();activateEpisode(button.dataset.nextEpisode,true)}));
document.querySelector('.lean-episodes').addEventListener('focusin',stopIntroAuto);
if('IntersectionObserver' in window){
 const introObserver=new IntersectionObserver(entries=>{
  introInView=entries[0].isIntersecting;
  if(introInView){
   const active=episodePanels.find(panel=>!panel.hidden);
   if(active)scheduleIntro(active.id);
  }else clearTimeout(introTimer);
  syncEpisodeVideos();
 },{threshold:.08});
 introObserver.observe(document.querySelector('.lean-episodes'));
}

document.querySelectorAll('[data-temporal-offset]').forEach(video=>{
 const setOffset=()=>{
  const offset=Number(video.dataset.temporalOffset||0);
  if(Number.isFinite(video.duration)&&video.duration>0)video.currentTime=offset%video.duration;
 };
 video.readyState>=1?setOffset():video.addEventListener('loadedmetadata',setOffset,{once:true});
});

const introWeatherOptions={
 fog:{file:'directors_cut_take06.mp4',label:'Fog',aria:'Restaged dashcam video with fog'},
 rain:{file:'weather_replication_rain_take04.mp4',label:'Rain',aria:'Restaged dashcam video with rain'},
 snow:{file:'weather_replication_snow_take04.mp4',label:'Snow',aria:'Restaged dashcam video with snow'}
};
document.querySelectorAll('[data-intro-weather]').forEach(button=>button.addEventListener('click',()=>{
 stopIntroAuto();
 document.querySelectorAll('[data-intro-weather]').forEach(item=>item.setAttribute('aria-pressed','false'));
 button.setAttribute('aria-pressed','true');
 const option=introWeatherOptions[button.dataset.introWeather];
 const video=document.querySelector('#introWeatherVideo');
 document.querySelector('#introWeatherLabel').textContent=option.label;
 document.querySelector('#cosmosCondition').textContent=`weather: ${option.label.toLowerCase()}`;
 video.src=`media/${option.file}`;
 document.querySelector('#inspectOutput').href=video.getAttribute('src');
 video.setAttribute('aria-label',option.aria);
 if(introInView&&!motionPaused)video.play().catch(()=>{});
}));
activateEpisode('episode2');

function renderTakes(){
 grid.innerHTML=takes.slice(0,budget).map(t=>`<article class="take-card ${t.n>budget?'locked-out':''} ${selected===t.n?'selected':''}" data-take="${t.n}">
  <span class="take-index">TAKE ${String(t.n).padStart(2,'0')}</span>
  <video src="media/${t.file}" poster="media/posters/take-${String(t.n).padStart(2,'0')}.jpg" controls muted loop playsinline preload="metadata" aria-label="Fog candidate Take ${t.n}"></video><p class="candidate-media-error" hidden>Playback could not start. <a href="media/${t.file}" download>Download this candidate</a>.</p>
  <div class="take-meta"><button type="button" aria-label="Choose Take ${t.n}" aria-pressed="${selected===t.n}"><b>Take ${String(t.n).padStart(2,'0')}</b><small>seed ${t.seed.toLocaleString()}</small></button><span class="pick-dot" aria-hidden="true"></span></div>
 </article>`).join('');
 grid.querySelectorAll('.take-card:not(.locked-out)').forEach(card=>card.querySelector('button').addEventListener('click',()=>chooseTake(Number(card.dataset.take))));
 grid.querySelectorAll('video').forEach(v=>v.addEventListener('error',()=>{v.parentElement.querySelector('.candidate-media-error').hidden=false;}));
 document.querySelector('#visibleCount').textContent=`${budget} ${budget===1?'take':'takes'} on screen`;
 if(allPlaying) playVisible();
}
function updateSelectionDock(){
 const ready=selected!==null&&budget>=4;
 document.querySelector('#lockChoice').disabled=!ready;
 if(selected===null){document.querySelector('#selectionText').textContent='Inspect the visible candidates. Select a take.';return;}
 const take=`Take ${String(selected).padStart(2,'0')}`;
 document.querySelector('#selectionText').textContent=budget<4?`${take} is selected. Expand the pool to N=4 or N=8 to submit.`:`Your judge currently ranks ${take} first.`;
}
function chooseTake(n){selected=n;for(const card of grid.querySelectorAll('[data-take]')){const on=Number(card.dataset.take)===n;card.classList.toggle('selected',on);card.querySelector('button').setAttribute('aria-pressed',String(on))}updateSelectionDock();}
function setBudget(n){if(n!==budget)selected=null;budget=n;document.querySelectorAll('[data-budget]').forEach(b=>{const on=Number(b.dataset.budget)===n;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on))});document.querySelector('#budgetOutput').textContent=`${n} ${n===1?'take':'takes'}`;document.querySelector('#budgetFill').style.width=`${n/8*100}%`;document.querySelector('#budgetNote').textContent=budgetNotes[n];document.querySelector('#allNCount').textContent=`${n} ${n===1?'output':'outputs'}`;renderTakes();updateSelectionDock();renderJudge();}
function visibleVideos(){return [...grid.querySelectorAll('.take-card:not(.locked-out) video')]}
function playVisible(){if(motionPaused)setMotionPaused(false);allPlaying=true;visibleVideos().forEach(v=>v.play().catch(()=>{}));document.querySelector('#playAll').textContent='❚❚ Pause all'}
function pauseVisible(){allPlaying=false;visibleVideos().forEach(v=>v.pause());document.querySelector('#playAll').textContent='▶ Play all'}

document.querySelectorAll('[data-budget]').forEach(b=>b.addEventListener('click',()=>setBudget(Number(b.dataset.budget))));
document.querySelector('#playAll').addEventListener('click',()=>allPlaying?pauseVisible():playVisible());
document.querySelector('#restartAll').addEventListener('click',()=>{visibleVideos().forEach(v=>v.currentTime=0);playVisible()});
document.querySelector('#heroReplay').addEventListener('click',()=>{if(motionPaused)setMotionPaused(false);['#heroVideoA','#heroVideoB'].forEach(id=>{const v=document.querySelector(id);v.currentTime=0;v.play().catch(()=>{})})});
document.querySelectorAll('[data-hook-answer]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-hook-answer]').forEach(x=>{x.classList.remove('selected');x.setAttribute('aria-pressed','false')});b.classList.add('selected');b.setAttribute('aria-pressed','true');const picked=Number(b.dataset.hookAnswer);document.querySelector('#hookFeedback').textContent=picked===0?'Neither candidate needs to be retained. State which condition or scene constraint each one fails.':picked===3?'You favored street fidelity. Another reviewer may value the requested weather more.':'You favored atmosphere. Another reviewer may reject the smoke-like plume.';document.querySelector('#hookTwist').classList.remove('hidden');document.querySelector('#startAudition').classList.remove('hidden');}));
document.querySelector('#lockChoice').addEventListener('click',()=>{const reveal=document.querySelector('#reveal');const selector=document.querySelector('#selector');reveal.classList.remove('hidden');selector.classList.remove('hidden');const same=selected===4;document.querySelector('#choiceComparison').innerHTML=same?'<span><b>Your choice matches the balanced rubric.</b></span><span>Take 04 balances fog intensity, street fidelity, and stability.</span>':`<span>You chose <b>Take ${String(selected).padStart(2,'0')}</b>.</span><span>Which criterion would explain the difference?</span>`;try{localStorage.setItem('cut-choice',String(selected))}catch{}reveal.focus({preventScroll:true});reveal.scrollIntoView({behavior:motionPaused?'auto':'smooth'});if(!motionPaused)document.querySelector('#judgeVideo').play().catch(()=>{});});

const judgeScores=[
 {n:1,fog:46,structure:91,stability:90},
 {n:2,fog:72,structure:70,stability:64},
 {n:3,fog:25,structure:96,stability:93},
 {n:4,fog:84,structure:91,stability:89},
 {n:5,fog:50,structure:89,stability:87},
 {n:6,fog:58,structure:92,stability:90},
 {n:7,fog:96,structure:54,stability:48},
 {n:8,fog:86,structure:68,stability:61}
];
const judgePresets={
 balanced:{fog:40,structure:35,stability:25},
 fidelity:{fog:5,structure:55,stability:40},
 fog:{fog:100,structure:0,stability:0}
};
const judgeReasons={
 1:'Your rubric rewards coherence more than fog strength.',
 2:'Your rubric accepts a color shift in exchange for atmosphere.',
 3:'Your rubric rewards structure and stability, even though the fog is weak.',
 4:'Your rubric balances the requested weather with a coherent street.',
 5:'Your rubric favors a conservative and stable edit.',
 6:'Your rubric favors a clean street and lighter fog.',
 7:'Your rubric rewards maximum atmosphere, even though the fog resembles smoke.',
 8:'Your rubric tolerates light bloom in exchange for strong mood.'
};
const judgeInputs={fog:document.querySelector('#fogWeight'),structure:document.querySelector('#structureWeight'),stability:document.querySelector('#stabilityWeight')};
function currentJudgeWeights(){return Object.fromEntries(Object.entries(judgeInputs).map(([key,input])=>[key,Number(input.value)]))}
function renderJudge(){
 const weights=currentJudgeWeights();
 Object.entries(weights).forEach(([key,value])=>document.querySelector(`#${key}WeightValue`).textContent=value);
 const total=weights.fog+weights.structure+weights.stability;
 const minStructure=Number(document.querySelector('#fogStructureGate').value);
 const minStability=Number(document.querySelector('#fogStabilityGate').value);
 document.querySelector('#fogStructureGateValue').textContent=minStructure;
 document.querySelector('#fogStabilityGateValue').textContent=minStability;
 const eligible=judgeScores.filter(c=>c.n<=budget && c.structure>=minStructure && c.stability>=minStability);
 document.querySelector('#fogEligible').textContent=`${eligible.length} of ${budget} candidates pass the thresholds.`;
 const outputVideo=document.querySelector('#judgeVideo');
 if(!eligible.length){
  document.querySelector('#judgeComposite').textContent='–';
  document.querySelector('#judgeTake').textContent='–';
  document.querySelector('#judgeTitle').textContent='Retain none';
  document.querySelector('#judgeReason').textContent='Every candidate fails at least one threshold. Adjust the requirements or generate a new pool.';
  document.querySelector('#judgeLeaderboard').innerHTML='';
  outputVideo.pause();outputVideo.hidden=true;return;
 }
 outputVideo.hidden=false;
 document.querySelectorAll('[data-judge-preset]').forEach(button=>{const preset=judgePresets[button.dataset.judgePreset];const active=Object.keys(weights).every(key=>weights[key]===preset[key]);button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active))});
 if(total===0){document.querySelector('#judgeComposite').textContent='0.0';document.querySelector('#judgeTake').textContent='--';document.querySelector('#judgeTitle').textContent='No decision';document.querySelector('#judgeReason').textContent='Raise a priority so the judge has a rule to apply.';document.querySelector('#judgeLeaderboard').innerHTML='';outputVideo.pause();outputVideo.hidden=true;return;}
 const ranked=eligible.map(candidate=>({...candidate,score:(candidate.fog*weights.fog+candidate.structure*weights.structure+candidate.stability*weights.stability)/total})).sort((a,b)=>b.score-a.score);
 const winner=ranked[0];
 const take=takes.find(item=>item.n===winner.n);
 document.querySelector('#judgeComposite').textContent=winner.score.toFixed(1);
 document.querySelector('#judgeTake').textContent=String(winner.n).padStart(2,'0');
 document.querySelector('#judgeTitle').textContent=`Take ${String(winner.n).padStart(2,'0')}`;
 document.querySelector('#judgeReason').textContent=judgeReasons[winner.n];
 const video=document.querySelector('#judgeVideo');
 const source=`media/${take.file}`;
 if(video.getAttribute('src')!==source){video.src=source;video.setAttribute('aria-label',`Current judge winner, Take ${winner.n}`);if(!motionPaused&&!document.querySelector('#selector').classList.contains('hidden'))video.play().catch(()=>{})}
 document.querySelector('#judgeLeaderboard').innerHTML=ranked.slice(0,3).map((candidate,index)=>`<div class="leaderboard-row"><span>${index+1}</span><b>Take ${String(candidate.n).padStart(2,'0')}</b><i><em style="width:${candidate.score}%"></em></i><strong>${candidate.score.toFixed(1)}</strong></div>`).join('');
}
Object.values(judgeInputs).forEach(input=>input.addEventListener('input',renderJudge));
document.querySelectorAll('.fog-gates input').forEach(input=>input.addEventListener('input',renderJudge));
document.querySelectorAll('[data-judge-preset]').forEach(button=>button.addEventListener('click',()=>{const preset=judgePresets[button.dataset.judgePreset];Object.entries(preset).forEach(([key,value])=>judgeInputs[key].value=value);renderJudge()}));

const weather={
 fog:{count:8,prompt:'Request: add moderate fog and soften distant buildings.',prefix:'directors_cut'},
 rain:{count:4,prompt:'Request: show steady rain, a wet road, and reflections.',prefix:'weather_replication_rain'},
 snow:{count:4,prompt:'Request: add light to moderate snowfall and a thin layer of snow on the sidewalks.',prefix:'weather_replication_snow'}
};
function renderWeather(kind){const w=weather[kind];document.querySelector('#weatherPrompt').textContent=w.prompt;document.querySelector('#weatherGrid').innerHTML=Array.from({length:w.count},(_,i)=>{const n=i+1;return `<article class="weather-card"><video src="media/${w.prefix}_take${String(n).padStart(2,'0')}.mp4" poster="${kind==='fog'?'media/posters/take-':'studio-media/'+kind+'-'}${String(n).padStart(2,'0')}.jpg" muted loop playsinline controls preload="none" aria-label="${kind} Take ${n}"></video><div><b>${kind[0].toUpperCase()+kind.slice(1)} · Take ${String(n).padStart(2,'0')}</b><small>seed ${takes[i].seed.toLocaleString()}</small></div></article>`}).join('')}
document.querySelectorAll('[data-weather]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-weather]').forEach(x=>x.setAttribute('aria-pressed','false'));b.setAttribute('aria-pressed','true');renderWeather(b.dataset.weather)}));

const solved=new Set();document.querySelectorAll('.quiz-card button').forEach(b=>b.addEventListener('click',()=>{const card=b.closest('.quiz-card');if(solved.has(card.dataset.question))return;card.querySelectorAll('button').forEach(x=>x.disabled=true);const good=b.dataset.correct==='true';b.classList.add(good?'correct':'wrong');if(!good)card.querySelector('[data-correct="true"]').classList.add('correct');const explanation=card.dataset.question==='1'?'Everything was fixed except the random seed.':'More candidates only help when the selector can rank them reliably.';card.querySelector('.quiz-feedback').textContent=good?`Correct. ${explanation}`:`Review the highlighted answer. ${explanation}`;solved.add(card.dataset.question);document.querySelector('#completion span').textContent=`${solved.size} / 2`;document.querySelector('#completion p').textContent=solved.size===2?'You can now explain the whole idea: generate options, then judge them well.':'1 more to go.';}));
document.querySelector('#resetLesson').addEventListener('click',()=>{try{localStorage.removeItem('cut-choice')}catch{}location.reload()});
renderTakes();renderJudge();renderWeather('fog');

document.querySelector('#motionToggle').addEventListener('click',()=>setMotionPaused(!motionPaused));
if(introMotionQuery.addEventListener)introMotionQuery.addEventListener('change',event=>{if(event.matches)setMotionPaused(true)});
setMotionPaused(motionPaused);
