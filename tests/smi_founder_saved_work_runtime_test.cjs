'use strict';
// Exercise the ACTUAL saved-work functions in the SMI chat template with a
// simulated browser and owned API. No credentials, live database or deployment.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const base=fs.readFileSync(
  path.join(__dirname,'../mission_control/templates/ollama_chat_base.html'),'utf8'
);
function between(start,end){
  const a=base.indexOf(start);
  assert(a>=0,'Missing saved-work start: '+start);
  const b=base.indexOf(end,a+start.length);
  assert(b>a,'Missing saved-work end: '+end);
  return base.slice(a,b);
}
const code=[
  between('let conversationId=null,','function renderMessage('),
  between('function resetConversation(){','function workedSeconds()'),
  between('async function loadConversations(){','async function deleteConversation('),
].join('\n');
assert(base.includes('loadHealth();loadConversations();setInterval(loadHealth,30000);'),
  'Saved-work bootstrap must be installed');

const A='11111111-1111-4111-8111-111111111111';
const B='22222222-2222-4222-8222-222222222222';
const KEY='oap:smi:active-conversation:v1';
const eventLog=[];
function node(){
  return {
    dataset:{},style:{},textContent:'',
    append(){},setAttribute(){},querySelectorAll(){return []},
    classList:{add(){},remove(){},toggle(){}},
  };
}
function harness({stored=null,owner=A,list=[],deferred=null}={}){
  const store=new Map(stored?[[KEY,stored]]:[]);
  const calls=[];
  const displayed=[];
  const messages=node();
  const historyList=node();
  let currentOwner=owner;
  const api=async(url)=>{
    calls.push({url,owner:currentOwner});
    if(url==='/mission/conversations'){
      return {ok:true,json:async()=>({conversations:list})};
    }
    if(url==='/mission/conversations/'+A){
      if(deferred)await deferred.promise;
      if(currentOwner!==A)return {
        ok:false,status:404,
        json:async()=>({error:{message:'Conversation not found.'}}),
      };
      return {
        ok:true,status:200,
        json:async()=>({
          conversation_id:A,
          messages:[
            {role:'user',content:'Founder-only War Room mission.'},
            {role:'assistant',content:'Reviewed; no deployment.'},
          ],
        }),
      };
    }
    throw Error('Unexpected URL '+url);
  };
  const context=vm.createContext({
    sessionStorage:{
      getItem:k=>store.get(k)??null,
      setItem:(k,v)=>store.set(k,v),
      removeItem:k=>store.delete(k),
    },
    fetch:api,
    conversationsUrl:'/mission/conversations',
    document:{
      createElement:node,
      getElementById:()=>node(),
      querySelector:()=>node(),
    },
    messages,historyList,
    historyStatus:node(),historyCount:node(),statusEl:node(),
    messageInput:{focus(){}},
    add:(content,role)=>displayed.push({content,role}),
    hideThinking(){},encodeURIComponent,Array,
  });
  vm.runInContext(code,context,{filename:'ollama_chat_base.saved_work.js'});
  return {
    store,calls,displayed,
    eval:source=>vm.runInContext(source,context),
    setOwner:v=>{currentOwner=v},
  };
}
function deferred(){
  let resolve;
  const promise=new Promise(r=>{resolve=r});
  return {promise,resolve};
}
async function test(label,fn){
  await fn();
  eventLog.push(label);
  process.stdout.write('PASS '+label+'\n');
}
(async()=>{
  await test('authenticated reload restores exact saved conversation',async()=>{
    const h=harness({stored:A,owner:A,list:[{conversation_id:A,title:'Founder work',message_count:2}]});
    await h.eval('loadConversations()');
    assert.equal(h.eval('conversationId'),A);
    assert.deepEqual(h.displayed.map(x=>x.content),
      ['Founder-only War Room mission.','Reviewed; no deployment.']);
    assert.deepEqual(h.calls.map(x=>x.url),
      ['/mission/conversations','/mission/conversations/'+A]);
    assert.deepEqual([...h.store.entries()],[[KEY,A]]);
  });
  await test('other identity cannot inherit saved Founder work',async()=>{
    const h=harness({stored:A,owner:B,list:[]});
    await h.eval('loadConversations()');
    assert.equal(h.eval('conversationId'),null);
    assert.equal(h.store.has(KEY),false);
    assert.equal(h.displayed.length,0);
  });
  await test('new chat wins over a delayed saved-work response',async()=>{
    const pending=deferred();
    const h=harness({stored:A,owner:A,deferred:pending});
    const restoring=h.eval('loadConversations()');
    for(let n=0;n<12&&!h.calls.some(x=>x.url.endsWith(A));n++)await Promise.resolve();
    assert(h.calls.some(x=>x.url.endsWith(A)),'Restore request started');
    h.eval('resetConversation()');
    pending.resolve();
    await restoring;
    assert.equal(h.eval('conversationId'),null);
    assert.equal(h.store.has(KEY),false);
    assert.equal(h.displayed.some(x=>x.content==='Founder-only War Room mission.'),false);
  });
  await test('invalid storage ID cannot trigger owned-content request',async()=>{
    const h=harness({stored:'not-a-uuid',owner:A});
    await h.eval('loadConversations()');
    assert.equal(h.store.has(KEY),false);
    assert.deepEqual(h.calls.map(x=>x.url),['/mission/conversations']);
  });
  await test('manual saved-work selection remains owner verified',async()=>{
    const h=harness({owner:A});
    await h.eval('openConversation("'+A+'")');
    assert.equal(h.eval('conversationId'),A);
    assert.equal(h.store.get(KEY),A);
    h.setOwner(B);
    h.eval('resetConversation()');
    await h.eval('openConversation("'+A+'")');
    assert.equal(h.eval('conversationId'),null);
    assert.equal(h.store.has(KEY),false);
  });
  assert.equal(eventLog.length,5);
  process.stdout.write('SMI_FOUNDER_SAVED_WORK_RUNTIME_SIMULATION_PASS\n');
})().catch(error=>{console.error(error);process.exitCode=1});
