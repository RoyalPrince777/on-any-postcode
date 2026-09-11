(()=>{
const cfg=window.OAP_SMI_UI||{};
const publicOapOrigin='https://on-any-postcode.onrender.com/';
const publicFrontDoor=[...document.querySelectorAll('.navs a')].find(link=>link.textContent.trim()==='OAP Front Door');
if(publicFrontDoor){publicFrontDoor.href=publicOapOrigin;publicFrontDoor.rel='noopener'}
const plusButton=document.getElementById('plus-button'),attachMenu=document.getElementById('attach-menu'),composerInput=document.getElementById('message'),thinkingPanel=document.getElementById('thinking');
if(plusButton){plusButton.setAttribute('aria-label','Open connected tools and attachments');plusButton.setAttribute('title','Add files, media or connected tools')}
if(thinkingPanel){thinkingPanel.setAttribute('aria-label','Safe SMI Thinking Process stages only');thinkingPanel.setAttribute('title','Shows governed operational state only; private chain-of-thought is never exposed.')}
async function launchStudio(){try{const response=await fetch(cfg.workbenchUrl,{cache:'no-store',credentials:'same-origin'}),workbench=await response.json();if(!response.ok)throw new Error(workbench?.error?.message||'Studio unavailable');const studio=(workbench.capabilities||[]).find(item=>item.id==='oap-studio-intelligence');if(!studio)throw new Error('OAP Studio Intelligence is not registered.');composerInput.value=studio.activation_prompt||'OAP Studio Intelligence mode. Help me create: ';composerInput.focus();composerInput.dispatchEvent(new Event('input',{bubbles:true}))}catch(error){console.warn('OAP Studio Intelligence unavailable',error)}finally{attachMenu?.classList.remove('show');plusButton?.setAttribute('aria-expanded','false')}}
if(plusButton&&attachMenu&&!attachMenu.querySelector('[data-oap-studio]')){const studioButton=document.createElement('button');studioButton.type='button';studioButton.className='attach-option connector';studioButton.dataset.oapStudio='true';studioButton.innerHTML='<span class="connector-copy"><span>🎬</span><span>OAP Studio Intelligence</span></span><span class="connector-state ready">SMI</span>';studioButton.addEventListener('click',launchStudio);attachMenu.append(studioButton)}
})();
