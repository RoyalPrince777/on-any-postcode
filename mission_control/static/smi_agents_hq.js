"use strict";
(() => {
  const form = document.getElementById("oap-agents-hq-form");
  if (!form) return;
  const input = document.getElementById("oap-agents-hq-message");
  const button = document.getElementById("oap-agents-hq-send");
  const status = document.getElementById("oap-agents-hq-status");
  const transcript = document.getElementById("oap-agents-hq-transcript");
  const select = document.getElementById("oap-alliance-select");
  const allianceStatus = document.getElementById("oap-alliance-status");
  const allianceResults = document.getElementById("oap-alliance-results");
  if (select && allianceStatus && allianceResults) {
    select.addEventListener("click", async () => {
      const mission = input.value.trim();
      if (!mission || select.disabled) {
        allianceStatus.textContent = "Enter a mission above before selecting specialists.";
        return;
      }
      select.disabled = true;
      allianceResults.replaceChildren();
      allianceStatus.textContent = "Checking canonical ACTIVE passports…";
      try {
        const response = await fetch(select.dataset.endpoint, {
          method: "POST",
          credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-OAP-CSRF": form.dataset.csrf},
          body: JSON.stringify({mission, task_type: "GENERAL"})
        });
        if (!response.ok) {
          allianceStatus.textContent = "Alliance selection unavailable (" + response.status + ").";
          return;
        }
        const result = await response.json();
        if (result.advisory_only !== true || result.execution_authorised !== false ||
            result.agent_messages_generated !== false || result.founder_final !== true ||
            !Array.isArray(result.recommended_specialists)) {
          allianceStatus.textContent = "Untrusted alliance result rejected.";
          return;
        }
        const list = result.recommended_specialists.filter(name => typeof name === "string");
        allianceResults.textContent = list.length ?
          "Eligible advisory specialists: " + list.join(", ") :
          "No eligible specialist passports confirmed for this mission.";
        allianceStatus.textContent = "Passport selection returned. No agents activated; Founder Final retained.";
      } catch (_error) {
        allianceStatus.textContent = "Alliance selection not verified. No agents activated.";
      } finally {
        select.disabled = false;
      }
    });
  }
  let conversationId = null;
  function entry(author, message) {
    const card = document.createElement("article");
    card.className = "org-card";
    const heading = document.createElement("h3");
    heading.textContent = author;
    const body = document.createElement("p");
    body.textContent = message;
    card.append(heading, body);
    transcript.appendChild(card);
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || button.disabled) return;
    button.disabled = true;
    status.textContent = "Sending to governed SMI…";
    try {
      const response = await fetch(form.dataset.endpoint, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-OAP-CSRF": form.dataset.csrf
        },
        body: JSON.stringify({message, conversation_id: conversationId})
      });
      if (!response.ok) {
        status.textContent = "SMI request not completed (" + response.status + "). No reply recorded here.";
        return;
      }
      const data = await response.json();
      if (data.reply_source !== "existing_governed_smi_runtime" ||
          data.individual_agent_reply_verified !== false) {
        status.textContent = "Reply rejected: unexpected identity attribution.";
        return;
      }
      const reply = data.smi_reply || {};
      const text = typeof reply.response === "string" ? reply.response : "";
      if (!text) {
        status.textContent = "No confirmed SMI response received.";
        return;
      }
      entry("Founder", message);
      entry("SMI (governed runtime)", text);
      conversationId = typeof reply.conversation_id === "string" ?
        reply.conversation_id : conversationId;
      input.value = "";
      status.textContent = "SMI responded. Individual agent dialogue is not yet verified.";
    } catch (_error) {
      status.textContent = "SMI request failed. No conversation completion confirmed.";
    } finally {
      button.disabled = false;
    }
  });
})();
