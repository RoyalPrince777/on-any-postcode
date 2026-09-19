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
if(!oapForm||!oapInput||!oapSend)return;

let oapLocked=false,oapAbort=null,oapRecognition=null,oapListening=false,oapListenStarted=0,oapListenTimer=null;
let oapPaused=false,oapWorkStarted=0,oapWorkTimer=null;
let oapVoiceEnabled=(oapSpeaker?.getAttribute('aria-pressed')!=='false');

function oapSetStatus(text){if(oapStatus)oapStatus.textContent=text;}
function oapRelease(){oapLocked=false;oapAbort=null;oapPaused=false;}
function oapElapsed(){return oapListenStarted?Math.max(0,Math.floor((Date.now()-oapListenStarted)/1000)):0;}
function oapStopListenTimer(){if(oapListenTimer)clearInterval(oapListenTimer);oapListenTimer=null;}
function oapWorkSeconds(){return oapWorkStarted?Math.max(0,Math.round((performance.now()-oapWorkStarted)/100)/10):0;}
function oapUpdateWorkedFor(){if(oapThinkingElapsed)oapThinkingElapsed.textContent=`Worked for ${oapWorkSeconds().toFixed(1)}s`;}
function oapBeginWork(){oapWorkStarted=performance.now();oapUpdateWorkedFor();if(oapWorkTimer)clearInterval(oapWorkTimer);oapWorkTimer=setInterval(oapUpdateWorkedFor,100);}
function oapEndWork(){const seconds=oapWorkSeconds();if(oapWorkTimer)clearInterval(oapWorkTimer);oapWorkTimer=null;if(oapThinkingElapsed)oapThinkingElapsed.textContent=`Worked for ${seconds.toFixed(1)}s`;oapWorkStarted=0;return seconds;}
function oapSpeak(text){if(!oapVoiceEnabled||!('speechSynthesis' in window)||!text)return;window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(String(text));utterance.lang='en-GB';window.speechSynthesis.speak(utterance);}
function oapCloseAttach(){if(oapAttachMenu)oapAttachMenu.classList.remove('show');if(oapPlus)oapPlus.setAttribute('aria-expanded','false');}
function oapToggleAttach(){if(!oapAttachMenu||!oapPlus)return;const open=!oapAttachMenu.classList.contains('show');oapAttachMenu.classList.toggle('show',open);oapPlus.setAttribute('aria-expanded',String(open));oapSetStatus(open?'Tools and attachments open':'Tools and attachments closed');}
function oapStopAll(){responseStopped=true;oapPaused=false;if(oapAbort)oapAbort.abort();if(oapRecognition&&oapListening){try{oapRecognition.stop()}catch{}}oapStopListenTimer();if(oapWorkTimer)clearInterval(oapWorkTimer);oapWorkTimer=null;oapWorkStarted=0;if('speechSynthesis' in window)window.speechSynthesis.cancel();oapRelease();try{hideThinking()}catch{}try{setRunning(false)}catch{}oapSetStatus('Response stopped by Human Authority');}
function oapTogglePause(){if(!oapLocked)return;oapPaused=!oapPaused;if(oapPause){oapPause.classList.toggle('active',oapPaused);oapPause.setAttribute('aria-pressed',String(oapPaused));oapPause.textContent=oapPaused?'▶':'Ⅱ';}const provider=document.getElementById('provider-state');if(provider)provider.textContent=oapPaused?'Paused':'Working';if('speechSynthesis' in window){if(oapPaused)window.speechSynthesis.pause();else window.speechSynthesis.resume();}oapSetStatus(oapPaused?'Paused by Human Authority':'Resumed');}
function oapSetCapturedImage(dataUrl,name){if(typeof selectedImage==='undefined')return false;selectedImage=dataUrl;const preview=document.getElementById('image-preview'),img=document.getElementById('preview-img'),label=document.getElementById('preview-name');if(img)img.src=dataUrl;if(label)label.textContent=name;if(preview)preview.classList.add('show');oapInput.dispatchEvent(new Event('input',{bubbles:true}));return true;}
async function oapCaptureFrame(stream,label){try{const video=document.createElement('video');video.srcObject=stream;video.muted=true;video.playsInline=true;await video.play();await new Promise(resolve=>setTimeout(resolve,180));const track=stream.getVideoTracks()[0],settings=track?.getSettings?.()||{};const canvas=document.createElement('canvas');canvas.width=settings.width||video.videoWidth||1280;canvas.height=settings.height||video.videoHeight||720;canvas.getContext('2d').drawImage(video,0,0,canvas.width,canvas.height);const ok=oapSetCapturedImage(canvas.toDataURL('image/jpeg',0.9),label);oapSetStatus(ok?`${label} captured · routed through existing image/Studio path`:`${label} capture unavailable`);}finally{stream.getTracks().forEach(track=>track.stop());}}
async function oapCamera(){oapCloseAttach();if(!navigator.mediaDevices?.getUserMedia){oapSetStatus('Camera unavailable on this device');return;}oapSetStatus('Camera permission required…');try{const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});await oapCaptureFrame(stream,'Camera');}catch(error){oapSetStatus(error?.name==='NotAllowedError'?'Camera permission blocked':'Camera unavailable');}}
async function oapScreen(){oapCloseAttach();if(!navigator.mediaDevices?.getDisplayMedia){oapSetStatus('Screen sharing unavailable on this device');return;}oapSetStatus('Choose a screen to share…');try{const stream=await navigator.mediaDevices.getDisplayMedia({video:true,audio:false});oapSetStatus('Sharing · capturing one governed frame…');await oapCaptureFrame(stream,'Screen');}catch(error){oapSetStatus(error?.name==='NotAllowedError'?'Screen sharing cancelled or blocked':'Screen sharing unavailable');}}
function oapAddCaptureOptions(){if(!oapAttachMenu||oapAttachMenu.dataset.oapCaptureReady==='true')return;oapAttachMenu.dataset.oapCaptureReady='true';const camera=document.createElement('button');camera.type='button';camera.className='attach-option';camera.id='camera-button';camera.textContent='📷 Camera';camera.setAttribute('aria-label','Capture camera image');camera.addEventListener('click',oapCamera);const screen=document.createElement('button');screen.type='button';screen.className='attach-option';screen.id='screen-capture-button';screen.textContent='🖥️ Share Screen';screen.setAttribute('aria-label','Share screen and capture frame');screen.addEventListener('click',oapScreen);oapAttachMenu.prepend(screen);oapAttachMenu.prepend(camera);}

