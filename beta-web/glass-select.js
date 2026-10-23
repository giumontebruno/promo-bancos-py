/* Native selects remain the data/event source and fallback. The enhanced UI is a modal listbox. */
(()=>{
 const selector='.glass-filters select,#detailBranch';
 const dialog=document.createElement('dialog');dialog.className='glass-picker';dialog.setAttribute('aria-labelledby','glassPickerTitle');
 dialog.innerHTML='<header><h2 id="glassPickerTitle"></h2><button type="button" aria-label="Cerrar selector">×</button></header><div class="glass-picker-list" role="listbox"></div>';
 document.body.append(dialog);const list=dialog.querySelector('[role=listbox]');let source=null,trigger=null;
 dialog.querySelector('header button').onclick=()=>dialog.close();
 dialog.addEventListener('close',()=>{trigger?.setAttribute('aria-expanded','false');if(trigger?.isConnected)trigger.focus();});
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
 function open(select,button){source=select;trigger=button;const title=select.getAttribute('aria-label')||'Elegí una sucursal';dialog.querySelector('h2').textContent=title;list.setAttribute('aria-label',title);list.replaceChildren();
  [...select.options].forEach((o,i)=>{const option=document.createElement('button');option.type='button';option.setAttribute('role','option');option.setAttribute('aria-selected',String(o.selected));option.tabIndex=o.selected?0:-1;option.disabled=o.disabled;option.dataset.index=i;const text=document.createElement('span');text.textContent=o.text;const check=document.createElement('span');check.textContent=o.selected?'✓':'';check.setAttribute('aria-hidden','true');option.append(text,check);option.onclick=()=>{select.value=o.value;select.dispatchEvent(new Event('change',{bubbles:true}));sync();dialog.close();};list.append(option);});
  button.setAttribute('aria-expanded','true');dialog.showModal();const selected=list.querySelector('[aria-selected=true]:not(:disabled)')||list.querySelector('button:not(:disabled)');selected?.focus();selected?.scrollIntoView({block:'nearest'});
 }
 list.addEventListener('keydown',e=>{const options=[...list.querySelectorAll('button:not(:disabled)')],i=options.indexOf(document.activeElement);let n;if(e.key==='ArrowDown')n=(i+1)%options.length;if(e.key==='ArrowUp')n=(i-1+options.length)%options.length;if(e.key==='Home')n=0;if(e.key==='End')n=options.length-1;if(n!==undefined){e.preventDefault();options.forEach(o=>o.tabIndex=-1);options[n].tabIndex=0;options[n].focus();}});
 function sync(){document.querySelectorAll(selector).forEach(select=>{let button=select.nextElementSibling;if(!button?.classList.contains('glass-select-trigger')){button=document.createElement('button');button.type='button';button.className='glass-select-trigger';button.setAttribute('aria-haspopup','dialog');button.setAttribute('aria-expanded','false');button.onclick=()=>open(select,button);select.after(button);select.hidden=true;}const label=select.getAttribute('aria-label')||'Sucursal';const text=select.selectedOptions[0]?.text||label;const next=label+': '+text;if(button.getAttribute('aria-label')!==next){button.setAttribute('aria-label',next);button.textContent=text+' ⌄';}button.disabled=select.disabled;});}
 new MutationObserver(sync).observe(document.querySelector('.app-shell')||document.body,{childList:true,subtree:true});
 new MutationObserver(sync).observe(document.querySelector('#dialogContent'),{childList:true,subtree:true});
 document.addEventListener('change',e=>{if(e.target.matches(selector))sync();});sync();
})();
