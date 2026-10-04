(() => {
  const app = document.querySelector("[data-linkup-app]");
  if (!app) return;

  const buttons = Array.from(document.querySelectorAll("[data-linkup-thread]"));
  const panels = Array.from(document.querySelectorAll("[data-linkup-panel]"));
  const search = document.querySelector("[data-linkup-search]");

  const openPanel = (id) => {
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
    activePanel?.querySelector("textarea")?.focus({ preventScroll: true });
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
        : intent === "ptt"
          ? "[data-oap-ptt-control]"
          : "";
    const control = selector ? panel.querySelector(selector) : null;
    if (!control) return;
    control.scrollIntoView({ block: "center", behavior: "smooth" });
    control.focus({ preventScroll: true });
  });
})();
