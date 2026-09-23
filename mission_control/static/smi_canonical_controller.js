(()=>{
'use strict';
const oapForm=document.getElementById('chat-form');
const oapInput=document.getElementById('message');
const oapSend=document.getElementById('send');
const oapMic=document.getElementById('mic-button');
const oapSpeaker=document.getElementById('speaker-button');
const oapStop=document.getElementById('stop-button');
const oapPause=document.getElementById('pause-button');
const oapPlus=document.getElementById('plus-button');
const oapStatus=document.getElementById('status');
const oapAttachMenu=document.getElementById('attach-menu');
const oapThinkingLevel=document.getElementById('thinking-level');
const oapThinkingElapsed=document.getElementById('thinking-elapsed');
const oapLiveToggle=document.getElementById('live-character-toggle');
const oapCharacter=document.getElementById('smi-character');
const oapCharacterLabel=document.getElementById('smi-character-state');
const oapLiveCaption=document.getElementById('smi-live-reply-caption');
if(!oapForm||!oapInput||!oapSend)return;

const oapStateApi=window.OAP_SMI_LIVE_STATE;
let oapRuntime=oapStateApi?.initialState?oapStateApi.initialState():null;
let oapLocked=false,oapAbort=null,oapRecognition=null,oapListening=false,oapListenStarted=0,oapListenTimer=null;
let oapPaused=false,oapWorkStarted=0,oapWorkTimer=null,oapLiveRestartTimer=null,oapRecognitionToken=null,oapFinalTranscript='',oapResumeListenAfterPause=false,oapSpeechSeq=0;
let oapVoiceEnabled=(oapSpeaker?.getAttribute('aria-pressed')!=='false');
const oapLiveProof={
 startedAt:new Date().toISOString(),
 events:[],
 counters:{listenStart:0,listenEnd:0,speakStart:0,speakEnd:0,stop:0,pause:0,resume:0,liveOff:0,permissionDenied:0,staleCallbackSuppressed:0,halfDuplexDenied:0},
 storesAudio:false,
 storesTranscript:false,
};
function oapProof(event,detail={}){
 const safe={event:String(event),at:new Date().toISOString(),...detail};
 delete safe.transcript;delete safe.text;delete safe.audio;
 oapLiveProof.events.push(safe);
 if(oapLiveProof.events.length>80)oapLiveProof.events.shift();
 if(Object.prototype.hasOwnProperty.call(oapLiveProof.counters,event))oapLiveProof.counters[event]+=1;
}
function oapProofSnapshot(){
 return JSON.parse(JSON.stringify({
  startedAt:oapLiveProof.startedAt,
  counters:oapLiveProof.counters,
  events:oapLiveProof.events,
  storesAudio:false,
  storesTranscript:false,
  runtimeState:oapRuntime?{state:oapRuntime.state,live:oapRuntime.live,stopped:oapRuntime.stopped,paused:oapRuntime.paused,listening:oapRuntime.listening,thinking:oapRuntime.thinking,speaking:oapRuntime.speaking,epoch:oapRuntime.epoch}:null,
 }));
}


// Browser TTS lifecycle is not decoded audio or accurate lip-sync proof.
function oapPlaybackState(phase,epoch){
 if(oapCharacter)oapCharacter.dataset.audioPlayback=phase;
 window.dispatchEvent(new CustomEvent('oap-smi-playback-state',{
  detail:{phase,epoch,source:'browser-speech-synthesis',decodedAudio:false,
   accurateLipSyncProven:false,productionApproved:false}
 }));
}
// Display only a real, completed response, never untrusted HTML or inferred visemes.
function oapShowLiveReply(text){
 if(!oapLiveCaption)return;
 const visible=Boolean(oapRuntime?.live&&!oapRuntime.stopped&&String(text||'').trim());
 oapLiveCaption.textContent=visible?String(text):'';
 oapLiveCaption.hidden=!visible;
}
function oapSetStatus(text){if(oapStatus)oapStatus.textContent=text;}
function oapSyncHumanControls(){
 if(!oapRuntime)return;
 const active=Boolean(oapLocked||oapRuntime.live||oapRuntime.listening||oapRuntime.thinking||oapRuntime.speaking||oapRuntime.paused);
 if(oapStop)oapStop.classList.toggle('show',active&&!oapRuntime.stopped);
}
function oapRenderCharacter(){
 if(!oapRuntime)return;
 const labels={ready:'Ready',listening:'Listening',thinking:'Thinking',speaking:'Speaking',paused:'Paused',stopped:'Stopped'};
 if(oapCharacter)oapCharacter.dataset.state=oapRuntime.state;
 if(oapCharacterLabel)oapCharacterLabel.textContent=labels[oapRuntime.state]||oapRuntime.state;
 document.body.classList.toggle('smi-live-fullscreen',Boolean(oapRuntime.live&&!oapRuntime.stopped));
 oapSyncHumanControls();
 window.dispatchEvent(new CustomEvent('oap-smi-character-state',{detail:{...oapRuntime}}));
}
function oapApply(type){
 if(!oapStateApi||!oapRuntime)return oapRuntime;
 oapRuntime=oapStateApi.transition(oapRuntime,{type});
 oapListening=Boolean(oapRuntime.listening);
 oapPaused=Boolean(oapRuntime.paused);
 oapRenderCharacter();
 return oapRuntime;
}
function oapClearLiveRestart(){if(oapLiveRestartTimer)clearTimeout(oapLiveRestartTimer);oapLiveRestartTimer=null;}
function oapScheduleListening(delay=320){
 oapClearLiveRestart();
 if(!oapRuntime?.live||oapRuntime.stopped||oapRuntime.paused)return;
 const expected=oapStateApi.token(oapRuntime);
 oapLiveRestartTimer=setTimeout(()=>{
  oapLiveRestartTimer=null;
  if(oapStateApi.tokenIsCurrent(oapRuntime,expected)&&oapRuntime.live&&!oapRuntime.paused)oapRequestListening('live');
 },delay);
}
function oapUpdateLiveToggle(){
 if(!oapLiveToggle)return;
 const live=Boolean(oapRuntime?.live);
 oapLiveToggle.classList.toggle('active',live);
 oapLiveToggle.setAttribute('aria-pressed',String(live));
 oapLiveToggle.textContent=live?'✕ Exit Live SMI':'◉ Live SMI';
}
function oapSetLive(enabled){
 if(!oapRuntime||!oapStateApi){oapSetStatus('Live SMI state engine unavailable');return false;}
 if(enabled){
  if(!oapRecognition){oapSetStatus('Live SMI unavailable · browser speech recognition is not supported');oapUpdateLiveToggle();return false;}
  if(oapRuntime.stopped)oapApply('RESUME_FROM_STOP');
  oapApply('LIVE_ON');
  oapVoiceEnabled=true;
  if(oapSpeaker){oapSpeaker.classList.add('active');oapSpeaker.setAttribute('aria-pressed','true');oapSpeaker.textContent='🔊 Voice reply';}
  oapSetStatus('Live SMI full screen · voice-first · final recognised speech turns auto-send · browser speech-service locality not verified');
  oapUpdateLiveToggle();
  oapScheduleListening(180);
  return true;
 }
 oapClearLiveRestart();
 oapSpeechSeq+=1;
 oapApply('LIVE_OFF');oapRecognitionToken=null;oapFinalTranscript='';oapShowLiveReply('');oapPlaybackState('cancelled',oapRuntime?.epoch);oapProof('liveOff',{epoch:oapRuntime?.epoch});
 oapRecognitionToken=null;
 if(oapRecognition){try{oapRecognition.stop()}catch{}}
 if('speechSynthesis' in window)window.speechSynthesis.cancel();
 oapUpdateLiveToggle();
 document.body.classList.remove('smi-live-fullscreen');
 oapSetStatus('Live SMI off · text chat restored');
 return true;
}
function oapRequestListening(source='manual'){
 if(!oapRecognition||!oapRuntime||!oapStateApi)return false;
 if(source==='live'&&!oapRuntime.live)return false;
 if(!oapStateApi.canListen(oapRuntime)){
  oapProof('halfDuplexDenied',{source,reason:oapRuntime.stopped?'stopped':oapRuntime.speaking?'speaking':oapRuntime.thinking?'thinking':oapRuntime.paused?'paused':'busy'});
  if(source==='manual')oapSetStatus(oapRuntime.stopped?'Stopped by Human Authority':oapRuntime.speaking?'Wait for SMI to finish speaking':oapRuntime.thinking?'SMI is thinking':oapRuntime.paused?'Paused by Human Authority':'Voice input already active');
  return false;
 }
 oapFinalTranscript='';
 oapRecognitionToken=oapStateApi.token(oapRuntime);
 try{oapSetStatus('Microphone permission required…');oapRecognition.start();return true;}
 catch{oapSetStatus('Voice input unavailable');return false;}
}
function oapRelease(){oapLocked=false;oapAbort=null;if(!oapRuntime?.stopped)oapPaused=false;}
function oapElapsed(){return oapListenStarted?Math.max(0,Math.floor((Date.now()-oapListenStarted)/1000)):0;}
function oapStopListenTimer(){if(oapListenTimer)clearInterval(oapListenTimer);oapListenTimer=null;}
function oapWorkSeconds(){return oapWorkStarted?Math.max(0,Math.round((performance.now()-oapWorkStarted)/100)/10):0;}
function oapUpdateWorkedFor(){if(oapThinkingElapsed)oapThinkingElapsed.textContent=`Worked for ${oapWorkSeconds().toFixed(1)}s`;}
function oapBeginWork(){oapWorkStarted=performance.now();oapApply('THINK_START');oapUpdateWorkedFor();if(oapWorkTimer)clearInterval(oapWorkTimer);oapWorkTimer=setInterval(oapUpdateWorkedFor,100);}
function oapEndWork(){const seconds=oapWorkSeconds();if(oapWorkTimer)clearInterval(oapWorkTimer);oapWorkTimer=null;if(oapThinkingElapsed)oapThinkingElapsed.textContent=`Worked for ${seconds.toFixed(1)}s`;oapWorkStarted=0;if(!oapRuntime?.stopped)oapApply('THINK_END');return seconds;}
function oapSpeak(text){
 if(oapRuntime?.stopped)return;
 if(!text||!oapVoiceEnabled||!('speechSynthesis' in window)){if(oapRuntime?.live)oapScheduleListening(250);return;}
 oapSpeechSeq+=1;
 const seq=oapSpeechSeq,expected=oapStateApi.token(oapRuntime);
 window.speechSynthesis.cancel();
 const utterance=new SpeechSynthesisUtterance(String(text));utterance.lang='en-GB';
 utterance.onstart=()=>{if(seq!==oapSpeechSeq||!oapStateApi.tokenIsCurrent(oapRuntime,expected)){oapProof('staleCallbackSuppressed',{source:'tts-start'});return;}oapApply('SPEAK_START');oapPlaybackState('playing',oapRuntime?.epoch);oapProof('speakStart',{epoch:oapRuntime?.epoch});};
 const finish=phase=>{if(seq!==oapSpeechSeq||!oapStateApi.tokenIsCurrent(oapRuntime,expected)){oapProof('staleCallbackSuppressed',{source:'tts-finish'});return;}oapApply('SPEAK_END');oapPlaybackState(phase,oapRuntime?.epoch);if(phase==='ended')oapProof('speakEnd',{epoch:oapRuntime?.epoch});else oapSetStatus('Voice playback failed · reply remains in chat');if(oapRuntime.live&&!oapRuntime.paused)oapScheduleListening(320);};
 utterance.onend=()=>finish('ended');utterance.onerror=()=>finish('error');
 window.speechSynthesis.speak(utterance);
}
function oapCloseAttach(){if(oapAttachMenu)oapAttachMenu.classList.remove('show');if(oapPlus)oapPlus.setAttribute('aria-expanded','false');}
function oapToggleAttach(){if(!oapAttachMenu||!oapPlus)return;const open=!oapAttachMenu.classList.contains('show');oapAttachMenu.classList.toggle('show',open);oapPlus.setAttribute('aria-expanded',String(open));oapSetStatus(open?'Tools and attachments open':'Tools and attachments closed');}
function oapStopAll(){
 responseStopped=true;
 oapClearLiveRestart();
 oapSpeechSeq+=1;
 oapApply('STOP');oapRecognitionToken=null;oapFinalTranscript='';oapShowLiveReply('');oapPlaybackState('stopped',oapRuntime?.epoch);oapProof('stop',{epoch:oapRuntime?.epoch});
 oapUpdateLiveToggle();
 if(oapAbort)oapAbort.abort();
 if(oapRecognition){try{oapRecognition.stop()}catch{}}
 oapStopListenTimer();
 if(oapWorkTimer)clearInterval(oapWorkTimer);oapWorkTimer=null;oapWorkStarted=0;
 if('speechSynthesis' in window)window.speechSynthesis.cancel();
 oapRelease();try{hideThinking()}catch{}try{setRunning(false)}catch{}
 oapSetStatus('Response stopped by Human Authority · explicit new command or Live SMI restart required');
}
function oapTogglePause(){
 if(!oapRuntime||oapRuntime.stopped)return;
 const active=Boolean(oapLocked||oapRuntime.listening||oapRuntime.speaking||oapRuntime.paused);if(!active)return;
 if(!oapRuntime.paused){
  oapResumeListenAfterPause=Boolean(oapRuntime.listening&&oapRuntime.live);
  if(oapRuntime.listening)oapRecognitionToken=null;
  oapApply('PAUSE');oapProof('pause',{epoch:oapRuntime?.epoch});
  if(oapRecognition){try{oapRecognition.stop()}catch{}}
  if('speechSynthesis' in window)window.speechSynthesis.pause();
 }else{
  oapApply('RESUME');oapProof('resume',{epoch:oapRuntime?.epoch});
  if('speechSynthesis' in window)window.speechSynthesis.resume();
  if(oapRuntime.live&&!oapRuntime.listening&&!oapRuntime.thinking&&!oapRuntime.speaking)oapScheduleListening(180);
  oapResumeListenAfterPause=false;
 }
 if(oapPause){oapPause.classList.toggle('active',oapRuntime.paused);oapPause.setAttribute('aria-pressed',String(oapRuntime.paused));oapPause.textContent=oapRuntime.paused?'▶':'Ⅱ';}
 const provider=document.getElementById('provider-state');if(provider)provider.textContent=oapRuntime.paused?'Paused':'Working';
 oapSetStatus(oapRuntime.paused?'Paused by Human Authority':'Resumed');
}
function oapSetCapturedImage(dataUrl,name){if(typeof selectedImage==='undefined')return false;selectedImage=dataUrl;const preview=document.getElementById('image-preview'),img=document.getElementById('preview-img'),label=document.getElementById('preview-name');if(img)img.src=dataUrl;if(label)label.textContent=name;if(preview)preview.classList.add('show');oapInput.dispatchEvent(new Event('input',{bubbles:true}));return true;}
async function oapCaptureFrame(stream,label){try{const video=document.createElement('video');video.srcObject=stream;video.muted=true;video.playsInline=true;await video.play();await new Promise(resolve=>setTimeout(resolve,180));const track=stream.getVideoTracks()[0],settings=track?.getSettings?.()||{};const canvas=document.createElement('canvas');canvas.width=settings.width||video.videoWidth||1280;canvas.height=settings.height||video.videoHeight||720;canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);const ok=oapSetCapturedImage(canvas.toDataURL('image/jpeg',0.9),label);oapSetStatus(ok?`${label} captured · routed through existing image/Studio path`:`${label} capture unavailable`);}finally{stream.getTracks().forEach(track=>track.stop());}}
async function oapCamera(){oapCloseAttach();if(!navigator.mediaDevices?.getUserMedia){oapSetStatus('Camera unavailable on this device');return;}oapSetStatus('Camera permission required…');try{const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});await oapCaptureFrame(stream,'Camera');}catch(error){oapSetStatus(error?.name==='NotAllowedError'?'Camera permission blocked':'Camera unavailable');}}
async function oapScreen(){oapCloseAttach();if(!navigator.mediaDevices?.getDisplayMedia){oapSetStatus('Screen sharing unavailable on this device');return;}oapSetStatus('Choose a screen to share…');try{const stream=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});oapSetStatus('Sharing · capturing one governed frame…');await oapCaptureFrame(stream,'Screen');}catch(error){oapSetStatus(error?.name==='NotAllowedError'?'Screen sharing cancelled or blocked':'Screen sharing unavailable');}}
function oapAddCaptureOptions(){if(!oapAttachMenu||oapAttachMenu.dataset.oapCaptureReady==='true')return;oapAttachMenu.dataset.oapCaptureReady='true';const camera=document.createElement('button');camera.type='button';camera.className='attach-option';camera.id='camera-button';camera.textContent='📷 Camera';camera.setAttribute('aria-label','Capture camera image');camera.addEventListener('click',oapCamera);const screen=document.createElement('button');screen.type='button';screen.className='attach-option';screen.id='screen-capture-button';screen.textContent='🖥️ Share Screen';screen.setAttribute('aria-label','Share screen and capture frame');screen.addEventListener('click',oapScreen);oapAttachMenu.prepend(screen);oapAttachMenu.prepend(camera);}

