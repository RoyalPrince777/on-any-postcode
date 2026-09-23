"""Render the real Personal SMI Jinja page for isolated Chromium acceptance.

No HTTP service, credentials, DB calls or persistence. Generated file is CI-only.
"""
from __future__ import annotations

import importlib
import pathlib
import re
import sys

from flask import render_template

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

app_module = importlib.import_module("app")

OUTPUT = ROOT / "tests" / ".smi_mail_full_page.html"

with app_module.app.test_request_context("/mission/ollama"):
    html = render_template(
        "ollama_chat.html", chat={}, oap_csrf_token="browser-test-csrf",
    )

# Load real, unmodified local application scripts from the checkout. All
# unspecified external navigations/requests are blocked by the file scheme.
html = html.replace('src="/mission/static/', 'src="../mission_control/static/')
html = html.replace('href="/mission/static/', 'href="../mission_control/static/')
html = re.sub(r'<script>\s*window\.OAP_SMI_RIG_FOUNDATION=.*?</script>', "", html, flags=re.DOTALL)

# Set the Mail endpoint to a fake same-page fetch; do not call a Mail server.
html += """
<script>
window.OAP_SMI_MAIL_FULL_PAGE_TEST={
  started:false, requestCount:0, errors:[]
};
window.addEventListener("load",async()=>{
  const proof=document.getElementById("oap-mail-full-page-proof");
  const state=window.OAP_SMI_MAIL_FULL_PAGE_TEST;
  const check=(ok,why)=>{if(!ok)throw Error(why);};
  const tick=()=>new Promise(resolve=>setTimeout(resolve,0));
  try{
    const menu=document.getElementById("attach-menu");
    const plus=document.getElementById("plus-button");
    const button=document.getElementById("oap-mail-read-inbox");
    check(menu&&plus&&button,"real SMI drawer/control missing");
    check(Boolean(document.getElementById("messages")),"chat messages missing");
    window.confirm=()=>false;
    plus.click();
    check(menu.classList.contains("show"),"Plus drawer did not open");
    button.click();
    await tick();
    check(!document.querySelector("#oap-mail-private-dialog"),"consent cancel created private DOM");
    check(state.requestCount===0,"consent cancel fetched Mail");
    window.confirm=()=>true;
    const originalFetch=window.fetch;
    window.fetch=(url,options)=>{
      if(url!==window.OAP_SMI_UI.mailReadUrl)return Promise.reject(Error("fixture blocked non-Mail request"));
      state.requestCount++;
      check(options.method==="POST","wrong HTTP method");
      check(options.headers["X-OAP-CSRF"]==="browser-test-csrf","missing CSRF");
      check(JSON.parse(options.body).owner_consent===true,"missing fresh consent");
      return Promise.resolve({ok:true,json:async()=>({
        items:[{subject:"<PRIVATE SUBJECT>",body:"NEVER IN SMI CHAT"}],
        execute:false,delivery_enabled:false
      })});
    };
    button.click();
    await tick();await tick();
    const dialog=document.getElementById("oap-mail-private-dialog");
    check(dialog&&dialog.open,"Mail modal missing");
    check(dialog.textContent.includes("<PRIVATE SUBJECT>"),"Mail subject missing");
    check(!document.getElementById("messages").textContent.includes("PRIVATE SUBJECT"),"Mail leaked to chat");
    check(!dialog.textContent.includes("NEVER IN SMI CHAT"),"body leaked into dialog");
    dialog.querySelector("button").click();
    await tick();
    check(!document.getElementById("oap-mail-private-dialog"),"private Mail not cleared");
    window.fetch=originalFetch;
    state.started=true;
    proof.textContent="OAP_MAIL_FULL_SMI_PAGE_PASS";
  }catch(error){
    state.errors.push(error.message);
    proof.textContent="OAP_MAIL_FULL_SMI_PAGE_FAIL "+error.message;
  }
});
</script>
<pre id="oap-mail-full-page-proof">PENDING</pre>
"""
OUTPUT.write_text(html, encoding="utf-8")
print("Generated real SMI Jinja page for local browser fixture")
