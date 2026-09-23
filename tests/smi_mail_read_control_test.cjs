"use strict";
// Dependency-free DOM interaction regression, not a real Chromium acceptance test.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync("mission_control/static/smi_mail_read_control.js","utf8");

class Element{
  constructor(tag="div"){this.tag=tag;this.children=[];this.handlers={};this.dataset={};this.attributes={};this.open=false;this.disabled=false;this.textContent="";this.style={};this.classList={remove:()=>{},add:()=>{}};this.removed=false;}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=[...children];this.textContent="";}
  setAttribute(k,v){this.attributes[k]=v;}
  addEventListener(type,handler){(this.handlers[type]??=[]).push(handler);}
  async click(){for(const fn of this.handlers.click||[])await fn();}
  focus(){this.focused=true;}
  remove(){this.removed=true;}
  showModal(){this.open=true;}
  close(){this.open=false;for(const fn of this.handlers.close||[])fn();}
}
function setup(confirm=true){
  const menu=new Element(),plus=new Element(),body=new Element();
  let dialog,request,requested=0;
  const elements={"attach-menu":menu,"plus-button":plus};
  const document={
    readyState:"complete",body,
    getElementById:id=>elements[id]||null,
    createElement:tag=>new Element(tag),
  };
  const window={
    OAP_SMI_UI:{mailReadUrl:"/mission/chat/tools/mail/read",csrfToken:"csrf"},
    confirm:()=>confirm,
    addEventListener:()=>{},
  };
  let respond;
  const fetch=(url,opts)=>{requested++;request={url,opts};return new Promise(resolve=>{respond=resolve;});};
  const context={document,window,fetch,HTMLDialogElement:Element,AbortController};
  vm.runInNewContext(source,context);
  const button=menu.children[0];
  return {menu,plus,body,button,request:()=>request,requested:()=>requested,respond:response=>respond(response),dialog:()=>body.children.find(e=>e.tag==="dialog")};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  const denied=setup(false);
  await denied.button.click();
  assert.equal(denied.requested(),0,"cancel must not fetch Mail");
  assert.equal(denied.dialog(),undefined,"cancel must not create a Mail DOM panel");

  const yes=setup(true);
  const pending=yes.button.click();
  assert.equal(yes.requested(),1);
  const {url,opts}=yes.request();
  assert.equal(url,"/mission/chat/tools/mail/read");
  assert.equal(opts.method,"POST");
  assert.equal(opts.headers["X-OAP-CSRF"],"csrf");
  assert.equal(JSON.parse(opts.body).owner_consent,true);
  assert.equal(yes.button.disabled,true);
  const dlg=yes.dialog();
  assert.equal(dlg.open,true);
  yes.respond({ok:true,json:async()=>({items:[{subject:"<private>",correspondent:"owner@example.test",body:"SECRET BODY"}],execute:false,delivery_enabled:false})});
  await pending;
  const result=dlg.children[2];
  assert.equal(result.children[0].textContent,"<private> · owner@example.test");
  assert(!JSON.stringify(result).includes("SECRET BODY"));
  assert(!yes.body.children.some(el=>el.attributes?.class==="msg"),"no conversation message created");
  dlg.close();
  assert.equal(dlg.removed,true);
  assert.equal(dlg.children.length,0);
  assert.equal(yes.button.disabled,false);
  assert.equal(opts.signal.aborted,true);

  const late=setup(true);
  const fetching=late.button.click();
  const last=late.dialog();
  last.close();
  late.respond({ok:true,json:async()=>({items:[{subject:"late private"}],execute:false,delivery_enabled:false})});
  await fetching;
  assert.equal(last.children.length,0,"late response must not recreate private Mail DOM");
  assert.equal(last.removed,true);

  const failed=setup(true);
  const attempt=failed.button.click();
  failed.respond({ok:false,status:503});
  await attempt;
  assert.equal(failed.dialog().children[2].textContent,"OAP Mail read unavailable · no Mail sent.");
  failed.dialog().close();
  console.log("OAP_MAIL_DOM_BOUNDARY_PASS: cancel, consent, CSRF, subject-only, isolation, close, abort, late response, error");
})().catch(e=>{console.error(e);process.exitCode=1;});
