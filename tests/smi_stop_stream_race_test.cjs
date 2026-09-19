"use strict";
// Execute the real SMI submit function with controlled browser-stream promises.
// Local interaction simulation only: no Founder sign-in, external provider or live upload.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("mission_control/static/smi_canonical_controller.js","utf8");
const start = source.indexOf("async function oapSubmit(options={}){");
const end = source.indexOf("\noapInput.addEventListener('keydown'",start);
assert.ok(start >= 0 && end > start, "canonical submit function must be extractable");
const submitSource = source.slice(start,end);

async function exercise(where) {
  const requests=[],shown=[],completions=[],running=[];
  let readOld;
  const context={
    AbortController, TextDecoder, TextEncoder,
    Event:class Event {constructor(name,options){this.type=name;this.bubbles=options?.bubbles;}},
    CustomEvent:class CustomEvent {constructor(type,options){this.type=type;this.detail=options?.detail;}},
    window:{dispatchEvent:event=>completions.push(event)},
    document:{getElementById:()=>null},
    messages:{scrollTop:0,scrollHeight:10},
    streamUrl:"/test-stream",csrfToken:"test-csrf",conversationId:null,
    oapRuntime:{stopped:false},oapLocked:false,oapAbort:null,responseStopped:false,
    oapSend:{disabled:false},oapInput:{value:"old",dispatchEvent(){}},
    oapThinkingLevel:{value:"auto"},
    selectedImage:"",selectedAttachment:null,codeMode:false,studioMode:false,
    oapPaused:false,oapWorkStarted:1,
    fetch:(_url,options)=>new Promise(resolve=>requests.push({resolve,signal:options.signal})),
    oapApply(type){if(type==="RESUME_FROM_STOP")context.oapRuntime.stopped=false;},
    oapSetStatus(){},setRunning(value){running.push(value);},
    add(value,role){shown.push({value,role});return{};},
    showStage(){},oapBeginWork(){},oapEndWork(){return 0.1;},
    renderMessage(){},oapSpeak(){},clearAttachments(){},
    loadConversations:async()=>{},
    hideThinking(){},oapSyncHumanControls(){},loadHealth(){},
    oapRelease(){context.oapLocked=false;context.oapAbort=null;},
    parseEventBlock(block){
      if(block.includes("event: complete"))return{
        event:"complete",data:{result:{response:"new result",conversation_id:"new"}}
      };
      return null;
    },
  };
  vm.createContext(context);
  vm.runInContext(submitSource,context);

  const old = context.oapSubmit();
  assert.equal(requests.length,1);
  if(where==="read"){
    requests[0].resolve({
      ok:true,body:{getReader(){return{read:()=>new Promise(resolve=>{readOld=resolve;})};}}
    });
    for(let i=0;i<6;i++)await Promise.resolve();
    assert.equal(typeof readOld,"function","old stream must be awaiting read");
  }

  // STOP aborts and releases a request; a new explicit command starts immediately.
  context.responseStopped=true;
  context.oapAbort.abort();
  context.oapAbort=null;
  context.oapLocked=false;
  context.oapRuntime.stopped=true;
  context.oapInput.value="new";
  const next=context.oapSubmit();
  assert.equal(requests.length,2);

  if(where==="fetch"){
    requests[0].resolve({ok:true,body:{getReader(){throw Error("stale fetch must not consume body");}}});
  }else{
    readOld({done:false,value:new TextEncoder().encode(
      'event: complete\\ndata: {"result":{"response":"stale result"}}\\n\\n'
    )});
  }
  await old;
  assert.equal(completions.length,0,"STOP must suppress stale completion");
  assert.equal(shown.filter(item=>item.role==="assistant").length,0,
    "STOP must suppress stale assistant response");
  assert.equal(context.oapLocked,true,"stale finally must not unlock new work");
  assert.equal(context.oapAbort,requests[1].signal ? context.oapAbort:null);
  assert.equal(running.filter(value=>value===false).length,0,
    "stale finally must not reset newer request UI");

  let readCount=0;
  requests[1].resolve({ok:true,body:{getReader(){return{async read(){
    if(readCount++===0)return{done:false,value:new TextEncoder().encode(
      'event: complete\\ndata: {"result":{"response":"new result"}}\\n\\n'
    )};
    return{done:true};
  }};}}});
  await next;
  assert.equal(completions.length,1,"new request alone may complete");
  assert.equal(shown.filter(item=>item.role==="assistant").length,1);
  assert.equal(shown.find(item=>item.role==="assistant").value,"new result");
  assert.equal(running.filter(value=>value===false).length,1,
    "only current request cleanup should end running UI");
}
(async()=>{
 await exercise("fetch");
 await exercise("read");
 console.log("SMI_STOP_STREAM_RACE_PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});
