(() => {
 'use strict';
 // Anchors inside optional teaching material open the enclosing panels.
 function openRoute(){
  if(!location.hash)return;let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return}
  const target=document.getElementById(id);if(!target)return;
  let ancestor=target,changed=false;
  while(ancestor){if(ancestor.tagName==='DETAILS'&&!ancestor.open){ancestor.open=true;changed=true}ancestor=ancestor.parentElement}
  if(changed)target.scrollIntoView({block:'start'});
 }
 window.addEventListener('hashchange',openRoute);openRoute();
 for(const panel of document.querySelectorAll('details')){
  panel.addEventListener('toggle',()=>{if(!panel.open)panel.querySelectorAll('video').forEach(v=>v.pause());});
 }
 for(const v of document.querySelectorAll('.vlm-film video,.reel-drawer video')){
  if('IntersectionObserver' in window)new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)v.pause()}).observe(v);
 }
})();
(() => {
 const trigger=document.querySelector('#inspectOutput'),dialog=document.querySelector('#outputDialog');
 if(trigger&&dialog&&typeof dialog.showModal==='function'){
  const source=document.querySelector('#introWeatherVideo'),big=dialog.querySelector('video'),close=document.querySelector('#closeOutput');let resume=false,t=0;
  trigger.addEventListener('click',ev=>{
   ev.preventDefault();resume=!source.paused;t=source.currentTime||0;source.pause();dialog.querySelector('h2').textContent='Generated '+document.querySelector('#introWeatherLabel').textContent.toLowerCase();
   big.src=source.currentSrc||source.src;big.addEventListener('loadedmetadata',()=>{if(Number.isFinite(big.duration))big.currentTime=Math.min(t,big.duration-.05)},{once:true});dialog.showModal();close.focus();if(resume)big.play().catch(()=>{});
  });close.addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{big.pause();source.currentTime=big.currentTime||t;if(resume&&!document.documentElement.classList.contains('motion-paused'))source.play().catch(()=>{});trigger.focus()});
 }
 // Release decoder time outside the blind-comparison stage.
 const block=document.querySelector('#challenge');
 if(block&&'IntersectionObserver' in window){
  const vids=[document.querySelector('#heroVideoA'),document.querySelector('#heroVideoB')];let primed=false;
  new IntersectionObserver(entries=>{const visible=entries[0].isIntersecting;if(!visible){vids.forEach(v=>v.pause());return}
   if(!primed&&!document.documentElement.classList.contains('motion-paused')&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches){primed=true;vids.forEach(v=>v.play().catch(()=>{}))}
  },{threshold:.07}).observe(block);
 }
})();
