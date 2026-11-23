(() => {
  const app = document.querySelector("[data-linkup-app]");
  if (!app) return;

  const buttons = Array.from(document.querySelectorAll("[data-linkup-thread]"));
  const panels = Array.from(document.querySelectorAll("[data-linkup-panel]"));
  const search = document.querySelector("[data-linkup-search]");

  const openPanel = (id, { focusComposer = true } = {}) => {
    buttons.forEach((button) => {
      const active = button.dataset.linkupThread === id;
      button.dataset.active = active ? "true" : "false";
      button.setAttribute("aria-selected", active ? "true" : "false");
    });
    panels.forEach((panel) => {
      panel.dataset.active = panel.dataset.linkupPanel === id ? "true" : "false";
    });
    app.dataset.chatOpen = "true";
    window.dispatchEvent(new CustomEvent("oap:linkup-engaged", { detail: { panel: id } }));
    const activePanel = panels.find((panel) => panel.dataset.linkupPanel === id);
    if (focusComposer) activePanel?.querySelector("textarea")?.focus({ preventScroll: true });
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => openPanel(button.dataset.linkupThread));
  });

  document.querySelectorAll("[data-linkup-back]").forEach((button) => {
    button.addEventListener("click", () => {
      app.dataset.chatOpen = "false";
    });
  });

  document.querySelectorAll("[data-linkup-new]").forEach((button) => {
    button.addEventListener("click", () => openPanel("new"));
  });

  if (search) {
    search.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      buttons.forEach((button) => {
        const haystack = (button.dataset.search || button.textContent || "").toLowerCase();
        button.hidden = Boolean(query) && !haystack.includes(query);
      });
    });
  }


  // Mobile chat is a separate panel; a hash alone cannot reveal it.
  // Keep Link Ups and Now in the list, and reveal the correct panel for
  // Ring, Incoming and More without enabling any locked call or chat control.
  document.querySelector('[aria-label="Link Up private menu"]')?.addEventListener("click", (event) => {
    const link = event.target.closest('a[href^="#linkup-"]');
    if (!link) return;
    const targetId = link.getAttribute("href");
    if (!["#linkup-ring", "#linkup-incoming", "#linkup-more"].includes(targetId)) return;
    const target = document.querySelector(targetId);
    if (!target) return;
    event.preventDefault();
    const active = panels.find((panel) => panel.dataset.active === "true")
      || panels.find((panel) => panel.dataset.linkupPanel === "new")
      || panels[0];
    if (active) openPanel(active.dataset.linkupPanel, { focusComposer: false });
    if (targetId === "#linkup-more") target.open = true;
    window.requestAnimationFrame(() => {
      target.scrollIntoView({ block: "start", behavior: "auto" });
      const focusTarget = targetId === "#linkup-more" ? target.querySelector("summary") : target;
      if (focusTarget) {
        if (focusTarget === target) focusTarget.setAttribute("tabindex", "-1");
        focusTarget.focus({ preventScroll: true });
      }
    });
  });

  const first = buttons.find((button) => button.dataset.active === "true") || buttons[0];
  const hasActivePanel = panels.some((panel) => panel.dataset.active === "true");
  if (first && !hasActivePanel) {
    openPanel(first.dataset.linkupThread);
    app.dataset.chatOpen = "false";
  } else if (!first && panels.some((panel) => panel.dataset.linkupPanel === "new")) {
    openPanel("new");
  }

  const intent = (app.dataset.linkupIntent || "").trim();
  if (!intent) return;

  const activePanel = () => panels.find((panel) => panel.dataset.active === "true") || null;
  window.requestAnimationFrame(() => {
    const panel = activePanel();
    if (!panel) return;
    if (intent === "message") {
      panel.querySelector("textarea")?.focus({ preventScroll: true });
      return;
    }
    const selector =
      intent === "link-call"
        ? '[data-oap-call-control][data-call-mode="face_up"]'
        : "";
    const control = selector ? panel.querySelector(selector) : null;
    if (!control) return;
    control.scrollIntoView({ block: "center", behavior: "smooth" });
    control.focus({ preventScroll: true });
  });
})();
