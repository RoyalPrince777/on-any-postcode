(()=>{
'use strict';
const ready=()=>{
  document.body.classList.add('smi-noise-strip');
  document.body.classList.remove('smi-booting');

  const status=document.getElementById('status');
  const plus=document.getElementById('plus-button');
  const mic=document.getElementById('mic-button');
  const pause=document.getElementById('pause-button');
  const stop=document.getElementById('stop-button');
  const send=document.getElementById('send');
  const speaker=document.getElementById('speaker-button');
  const liveToggle=document.getElementById('live-character-toggle');

  // Live SMI is a primary control. Keep it outside any reparented character/dashboard
  // container so later Command Center layout changes cannot hide it.
  if(liveToggle){
    document.body.appendChild(liveToggle);
    liveToggle.style.setProperty('display','grid','important');
    liveToggle.style.setProperty('visibility','visible','important');
    liveToggle.style.setProperty('opacity','1','important');
    liveToggle.style.setProperty('pointer-events','auto','important');
    liveToggle.style.setProperty('z-index','1200','important');
  }
  const input=document.getElementById('message');
  const form=document.getElementById('chat-form');
  const savedWork=document.getElementById('saved-work-button');
  const history=document.querySelector('.history');
  const historyBackdrop=document.querySelector('.history-backdrop');

  if(savedWork){
    savedWork.addEventListener('click',()=>{
      history?.classList.add('mobile-open');
      historyBackdrop?.classList.add('mobile-open');
      document.getElementById('attach-menu')?.classList.remove('show');
      plus?.setAttribute('aria-expanded','false');
    });
  }

  if(plus){plus.title='Tools';plus.setAttribute('aria-label','Open tools and attachments');}
  if(mic){mic.title='Voice input';}
  if(pause){pause.title='Pause or resume';}
  if(stop){stop.title='Stop';}
  if(send){send.title='Send';}
  if(speaker){speaker.title='Voice reply';speaker.setAttribute('aria-label','Voice reply');}

  // Keep the main composer one-line until content actually needs more room.
  if(input){
    input.rows=1;
    input.setAttribute('aria-label','Message SMI');
  }

  // Fail visibly rather than leave a dead-looking core control.
  const required=[
    ['plus-button','Tools'],
    ['mic-button','Voice'],
    ['pause-button','Pause'],
    ['stop-button','Stop'],
    ['send','Send']
  ];
  const missing=required.filter(([id])=>!document.getElementById(id)).map(([,label])=>label);
  if(missing.length&&status) status.textContent='Control check failed · missing: '+missing.join(', ');

  // Keep button alignment stable when long status messages or mode changes occur.
  const bar=document.querySelector('.composer-bar');
  if(bar) bar.dataset.noiseStrip='1';

  // Enter and Shift+Enter remain owned by the canonical controller. No second key handler here.


  // Founder-approved reference layout: real controls and evidence, never fake metrics.
  if(!document.getElementById('smi-reference-top')){
    const shell=document.querySelector('.smi-shell');
    if(shell){
      document.body.classList.add('smi-reference-layout');
      const top=document.createElement('header');
      top.id='smi-reference-top';
      top.className='smi-reference-top';
      const brand=document.createElement('a');
      brand.href='/mission/ollama';brand.className='smi-reference-brand';
      brand.textContent='♛ OAP · ON ANY POSTCODE';
      const heading=document.createElement('div');
      heading.className='smi-reference-title';
      const name=document.createElement('strong');name.textContent='SMI';
      const sub=document.createElement('small');sub.textContent='SOVEREIGN MEGAVERSE INTELLIGENCE';
      heading.append(name,sub);
      const menu=document.createElement('button');
      menu.type='button';menu.className='smi-reference-menu';
      menu.setAttribute('aria-expanded','false');
      menu.setAttribute('aria-controls','smi-reference-left');
      menu.setAttribute('aria-label','Toggle SMI navigation');
      menu.textContent='☰';
      const evidenceButton=document.createElement('button');
      evidenceButton.type='button';evidenceButton.className='smi-reference-evidence-toggle';
      evidenceButton.setAttribute('aria-controls','smi-reference-right');
      evidenceButton.setAttribute('aria-expanded','false');
      evidenceButton.setAttribute('aria-label','Open SMI system evidence');
      evidenceButton.textContent='◈';
      top.append(brand,heading,evidenceButton,menu);
      const left=document.createElement('nav');
      left.id='smi-reference-left';left.className='smi-reference-side smi-reference-left';
      left.setAttribute('aria-label','SMI private navigation');
      const leftHeading=document.createElement('h2');leftHeading.textContent='SMI CONTROL';
      left.append(leftHeading);
      const links=[
        ['🧠','SMI Chat','/mission/ollama'],
        ['◉','SMI Brain','/mission/brain'],
        ['◇','Mission Control','/mission'],
        ['⚖','War Room','/mission/war-room'],
        ['♛','Judgement','/mission/judgement']
      ];
      for(const [symbol,label,href] of links){
        const a=document.createElement('a');a.href=href;
        a.textContent=symbol+'  '+label;
        if(href==='/mission/ollama')a.setAttribute('aria-current','page');
        left.append(a);
      }
      const right=document.createElement('aside');
      right.id='smi-reference-right';right.className='smi-reference-side smi-reference-right';
      right.setAttribute('aria-label','Verified SMI system evidence');
      const rightHeading=document.createElement('h2');rightHeading.textContent='SYSTEM EVIDENCE';
      const summary=document.createElement('p');summary.id='smi-reference-evidence';
      summary.setAttribute('role','status');summary.textContent='Runtime evidence not checked';
      const checks=document.createElement('div');checks.id='smi-reference-checks';
      checks.textContent='Unknown until verified';
      const refresh=document.createElement('button');refresh.type='button';
      refresh.textContent='↻ Check evidence';refresh.className='smi-reference-refresh';
      right.append(rightHeading,summary,checks,refresh);
      const foot=document.createElement('div');
      foot.className='smi-reference-foot';
      foot.textContent='OAP INTELLIGENCE · ONE SMI BRAIN · FOUNDER FINAL';
      shell.append(top,left,right,foot);
      const closeEvidence=()=>{
        document.body.classList.remove('smi-reference-evidence-open');
        evidenceButton.setAttribute('aria-expanded','false');
      };
      const closeMenu=()=>{document.body.classList.remove('smi-reference-nav-open');menu.setAttribute('aria-expanded','false');};
      evidenceButton.addEventListener('click',()=>{
        closeMenu();
        const open=document.body.classList.toggle('smi-reference-evidence-open');
        evidenceButton.setAttribute('aria-expanded',String(open));
      });
      menu.addEventListener('click',()=>{
        closeEvidence();
        const open=document.body.classList.toggle('smi-reference-nav-open');
        menu.setAttribute('aria-expanded',String(open));
      });
      left.addEventListener('click',event=>{if(event.target.closest('a'))closeMenu();});
      left.addEventListener('keydown',event=>{if(event.key==='Escape'){closeMenu();menu.focus();}});
      right.addEventListener('keydown',event=>{if(event.key==='Escape'){closeEvidence();evidenceButton.focus();}});
      const update=async()=>{
        summary.textContent='Checking real runtime evidence…';
        checks.replaceChildren();
        const url=window.OAP_SMI_UI?.healthUrl;
        if(!url){summary.textContent='Health route unavailable';checks.textContent='Unknown';return;}
        try{
          const response=await fetch(url,{credentials:'same-origin',cache:'no-store'});
          if(!response.ok)throw new Error('Health route unavailable');
          const data=await response.json();
          const values=data&&typeof data.checks==='object'&&!Array.isArray(data.checks)?Object.entries(data.checks):[];
          summary.textContent='SMI runtime response received · evidence below';
          if(!values.length){checks.textContent='Detailed checks unavailable · Unknown';return;}
          const fragment=document.createDocumentFragment();
          for(const [key,value] of values.slice(0,12)){
            const item=document.createElement('div');item.className='smi-reference-check';
            const label=document.createElement('span');label.textContent=key.replace(/_/g,' ');
            const state=document.createElement('span');state.textContent=value===true?'Passed':value===false?'Not proven':'Unknown';
            state.dataset.state=value===true?'passed':'unknown';
            item.append(label,state);fragment.append(item);
          }
          checks.append(fragment);
        }catch{
          summary.textContent='Runtime evidence unavailable';
          checks.textContent='Unknown · No Green inferred';
        }
      };
      refresh.addEventListener('click',update);
      update();
    }
  }

  window.OAP_SMI_NOISE_STRIP=Object.freeze({
    version:'1.0',
    applied:true,
    coreControlsPresent:missing.length===0,
    upgradeOnly:true
  });
};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
})();