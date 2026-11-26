/* A synchronized comparison: both panels are decoded from one published clip. */
(() => {
 'use strict';
 const settings=window.CUT_FIELD;
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 for(const root of document.querySelectorAll('[data-final-cut]')){
  const q=k=>root.querySelector('[data-fc-'+k+']'), all=s=>Array.from(root.querySelectorAll(s));
  const video=q('video'),can=q('canvas'),screen=q('screen'),range=q('range'),bar=q('divider'),ctx=can.getContext&&can.getContext('2d');
  let scene=settings[0],pos=100,still=null,seq=0,loop=0,tween=0;const answers={},timestamps={},notes={};
  const globallyPaused=()=>reduced.matches||document.documentElement.classList.contains('motion-paused');
  function paint(){
   if(!ctx)return;
   const p=scene.picture;
   const source=video.readyState>=2&&video.videoWidth===p.frame_width&&video.videoHeight===p.frame_height?video:still;
   if(!source)return;
   const w=source.videoWidth||source.naturalWidth,h=source.videoHeight||source.naturalHeight;if(!w||!h)return;
   if(w!==p.frame_width || h!==p.frame_height)return;
   const ow=p.width,oh=p.height;
   if(can.width!==ow || can.height!==oh){can.width=ow;can.height=oh}
   ctx.drawImage(source,p.left,p.top,ow,oh,0,0,ow,oh);
   const x=Math.round(ow*pos/100);
   if(x<ow){ctx.save();ctx.beginPath();ctx.rect(x,0,ow-x,oh);ctx.clip();ctx.drawImage(source,p.right,p.top,ow,oh,0,0,ow,oh);ctx.restore();}
   can.hidden=false;video.hidden=true;q('overlay').hidden=false;
   screen.classList.add('fc-ready');bar.hidden=pos<1||pos>99;q('left').hidden=pos<19;q('right').hidden=pos>81;bar.style.left=pos+'%';
  }
  function move(v){pos=Math.max(0,Math.min(100,Math.round(v)));range.value=pos;range.setAttribute('aria-valuetext',pos===0?'All generated':pos===100?'All recorded':pos+' percent recorded on the left');paint()}
  function run(){cancelAnimationFrame(loop);if(!video.paused&&!video.ended){paint();loop=requestAnimationFrame(run);}}
  video.addEventListener('play',()=>{q('play').textContent='Pause scene';run()});video.addEventListener('pause',()=>{q('play').textContent='Play scene';cancelAnimationFrame(loop);paint()});
  for(const ev of ['loadeddata','seeked','canplay'])video.addEventListener(ev,paint);
  video.addEventListener('error',()=>{q('feedback').textContent='Playback is unavailable. Open the side-by-side video below or inspect the still with the divider.';paint();});
  const words={keep:'Keep for review',reject:'Reject',more:'Need more evidence'};
  function stamp(id){const t=timestamps[id];return t===null||t===undefined?'poster frame':t.toFixed(2)+' s'}
  function refreshLog(){
   const reviewed=settings.filter(s=>answers[s.id]);q('count').textContent=reviewed.length+' / '+settings.length;
   q('note').disabled=!answers[scene.id];q('note').value=notes[scene.id]||'';
   q('picks').replaceChildren();for(const item of reviewed){const li=document.createElement('li');li.textContent=item.short+' · '+words[answers[item.id]]+' · '+stamp(item.id);q('picks').append(li)}
   q('save').disabled=reviewed.length===0;
  }
  function feedback(){
   const pick=answers[scene.id];for(const b of all('[data-fc-vote]'))b.setAttribute('aria-pressed',String(pick===b.dataset.fcVote));
   if(!pick){q('feedback').textContent='Name one detail in the footage that supports your choice.';}
   else{
    const time=document.createElement('b');time.className='fc-stamp';time.textContent=words[pick]+' · '+stamp(scene.id);
    const cue=document.createElement('span');cue.textContent=scene.prompt;
    q('feedback').replaceChildren(time,cue);
   }
   refreshLog();
  }
  q('note').addEventListener('input',()=>{if(answers[scene.id])notes[scene.id]=q('note').value;});
  q('save').addEventListener('click',()=>{
   const rows=settings.filter(s=>answers[s.id]).map(s=>[s.short+' | '+words[answers[s.id]]+' | '+stamp(s.id),'Target: '+s.target,'Observation: '+(notes[s.id]||'(not recorded)'),'Check: '+s.prompt,s.caution].join('\n'));
   if(!rows.length)return;
   const u=URL.createObjectURL(new Blob(['CUT! Best-of-N Studio | Screening notes\n\n'+rows.join('\n\n')+'\n'],{type:'text/plain;charset=utf-8'}));
   const a=document.createElement('a');a.href=u;a.download='CUT-screening-notes.txt';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);
  });
  function show(next){
   seq++;const s=seq;cancelAnimationFrame(tween);video.pause();scene=next;still=null;can.hidden=true;video.hidden=false;bar.hidden=true;q('overlay').hidden=true;screen.classList.remove('fc-ready');
   video.poster=next.still;video.src=next.base+'.mp4';video.setAttribute('aria-label',next.short+': recorded and generated footage, side by side.');video.load();
   q('target').textContent=next.target;q('question').textContent=next.title;q('link').href=next.base+'.mp4';move(100);
   const picture=new Image();picture.onload=()=>{if(seq===s){still=picture;paint()}};picture.src=next.still;
   for(const b of all('[data-field]'))b.setAttribute('aria-pressed',String(b.dataset.field===next.id));feedback();
  }
  function reveal(){cancelAnimationFrame(tween);if(!ctx){video.hidden=false;video.play().catch(()=>{});return}
   const from=pos,to=from>60?45:from<40?55:100;if(globallyPaused()){move(to);return}
   const start=performance.now();function tick(now){const u=Math.min(1,(now-start)/680);move(from+(to-from)*(u*u*(3-2*u)));if(u<1)tween=requestAnimationFrame(tick)}tween=requestAnimationFrame(tick);
  }
  q('size').addEventListener('click',()=>{
   const fit=root.dataset.pictureSize!=='fit';root.dataset.pictureSize=fit?'fit':'native';
   q('size').setAttribute('aria-pressed',String(fit));q('size').textContent=fit?'Use native width':'Enlarge picture';
   q('pixels').textContent=fit?'Room view · 472 × 248 source pixels':'472 × 248 per view';
  });
  q('reveal').addEventListener('click',reveal);range.addEventListener('input',()=>{cancelAnimationFrame(tween);move(Number(range.value))});
  q('play').addEventListener('click',()=>{if(!video.paused){video.pause();return}video.play().catch(()=>{q('feedback').textContent='Use Open side-by-side video below to play this scene.'})});
  let drag=null;function pointer(e){const b=screen.getBoundingClientRect();if(b.width)move(100*(e.clientX-b.left)/b.width)}
  screen.addEventListener('pointerdown',e=>{if(!ctx||can.hidden||e.button!==0)return;drag=e.pointerId;cancelAnimationFrame(tween);screen.setPointerCapture(drag);pointer(e)});
  screen.addEventListener('pointermove',e=>{if(drag===e.pointerId)pointer(e)});
  for(const ev of ['pointerup','pointercancel','lostpointercapture'])screen.addEventListener(ev,()=>{drag=null});
  all('[data-field]').forEach(b=>b.addEventListener('click',()=>show(settings.find(o=>o.id===b.dataset.field))));
  all('[data-fc-vote]').forEach(b=>b.addEventListener('click',()=>{video.pause();timestamps[scene.id]=video.readyState>=2&&Number.isFinite(video.currentTime)?video.currentTime:null;answers[scene.id]=b.dataset.fcVote;feedback()}));
  if('IntersectionObserver' in window)new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)video.pause()}).observe(root);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)video.pause()});
  document.addEventListener('cut-restart',()=>{for(const k of Object.keys(answers)){delete answers[k];delete notes[k];delete timestamps[k];}root.dataset.pictureSize='native';q('size').setAttribute('aria-pressed','false');q('size').textContent='Enlarge picture';q('pixels').textContent='472 × 248 per view';show(settings[0]);});
  // The fallback is an ordinary labelled video when canvas is unavailable.
  if(!ctx){q('size').hidden=true;range.disabled=true;root.classList.add('fc-native')}
  show(settings[0]);
 }
})();
