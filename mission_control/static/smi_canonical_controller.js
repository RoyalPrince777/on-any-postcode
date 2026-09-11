(()=>{
'use strict';
const oapForm=document.getElementById('chat-form');
const oapInput=document.getElementById('message');
const oapSend=document.getElementById('send');
const oapMic=document.getElementById('mic-button');
const oapSpeaker=document.getElementById('speaker-button');
const oapStop=document.getElementById('stop-button');
const oapStatus=document.getElementById('status');
if(!oapForm||!oapInput||!oapSend)return;
let oapLocked=false;
let oapAbort=null;
let oapRecognition=null;
let oapListening=false;
let oapVoiceEnabled=(oapSpeaker?.getAttribute('aria-pressed')!=='false');

function oapSetStatus(text){if(oapStatus)oapStatus.textContent=text;}
function oapRelease(){oapLocked=false;oapAbort=null;}
function oapSpeak(text){
  if(!oapVoiceEnabled||!('speechSynthesis' in window)||!text)return;
  window.speechSynthesis.cancel();
  const utterance=new SpeechSynthesisUtterance(String(text));
  utterance.lang='en-GB';
  window.speechSynthesis.speak(utterance);
}
function oapStopAll(){
  if(oapAbort)oapAbort.abort();
  if(oapRecognition&&oapListening){try{oapRecognition.stop()}catch{}}
  if('speechSynthesis' in window)window.speechSynthesis.cancel();
  oapRelease();
  try{hideThinking()}catch{}
  try{setRunning(false)}catch{}
  oapSetStatus('Response stopped by Human Authority');
}

async function oapSubmit(){
  if(oapLocked||oapSend.disabled)return;
  const text=oapInput.value.trim();
  const hasImage=typeof selectedImage!=='undefined'&&Boolean(selectedImage);
  const hasAttachment=typeof selectedAttachment!=='undefined'&&Boolean(selectedAttachment);
  if(!text&&!hasImage&&!hasAttachment)return;
  oapLocked=true;
  responseStopped=false;
  const userLabel=(text||'Analyse attached media')+(hasImage?'\n📷 Image attached':'')+(hasAttachment?'\n📎 '+selectedAttachment.name:'')+(codeMode?'\n⌘ Code proposal mode':'');
  add(userLabel,'user');
  oapInput.value='';
  oapAbort=new AbortController();
  activeController=oapAbort;
  setRunning(true);
  showStage('Understand');
  let assistantBody=null;
  let completeResult=null;
  let streamError=null;
  let streamText='';
  try{
    const response=await fetch(streamUrl,{
      method:'POST',
      signal:oapAbort.signal,
      headers:{'Content-Type':'application/json','X-OAP-CSRF':csrfToken},
      credentials:'same-origin',
      body:JSON.stringify({
        message:text,
        display_name:document.getElementById('display-name')?.value||'OAP Founder',
        conversation_id:conversationId,
        image_data:selectedImage,
        attachment:selectedAttachment,
        code_mode:codeMode
      })
    });
    if(!response.ok){
      let payload={};
      try{payload=await response.json()}catch{}
      throw new Error(payload?.error?.message||'Request failed');
    }
    if(!response.body)throw new Error('Streaming is not supported by this browser');
    const reader=response.body.getReader();
    const decoder=new TextDecoder();
    let buffer='';
    while(true){
      const chunk=await reader.read();
      if(chunk.done)break;
      buffer=(buffer+decoder.decode(chunk.value,{stream:true})).replace(/\r\n/g,'\n');
      let boundary=-1;
      while((boundary=buffer.indexOf('\n\n'))>=0){
        const block=buffer.slice(0,boundary);
        buffer=buffer.slice(boundary+2);
        const parsed=parseEventBlock(block);
        if(!parsed)continue;
        if(parsed.event==='stage')showStage(parsed.data.label||parsed.data.stage||'Working');
        if(parsed.event==='delta'){
          if(!assistantBody)assistantBody=add('','assistant');
          streamText+=parsed.data.delta||'';
          renderMessage(assistantBody,streamText);
          messages.scrollTop=messages.scrollHeight;
        }
        if(parsed.event==='complete')completeResult=parsed.data.result;
        if(parsed.event==='error')streamError=new Error(parsed.data.message||'Request failed');
      }
    }
    if(streamError)throw streamError;
    if(!completeResult)throw new Error('The governed response did not finish recording.');
    conversationId=completeResult.conversation_id;
    if(!assistantBody)assistantBody=add(completeResult.response,'assistant');
    else renderMessage(assistantBody,completeResult.response);
    window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:completeResult}));
    oapSpeak(completeResult.response);
    clearAttachments();
    oapSetStatus(completeResult.code_proposal?.active?'Code proposal ready · Human review required':'Ready · governed response recorded');
    await loadConversations();
  }catch(error){
    if(error?.name!=='AbortError'&&!responseStopped){
      add(error?.message||'Request not completed safely','system');
      oapSetStatus('Request not completed safely');
    }
  }finally{
    try{hideThinking()}catch{}
    try{setRunning(false)}catch{}
    oapRelease();
    try{loadHealth()}catch{}
  }
}

