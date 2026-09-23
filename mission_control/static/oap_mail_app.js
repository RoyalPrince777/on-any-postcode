/* First-party owner Mail UI: explicit folder reads and unsent drafts only. */
(()=>{
  "use strict";
  const boot=()=>{
    const root=document.getElementById("oap-mail-app");
    if(!root)return;
    const status=document.getElementById("mail-status");
    const items=document.getElementById("mail-items");
    const title=document.getElementById("mail-folder-title");
    const form=document.getElementById("mail-draft-form");
    if(!status||!items||!title||!form)return;
    const folderUrl=root.dataset.folderUrl;
    const draftUrl=root.dataset.draftUrl;
    const csrf=root.dataset.csrfToken;
    if(!folderUrl||!draftUrl||!csrf)return;
    let active=null;
    const clear=()=>{if(active)active.abort();active=null;items.replaceChildren();};
    const renderItem=item=>{
      if(item===null||typeof item!=="object"||Array.isArray(item)||
        typeof item.subject!=="string"||typeof item.body!=="string"||
        typeof item.correspondent!=="string")throw new Error("Invalid Mail item");
      const card=document.createElement("article");
      card.className="mail-entry";
      const heading=document.createElement("strong");
      heading.textContent=item.subject||"(no subject)";
      const contact=document.createElement("p");
      contact.className="secondary";
      contact.textContent=item.correspondent||"No correspondent";
      const body=document.createElement("p");
      body.textContent=item.body;
      card.append(heading,contact,body);
      return card;
    };
    for(const button of root.querySelectorAll("[data-mail-folder]")){
      button.addEventListener("click",async()=>{
        const folder=button.dataset.mailFolder;
        if(!["inbox","draft","sent","review"].includes(folder))return;
        clear();
        const controller=new AbortController();
        active=controller;
        title.textContent=folder==="draft"?"Drafts":folder[0].toUpperCase()+folder.slice(1);
        status.textContent="Reading your private mailbox…";
        try{
          const response=await fetch(folderUrl.replace("__FOLDER__",folder),{
            credentials:"same-origin",cache:"no-store",signal:controller.signal
          });
          if(!response.ok)throw new Error("Mail unavailable");
          const payload=await response.json();
          if(!Array.isArray(payload.items)||payload.items.length>50||
            payload.delivery_enabled!==false)throw new Error("Invalid Mail response");
          const fragment=document.createDocumentFragment();
          for(const entry of payload.items)fragment.append(renderItem(entry));
          if(controller.signal.aborted)return;
          items.replaceChildren(fragment);
          status.textContent=payload.items.length?
            "Private Mail loaded. No message has been sent.":"No Mail in this folder.";
        }catch{
          if(!controller.signal.aborted){
            items.replaceChildren();
            status.textContent="Mailbox unavailable. No Mail sent.";
          }
        }finally{if(active===controller)active=null;}
      });
    }
    form.addEventListener("submit",async event=>{
      event.preventDefault();
      const button=form.querySelector('button[type="submit"]');
      if(!button||button.disabled)return;
      button.disabled=true;
      status.textContent="Saving unsent draft…";
      const data=new FormData(form);
      const payload={
        subject:data.get("subject"),body:data.get("body"),
        correspondent:data.get("correspondent")
      };
      try{
        const response=await fetch(draftUrl,{
          method:"POST",credentials:"same-origin",cache:"no-store",
          headers:{"Content-Type":"application/json","X-OAP-CSRF":csrf},
          body:JSON.stringify(payload)
        });
        if(!response.ok)throw new Error("Draft unavailable");
        const result=await response.json();
        if(typeof result.draft_id!=="string"||result.sent!==false)
          throw new Error("Invalid draft receipt");
        status.textContent="Unsent draft saved. No email delivered.";
      }catch{
        status.textContent="Draft could not be saved. No email delivered.";
      }finally{button.disabled=false;}
    });
    window.addEventListener("pagehide",clear,{once:true});
  };
  if(document.readyState==="loading")
    document.addEventListener("DOMContentLoaded",boot,{once:true});
  else boot();
})();
