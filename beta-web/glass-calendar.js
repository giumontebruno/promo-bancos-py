/* Civil dates use noon UTC for arithmetic; today always comes from America/Asuncion. */
(()=>{
 const dates=window.PaybackDates,input=document.querySelector('#datePicker');
 const arrow=direction=>`<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="${direction==='left'?'m14 6-6 6 6 6':'m10 6 6 6-6 6'}"/></svg>`;
 const dialog=document.createElement('dialog');dialog.className='glass-picker glass-calendar';dialog.setAttribute('aria-labelledby','calendarTitle');
 dialog.innerHTML=`<header><h2 id="calendarTitle">Elegí el día</h2><button type="button" data-close aria-label="Cerrar calendario">×</button></header><div class="calendar-month"><button type="button" data-prev aria-label="Mes anterior">${arrow('left')}</button><h3 id="calendarMonth" aria-live="polite"></h3><button type="button" data-next aria-label="Mes siguiente">${arrow('right')}</button></div><div class="calendar-grid" role="grid" aria-labelledby="calendarMonth"></div><div class="calendar-legend"><span>○ Hoy</span><span>● Seleccionado</span></div><button type="button" class="calendar-today">Ir a hoy</button>`;
 document.body.append(dialog);let focused='',selected='',month='';const grid=dialog.querySelector('.calendar-grid');
 const civil=iso=>new Date(iso+'T12:00:00Z'),iso=d=>d.toISOString().slice(0,10);
 function moveMonth(value,offset){const d=civil(value),day=d.getUTCDate();d.setUTCDate(1);d.setUTCMonth(d.getUTCMonth()+offset);const last=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();d.setUTCDate(Math.min(day,last));return iso(d);}
 function focusDate(value){focused=value<dates.today()?dates.today():value;month=focused.slice(0,7);render();grid.querySelector(`[data-date="${focused}"]`)?.focus();}
 function render(){
  const first=civil(month+'-01'),offset=(first.getUTCDay()+6)%7,last=new Date(Date.UTC(first.getUTCFullYear(),first.getUTCMonth()+1,0)).getUTCDate();
  dialog.querySelector('#calendarMonth').textContent=new Intl.DateTimeFormat('es-PY',{month:'long',year:'numeric',timeZone:'UTC'}).format(first);
  dialog.querySelector('[data-prev]').disabled=month<=dates.today().slice(0,7);
  grid.replaceChildren();const head=document.createElement('div');head.className='calendar-row';head.setAttribute('role','row');
  ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'].forEach(day=>{const el=document.createElement('span');el.setAttribute('role','columnheader');el.setAttribute('aria-label',day);el.textContent=day.slice(0,2);head.append(el)});grid.append(head);
  for(let n=0;n<Math.ceil((offset+last)/7)*7;n+=7){const row=document.createElement('div');row.className='calendar-row';row.setAttribute('role','row');
   for(let col=0;col<7;col++){const day=n+col-offset+1;if(day<1||day>last){const blank=document.createElement('span');blank.setAttribute('aria-hidden','true');row.append(blank);continue;}
    const value=month+'-'+String(day).padStart(2,'0'),button=document.createElement('button');button.type='button';button.dataset.date=value;button.textContent=day;button.setAttribute('role','gridcell');button.setAttribute('aria-selected',String(value===selected));button.setAttribute('aria-label',new Intl.DateTimeFormat('es-PY',{dateStyle:'full',timeZone:'UTC'}).format(civil(value)));if(value===dates.today())button.setAttribute('aria-current','date');button.disabled=value<dates.today();button.tabIndex=value===focused?0:-1;button.onclick=()=>{input.value=value;input.dispatchEvent(new Event('change',{bubbles:true}));dialog.close();};row.append(button);
   }grid.append(row);
  }
 }
 dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.querySelector('[data-prev]').onclick=()=>{focused=moveMonth(focused,-1);if(focused<dates.today())focused=dates.today();month=focused.slice(0,7);render();};dialog.querySelector('[data-next]').onclick=()=>{focused=moveMonth(focused,1);month=focused.slice(0,7);render();};dialog.querySelector('.calendar-today').onclick=()=>focusDate(dates.today());
 grid.addEventListener('keydown',e=>{if(!e.target.dataset.date)return;const current=e.target.dataset.date,dow=(civil(current).getUTCDay()+6)%7;let next;
  if(e.key==='ArrowRight')next=dates.shift(current,1);if(e.key==='ArrowLeft')next=dates.shift(current,-1);if(e.key==='ArrowDown')next=dates.shift(current,7);if(e.key==='ArrowUp')next=dates.shift(current,-7);if(e.key==='Home')next=dates.shift(current,-dow);if(e.key==='End')next=dates.shift(current,6-dow);if(e.key==='PageDown')next=moveMonth(current,e.shiftKey?12:1);if(e.key==='PageUp')next=moveMonth(current,e.shiftKey?-12:-1);if(next){e.preventDefault();focusDate(next);}
 });
 dialog.addEventListener('close',()=>document.querySelector('[data-day="fecha"]')?.focus());
 window.PaybackCalendar={open(){selected=dates.valid(input.value)?input.value:dates.today();focused=selected<dates.today()?dates.today():selected;month=focused.slice(0,7);render();dialog.showModal();grid.querySelector(`[data-date="${focused}"]`)?.focus();}};
})();
