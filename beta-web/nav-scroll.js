(function(root){
 function initial(y=0){return {y,mode:'full',direction:0,total:0};}
 function step(previous,y,max,{overlay=false,keyboard=false,focus=false}={}){
  y=Math.max(0,Math.min(y,Math.max(0,max)));
  if(keyboard||focus||y<=24)return initial(y);
  if(overlay)return {...previous,y,direction:0,total:0};
  const delta=y-previous.y;if(Math.abs(delta)<2)return previous;
  const direction=Math.sign(delta),total=direction===previous.direction?previous.total+Math.abs(delta):Math.abs(delta);
  let mode=previous.mode;if(direction>0&&total>=36)mode='hidden';if(direction<0&&total>=12)mode=previous.mode==='full'?'full':'mini';if(direction<0&&total>=76)mode='full';
  return {y,mode,direction,total};
 }
 if(typeof module==='object'){module.exports={initial,step};return;}
 const nav=document.querySelector('#bottomNav');if(!nav)return;let state=initial(scrollY),keyboard=false,pending=false;
 nav.querySelectorAll('button').forEach(button=>{const text=[...button.childNodes].find(n=>n.nodeType===3&&n.textContent.trim());if(text){const span=document.createElement('span');span.className='nav-label';span.textContent=text.textContent;button.setAttribute('aria-label',text.textContent.trim());text.replaceWith(span);}});
 const apply=()=>nav.dataset.scrollState=state.mode;
 const reset=()=>{state=initial(Math.max(0,scrollY));apply();};
 addEventListener('scroll',()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;state=step(state,scrollY,document.documentElement.scrollHeight-innerHeight,{overlay:!!document.querySelector('dialog[open]'),keyboard,focus:nav.contains(document.activeElement)&&document.activeElement.matches(':focus-visible')});apply();});},{passive:true});
 addEventListener('keydown',e=>{if(e.key==='Tab'){keyboard=true;reset();}});addEventListener('pointerdown',()=>keyboard=false,{passive:true});nav.addEventListener('focusin',()=>{if(keyboard)reset();});
 document.addEventListener('click',e=>{if(e.target.closest('[data-view],#profileButton,[data-profile-favorites]'))reset();});
 new MutationObserver(reset).observe(document.querySelector('#viewTitle'),{childList:true,subtree:true});reset();
})(typeof window==='object'?window:globalThis);
