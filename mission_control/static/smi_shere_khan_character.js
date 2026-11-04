/* Shere Khan optional character view; one existing SMI brain and voice path.
 * This is an SVG/CSS character representation, not a verified 3D rig or lip sync.
 */
(() => {
  "use strict";
  const allowed = new Set(["ready","listening","thinking","speaking","paused","stopped"]);
  const root = document.querySelector(".smi-shell");
  if (!root) return;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "shere-khan-toggle";
  button.textContent = "🐅 Shere Khan";
  button.setAttribute("aria-expanded", "false");
  button.setAttribute("aria-controls", "shere-khan-presence");
  button.title = "Show or hide Shere Khan character view";
  const panel = document.createElement("aside");
  panel.id = "shere-khan-presence";
  panel.className = "shere-khan-presence";
  panel.hidden = true;
  panel.setAttribute("aria-label", "Shere Khan animated character");
  panel.dataset.state = "ready";
  panel.innerHTML = `
    <div class="shere-khan-stage" aria-hidden="true">
      <svg viewBox="0 0 340 300" role="img" aria-label="Stylized tiger portrait">
        <defs><radialGradient id="shere-amber"><stop stop-color="#ffbe58"/><stop offset="1" stop-color="#b45f25"/></radialGradient></defs>
        <g class="shere-breath">
          <path d="M48 288Q56 215 170 203Q284 215 292 288" fill="#8d4b26" stroke="#2b201a" stroke-width="9"/>
          <path d="M90 264Q119 244 170 250Q221 244 250 264" fill="none" stroke="#efae53" stroke-width="12"/>
        </g>
        <g class="shere-head">
          <path d="M75 75L70 15Q96 0 121 37L139 66M265 75L270 15Q244 0 219 37L201 66" fill="#b46a34" stroke="#2d211b" stroke-width="8" stroke-linejoin="round"/>
          <path d="M85 67L86 30L115 54M255 67L254 30L225 54" fill="#6f3e37"/>
          <path d="M57 101Q62 31 170 32Q278 31 283 101L266 198Q240 248 170 257Q100 248 74 198Z" fill="url(#shere-amber)" stroke="#30231c" stroke-width="9"/>
          <path d="M110 42L136 99L119 128L93 69M230 42L204 99L221 128L247 69M167 38L154 91L170 115L186 91Z" fill="#3a231c"/>
          <path d="M65 107L110 136L82 154M275 107L230 136L258 154M76 176L119 182L95 207M264 176L221 182L245 207" fill="#39241c"/>
          <g class="shere-eyes">
            <path d="M97 137Q124 120 148 139Q123 162 97 137ZM192 139Q216 120 243 137Q217 162 192 139Z" fill="#fff1ca" stroke="#35251b" stroke-width="7"/>
            <ellipse cx="124" cy="140" rx="7" ry="15" fill="#1b241c"/><ellipse cx="216" cy="140" rx="7" ry="15" fill="#1b241c"/>
          </g>
          <path d="M139 169Q109 158 103 192Q106 227 167 231Q229 227 237 192Q231 159 201 169Z" fill="#f4dbb6"/>
          <path d="M144 175L170 186L196 175L184 199L170 205L156 199Z" fill="#382820"/>
          <path d="M170 205V221M137 221Q170 232 203 221" stroke="#382820" stroke-width="6" fill="none" stroke-linecap="round"/>
          <g stroke="#493528" stroke-width="2.5"><path d="M121 202L58 190M119 214L52 218M219 202L282 190M221 214L288 218"/></g>
        </g>
      </svg>
    </div>
    <strong>SHERE KHAN</strong>
    <span class="shere-status" aria-live="off">Ready · Character view only</span>
    <small>Loyalty Over Everything · Founder Final</small>`;
  root.append(button,panel);
  function setState(value) {
    const state = allowed.has(value) ? value : "ready";
    panel.dataset.state = state;
    const label = panel.querySelector(".shere-status");
    if (label) label.textContent = state.charAt(0).toUpperCase()+state.slice(1)+" · Character view only";
  }
  button.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    button.setAttribute("aria-expanded", String(!panel.hidden));
  });
  window.addEventListener("oap-smi-character-state", event => setState(event.detail?.state));
  setState(document.querySelector("#smi-character")?.dataset.state || "ready");
})();
