(() => {
 'use strict';
 const q=s=>document.querySelector(s),all=s=>Array.from(document.querySelectorAll(s));
 const stops=all('[data-stop]'),reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 let paused=reduced.matches,step=0,n=4,rule='balanced',gate=0,caseId='hood',assessed=null;
 const play=v=>{if(!paused&&v&&!v.hidden){const p=v.play();if(p)p.catch(()=>{})}};
 const press=(name,value)=>all('[data-'+name+']').forEach(b=>b.setAttribute('aria-pressed',String(b.getAttribute('data-'+name)===String(value))));
 function loadVideo(v,src,poster,name){
  if(v.getAttribute('src')!==src){v.pause();v.setAttribute('src',src);if(poster)v.setAttribute('poster',poster);v.load()}
  if(name)v.setAttribute('aria-label',name);
 }
 function control(name,handler){all('[data-'+name+']').forEach(b=>b.addEventListener('click',()=>handler(b.getAttribute('data-'+name))))}
 function rankFog(){
  const pool=window.CUT_FOG_ANNOTATIONS.filter(row=>row.n<=n);
  const eligible=pool.filter(row=>row.structure>=gate).map(row=>({row,score:rule==='intensity'?row.intensity:(40*row.intensity+35*row.structure+25*row.stability)/100})).sort((a,b)=>b.score-a.score||a.row.n-b.row.n);
  const top=eligible[0],video=q('#pdWinnerVideo');press('pd-n',n);press('pd-gate',gate);press('pd-rule',rule);
  q('#pdEligible').textContent=eligible.length+' of '+n+' eligible.';
  q('#pdPolicy').textContent='Keep all: '+n+' retained.  With this rule: '+(top?1:0)+' retained.';
  if(!top){q('#pdCalculation').textContent='Apply the minimum requirement first. Only surviving clips receive a rank.';video.pause();video.hidden=true;q('#pdWinner').textContent='Retain none';q('#pdEvidence').textContent='No take meets the minimum street fidelity. There is nothing eligible to rank.';return}
  const id=String(top.row.n).padStart(2,'0');
  q('#pdCalculation').textContent=rule==='intensity'?'Intensity only: '+top.row.intensity+' out of 100. Street fidelity and stability carry zero weight.':'Fog '+top.row.intensity+' × 0.40 + street '+top.row.structure+' × 0.35 + stability '+top.row.stability+' × 0.25 = '+top.score.toFixed(1)+'.';
  q('#pdWinner').textContent='Take '+id+' · '+top.score.toFixed(1)+'/100';q('#pdEvidence').textContent=top.row.observation;video.hidden=false;
  if(step===2){loadVideo(video,'media/directors_cut_take'+id+'.mp4','media/posters/take-'+id+'.jpg','Retained fog candidate, Take '+id);play(video)}
 }
 function renderCase(){
  const c=window.CUT_RESEARCH.cases.find(a=>a.id===caseId),rain=caseId==='day',v=q('#pdCaseVideo');
  press('pd-case',caseId);assessed=null;press('pd-assess','');
  q('#pdCaseQ').textContent=rain?'Does the scene read as a rainy night?':'Does the foreground match the original drive?';
  q('#pdAssessNote').textContent='Point to the visual evidence.';
  q('#pdNumbers').textContent='Blind overall: '+c.blind.overall+'/5. Paired '+(rain?'condition: '+c.paired.condition_achieved:'structure: '+c.paired.structure_preserved)+'/5.';
  const raw=rain?c.paired.contradictions:c.paired.added_objects,quote=raw.find(x=>rain?/daytime/i.test(x):/striped hood/i.test(x))||raw[0];
  q('#pdQuote').textContent='“'+quote+'”';
  q('#pdMeaning').textContent=rain?'The paired review has the target and flags the daylight.':'The paired review names a new hood and still awards full structure marks.';
  q('#invented-hood').textContent=rain?'Wet pavement in daylight':'The invented racing hood';
  q('#pdGap').textContent=rain?'Next test: independently label wetness and time of day.':'Next test: count known object additions that a structure gate lets through.';
  q('#pdFileLink').href=rain?'index.html#lessons-learned':'index.html#invented-hood';
  q('#pdFileLink').textContent=rain?'See the evidence and open questions':'Inspect the matched hood frame';
  q('#pdSaved').hidden=true;q('#pdReveal').textContent='Reveal model response';q('#pdReveal').setAttribute('aria-expanded','false');
  if(step===4){loadVideo(v,'studio-media/case-'+caseId+'.v31.mp4','studio-media/case-'+caseId+'.v31.png','Recorded and generated '+(rain?'night rain':'frost at dawn')+' comparison');play(v)}
 }
 function motion(value){
  paused=value;document.documentElement.classList.toggle('motion-paused',value);
  q('#pdMotion').textContent=value?'Resume motion':'Pause motion';q('#pdMotion').setAttribute('aria-pressed',String(value));
  if(value)all('video').forEach(v=>v.pause());else auto();
 }
 function auto(){
  if(step===0||step===1)stops[step].querySelectorAll('video').forEach(play);
  if(step===2)play(q('#pdWinnerVideo'));if(step===3)play(stops[3].querySelector('.vlm-film video'));if(step===4)play(q('#pdCaseVideo'));
 }
 function go(i,focus=true,routeHash=null){
  step=Math.min(stops.length-1,Math.max(0,i));all('video').forEach(v=>v.pause());
  stops.forEach((s,j)=>{s.hidden=j!==step;});
  const active=stops[step];active.querySelectorAll('video[data-load]').forEach(v=>loadVideo(v,v.dataset.load,v.getAttribute('poster')));
  if(step===2)rankFog();if(step===4)renderCase();
  q('#pdPosition').textContent=(step+1)+' / '+stops.length+' · '+active.dataset.stop;
  q('#pdMeter').querySelector('i').style.width=100*(step+1)/stops.length+'%';
  q('#pdBack').disabled=step===0;q('#pdNext').textContent=step===stops.length-1?'Start again':'Next';
  try{history.replaceState(null,'',routeHash||'#stop-'+(step+1))}catch{}
  if(focus){active.querySelector('h2').focus({preventScroll:true});window.scrollTo(0,0)}
  auto();
 }
 function restart(){n=4;rule='balanced';gate=0;caseId='hood';press('pd-vote','');q('#pdVoteResult').textContent='Ask for a show of hands and one visible reason.';for(const d of all('details'))d.open=false;document.dispatchEvent(new Event('cut-restart'));go(0)}
 q('#pdNext').addEventListener('click',()=>{if(step===stops.length-1)restart();else go(step+1)});q('#pdBack').addEventListener('click',()=>go(step-1));
 q('#pdMotion').addEventListener('click',()=>motion(!paused));
 if(!document.documentElement.requestFullscreen){q('#pdFull').hidden=true}
 else{q('#pdFull').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen()}catch{q('#pdFull').textContent='Use browser full screen'}});document.addEventListener('fullscreenchange',()=>{q('#pdFull').textContent=document.fullscreenElement?'Exit full screen':'Full screen'})}
 document.addEventListener('keydown',e=>{
  if(e.defaultPrevented||e.altKey||e.ctrlKey||e.metaKey||e.shiftKey||e.target.closest('input,textarea,select,video,[contenteditable="true"]'))return;
  if(e.key==='ArrowRight'&&step<stops.length-1){e.preventDefault();go(step+1)}
  if(e.key==='ArrowLeft'&&step>0){e.preventDefault();go(step-1)}
  if(e.key==='Home'){e.preventDefault();go(0)}if(e.key==='End'){e.preventDefault();go(stops.length-1)}
 });
 control('pd-vote',choice=>{press('pd-vote',choice);q('#pdVoteResult').textContent=({A:'A preserves clear lane markings. Does it show enough fog?',B:'B has a strong plume. Does it look like weather on this street?',neither:'What minimum requirement would exclude each candidate?'}[choice])});
 q('#pdReplay').addEventListener('click',()=>{for(const v of stops[1].querySelectorAll('video')){v.currentTime=0;v.play().catch(()=>{})}});
 control('pd-n',v=>{n=Number(v);rankFog()});control('pd-rule',v=>{rule=v;rankFog()});control('pd-gate',v=>{gate=Number(v);rankFog()});
 control('pd-case',v=>{caseId=v;renderCase()});control('pd-assess',v=>{assessed=v;press('pd-assess',v);q('#pdAssessNote').textContent=({keep:'Which feature supports keeping it?',reject:'Which visible change breaks your rule?',unsure:'What additional evidence would resolve the uncertainty?'}[v])});
 q('#pdReveal').addEventListener('click',()=>{const a=q('#pdSaved');a.hidden=!a.hidden;q('#pdReveal').setAttribute('aria-expanded',String(!a.hidden));q('#pdReveal').textContent=a.hidden?'Reveal model response':'Hide model response'});
 document.addEventListener('visibilitychange',()=>{if(document.hidden)all('video').forEach(v=>v.pause())});
 for(const d of all('details'))d.addEventListener('toggle',()=>{if(!d.open)d.querySelectorAll('video').forEach(v=>v.pause())});
 if(reduced.addEventListener)reduced.addEventListener('change',ev=>motion(ev.matches));
 for(const v of all('video'))v.addEventListener('error',()=>{const path=v.getAttribute('src');if(!path||v.hasAttribute('data-recovery'))return;v.setAttribute('data-recovery','');const a=document.createElement('a');a.href=path;a.textContent='Open this video directly';a.className='pd-recovery';v.after(a)});
 function route(focus){
  const key=location.hash.match(/^#stop-([1-6])$/);
  if(location.hash==='#invented-hood'){
   caseId='hood';go(4,focus,'#invented-hood');const vid=q('#pdCaseVideo');vid.pause();vid.setAttribute('poster','studio-media/hood-frame-pair.v31.png');
   const seek=()=>{if(step===4&&caseId==='hood'&&Number.isFinite(vid.duration)&&vid.duration>2.875){vid.currentTime=2.875;vid.pause()}};
   if(vid.readyState>=1)seek();else{vid.addEventListener('loadedmetadata',seek,{once:true});vid.preload='auto';vid.load();}
   q('#pdSaved').hidden=false;q('#pdReveal').setAttribute('aria-expanded','true');q('#pdReveal').textContent='Hide model response';
  }else if(location.hash==='#lessons-learned'){
   go(5,focus,'#lessons-learned');q('#lessons-learned').open=true;q('#lessons-learned').scrollIntoView({block:'nearest'});
  }else go(key?Number(key[1])-1:0,focus);
 }
 document.documentElement.classList.toggle('motion-paused',paused);q('#pdMotion').textContent=paused?'Resume motion':'Pause motion';q('#pdMotion').setAttribute('aria-pressed',String(paused));route(false);
 window.addEventListener('hashchange',()=>route(true));
})();
