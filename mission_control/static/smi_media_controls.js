(() => {
  "use strict";

  function bootMediaControls() {
    const interaction = document.getElementById("interaction-strip");
    const menu = document.getElementById("attach-menu");
    const input = document.getElementById("message");
    const status = document.getElementById("status");
    const preview = document.getElementById("image-preview");
    const previewImg = document.getElementById("preview-img");
    const previewName = document.getElementById("preview-name");
    if (!interaction || !menu || !input || document.getElementById("studio-creation-strip")) return;

    const setStatus = (text) => {
      if (status) status.textContent = text;
    };
    const hasReference = () =>
      typeof selectedImage !== "undefined" && Boolean(selectedImage);

    const addStudioTool = (toolId, proofAction, icon, label) => {
      let button = menu.querySelector('[data-studio-tool="' + toolId + '"]');
      if (button) return button;
      button = document.createElement("button");
      button.type = "button";
      button.className = "attach-option connector smi-v2-option";
      button.dataset.studioTool = toolId;
      button.dataset.proofAction = proofAction;
      button.innerHTML =
        '<span class="connector-copy"><span>' + icon + '</span><span>' + label +
        '</span></span><span class="connector-state">Run</span>';
      const firstVideo = menu.querySelector('[data-studio-tool="bring_alive"]');
      if (firstVideo) firstVideo.before(button);
      else menu.append(button);
      return button;
    };

    addStudioTool("edit_image", "studio-edit", "✏️", "Edit · Image → Image");
    addStudioTool("refine_image", "studio-refine", "💎", "Refine · Preserve + Improve");

    const controls = document.createElement("nav");
    controls.id = "studio-creation-strip";
    controls.className = "smi-interaction-strip smi-creation-strip";
    controls.setAttribute("aria-label", "OAP Studio creation controls");
    controls.innerHTML = [
      '<button type="button" class="smi-interaction-tab" id="create-mode-button">✨ <span>Create</span></button>',
      '<button type="button" class="smi-interaction-tab" id="edit-mode-button">✏️ <span>Edit</span></button>',
      '<button type="button" class="smi-interaction-tab" id="refine-mode-button">💎 <span>Refine</span></button>',
      '<button type="button" class="smi-interaction-tab" id="animate-mode-button">🎞️ <span>Animate</span></button>',
      '<button type="button" class="smi-interaction-tab smi-character-lock" id="character-lock-button" aria-pressed="false">🔓 <span>Same Character</span></button>'
    ].join("");
    interaction.insertAdjacentElement("afterend", controls);

    const lockButton = controls.querySelector("#character-lock-button");
    const setCharacterLock = (enabled) => {
      const active = Boolean(enabled);
      window.OAP_SMI_CHARACTER_LOCK = active;
      lockButton.setAttribute("aria-pressed", String(active));
      lockButton.classList.toggle("active", active);
      lockButton.innerHTML = active
        ? '🔒 <span>Same Character</span>'
        : '🔓 <span>Same Character</span>';
      try {
        sessionStorage.setItem("oap_smi_character_lock", active ? "1" : "0");
      } catch {}
    };
    try {
      setCharacterLock(sessionStorage.getItem("oap_smi_character_lock") === "1");
    } catch {
      setCharacterLock(false);
    }

    lockButton.addEventListener("click", () => {
      const enabled = lockButton.getAttribute("aria-pressed") !== "true";
      setCharacterLock(enabled);
      setStatus(
        enabled
          ? "Same Character locked · reference image required for identity continuity"
          : "Same Character unlocked"
      );
    });

    const run = (mode) => {
      const locked = Boolean(window.OAP_SMI_CHARACTER_LOCK);
      const reference = hasReference();
      let toolId = "imagine";

      if (mode === "edit") toolId = "edit_image";
      else if (mode === "refine") toolId = "refine_image";
      else if (mode === "animate") toolId = reference ? "bring_alive" : "scene_builder";
      else if (mode === "create" && locked && reference) toolId = "edit_image";

      if ((mode === "edit" || mode === "refine") && !reference) {
        setStatus(mode[0].toUpperCase() + mode.slice(1) + " needs a reference image · attach, capture or reuse one");
        document.getElementById("image-input")?.click();
        return;
      }
      if (locked && !reference) {
        setStatus("Same Character is locked · attach or reuse the character reference first");
        document.getElementById("image-input")?.click();
        return;
      }
      if ((mode === "create" || mode === "edit") && !input.value.trim()) {
        setStatus((mode === "create" ? "Create" : "Edit") + " needs a written instruction first");
        input.focus();
        return;
      }

      const tool = menu.querySelector('[data-studio-tool="' + toolId + '"]');
      if (!tool) {
        setStatus("OAP Studio control unavailable · no execution claimed");
        return;
      }
      controls.querySelectorAll(".smi-interaction-tab:not(.smi-character-lock)").forEach((button) => {
        button.classList.toggle("active", button.dataset.mediaMode === mode);
      });
      tool.click();
    };

    [
      ["create-mode-button", "create"],
      ["edit-mode-button", "edit"],
      ["refine-mode-button", "refine"],
      ["animate-mode-button", "animate"]
    ].forEach(([id, mode]) => {
      const button = controls.querySelector("#" + id);
      button.dataset.mediaMode = mode;
      button.addEventListener("click", () => run(mode));
    });

    const useAsReference = (card) => {
      if (!card || card.dataset.characterReferenceControl === "1") return;
      const image = card.querySelector("img.smi-studio-image");
      if (!image || !image.src) return;
      card.dataset.characterReferenceControl = "1";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "action-btn smi-use-character-reference";
      button.textContent = "🔒 Use as character reference";
      button.addEventListener("click", () => {
        if (typeof selectedImage === "undefined") {
          setStatus("Reference image state unavailable · no lock claimed");
          return;
        }
        selectedImage = image.src;
        if (previewImg) previewImg.src = image.src;
        if (previewName) previewName.textContent = "Studio character reference";
        if (preview) preview.classList.add("show");
        setCharacterLock(true);
        input.dispatchEvent(new Event("input", {bubbles: true}));
        setStatus("Character reference loaded · Same Character locked");
      });
      card.append(button);
    };

    document.querySelectorAll(".smi-studio-artifact").forEach(useAsReference);
    const observer = new MutationObserver((records) => {
      for (const record of records) {
        record.addedNodes.forEach((node) => {
          if (!(node instanceof Element)) return;
          if (node.matches?.(".smi-studio-artifact")) useAsReference(node);
          node.querySelectorAll?.(".smi-studio-artifact").forEach(useAsReference);
        });
      }
    });
    const messages = document.getElementById("messages");
    if (messages) observer.observe(messages, {childList: true, subtree: true});

    window.OAP_SMI_MEDIA_CONTROLS = Object.freeze({
      version: "1.0",
      create: true,
      edit: true,
      refine: true,
      animate: true,
      characterLock: true,
      duplicateStudioEngine: false
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootMediaControls, {once: true});
  } else {
    bootMediaControls();
  }
})();