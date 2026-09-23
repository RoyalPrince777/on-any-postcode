/* Explicit owner action only. Mail contents never enter chat messages/history. */
(()=>{
  "use strict";
  const boot=()=>{
    const cfg=window.OAP_SMI_UI||{};
    const menu=document.getElementById("attach-menu");
    const plus=document.getElementById("plus-button");
    if(!menu||!cfg.mailReadUrl||!cfg.csrfToken)return;
    if(document.getElementById("oap-mail-read-inbox"))return;
    const button=document.createElement("button");
    button.type="button";
    button.id="oap-mail-read-inbox";
    button.className="attach-option";
    button.textContent="📥 OAP Mail · Read Inbox";
    button.setAttribute("aria-label","Read my OAP Mail inbox with fresh consent");
    menu.append(button);

    button.addEventListener("click",async ()=>{
      if(button.disabled)return;
      menu.classList.remove("show");
      if(plus)plus.setAttribute("aria-expanded","false");
      if(!window.confirm("Read up to 50 messages from your OAP Mail inbox this time only? No sending or automatic SMI access."))return;
      if(typeof HTMLDialogElement==="undefined"||typeof HTMLDialogElement.prototype.showModal!=="function")return;
      button.disabled=true;
      const dialog=document.createElement("dialog");
      dialog.id="oap-mail-private-dialog";
      dialog.setAttribute("aria-label","Private OAP Mail inbox");
      dialog.style.cssText="max-width:min(520px,92vw);max-height:75vh;overflow:auto;background:#101c16;color:#fff;border:1px solid #466b52;border-radius:12px;padding:20px";
      const heading=document.createElement("h2");
      heading.textContent="📥 OAP Mail · Inbox (private, read-only)";
      const close=document.createElement("button");
      close.type="button";
      close.textContent="Close and clear Mail";
      close.setAttribute("aria-label","Close and clear private Mail");
      const results=document.createElement("div");
      results.setAttribute("role","status");
      results.setAttribute("aria-live","polite");
      results.textContent="Reading your inbox…";
      dialog.append(heading,close,results);
      let controller=new AbortController();
      dialog.addEventListener("close",()=>{
        controller.abort();
        dialog.replaceChildren();
        dialog.remove();
        button.disabled=false;
        button.focus();
      },{once:true});
      close.addEventListener("click",()=>dialog.close());
      const leave=()=>{if(dialog.open)dialog.close();};
      window.addEventListener("pagehide",leave,{once:true});
      document.body.append(dialog);
      try{
        dialog.showModal();
        close.focus();
        const response=await fetch(cfg.mailReadUrl,{
          method:"POST",credentials:"same-origin",cache:"no-store",
          headers:{"Content-Type":"application/json","X-OAP-CSRF":cfg.csrfToken},
          body:JSON.stringify({folder:"inbox",ability:"mail.read",owner_consent:true}),
          signal:controller.signal
        });
        if(!response.ok)throw new Error("Mail read denied or unavailable");
        const payload=await response.json();
        if(!Array.isArray(payload.items)||payload.execute!==false||payload.delivery_enabled!==false){
          throw new Error("Unexpected Mail read response");
        }
        if(!dialog.open||controller.signal.aborted)return;
        results.replaceChildren();
        if(!payload.items.length)results.textContent="No inbox items returned.";
        for(const item of payload.items.slice(0,50)){
          const entry=document.createElement("p");
          const subject=String(item.subject||"(no subject)");
          const correspondent=String(item.correspondent||"");
          entry.textContent=subject+(correspondent?" · "+correspondent:"");
          results.append(entry);
        }
      }catch{
        if(dialog.open&&!controller.signal.aborted){
          results.textContent="OAP Mail read unavailable · no Mail sent.";
        }
      }finally{
        if(!dialog.open){
          controller.abort();
          dialog.replaceChildren();
          dialog.remove();
          button.disabled=false;
        }
      }
    });
  };
  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",boot,{once:true});
  }else boot();
})();
