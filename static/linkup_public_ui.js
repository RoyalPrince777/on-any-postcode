// Public feature search filters visible OAP destination cards, never private people data.
(() => {
  "use strict";
  const field = document.querySelector("[data-oap-public-filter]");
  const note = document.querySelector("[data-oap-public-search-note]");
  if (!field || !note) return;
  const cards = Array.from(document.querySelectorAll("[data-public-filter-item]"));
  const secondary = document.querySelector("[data-linkup-secondary]");
  field.addEventListener("input", () => {
    const term = field.value.trim().toLocaleLowerCase();
    let showing = 0;
    cards.forEach(card => {
      const match = !term || (card.dataset.publicFilterItem || "").toLocaleLowerCase().includes(term);
      card.hidden = !match;
      if (match) showing += 1;
    });
    // Search also reveals matching public cards in the collapsed More section.
    // It never queries private people, messages, location or certification records.
    if (term && secondary && cards.some(card => !card.hidden && secondary.contains(card))) {
      secondary.open = true;
    }
    note.textContent = !term
      ? "Search public OAP sections. People require sign-in."
      : showing
        ? showing + " matching public sections. People require sign-in."
        : "No matching public sections. Individual people are not searched here.";
  });
  field.addEventListener("keydown", event => {
    if (event.key === "Escape" && field.value) {
      field.value = "";
      field.dispatchEvent(new Event("input", { bubbles: true }));
      event.preventDefault();
    }
  });
})();