async function oapSubmit(options={}){
 const fromLive=options?.fromLive===true;
 if(oapRuntime?.stopped){if(fromLive)return;oapApply('RESUME_FROM_STOP');}
 if(oapLocked||oapSend.disabled)return;const text=oapInput.value.trim();const hasImage=typeof selectedImage!=='undefined'&&Boolean(selectedImage);const hasAttachment=typeof selectedAttachment!=='undefined'&&Boolean(selectedAttachment);if(!text&&!hasImage&&!hasAttachment)return;
 const selectedThinkingLevel=oapThinkingLevel?.value||'auto';
 const selectedStudioMode=(typeof studioMode!=='undefined')?Boolean(studioMode):Boolean(document.getElementById('studio-button')?.classList.contains('active'));
 const userLabel=(text||'Analyse attached media')+(hasImage?'\n📷 Image attached':'')+(hasAttachment?'\n📎 '+selectedAttachment.name:'')+(codeMode?'\n⌘ Code proposal mode':'');
 add(userLabel,'user');
 oapLocked=true;responseStopped=false;oapPaused=false;oapShowLiveReply('');oapInput.value='';oapInput.dispatchEvent(new Event('input',{bubbles:true}));oapSetStatus('Command received · generating governed result');oapAbort=new AbortController();activeController=oapAbort;setRunning(true);oapBeginWork();showStage('Understand');showStage('Context');let assistantBody=null,completeResult=null,streamError=null,streamText='';
 try{
  const response=await fetch(streamUrl,{method:'POST',signal:oapAbort.signal,headers:{'Content-Type':'application/json','X-OAP-CSRF':csrfToken},credentials:'same-origin',body:JSON.stringify({message:text,display_name:document.getElementById('display-name')?.value||'OAP Founder',conversation_id:conversationId,image_data:selectedImage,attachment:selectedAttachment,code_mode:codeMode,thinking_level:selectedThinkingLevel,studio_mode:selectedStudioMode})});
  if(!response.ok){let payload={};try{payload=await response.json()}catch{}throw new Error(payload?.error?.message||'Request failed');}
  if(!response.body)throw new Error('Streaming is not supported by this browser');
  const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
  while(true){
   while(oapPaused&&!responseStopped)await new Promise(resolve=>setTimeout(resolve,80));
   const chunk=await reader.read();if(chunk.done)break;
   buffer=(buffer+decoder.decode(chunk.value,{stream:true})).replace(/\r\n/g,'\n');
   let boundary=-1;
   while((boundary=buffer.indexOf('\n\n'))>=0){
    const block=buffer.slice(0,boundary);buffer=buffer.slice(boundary+2);const parsed=parseEventBlock(block);if(!parsed)continue;
    if(parsed.event==='stage')showStage(parsed.data.label||parsed.data.stage||'Working');
    if(parsed.event==='delta'){if(!assistantBody)assistantBody=add('','assistant');streamText+=parsed.data.delta||'';renderMessage(assistantBody,streamText);messages.scrollTop=messages.scrollHeight;}
    if(parsed.event==='complete')completeResult=parsed.data.result;
    if(parsed.event==='error')streamError=new Error(parsed.data.message||'Request failed');
   }
  }
  if(streamError)throw streamError;if(!completeResult)throw new Error('The governed response did not finish recording.');
  conversationId=completeResult.conversation_id;if(!assistantBody)assistantBody=add(completeResult.response,'assistant');else renderMessage(assistantBody,completeResult.response);
  const workedFor=oapEndWork();add(`🧠 ${selectedThinkingLevel.replace('_',' ').toUpperCase()} · Worked for ${workedFor.toFixed(1)}s · ${completeResult.task_type||'governed task'} · Signal ${completeResult.signal_level||'recorded'}`,'system');
  window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:completeResult}));oapShowLiveReply(completeResult.response);oapSpeak(completeResult.response);clearAttachments();oapSetStatus(completeResult.code_proposal?.active?'Code proposal ready · Human review required':'Ready · governed result recorded');await loadConversations();
 }catch(error){if(error?.name!=='AbortError'&&!responseStopped){add(error?.message||'Request not completed safely','system');oapSetStatus('Request not completed safely');}}
 finally{if(oapWorkStarted)oapEndWork();try{hideThinking()}catch{}try{setRunning(false)}catch{}oapRelease();oapSyncHumanControls();try{loadHealth()}catch{}}
}