async function oapSubmit(){
 if(oapLocked||oapSend.disabled)return;const text=oapInput.value.trim();const hasImage=typeof selectedImage!=='undefined'&&Boolean(selectedImage);const hasAttachment=typeof selectedAttachment!=='undefined'&&Boolean(selectedAttachment);if(!text&&!hasImage&&!hasAttachment)return;
 const selectedThinkingLevel=oapThinkingLevel?.value||'auto';
 const selectedStudioMode=(typeof studioMode!=='undefined')?Boolean(studioMode):Boolean(document.getElementById('studio-button')?.classList.contains('active'));
 const userLabel=(text||'Analyse attached media')+(hasImage?'\n📷 Image attached':'')+(hasAttachment?'\n📎 '+selectedAttachment.name:'')+(codeMode?'\n⌘ Code proposal mode':'');
 add(userLabel,'user');
 oapLocked=true;responseStopped=false;oapPaused=false;oapInput.value='';oapInput.dispatchEvent(new Event('input',{bubbles:true}));oapSetStatus('Command received · generating governed result');oapAbort=new AbortController();activeController=oapAbort;setRunning(true);oapBeginWork();showStage('Understand');showStage('Context');let assistantBody=null,completeResult=null,streamError=null,streamText='';
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
  const workedFor=oapEndWork();const resolvedLabel=completeResult.auto_selected?(`AUTO → ${completeResult.resolved_depth||'?'}`):(`${String(completeResult.thinking_level||selectedThinkingLevel).replace('_',' ').toUpperCase()}${completeResult.resolved_depth?(' · '+completeResult.resolved_depth):''}`);add(`🧠 ${resolvedLabel} · Worked for ${workedFor.toFixed(1)}s · ${completeResult.task_type||'governed task'} · Signal ${completeResult.signal_level||'recorded'}`,'system');
  window.dispatchEvent(new CustomEvent('oap-smi-complete',{detail:completeResult}));oapSpeak(completeResult.response);clearAttachments();oapSetStatus(completeResult.code_proposal?.active?'Code proposal ready · Human review required':'Ready · governed result recorded');await loadConversations();
 }catch(error){if(error?.name!=='AbortError'&&!responseStopped){add(error?.message||'Request not completed safely','system');oapSetStatus('Request not completed safely');}}
 finally{if(oapWorkStarted)oapEndWork();try{hideThinking()}catch{}try{setRunning(false)}catch{}oapRelease();try{loadHealth()}catch{}}
}

