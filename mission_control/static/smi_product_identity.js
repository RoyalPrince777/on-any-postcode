(()=>{
'use strict';
const SMI_CAPABILITIES=Object.freeze({
  adaptive:'Governed learning and calibration from evidence and changing conditions',
  coherent:'Shared OAP laws, terminology, state and evidence across modules and agents',
  hybrid:'Routes appropriate local intelligence, remote intelligence, deterministic software, specialist tools and Human Authority',
  omniDistribution:'Routes authorised intelligence and outputs across approved OAP channels',
  civilization:'Reasons across Postcode, Borough, County/Region, Country, Continent, Global and Universe layers without claiming governmental authority',
  autonomy:'Bounded SMI AUTO operation through 3/7/21 gates, Guardian, Chronicle and Human Authority',
  sovereign:'OAP-controlled authority boundaries, OAP Data doctrine and fail-closed Founder control'
});
function applySmiIdentity(){
  document.title='SMI · Sovereign Megaverse Intelligence';
  const title=document.querySelector('.chat-title');
  if(title) title.textContent='SMI';
  const subtitle=document.querySelector('.chat-subtitle');
  if(subtitle) subtitle.textContent='Adaptive · Coherent · Hybrid · Omni Distribution · Civilization Intelligence · SMI AUTO';
  const input=document.getElementById('message');
  if(input){ input.placeholder='Message SMI'; input.setAttribute('aria-label','Message SMI'); }
  const label=document.querySelector('label[for="message"]');
  if(label) label.textContent='Message SMI';
  const providerState=document.getElementById('provider-state');
  if(providerState){ providerState.setAttribute('aria-label','SMI intelligence state'); providerState.dataset.smiIdentity='canonical'; }
  const first=document.querySelector('#messages .msg.assistant .msg-text');
  if(first && first.textContent.trim()==='Ready. What do you want to work on?') first.textContent='SMI ready. What do you want to work on?';
  document.querySelectorAll('.smi-hero h1').forEach(el=>el.textContent='SMI');
  document.querySelectorAll('.smi-hero .mc-eyebrow').forEach(el=>el.textContent='SOVEREIGN MEGAVERSE INTELLIGENCE · PRIVATE FOUNDER WORKSPACE');
  document.documentElement.dataset.smiProductIdentity='canonical';
  document.documentElement.dataset.smiIntelligenceModel='adaptive-coherent-hybrid-omni-civilization';
}
if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',applySmiIdentity,{once:true}); else applySmiIdentity();
window.OAP_SMI_PRODUCT={
  name:'SMI',
  fullName:'Sovereign Megaverse Intelligence',
  auto:'SMI AUTO',
  canonical:true,
  duplicateMindIdentity:false,
  dataDoctrine:'OAP Data',
  dataSourceDefault:'first-party-only',
  zeroTolerance:true,
  capabilities:SMI_CAPABILITIES,
  humanAuthorityFinal:true,
  productionGreenRequiresEvidence:true
};
})();
