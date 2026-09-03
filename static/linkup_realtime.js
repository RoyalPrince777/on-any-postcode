(() => {
  "use strict";

  const composers = document.querySelectorAll("[data-oap-link-composer]");

  composers.forEach((composer) => {
    const plus = composer.querySelector("[data-oap-plus]");
    const tray = composer.querySelector("[data-oap-tray]");
    const textarea = composer.querySelector("textarea");

    if (plus && tray) {
      plus.addEventListener("click", () => {
        const nextOpen = tray.getAttribute("data-open") !== "true";
        tray.setAttribute("data-open", String(nextOpen));
        plus.setAttribute("aria-expanded", String(nextOpen));
      });
    }

    if (textarea) {
      textarea.addEventListener("input", () => {
        textarea.style.height = "auto";
        const boundedHeight = Math.min(textarea.scrollHeight, 144);
        textarea.style.height = `${boundedHeight}px`;
      });
    }
  });

  document.querySelectorAll("[data-runtime-locked]").forEach((control) => {
    control.addEventListener("click", (event) => {
      event.preventDefault();
    });
  });
})();