oapInput.addEventListener('keydown',event=>{if(event.key!=='Enter'||event.shiftKey||event.isComposing)return;event.preventDefault();event.stopImmediatePropagation();oapSubmit();},true);
oapForm.addEventListener('submit',event=>{event.preventDefault();event.stopImmediatePropagation();oapSubmit();},true);
if(oapPlus)oapPlus.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapToggleAttach();},true);
document.addEventListener('click',event=>{if(oapAttachMenu&&oapPlus&&!event.target.closest('.attach-wrap'))oapCloseAttach();});
if(oapPause)oapPause.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapTogglePause();},true);
if(oapStop)oapStop.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapStopAll();},true);
if(oapSpeaker)oapSpeaker.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();oapVoiceEnabled=!oapVoiceEnabled;oapSpeaker.classList.toggle('active',oapVoiceEnabled);oapSpeaker.setAttribute('aria-pressed',String(oapVoiceEnabled));oapSpeaker.textContent=oapVoiceEnabled?'🔊 Voice reply':'🔇 Voice off';if(!oapVoiceEnabled&&'speechSynthesis' in window)window.speechSynthesis.cancel();oapSetStatus(oapVoiceEnabled?'Voice reply on':'Voice reply off');},true);
if(oapMic){const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;if(Recognition){oapRecognition=new Recognition();oapRecognition.lang='en-GB';oapRecognition.interimResults=true;oapRecognition.continuous=false;oapRecognition.onstart=()=>{oapListening=true;oapListenStarted=Date.now();oapMic.classList.add('active');oapMic.setAttribute('aria-pressed','true');oapMic.setAttribute('aria-label','Stop voice input');oapMic.textContent='■';oapSetStatus('Listening · 0s');oapListenTimer=setInterval(()=>oapSetStatus(`Listening · ${oapElapsed()}s`),1000);};oapRecognition.onresult=event=>{oapInput.value=Array.from(event.results).map(result=>result[0].transcript).join('');oapInput.dispatchEvent(new Event('input',{bubbles:true}));};oapRecognition.onend=()=>{oapStopListenTimer();oapListening=false;oapMic.classList.remove('active');oapMic.setAttribute('aria-pressed','false');oapMic.setAttribute('aria-label','Voice input');oapMic.textContent='🎙️';oapSetStatus('Voice captured · edit or send');};oapRecognition.onerror=event=>{oapStopListenTimer();oapListening=false;oapMic.classList.remove('active');oapMic.setAttribute('aria-pressed','false');oapMic.setAttribute('aria-label','Voice input');oapMic.textContent='🎙️';oapSetStatus(event?.error==='not-allowed'?'Microphone permission blocked':'Voice input unavailable');};oapMic.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();try{if(oapListening)oapRecognition.stop();else{oapSetStatus('Microphone permission required…');oapRecognition.start();}}catch{oapSetStatus('Voice input unavailable');}},true);}else{oapMic.disabled=true;oapMic.title='Voice input is not supported by this browser';oapMic.setAttribute('aria-disabled','true');}}
oapAddCaptureOptions();
window.OAP_SMI_CANONICAL={version:'1.5',singleSubmitOwner:true,composerOwner:true,plusOwner:true,pauseOwner:true,timingOwner:true,thinkingModeOwner:true,studioModeOwner:true,micOwner:true,voiceOwner:true,stopOwner:true,cameraCapture:true,screenCapture:true,studioDuplicate:false,resultStreamOnly:true};
})();