oapInput.addEventListener('keydown',event=>{if(event.key!=='Enter'||event.shiftKey||event.isComposing)return;event.preventDefault();event.stopImmediatePropagation();oapSubmit();},true);
oapForm.addEventListener('submit',event=>{event.preventDefault();event.stopImmediatePropagation();oapSubmit();},true);
if(oapPlus)oapPlus.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapToggleAttach();},true);
document.addEventListener('click',event=>{if(oapAttachMenu&&oapPlus&&!event.target.closest('.attach-wrap')&&!event.target.closest('#tools-mode-button'))oapCloseAttach();});
if(oapPause)oapPause.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapTogglePause();},true);
if(oapStop)oapStop.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapStopAll();},true);
if(oapSpeaker)oapSpeaker.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapVoiceEnabled=!oapVoiceEnabled;oapSpeaker.classList.toggle('active',oapVoiceEnabled);oapSpeaker.setAttribute('aria-pressed',String(oapVoiceEnabled));oapSpeaker.textContent=oapVoiceEnabled?'🔊 Voice reply':'🔇 Voice off';if(!oapVoiceEnabled&&'speechSynthesis' in window){oapSpeechSeq+=1;window.speechSynthesis.cancel();oapPlaybackState('cancelled',oapRuntime?.epoch);if(oapRuntime?.speaking)oapApply('SPEAK_END');if(oapRuntime?.live)oapScheduleListening(180);}oapSetStatus(oapVoiceEnabled?'Voice reply on':'Voice reply off');},true);
if(oapMic){
 const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(Recognition&&oapStateApi){
  oapRecognition=new Recognition();oapRecognition.lang='en-GB';oapRecognition.interimResults=true;oapRecognition.continuous=false;
  oapRecognition.onstart=()=>{
   const expected=oapRecognitionToken;
   if(!oapStateApi.tokenIsCurrent(oapRuntime,expected)){oapProof('staleCallbackSuppressed',{source:'recognition-start'});try{oapRecognition.stop()}catch{}return;}
   oapApply('LISTEN_START');oapProof('listenStart',{epoch:oapRuntime?.epoch});oapListenStarted=Date.now();oapMic.classList.add('active');oapMic.setAttribute('aria-pressed','true');oapMic.setAttribute('aria-label','Stop voice input');oapMic.textContent='■';oapSetStatus('Listening · 0s');oapListenTimer=setInterval(()=>oapSetStatus(`Listening · ${oapElapsed()}s`),1000);
  };
  oapRecognition.onresult=event=>{
   if(!oapStateApi.tokenIsCurrent(oapRuntime,oapRecognitionToken)||!oapRuntime?.listening){oapProof('staleCallbackSuppressed',{source:'recognition-result'});return;}
   const results=Array.from(event.results),full=results.map(result=>result[0].transcript).join(' '),finalText=results.filter(result=>result.isFinal).map(result=>result[0].transcript).join(' ').trim();
   oapInput.value=full;oapFinalTranscript=finalText;oapInput.dispatchEvent(new Event('input',{bubbles:true}));
  };
  oapRecognition.onend=()=>{
   const expected=oapRecognitionToken;oapStopListenTimer();oapMic.classList.remove('active');oapMic.setAttribute('aria-pressed','false');oapMic.setAttribute('aria-label','Voice input');oapMic.textContent='🎙️';
   if(!oapStateApi.tokenIsCurrent(oapRuntime,expected)){oapProof('staleCallbackSuppressed',{source:'recognition-end'});return;}
   oapApply('LISTEN_END');oapProof('listenEnd',{epoch:oapRuntime?.epoch});
   if(oapRuntime.live){
    const submitToken=oapStateApi.token(oapRuntime);
    const mayAutoSubmit=oapStateApi.canAutoSubmitFinal(
      oapRuntime,
      oapFinalTranscript,
      oapStateApi.tokenIsCurrent(oapRuntime,submitToken)
    );
    if(mayAutoSubmit){
     oapInput.value=oapFinalTranscript;oapInput.dispatchEvent(new Event('input',{bubbles:true}));
     setTimeout(()=>{
      const stillAllowed=oapStateApi.canAutoSubmitFinal(
        oapRuntime,
        oapFinalTranscript,
        oapStateApi.tokenIsCurrent(oapRuntime,submitToken)
      );
      if(stillAllowed)oapSubmit({fromLive:true});
     },120);
    }else if(!oapRuntime.paused){oapSetStatus('Live SMI · no final speech captured');oapScheduleListening(350);}
   }else{oapSetStatus(oapFinalTranscript?'Voice captured · edit or send':'Voice input ended without a final transcript');}
  };
  oapRecognition.onerror=event=>{
   const expected=oapRecognitionToken;oapStopListenTimer();oapMic.classList.remove('active');oapMic.setAttribute('aria-pressed','false');oapMic.setAttribute('aria-label','Voice input');oapMic.textContent='🎙️';
   if(!oapStateApi.tokenIsCurrent(oapRuntime,expected)){oapProof('staleCallbackSuppressed',{source:'recognition-error'});return;}
   oapApply('LISTEN_END');oapProof('listenEnd',{epoch:oapRuntime?.epoch,error:String(event?.error||'unknown')});
   if(event?.error==='not-allowed')oapProof('permissionDenied',{});
   if(oapRuntime.live)oapSetLive(false);
   oapSetStatus(event?.error==='not-allowed'?'Microphone permission blocked':'Voice input unavailable');
  };
  oapMic.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();if(oapRuntime?.listening){try{oapRecognition.stop()}catch{}}else{oapRequestListening('manual');}},true);
 }else{
  oapMic.disabled=true;oapMic.title='Voice input is not supported by this browser';oapMic.setAttribute('aria-disabled','true');
  if(oapLiveToggle){oapLiveToggle.disabled=true;oapLiveToggle.setAttribute('aria-disabled','true');oapLiveToggle.title='Live SMI requires browser speech recognition';}
 }
}
if(oapLiveToggle)oapLiveToggle.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapSetLive(!Boolean(oapRuntime?.live));},true);
window.addEventListener('pagehide',()=>{document.body.classList.remove('smi-live-fullscreen');oapClearLiveRestart();oapSpeechSeq+=1;if(oapRuntime&&!oapRuntime.stopped)oapApply('LIVE_OFF');oapRecognitionToken=null;oapFinalTranscript='';oapShowLiveReply('');oapPlaybackState('cancelled',oapRuntime?.epoch);if(oapRecognition){try{oapRecognition.stop()}catch{}}if('speechSynthesis' in window)window.speechSynthesis.cancel();});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&oapRuntime?.live){oapSetLive(false);oapSetStatus('Live SMI off while this page is hidden');}});
oapRenderCharacter();oapUpdateLiveToggle();
oapAddCaptureOptions();
window.OAP_SMI_LIVE_PROOF={snapshot:oapProofSnapshot,privacy:{storesAudio:false,storesTranscript:false}};
window.OAP_SMI_CANONICAL={version:'2.2',singleSubmitOwner:true,composerOwner:true,plusOwner:true,pauseOwner:true,timingOwner:true,thinkingModeOwner:true,studioModeOwner:true,micOwner:true,voiceOwner:true,stopOwner:true,cameraCapture:true,screenCapture:true,studioDuplicate:false,liveCharacter:true,liveFullscreen:true,voiceFirstFullscreen:true,persistentThinkingProcess:true,halfDuplexLiveVoice:true,stickyHumanStop:true,finalTranscriptAutoSendOnly:true,browserSpeechLocalityVerified:false,runtimeProofLedger:true,resultStreamOnly:true};
})();
