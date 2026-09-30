(()=>{
'use strict';
const ready=()=>{
  document.body.classList.add('smi-noise-strip');

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

  window.OAP_SMI_NOISE_STRIP=Object.freeze({
    version:'1.1',
    applied:true,
    coreControlsPresent:missing.length===0,
    upgradeOnly:true
  });
};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready,{once:true});else ready();
})();