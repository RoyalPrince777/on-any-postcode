(()=>{
'use strict';
function applySmiIdentity(){
  document.title='SMI · Sovereign Megaverse Intelligence';
  const title=document.querySelector('.chat-title');
  if(title) title.textContent='SMI';
  const subtitle=document.querySelector('.chat-subtitle');
  if(subtitle) subtitle.textContent='Founder Intelligence · SMI AUTO · HRM/JOOG';
  const input=document.getElementById('message');
  if(input){
    input.placeholder='Ask SMI…';
    input.setAttribute('aria-label','Ask SMI');
  }
  const label=document.querySelector('label[for="message"]');
  if(label) label.textContent='Ask SMI';
  const first=document.querySelector('#messages .msg.assistant .msg-text');
  if(first && first.textContent.trim()==='Ready. What do you want to work on?'){
    first.textContent='SMI ready. What do you want to work on?';
  }
  document.querySelectorAll('.smi-hero h1').forEach(el=>el.textContent='SMI');
  document.querySelectorAll('.smi-hero .mc-eyebrow').forEach(el=>el.textContent='SOVEREIGN MEGAVERSE INTELLIGENCE · PRIVATE FOUNDER WORKSPACE');
  document.documentElement.dataset.smiProductIdentity='canonical';
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',applySmiIdentity,{once:true});
else applySmiIdentity();
window.OAP_SMI_PRODUCT={name:'SMI',fullName:'Sovereign Megaverse Intelligence',auto:'SMI AUTO',canonical:true,duplicateMindIdentity:false};
})();
