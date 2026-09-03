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

  document.querySelectorAll("[data-oap-plus]").forEach((button) => {
    button.addEventListener("click", () => {
      const composer = button.closest("form") || button.closest(".linkup-composer-wrap");
      const tray = composer?.querySelector("[data-oap-tray]");
      if (!tray) return;
      const open = tray.dataset.open !== "true";
      tray.dataset.open = open ? "true" : "false";
      button.setAttribute("aria-expanded", open ? "true" : "false");
    });
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
  if (first && !panels.some((panel) => panel.dataset.active === "true")) {
    openPanel(first.dataset.linkupThread);
    app.dataset.chatOpen = "false";
  }
})();