// Canonical capture-phase ownership: these handlers run before legacy bubble handlers.
oapInput.addEventListener('keydown',event=>{
  if(event.key!=='Enter'||event.shiftKey||event.isComposing)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  oapSubmit();
},true);
oapForm.addEventListener('submit',event=>{
  event.preventDefault();
  event.stopImmediatePropagation();
  oapSubmit();
},true);
if(oapStop)oapStop.addEventListener('click',event=>{
  event.preventDefault();
  event.stopImmediatePropagation();
  oapStopAll();
},true);
if(oapSpeaker)oapSpeaker.addEventListener('click',event=>{
  event.preventDefault();
  event.stopImmediatePropagation();
  oapVoiceEnabled=!oapVoiceEnabled;
  oapSpeaker.classList.toggle('active',oapVoiceEnabled);
  oapSpeaker.setAttribute('aria-pressed',String(oapVoiceEnabled));
  oapSpeaker.textContent=oapVoiceEnabled?'🔊 Voice reply':'🔇 Voice off';
  if(!oapVoiceEnabled&&'speechSynthesis' in window)window.speechSynthesis.cancel();
  oapSetStatus(oapVoiceEnabled?'Voice reply on':'Voice reply off');
},true);
if(oapMic){
  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(Recognition){
    oapRecognition=new Recognition();
    oapRecognition.lang='en-GB';
    oapRecognition.interimResults=true;
    oapRecognition.continuous=false;
    oapRecognition.onstart=()=>{oapListening=true;oapMic.classList.add('active');oapSetStatus('Listening…')};
    oapRecognition.onresult=event=>{
      oapInput.value=Array.from(event.results).map(result=>result[0].transcript).join('');
      oapInput.dispatchEvent(new Event('input',{bubbles:true}));
    };
    oapRecognition.onend=()=>{oapListening=false;oapMic.classList.remove('active');oapSetStatus('Voice captured — edit or send')};
    oapRecognition.onerror=event=>{oapListening=false;oapMic.classList.remove('active');oapSetStatus(event?.error==='not-allowed'?'Microphone permission blocked':'Voice input unavailable')};
    oapMic.addEventListener('click',event=>{
      event.preventDefault();
      event.stopImmediatePropagation();
      try{
        if(oapListening)oapRecognition.stop();
        else oapRecognition.start();
      }catch{oapSetStatus('Voice input unavailable')}
    },true);
  }else{
    oapMic.disabled=true;
    oapMic.title='Voice input is not supported by this browser';
  }
}
window.OAP_SMI_CANONICAL={version:'1.0',singleSubmitOwner:true,micOwner:true,voiceOwner:true,stopOwner:true};
})();
