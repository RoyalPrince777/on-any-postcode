/* Explicit owner action only. Never infer Mail consent from chat text. */
(()=>{
  "use strict";
  const boot=()=>{
    const cfg=window.OAP_SMI_UI||{};
    const menu=document.getElementById("attach-menu");
    const messages=document.getElementById("messages");
    const plus=document.getElementById("plus-button");
    if(!menu||!messages||!cfg.mailReadUrl||!cfg.csrfToken)return;
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
      button.disabled=true;
      const status=document.getElementById("status");
      try{
        const response=await fetch(cfg.mailReadUrl,{
          method:"POST",credentials:"same-origin",cache:"no-store",
          headers:{"Content-Type":"application/json","X-OAP-CSRF":cfg.csrfToken},
          body:JSON.stringify({folder:"inbox",ability:"mail.read",owner_consent:true})
        });
        if(!response.ok)throw new Error("OAP Mail read unavailable ("+response.status+").");
        const payload=await response.json();
        if(!Array.isArray(payload.items)||payload.execute!==false||payload.delivery_enabled!==false){
          throw new Error("OAP Mail response did not meet the read-only contract.");
        }
        const panel=document.createElement("div");
        panel.className="msg system oap-mail-private-read";
        const heading=document.createElement("strong");
        heading.textContent="📥 OAP Mail · Inbox (private, read-only)";
        panel.append(heading);
        if(!payload.items.length){
          const empty=document.createElement("p");
          empty.textContent="No inbox items returned.";
          panel.append(empty);
        }
        for(const item of payload.items.slice(0,50)){
          const entry=document.createElement("p");
          const subject=String(item.subject||"(no subject)");
          const correspondent=String(item.correspondent||"");
          entry.textContent=subject+(correspondent?" · "+correspondent:"");
          panel.append(entry);
        }
        messages.append(panel);
        messages.scrollTop=messages.scrollHeight;
        if(status)status.textContent="Mail inbox read complete · not added to SMI conversation";
      }catch{
        if(status)status.textContent="OAP Mail read unavailable · no mail sent";
      }finally{
        button.disabled=false;
      }
    });
  };
  if(document.readyState==="loading"){
    document.addEventListener("DOMContentLoaded",boot,{once:true});
  }else boot();
})();
