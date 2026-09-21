/* First-party War Room mission contract. Additive to the canonical SMI chat. */
(() => {
  "use strict";
  const MISSIONS = Object.freeze([
    ["centre", "👑 Command Centre + all chats"],
    ["egress", "🔒 External egress"],
    ["hrm", "🧠 HRM rollback"],
    ["home", "🏠 Home Node custody"],
    ["bypass", "🛡️ Provider bypasses"],
    ["hosted", "🧪 Hosted proof"],
    ["media", "🎙️ Private media"],
    ["judges", "⭐ Seven judges"],
    ["red", "⚔️ Red Team"],
    ["voices", "🗣️ Specialists speak"],
    ["lenses", "📊 SWOT + 26 lenses"]
  ]);
  const allowed = new Set(MISSIONS.map(item => item[0]));
  const buildContract = ({selected, depth, mode, instruction, approved}) => {
    const ids = [...new Set(selected)].filter(id => allowed.has(id));
    if (!ids.length || ![3, 7, 21].includes(Number(depth)) ||
        !["review", "simulation", "build"].includes(mode)) {
      throw new Error("war_room_selection_required");
    }
    if (mode === "build" && approved !== true) {
      throw new Error("draft_approval_required");
    }
    const main = String(instruction || "").trim().slice(0, 750);
    const names = ids.map(id => MISSIONS.find(item => item[0] === id)[1]);
    return "🟣 SMI AUTO " + depth + " · GOLD WAR ROOM. MAIN FOUNDER MISSION: " +
      (main || "Advance selected first-party intelligence work.") +
      " Selected missions: " + names.join("; ") + ". Mode: " + mode +
      ". Check exact source and CI. Lead with evidence-backed seven-star proof, 21 denominated signals, four-step checkpoints, Done/Next/Recovery and Founder Final. " +
      "Separate genuine votes from simulated first-party views. " +
      (mode === "build"
        ? "Draft-only changes and tests approved; no merge or deployment. "
        : "Review/simulation only; no repository writes or tests. ") +
      "No fake green. Preserve every chat, history, composer, Plus/upload, STOP, character and canonical controller.";
  };
  window.OAP_SMI_WAR_ROOM_MISSIONS = Object.freeze({missions: MISSIONS, buildContract});
  const centre = document.getElementById("smi-command-centre");
  const composer = document.getElementById("message");
  const toggle = document.querySelector(".smi-command-toggle");
  if (!centre || !composer || !toggle) return;

  const selector = document.createElement("section");
  selector.className = "smi-war-missions";
  selector.setAttribute("aria-label", "Founder War Room mission selector");
  selector.innerHTML = '<button type="button" data-war-close aria-label="Close War Room selector">✕ Close War Room</button><h3>🟣 SMI · 👑 GOLD WAR ROOM</h3>' +
    '<p>Multiple missions · one canonical chat request · Founder Final</p>' +
    '<div class="smi-war-options" role="group" aria-label="Select War Room missions"></div>' +
    '<div class="smi-war-fields"><label>Depth <select data-war-depth><option value="3">3 · Quick</option><option value="7">7 · Deep</option><option value="21" selected>21 · Full</option></select></label>' +
    '<label>Action <select data-war-mode><option value="review">Review + recommend</option><option value="simulation">Simulation only</option><option value="build">Build + test draft only</option></select></label></div>' +
    '<label class="smi-war-main">MAIN Founder instruction<textarea data-war-instruction rows="2" maxlength="750" placeholder="Your instruction takes priority"></textarea></label>' +
    '<label class="smi-war-approval"><input type="checkbox" data-war-approval> Approve bounded draft-only edits and tests (Build mode only)</label>' +
    '<div class="smi-war-controls"><button type="button" data-war-all>Select all</button><button type="button" data-war-p0>Command + P0</button><button type="button" data-war-clear>Clear</button></div>' +
    '<button type="button" data-war-prepare>🟣 PREPARE IN CHAT · Press Send to run</button>' +
    '<p data-war-feedback role="status" aria-live="polite">Review only · no proof awarded from a selection.</p>';
  centre.querySelector(".smi-command-universe").before(selector);
  const options = selector.querySelector(".smi-war-options");
  const selectedDefault = new Set(["centre", "egress", "hrm", "home", "bypass", "hosted", "media", "judges", "red"]);
  MISSIONS.forEach(([id, label]) => {
    const item = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox"; input.value = id; input.checked = selectedDefault.has(id);
    item.append(input, document.createTextNode(" " + label));
    options.append(item);
  });
  const feedback = selector.querySelector("[data-war-feedback]");
  const checkboxes = () => [...options.querySelectorAll('input[type="checkbox"]')];
  const setSelection = ids => checkboxes().forEach(box => { box.checked = ids.includes(box.value); });
  selector.querySelector("[data-war-all]").addEventListener("click", () => setSelection(MISSIONS.map(m => m[0])));
  selector.querySelector("[data-war-p0]").addEventListener("click", () => setSelection(["centre", "egress", "hrm", "home", "bypass", "hosted"]));
  selector.querySelector("[data-war-clear]").addEventListener("click", () => setSelection([]));
  const mode = selector.querySelector("[data-war-mode]");
  const approval = selector.querySelector("[data-war-approval]");
  const syncApproval = () => { approval.disabled = mode.value !== "build"; if (approval.disabled) approval.checked = false; };
  mode.addEventListener("change", syncApproval);
  syncApproval();
  const open = document.createElement("button");
  open.type = "button"; open.className = "smi-war-open"; open.dataset.smiWarRoomOpen = "1";
  open.textContent = "⚔️ War Room"; open.setAttribute("aria-controls", "smi-war-missions");
  selector.id = "smi-war-missions";
  toggle.after(open);
  open.addEventListener("click", () => {
    if (!document.body.classList.contains("smi-command-open")) toggle.click();
    centre.classList.add("smi-war-missions-open");
    selector.querySelector("[data-war-instruction]").focus();
  });
  selector.querySelector("[data-war-close]").addEventListener("click", () => centre.classList.remove("smi-war-missions-open"));
  centre.querySelector(".smi-command-close").addEventListener("click", () => centre.classList.remove("smi-war-missions-open"));
  toggle.addEventListener("click", () => {
    if (!document.body.classList.contains("smi-command-open")) centre.classList.remove("smi-war-missions-open");
  });
  selector.querySelector("[data-war-prepare]").addEventListener("click", () => {
    try {
      if (composer.value.trim()) {
        feedback.textContent = "Your current chat draft is preserved. Clear or send it before preparing a War Room request.";
        return;
      }
      const prompt = buildContract({
        selected: checkboxes().filter(input => input.checked).map(input => input.value),
        depth: selector.querySelector("[data-war-depth]").value,
        mode: mode.value,
        instruction: selector.querySelector("[data-war-instruction]").value,
        approved: approval.checked
      });
      if (prompt.length > Number(composer.maxLength || 4000)) throw new Error("war_room_prompt_too_long");
      composer.value = prompt;
      composer.dispatchEvent(new Event("input", {bubbles:true}));
      feedback.textContent = "Prepared in the existing chat composer. Press Send to run; no action or proof has been claimed.";
      centre.classList.remove("smi-war-missions-open");
      toggle.click();
      composer.focus();
    } catch (error) {
      feedback.textContent = error.message === "draft_approval_required"
        ? "Build mode requires your separate draft-only approval."
        : "Select missions and a valid depth before preparing the request.";
    }
  });
})();
