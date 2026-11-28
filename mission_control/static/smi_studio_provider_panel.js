/* Canonical SMI Studio provider explorer. Never sends a prompt, media or API key. */
(() => {
  "use strict";
  const root = document.getElementById("oap-studio-command");
  if (!root) return;

  const q = (selector) => root.querySelector(selector);
  const modelGrid = q("#oap-studio-model-grid");
  const task = q("#oap-studio-task");
  const aspect = q("#oap-studio-aspect");
  const seconds = q("#oap-studio-seconds");
  const brief = q("#oap-studio-brief");
  const output = q("#oap-studio-evidence");
  const modelDocs = q("#oap-studio-model-docs");
  const refreshButton = q("#oap-studio-refresh");
  const preflightButton = q("#oap-studio-preflight");
  const copyButton = q("#oap-studio-copy");
  const ownerRights = q("#oap-studio-rights");
  const subjectConsent = q("#oap-studio-consent");
  const remoteApproved = q("#oap-studio-remote");
  const csrf = document.querySelector('meta[name="oap-csrf-token"]')?.content || "";

  let models = [];
  let selected = null;
  const endpoints = Object.freeze({
    catalogue: "/mission/studio/providers",
    preflight: "/mission/studio/providers/preflight",
    canonicalStudio: "/mission/ollama"
  });
  const labels = Object.freeze({
    image: "Generate image",
    edit: "Edit / preserve reference",
    video: "Generate video",
    animate: "Animate reference",
    voice: "Generate speech",
    dub: "Dub authorised audio",
    composite: "Local composition",
    graphics_engineering: "Graphics engineering", generate_mesh: "Generate 3D mesh",
    texture_mesh: "Texture mesh", rig_mesh: "Rig character", facial_animation: "Facial animation",
    bake_materials: "Bake PBR materials", optimize_mesh: "Optimize GLB", validate_mesh: "Validate GLB",
    render_check: "Device render check", visual_reference: "Visual reference"
  });
  const iconFor = Object.freeze({
    image: "✦", video: "🎬", voice: "🎙", editing: "◈", "3d": "◇", animation: "◉", engineering: "⚙"
  });

  function show(message, state = "unknown") {
    output.dataset.state = state;
    output.textContent = message;
  }
  function taskList(model) {
    task.replaceChildren();
    for (const id of model.tasks) {
      const option = document.createElement("option");
      option.value = id;
      option.textContent = labels[id] || id;
      task.append(option);
    }
    seconds.disabled = !model.tasks.some(x => x === "video" || x === "animate");
  }
  function selectModel(id) {
    selected = models.find(x => x.id === id) || models[0] || null;
    if (!selected) return;
    for (const button of modelGrid.querySelectorAll("[data-provider-id]")) {
      button.setAttribute("aria-pressed", String(button.dataset.providerId === selected.id));
    }
    taskList(selected);
    const docs = selected.docs;
    modelDocs.hidden = !(typeof docs === "string" &&
      (docs.startsWith("https://") || docs.startsWith("/mission/")));
    if (!modelDocs.hidden) modelDocs.href = docs;
    show(
      selected.name + " · " + selected.state.replaceAll("_", " ") + ".\n" +
      selected.note + "\n" +
      "This panel cannot start a render, make a payment, or transfer private files.",
      "blocked"
    );
  }
  function renderModels() {
    modelGrid.replaceChildren();
    models.forEach((model) => {
      const button = document.createElement("button");
      button.className = "oap-studio-model";
      button.type = "button";
      button.dataset.providerId = model.id;
      button.setAttribute("aria-pressed", "false");
      const glyph = document.createElement("span");
      glyph.setAttribute("aria-hidden", "true");
      glyph.textContent = iconFor[model.kind] || "✦";
      const name = document.createElement("b");
      name.textContent = model.name;
      const sub = document.createElement("small");
      sub.textContent = model.maker;
      const chip = document.createElement("span");
      chip.className = "oap-studio-chip";
      chip.textContent = model.adapter_configured ? "Configured · unverified" :
        model.integration === "research_only" ? "Research · not connected" :
        "Source present · unverified";
      button.append(glyph, name, sub, chip);
      button.addEventListener("click", () => selectModel(model.id));
      modelGrid.append(button);
    });
    selectModel(selected?.id || models[0]?.id);
  }
  async function refresh() {
    refreshButton.disabled = true;
    show("Reading Founder-only Studio provider evidence…");
    try {
      const response = await fetch(endpoints.catalogue, {
        credentials: "same-origin", cache: "no-store",
        headers: {"Accept": "application/json"}
      });
      if (!response.ok) throw new Error("catalogue HTTP " + response.status);
      const data = await response.json();
      if (!data.one_canonical_studio || !Array.isArray(data.provider_catalogue)) {
        throw new Error("invalid catalogue contract");
      }
      models = data.provider_catalogue.filter(x =>
        x && typeof x.id === "string" && Array.isArray(x.tasks));
      renderModels();
    } catch (error) {
      models = [];
      selected = null;
      modelGrid.replaceChildren();
      show("UNKNOWN · No catalogue proof could be loaded. Founder sign-in or runtime may be unavailable. No provider enabled.", "unknown");
    } finally {
      refreshButton.disabled = false;
    }
  }
  async function preflight() {
    if (!selected) return show("Select a provider after loading the catalogue.");
    if (!csrf) return show("BLOCKED · CSRF token unavailable. Refresh Founder session.", "blocked");
    const payload = {
      model_id: selected.id,
      task: task.value,
      aspect_ratio: aspect.value,
      duration_seconds: Number(seconds.value),
      owner_rights_confirmed: ownerRights.checked,
      subject_consent_confirmed: subjectConsent.checked,
      remote_approved: remoteApproved.checked
    };
    preflightButton.disabled = true;
    show("Checking rights, privacy, model route and evidence requirements…");
    try {
      const response = await fetch(endpoints.preflight, {
        method: "POST", cache: "no-store", credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
          "X-OAP-CSRF": csrf
        },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.error?.message || "preflight HTTP " + response.status);
      if (data.execution_granted !== false || data.provider_called !== false) {
        throw new Error("unexpected execution-authority response");
      }
      const missing = Array.isArray(data.missing_evidence) ?
        data.missing_evidence.map(x => "• " + String(x).replaceAll("_", " ")) : [];
      show(
        "🟣 Prepared for review · NO render / payment / upload.\n" +
        selected.name + " · " + (labels[data.task] || data.task) + " · " +
        data.aspect_ratio + "\n" +
        "Missing proof:\n" + missing.join("\n"),
        "blocked"
      );
    } catch (error) {
      show("BLOCKED · " + (error.message || "preflight failed") + "\nNo provider called.", "unknown");
    } finally {
      preflightButton.disabled = false;
    }
  }

  refreshButton.addEventListener("click", refresh);
  preflightButton.addEventListener("click", preflight);
  copyButton.addEventListener("click", async () => {
    if (!brief.value.trim()) return show("Write a scene brief before copying it.", "blocked");
    try {
      await navigator.clipboard.writeText(brief.value.trim());
      show("Scene brief copied locally. Open canonical SMI Studio to submit intentionally. No prompt transmitted.", "blocked");
    } catch (_) {
      brief.focus();
      brief.select();
      show("Clipboard unavailable. Brief selected; use Copy on your device. No prompt transmitted.", "blocked");
    }
  });
  refresh();
  window.OAP_SMI_STUDIO_PROVIDER_PANEL = Object.freeze({
    canonicalStudio: endpoints.canonicalStudio,
    executionAuthority: false,
    parallelRenderer: false,
    preflightOnly: true
  });
})();
