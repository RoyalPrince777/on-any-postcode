// Public feature search filters visible OAP destination cards, never private people data.
(() => {
  "use strict";
  const field = document.querySelector("[data-oap-public-filter]");
  const note = document.querySelector("[data-oap-public-search-note]");
  if (!field || !note) return;
  const cards = Array.from(document.querySelectorAll("[data-public-filter-item]"));
  field.addEventListener("input", () => {
    const term = field.value.trim().toLocaleLowerCase();
    let showing = 0;
    cards.forEach(card => {
      const match = !term || (card.dataset.publicFilterItem || "").toLocaleLowerCase().includes(term);
      card.hidden = !match;
      if (match) showing += 1;
    });
    note.textContent = !term
      ? "Public sections only. Finding people requires sign-in."
      : showing
        ? showing + " matching public sections. People require sign-in."
        : "No matching public sections. Individual people are not searched here.";
  });
})();
